from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from analyzer import analyze_url
import os
import re
import asyncio
from typing import List

app = FastAPI(title="GEO Audit Tool", version="2.6.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

URL_PATTERN = re.compile(r"^(https?://)?[\w\-.]+(\.[\w\-]+)+([\w\-._~:/?#\[\]@!$&'()*+,;=%]*)?$")


class AnalyzeRequest(BaseModel):
    url: str


class AnalyzeBulkRequest(BaseModel):
    urls: List[str]


@app.get("/")
async def root():
    return FileResponse("static/index.html")


@app.post("/analyze")
async def analyze(request: AnalyzeRequest):
    url = request.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="URL을 입력해주세요.")
    if not URL_PATTERN.match(url):
        raise HTTPException(status_code=400, detail="유효하지 않은 URL입니다.")
    try:
        result = await analyze_url(url)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
