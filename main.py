"""GEO Audit Tool — AI Readability Analytics

모델 사용 가이드:
  - 개발(Development): Claude Opus (claude-opus-4-6) — 코드 작성, 리팩토링, 디버깅
  - 운영(Production):  Claude Sonnet (claude-sonnet-4-6) — 코드 리뷰, 모니터링, 경량 작업
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from analyzer import analyze_url
import os
import re
import asyncio
import ipaddress
import socket
from typing import List
from urllib.parse import urlparse

app = FastAPI(title="GEO Audit Tool", version="2.17.0")

# 프로덕션 배포 시 실제 도메인으로 교체하세요
ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

URL_PATTERN = re.compile(r"^(https?://)?[\w\-.]+(\.[\w\-]+)+([\w\-._~:/?#\[\]@!$&'()*+,;=%]*)?$")


def _is_private_url(url: str) -> bool:
    """SSRF 방지: 내부/프라이빗 IP 주소 접근을 차단합니다."""
    try:
        parsed = urlparse(url if url.startswith(("http://", "https://")) else f"https://{url}")
        hostname = parsed.hostname
        if not hostname:
            return True
        # localhost 차단
        if hostname in ("localhost", "127.0.0.1", "::1", "0.0.0.0"):
            return True
        # IP 주소인 경우 private 범위 체크
        try:
            addr = ipaddress.ip_address(hostname)
            return addr.is_private or addr.is_loopback or addr.is_link_local or addr.is_reserved
        except ValueError:
            pass
        # 도메인인 경우 DNS resolve 후 체크
        try:
            resolved = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
            for _, _, _, _, sockaddr in resolved:
                addr = ipaddress.ip_address(sockaddr[0])
                if addr.is_private or addr.is_loopback or addr.is_link_local or addr.is_reserved:
                    return True
        except socket.gaierror:
            pass
        return False
    except Exception:
        return True


class AnalyzeRequest(BaseModel):
    url: str


class AnalyzeBulkRequest(BaseModel):
    urls: List[str]


@app.api_route("/", methods=["GET", "HEAD"])
async def root():
    return FileResponse("static/index.html")


@app.post("/analyze")
async def analyze(request: AnalyzeRequest):
    url = request.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="URL을 입력해주세요.")
    if not URL_PATTERN.match(url):
        raise HTTPException(status_code=400, detail="유효하지 않은 URL입니다.")
    if _is_private_url(url):
        raise HTTPException(status_code=400, detail="내부 네트워크 주소는 분석할 수 없습니다.")
    try:
        result = await analyze_url(url)
        return result
    except Exception:
        raise HTTPException(status_code=500, detail="분석 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.")


@app.post("/analyze-bulk")
async def analyze_bulk(request: AnalyzeBulkRequest):
    urls = [u.strip() for u in request.urls if u.strip()]
    if not urls:
        raise HTTPException(status_code=400, detail="URL을 하나 이상 입력해주세요.")
    if len(urls) > 1000:
        raise HTTPException(status_code=400, detail="한 번에 최대 1000개 URL까지 분석할 수 있습니다.")

    invalid = [u for u in urls if not URL_PATTERN.match(u)]
    if invalid:
        raise HTTPException(status_code=400, detail=f"유효하지 않은 URL: {invalid[0]}")

    private = [u for u in urls if _is_private_url(u)]
    if private:
        raise HTTPException(status_code=400, detail=f"내부 네트워크 주소는 분석할 수 없습니다: {private[0]}")

    sem = asyncio.Semaphore(20)

    async def safe_analyze(url: str):
        async with sem:
            try:
                return {"url": url, "result": await analyze_url(url), "error": None}
            except Exception as e:
                return {"url": url, "result": None, "error": str(e)}

    items = await asyncio.gather(*[safe_analyze(u) for u in urls])

    scores = [i["result"]["score"]["total"] for i in items if i["result"]]
    average = round(sum(scores) / len(scores), 1) if scores else 0

    return {"items": items, "average": average, "total": len(items), "success": len(scores)}


app.mount("/static", StaticFiles(directory="static"), name="static")


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
