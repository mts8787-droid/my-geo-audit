"""그림자 모드 — #33 데피니션 / #35 서머리 / #36 인용 가능 문장을 규칙(정규식)과 LLM(Ollama)이
나란히 판정해 비교한다. 점수에는 반영하지 않는다(파일 출력 전용).

사용:
  /usr/bin/python3 shadow_llm.py --n 200            # 표본 추출 + 판정 (이어하기 지원)
  /usr/bin/python3 shadow_llm.py --report           # 일치율 요약 + 불일치 목록

환경변수: OLLAMA_URL(기본 http://localhost:11434), OLLAMA_MODEL(기본 qwen3:8b)
"""
import argparse
import asyncio
import glob
import hashlib
import json
import os
import random
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime

import httpx

import rule_engine as RE
from analyzer import _fetch_page

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(ROOT, "reports", "shadow_llm")
OUT = os.path.join(OUT_DIR, "pilot.jsonl")
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434").rstrip("/")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen3:8b")
STRATEGIC = ["us", "uk", "de", "es", "ca", "au", "br", "mx", "in", "vn"]
SKIP_TYPES = {"unknown", "about", "support"}
WINDOW = 60          # LLM 에 보여줄 문장 수
FETCH_DELAY = 1.5    # LG 벨로시티 제한: 1~1.5초 간격, 동시성 1

CFG = json.load(open(os.path.join(ROOT, "scoring_config.json")))
PARAMS = {}
for _cat in CFG.values():
    if isinstance(_cat, dict):
        for _c in _cat.get("criteria", []):
            if _c["id"] in ("ai_definition", "ai_summary_box", "ai_citable"):
                PARAMS[_c["id"]] = _c["rule"]

SYS = ("You are a strict content auditor for AI-citation readiness of web pages. "
       "Answer ONLY with the requested JSON. Do not explain.")

PROMPT_CITABLE = """Below are numbered sentences extracted from the main content of a web page ({lang_hint}).
Select the sentences an AI assistant could cite as a concrete, verifiable fact about the product/topic:
specs with numbers and units, named standards or certifications with what they mean, tested/measured results,
statistics, dates, or statements attributed to a named source.
Do NOT select: marketing slogans, vague praise, calls to action, navigation/UI text, promotions,
payment/financing offers, legal boilerplate, or questions.

{numbered}

Return JSON: {{"citable": [<indices of selected sentences>]}}"""

PROMPT_DEF_SUM = """Below is the beginning of the main content of a web page ({lang_hint}), one sentence per line.

{numbered}

Answer two questions:
1. definition: Is there a sentence or short paragraph that DEFINES a term or explains what something is/means
   (e.g. "X is a ...", "X means ...", "X stands for ...")? Give the line index and an exact quote.
2. summary: Is there a block near the top that SUMMARIZES the whole page or lists its key points
   (a TL;DR / overview / key features / at-a-glance style block)? Give the first line index and an exact quote.

Return JSON: {{"definition": {{"found": true|false, "index": <int or null>, "quote": "<text or empty>"}},
"summary": {{"found": true|false, "index": <int or null>, "quote": "<text or empty>"}}}}"""


def _split(text: str):
    return [s.strip() for s in re.split(r"(?<=[.!?。\n])\s+", text) if len(s.strip()) > 5]


def _numbered(sents):
    return "\n".join(f"[{i}] {s[:240]}" for i, s in enumerate(sents))


def _rule(handler_type, rule_id, ctx):
    r = RE._HANDLERS[handler_type](PARAMS[rule_id]["params"], ctx)
    return {"pass": bool(r.get("pass")), "value": r.get("value")}


async def _llm(client, prompt):
    body = {
        "model": OLLAMA_MODEL, "stream": False, "think": False, "format": "json",
        "options": {"temperature": 0, "num_ctx": 8192, "num_predict": 400},
        "messages": [{"role": "system", "content": SYS}, {"role": "user", "content": prompt}],
    }
    r = await client.post(f"{OLLAMA_URL}/api/chat", json=body)
    r.raise_for_status()
    txt = r.json()["message"]["content"]
    try:
        return json.loads(txt)
    except Exception:
        return {"_raw": txt[:300]}


def _sample(n):
    """국가별 최신 전수 런에서 page_type 을 돌려가며 균등 추출(seed 고정)."""
    per_cc = max(1, n // len(STRATEGIC))
    rnd = random.Random(20261017)
    picks = []
    for cc in STRATEGIC:
        fs = sorted(glob.glob(os.path.join(ROOT, "data", "run_results", f"{cc}_2026-*_run_*.json")))
        best = None
        for f in fs:
            d = json.load(open(f))
            if len(d.get("summary") or []) >= 200:
                best = d
        if not best:
            continue
        by_pt = defaultdict(list)
        for it in best["summary"]:
            r = it.get("result") or {}
            pt = (r.get("page_type") or {}).get("id")
            if pt and pt not in SKIP_TYPES and not r.get("page_error"):
                by_pt[pt].append(it["url"])
        for v in by_pt.values():
            rnd.shuffle(v)
        order = sorted(by_pt, key=lambda k: -len(by_pt[k]))
        got = []
        while len(got) < per_cc and any(by_pt.values()):
            for pt in order:
                if by_pt[pt] and len(got) < per_cc:
                    got.append((by_pt[pt].pop(), pt))
        picks += [(cc, u, pt) for u, pt in got]
    return picks


def _done():
    if not os.path.exists(OUT):
        return set()
    return {json.loads(l)["url"] for l in open(OUT) if l.strip()}


async def run(n):
    os.makedirs(OUT_DIR, exist_ok=True)
    picks = [p for p in _sample(n) if p[1] not in _done()]
    print(f"표본 {len(picks)}개 (이미 완료분 제외) / 모델 {OLLAMA_MODEL}", flush=True)
    async with httpx.AsyncClient(timeout=180) as llm:
        for i, (cc, url, pt) in enumerate(picks, 1):
            t0 = datetime.now()
            page = await _fetch_page(url)
            await asyncio.sleep(FETCH_DELAY)
            soup = page.get("soup")
            if soup is None:
                print(f"[{i}/{len(picks)}] {cc} 로딩 실패 {url[-50:]}", flush=True)
                continue
            ctx = {"soup": soup, "page_data": page, "jsonld_types": set(), "jsonld_raw": [],
                   "base_url": "https://www.lg.com", "current_url": page.get("final_url") or url,
                   "csr_ratio_dict": {"status": "skipped"}}
            regex = {
                "definition": _rule("definition_pattern_min", "ai_definition", ctx),
                "summary": _rule("class_id_contains", "ai_summary_box", ctx),
                "citable": _rule("citable_density_min", "ai_citable", ctx),
            }
            text = RE._visible_text(soup, strip_boilerplate=True)
            sents, seen = [], set()
            for s in _split(text):
                if s not in seen:
                    seen.add(s)
                    sents.append(s)
            win = sents[:WINDOW]
            rx_flags = [bool(not RE._CITABLE_NOISE.search(s) and any(p.search(s) for p in RE._CITABLE_PATTERNS))
                        for s in win]
            lang = f"country={cc}"
            rec = {"url": url, "cc": cc, "page_type": pt, "regex": regex,
                   "sentences": win, "regex_flags": rx_flags, "regex_window_count": sum(rx_flags)}
            if win:
                c = await _llm(llm, PROMPT_CITABLE.format(lang_hint=lang, numbered=_numbered(win)))
                idx = [x for x in (c.get("citable") or []) if isinstance(x, int) and 0 <= x < len(win)]
                rec["llm_citable_idx"] = sorted(set(idx))
                d = await _llm(llm, PROMPT_DEF_SUM.format(lang_hint=lang, numbered=_numbered(win[:40])))
                rec["llm_definition"] = d.get("definition")
                rec["llm_summary"] = d.get("summary")
            with open(OUT, "a") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            print(f"[{i}/{len(picks)}] {cc} {pt} rx36={regex['citable']['value']} "
                  f"llm36={len(rec.get('llm_citable_idx', []))} {(datetime.now()-t0).seconds}s", flush=True)


def report():
    rows = [json.loads(l) for l in open(OUT) if l.strip()]
    print(f"페이지 {len(rows)}개\n")
    ag = Counter()
    dis = defaultdict(list)
    for r in rows:
        rx_c = r["regex_window_count"]; lm_c = len(r.get("llm_citable_idx", []))
        k36 = (rx_c >= 5, lm_c >= 5)
        ag["36_same" if k36[0] == k36[1] else "36_diff"] += 1
        if k36[0] != k36[1]:
            dis["36"].append((r["url"], rx_c, lm_c))
        ld = (r.get("llm_definition") or {}).get("found") is True
        k33 = (r["regex"]["definition"]["pass"], ld)
        ag["33_same" if k33[0] == k33[1] else "33_diff"] += 1
        if k33[0] != k33[1]:
            dis["33"].append((r["url"], k33))
        ls = (r.get("llm_summary") or {}).get("found") is True
        k35 = (r["regex"]["summary"]["pass"], ls)
        ag["35_same" if k35[0] == k35[1] else "35_diff"] += 1
        if k35[0] != k35[1]:
            dis["35"].append((r["url"], k35))
    for it in ("33", "35", "36"):
        s, d = ag[f"{it}_same"], ag[f"{it}_diff"]
        print(f"#{it} 페이지 판정 일치 {s}/{s+d} ({100*s/max(1,s+d):.0f}%)")
        for x in dis[it][:8]:
            print("   ", x)
    # 문장 단위(#36)
    tp = fp = fn = tn = 0
    for r in rows:
        li = set(r.get("llm_citable_idx", []))
        for i, f in enumerate(r["regex_flags"]):
            l = i in li
            tp += f and l; fp += f and not l; fn += (not f) and l; tn += (not f) and not l
    print(f"\n#36 문장 단위: 둘 다 {tp} / 규칙만 {fp} / LLM만 {fn} / 둘 다 아님 {tn}")


# ── 2차: 1차 사람 판정 반영 프롬프트 ─────────────────────────────────────────
OUT2 = os.path.join(OUT_DIR, "pilot_r2.jsonl")

PROMPT_CONFIRM = """Each numbered sentence below was flagged by a pattern rule as possibly citable (country={cc}).
Keep a sentence ONLY if an AI assistant could quote it as a concrete, verifiable FACT about a product,
technology or company: a spec/number with its meaning, a named standard or certification, a measured or
tested result, an award/ranking with its source, or a dated factual statement.
REJECT: promotions, discounts, coupons, financing/installment terms, prices lists, menus or navigation text
run together, page headers with dates, contact details, usage instructions, questions, slogans.
Examples — KEEP: "Die Angabe zur Reaktionszeit von 0,03 ms (GtG) bezieht sich auf LG UltraGear-Modelle mit OLED."
KEEP: "Variable refresh rate (VRR) is supported on models 17Z90R and 16Z90R with GPU option only."
REJECT: "Quy định chung: Thời gian trả góp: 3, 6, 9 và 12 tháng."  REJECT: "This is normal and occurs when warm indoor air meets cool air."

{numbered}

Return JSON: {{"keep": [<indices to keep>]}}"""

PROMPT_DEF2 = """Below is the beginning of a web page's main content (country={cc}), one sentence per line.
Find a sentence that DEFINES something: it names a term, product, feature or company and states what it IS
(its category, nature or purpose), e.g. "LG Channels es un servicio gratuito de LG que transmite televisión en directo",
"LG is a world-leading producer of TVs, refrigerators and air conditioners".
NOT a definition: instructions, questions, marketing slogans, legal or payment notices, sentences whose subject is
"this/it/there", or a sentence that only describes a benefit.

{numbered}

Return JSON: {{"found": true|false, "index": <int or null>, "quote": "<exact text or empty>"}}"""

PROMPT_SUM2 = """Below is the beginning of a web page's main content (country={cc}), one sentence per line.
Is there a SUMMARY block near the top: a short block that lists the page's key points or key features
(e.g. "Key Features: ...", "At a glance", "TL;DR", "Características principales") or one paragraph that
summarizes the whole page? A page title, headline, breadcrumb, menu or a single introductory sentence is NOT a summary.

{numbered}

Return JSON: {{"found": true|false, "index": <int or null>, "quote": "<exact text or empty>"}}"""


OUT3 = os.path.join(OUT_DIR, "pilot_r3.jsonl")

# 3차: #33 전용. 2차 예시("LG is a world-leading producer…")가 회사소개 보일러플레이트를 정의문으로 오인시킴(2차 판정 1/12 정답)
# → 예시 제거, 회사소개·제품명+스펙 나열·제목 제외를 명시.
PROMPT_DEF3 = """Below is the beginning of a web page's main content (country={cc}), one sentence per line.
Find ONE sentence that explains WHAT A TERM, TECHNOLOGY OR CONCEPT IS, written for a reader who does not know it
(a dictionary-style explanation of a technology, feature, standard or concept).
NOT a definition: a company profile or "About LG" boilerplate; a product name followed by a list of features or specs;
a page title, headline or breadcrumb; marketing claims or benefits; instructions; questions; legal, payment or
registration notices; sentences whose subject is "this/it/there".
If no sentence qualifies, return found=false. Be strict.

{numbered}

Return JSON: {{"found": true|false, "index": <int or null>, "quote": "<exact text or empty>"}}"""


async def run_r3():
    """3차: #33 정의문 프롬프트만 재판정(오프라인, LG 재요청 없음)."""
    rows = [json.loads(l) for l in open(OUT) if l.strip()]
    done = set()
    if os.path.exists(OUT3):
        done = {json.loads(l)["url"] for l in open(OUT3) if l.strip()}
    rows = [r for r in rows if r["url"] not in done]
    print(f"3차 대상 {len(rows)}페이지 / 모델 {OLLAMA_MODEL}", flush=True)
    async with httpx.AsyncClient(timeout=180) as llm:
        for i, r in enumerate(rows, 1):
            t0 = datetime.now()
            sents = [x for x in r["sentences"] if not x.startswith("html ")]
            rec = {"url": r["url"], "cc": r["cc"], "page_type": r["page_type"], "llm_def3": None}
            if sents:
                rec["llm_def3"] = await _llm(llm, PROMPT_DEF3.format(cc=r["cc"], numbered=_numbered(sents[:40])))
            with open(OUT3, "a") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            print(f"[{i}/{len(rows)}] {r['cc']} {r['page_type']} def3={(rec.get('llm_def3') or {}).get('found')} "
                  f"{(datetime.now()-t0).seconds}s", flush=True)


async def run_r2():
    """1차 저장 문장으로 오프라인 재판정(LG 재요청 없음). 규칙은 현재 rule_engine 기준."""
    rows = [json.loads(l) for l in open(OUT) if l.strip()]
    done = set()
    if os.path.exists(OUT2):
        done = {json.loads(l)["url"] for l in open(OUT2) if l.strip()}
    rows = [r for r in rows if r["url"] not in done]
    print(f"2차 대상 {len(rows)}페이지 / 모델 {OLLAMA_MODEL}", flush=True)
    async with httpx.AsyncClient(timeout=180) as llm:
        for i, r in enumerate(rows, 1):
            t0 = datetime.now()
            sents = [x for x in r["sentences"] if not x.startswith("html ")]
            flags = [bool(not RE._CITABLE_NOISE.search(x) and any(p.search(x) for p in RE._CITABLE_PATTERNS))
                     for x in sents]
            cand = [k for k, f in enumerate(flags) if f]
            rec = {"url": r["url"], "cc": r["cc"], "page_type": r["page_type"], "sentences": sents,
                   "regex_flags": flags, "llm_keep": []}
            if cand:
                num = "\n".join(f"[{k}] {sents[k][:240]}" for k in cand)
                c = await _llm(llm, PROMPT_CONFIRM.format(cc=r["cc"], numbered=num))
                rec["llm_keep"] = sorted({x for x in (c.get("keep") or []) if isinstance(x, int) and x in cand})
            if sents:
                head = _numbered(sents[:40])
                rec["llm_def2"] = await _llm(llm, PROMPT_DEF2.format(cc=r["cc"], numbered=head))
                rec["llm_sum2"] = await _llm(llm, PROMPT_SUM2.format(cc=r["cc"], numbered=head))
            with open(OUT2, "a") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            print(f"[{i}/{len(rows)}] {r['cc']} {r['page_type']} 규칙={len(cand)} 확인={len(rec['llm_keep'])} "
                  f"def={(rec.get('llm_def2') or {}).get('found')} sum={(rec.get('llm_sum2') or {}).get('found')} "
                  f"{(datetime.now()-t0).seconds}s", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=200)
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--r2", action="store_true", help="1차 저장 문장으로 2차 프롬프트 재판정")
    ap.add_argument("--r3", action="store_true", help="3차: #33 정의문 프롬프트만 재판정")
    a = ap.parse_args()
    if a.report:
        report()
    elif a.r2:
        asyncio.run(run_r2())
    elif a.r3:
        asyncio.run(run_r3())
    else:
        asyncio.run(run(a.n))
