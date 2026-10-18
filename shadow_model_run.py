"""
#33·#36 모델 결합 그림자 실행 — pilot 200페이지(10국×20)를 한 번씩 가져와
같은 soup 로 정규식 판정과 모델 판정을 모두 평가해 통과율 변화·소요 시간·모델 호출 수를 기록한다.
  AUDIT_MODEL_URL=http://127.0.0.1:11434 /usr/bin/python3 shadow_model_run.py [--delay 3] [--limit N]
출력: reports/shadow_llm/model_shadow.jsonl, 요약은 stdout.
"""
import argparse, asyncio, json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import audit_model
from analyzer import _fetch_page, _extract_json_ld, _normalize_url
from rule_engine import evaluate_rule_async

ap = argparse.ArgumentParser()
ap.add_argument("--delay", type=float, default=3.0)
ap.add_argument("--limit", type=int, default=0)
ap.add_argument("--out", default="reports/shadow_llm/model_shadow.jsonl")
a = ap.parse_args()
assert audit_model.enabled(), "AUDIT_MODEL_URL 을 설정하세요"

calls = {"n": 0}
_orig = audit_model.label_sentence
async def counted(s, c):
    calls["n"] += 1
    return await _orig(s, c)
audit_model.label_sentence = counted

RULES = {"definition": ("definition_pattern_min", {"min_count": 1, "model_scan_max": 40}),
         "citable":    ("citable_density_min",    {"min_count": 5})}

pages = [json.loads(l) for l in open("reports/shadow_llm/pilot.jsonl")]
if a.limit: pages = pages[:a.limit]
done = set()
if os.path.exists(a.out):
    done = {json.loads(l)["url"] for l in open(a.out) if l.strip()}

async def main():
    out = open(a.out, "a")
    for i, p in enumerate(pages, 1):
        if p["url"] in done: continue
        url, base = _normalize_url(p["url"])
        t0 = time.perf_counter()
        pd = await _fetch_page(url)
        t_fetch = time.perf_counter() - t0
        rec = {"url": p["url"], "cc": p["cc"], "page_type": p["page_type"], "http": pd.get("http_status"),
               "fetch_s": round(t_fetch, 2)}
        if pd.get("soup") is None:
            rec["error"] = pd.get("error") or "no soup"
        else:
            jl = _extract_json_ld(pd)
            ctx = {"soup": pd["soup"], "page_data": pd, "jsonld_types": {t.lower() for t in jl.get("all_types", [])},
                   "jsonld_raw": jl.get("raw", []), "base_url": base, "current_url": pd.get("final_url") or url,
                   "csr_ratio_dict": {"status": "skipped"}}
            for key, (rt, params) in RULES.items():
                r0 = await evaluate_rule_async({"type": rt, "params": {**params, "model": "no"}}, ctx)
                calls["n"] = 0; t1 = time.perf_counter()
                r1 = await evaluate_rule_async({"type": rt, "params": params}, ctx)
                rec[key] = {"regex": r0, "model": r1, "model_s": round(time.perf_counter() - t1, 2), "calls": calls["n"]}
        pd["soup"] = None
        out.write(json.dumps(rec, ensure_ascii=False) + "\n"); out.flush()
        print(f"[{i}/{len(pages)}] {p['cc']} {p['page_type']} fetch {t_fetch:.1f}s "
              + (f"def {rec['definition']['regex']['pass']}->{rec['definition']['model']['pass']} ({rec['definition']['calls']}calls {rec['definition']['model_s']}s) "
                 f"cit {rec['citable']['regex']['pass']}->{rec['citable']['model']['pass']} ({rec['citable']['calls']}calls {rec['citable']['model_s']}s)"
                 if "citable" in rec else f"ERR {rec.get('error')}"), flush=True)
        await asyncio.sleep(a.delay)

asyncio.run(main())
