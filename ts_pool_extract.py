"""
트러블슈팅(support_troubleshoot) 문장 풀 추출 — 학습 데이터 보강용 (2026-10-19).
리포트 집계분 트러블슈팅 페이지(국가별 해시순 상위 N)에서 #33·#36 정규식 후보 + 본문 앞부분(모델 탐색 구간)
+ 무작위 본문 문장을 뽑아 라벨링 배치(batches_ts/bNN.jsonl)로 쓴다. 기존 dataset_v1 문장과 중복은 제외.
  /usr/bin/python3 ts_pool_extract.py [--per-country 30] [--per-page 25] [--delay 1]
"""
import argparse, asyncio, json, os, random, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analyzer import _fetch_page, _extract_json_ld
from rule_engine import _eval_definition_pattern_min, _eval_citable_density_min
from gen_dashboard_data import pick_latest_runs, counted_results, current_page_type, RUNS

ap = argparse.ArgumentParser()
ap.add_argument("--per-country", type=int, default=30)
ap.add_argument("--per-page", type=int, default=25)
ap.add_argument("--delay", type=float, default=1.0)
ap.add_argument("--batch", type=int, default=200)
a = ap.parse_args()
random.seed(7)
T = "reports/shadow_llm/train"
CC = "us uk de es ca au br mx in vn".split()

def norm(t): return re.sub(r"\s+", " ", t).strip().lower()
seen = {norm(json.loads(l)["text"]) for l in open(f"{T}/dataset_v1.jsonl")}
pilot_urls = {json.loads(l)["url"] for l in open("reports/shadow_llm/pilot.jsonl")}

targets = []
for cc in CC:
    date, fn = pick_latest_runs()[cc]
    res, _ = counted_results(json.load(open(os.path.join(RUNS, fn))))
    urls = [r["url"] for r in res if current_page_type(r) == "support_troubleshoot" and r["url"] not in pilot_urls]
    targets += [(cc, u) for u in urls[: a.per_country]]
print(f"[ts-pool] 대상 {len(targets)}페이지", file=sys.stderr)

pool, nid = [], 0
async def main():
    global nid
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
        body = d["sentences"]
        defm, citc = set(d["matched"]), set(c["candidates"])
        cand = [s for s in body if s in defm or s in citc][:12]
        head = [s for s in body[:10] if s not in cand]
        rest = [s for s in body[10:] if s not in cand]
        pick = cand + head + random.sample(rest, min(5, len(rest)))
        n_add = 0
        for s in pick[: a.per_page]:
            k = norm(s)
            if len(s) < 15 or k in seen:
                continue
            seen.add(k)
            pool.append({"id": f"t{nid:05d}", "url": url, "cc": cc, "pt": "support_troubleshoot", "text": s,
                         "cand": {"def": s in defm, "cit": s in citc, "idx": body.index(s)}})
            nid += 1; n_add += 1
        print(f"[{i}/{len(targets)}] {cc} 본문 {len(body)}문장 후보 def{len(defm)}/cit{len(citc)} → {n_add}건", file=sys.stderr)
        await asyncio.sleep(a.delay)
asyncio.run(main())

json.dump(pool, open(f"{T}/pool_ts.json", "w"), ensure_ascii=False, indent=0)
os.makedirs(f"{T}/batches_ts", exist_ok=True)
for b in range(0, len(pool), a.batch):
    with open(f"{T}/batches_ts/b{b // a.batch:02d}.jsonl", "w") as f:
        for r in pool[b: b + a.batch]:
            f.write(json.dumps({"id": r["id"], "cc": r["cc"], "pt": r["pt"], "text": r["text"]}, ensure_ascii=False) + "\n")
cd = sum(r["cand"]["def"] for r in pool); cc_ = sum(r["cand"]["cit"] for r in pool)
print(f"[ts-pool] 문장 {len(pool)}건 (정의 후보 {cd}, 인용 후보 {cc_}), 배치 {-(-len(pool) // a.batch)}개 → {T}/batches_ts/")
