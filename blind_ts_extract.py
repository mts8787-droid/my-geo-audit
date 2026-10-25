"""
블라인드 평가용 트러블슈팅 새 문장 (2026-10-21).
학습·검수에 쓴 300페이지(국가별 해시순 상위 30) 다음 페이지에서 뽑아, 어느 모델도·검수자도 본 적 없는 문장만 쓴다.
모델 예측으로 고르지 않는다(정규식 후보·본문 앞부분·무작위) → 모델 중립.
  /usr/bin/python3 blind_ts_extract.py [--skip 30] [--pages 10] [--delay 1] → reports/shadow_llm/train/blind_eval/ts_pool.json
"""
import argparse, asyncio, json, os, random, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analyzer import _fetch_page, _extract_json_ld
from rule_engine import _eval_definition_pattern_min, _eval_citable_density_min
from gen_dashboard_data import pick_latest_runs, counted_results, current_page_type, RUNS

ap = argparse.ArgumentParser()
ap.add_argument("--skip", type=int, default=30)
ap.add_argument("--pages", type=int, default=10)
ap.add_argument("--delay", type=float, default=1.0)
a = ap.parse_args()
random.seed(2110)
T = "reports/shadow_llm/train"; OUT = f"{T}/blind_eval"; os.makedirs(OUT, exist_ok=True)
CC = "us uk de es ca au br mx in vn".split()
def norm(t): return re.sub(r"\s+", " ", t).strip().lower()
seen = {norm(json.loads(l)["text"]) for f in ("dataset_v1.jsonl", "dataset_ts_v1.jsonl") for l in open(f"{T}/{f}")}
targets = []
for cc in CC:
    date, fn = pick_latest_runs()[cc]
    res, _ = counted_results(json.load(open(os.path.join(RUNS, fn))))
    urls = [r["url"] for r in res if current_page_type(r) == "support_troubleshoot"]
    targets += [(cc, u) for u in urls[a.skip: a.skip + a.pages]]
print(f"[blind-ts] 대상 {len(targets)}페이지", file=sys.stderr)
pool = []
async def main():
    for i, (cc, url) in enumerate(targets, 1):
        try:
            pd = await _fetch_page(url)
        except Exception as e:
            print(f"[{i}] {cc} fetch 실패 {e}", file=sys.stderr); continue
        if not pd.get("soup"):
            continue
        jl = _extract_json_ld(pd)
        ctx = {"soup": pd["soup"], "page_data": pd, "jsonld_types": {t.lower() for t in jl.get("all_types", [])},
               "jsonld_raw": jl.get("raw", []), "base_url": url, "current_url": pd.get("final_url") or url}
        d = _eval_definition_pattern_min({"min_count": 1, "_return_sentences": True}, ctx)
        c = _eval_citable_density_min({"min_count": 5, "_return_sentences": True}, ctx)
        body = [s for s in d["sentences"] if len(s) >= 15 and norm(s) not in seen]
        defm, citc = set(d["matched"]), set(c["candidates"])
        groups = {"cand": [s for s in body if s in defm or s in citc], "head": [s for s in body[:10] if s not in defm and s not in citc],
                  "rand": [s for s in body[10:] if s not in defm and s not in citc]}
        for g, n in (("cand", 3), ("head", 2), ("rand", 1)):
            for s in random.sample(groups[g], min(n, len(groups[g]))):
                seen.add(norm(s)); pool.append({"text": s, "cc": cc, "page_type": "support_troubleshoot", "url": url, "group": g})
        print(f"[{i}/{len(targets)}] {cc} 본문 {len(body)} 후보 {len(groups['cand'])}", file=sys.stderr)
        await asyncio.sleep(a.delay)
asyncio.run(main())
json.dump(pool, open(f"{OUT}/ts_pool.json", "w"), ensure_ascii=False, indent=0)
import collections
print(f"[blind-ts] {len(pool)}문장", dict(collections.Counter(p['group'] for p in pool)))
