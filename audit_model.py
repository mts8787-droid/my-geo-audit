"""
문장 판정 모델(올라마 geo-audit-3b) 호출.

환경변수 AUDIT_MODEL_URL 이 비어 있으면 비활성(Render 등) — 룰 엔진은 정규식 판정으로 돌아간다.
모델은 문장 하나를 받아 {"citable","definition","summary","why"} 를 돌려준다.
시스템 프롬프트는 Modelfile(reports/shadow_llm/train/Modelfile.v2)에 내장돼 있어 문장만 보낸다.
"""
import json
import os

import httpx

MODEL_URL = os.environ.get("AUDIT_MODEL_URL", "").rstrip("/")
MODEL_NAME = os.environ.get("AUDIT_MODEL_NAME", "geo-audit-3b")
MAX_CHARS = 400


class ModelUnavailable(Exception):
    pass


def enabled() -> bool:
    return bool(MODEL_URL)


async def label_sentence(sentence: str, client: httpx.AsyncClient) -> dict:
    """한 문장을 판정한다. 연결 실패·HTTP 오류는 ModelUnavailable, 파싱 실패는 빈 dict."""
    body = {"model": MODEL_NAME, "stream": False, "format": "json",
            "messages": [{"role": "user", "content": sentence[:MAX_CHARS]}],
            "options": {"temperature": 0, "num_predict": 80}}
    try:
        r = await client.post(f"{MODEL_URL}/api/chat", json=body, timeout=60)
        r.raise_for_status()
        txt = r.json()["message"]["content"]
    except (httpx.HTTPError, KeyError, ValueError) as e:
        raise ModelUnavailable(str(e))
    try:
        out = json.loads(txt[txt.index("{"): txt.rindex("}") + 1])
    except Exception:
        return {}
    return {k: out.get(k) for k in ("citable", "definition", "summary", "why")}
