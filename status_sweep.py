#!/usr/bin/env python3
"""감사 표본의 HTTP 상태·리다이렉트를 훑는다.

감사 본체는 채점이 목적이라 한 건에 수 초가 걸린다. 여기서는 본문을 받지 않고
상태코드와 리다이렉트 사슬만 본다 — 표본 전체를 훑어 죽은 URL·이전된 URL 을
감사 전에 걸러내기 위한 것이다.

출력: reports/status_sweep.json  {url: {status, hops, types, final}}
사용: python3 status_sweep.py [--country us ...] [--concurrency 16] [--only-must]
"""
import argparse, asyncio, csv, io, json, os, sys, time
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "reports", "status_sweep.json")
COUNTRIES = ["us", "uk", "de", "es", "ca", "au", "br", "mx", "in", "vn", "global"]


def sample_for(cc, per_type=100):
    import contextlib, run_render_audit as R
    path = os.path.join(HERE, "reports", f"lg_urls_{cc}.csv")
    urls = [r[0] for r in csv.reader(open(path, encoding="utf-8")) if r and r[0] != "url"]
    must = R._load_must_audit(cc)
    with contextlib.redirect_stdout(io.StringIO()):
        return R._apply_must_audit(R._sample_by_page_type(urls, per_type, must), urls, cc)


async def sweep(urls, concurrency, headers):
    import httpx
    res, stat = {}, Counter()
    sem = asyncio.Semaphore(concurrency)
    t0 = time.time()
    done = 0

    async def one(u):
        nonlocal done
        async with sem:
            rec = {"status": None, "hops": 0, "types": [], "final": u}
            for attempt in range(3):
                try:
                    # 요청마다 새 클라이언트를 쓴다. 클라이언트를 공유하면 h2 커넥션이
                    # 한 번 깨졌을 때 풀에 남아 이후 요청이 전부 LocalProtocolError 로
                    # 죽는다(2026-09-17 실측: 251건 성공 후 13,025건 전량 실패).
                    # HTTP/1.1 로 낮추는 건 답이 아니다 — Akamai 가 403 을 준다.
                    async with httpx.AsyncClient(timeout=20, follow_redirects=True,
                                                 max_redirects=10, http2=True) as client:
                        # GET 이되 본문은 버린다 — LG 서버가 HEAD 에 405/403 을 준다.
                        async with client.stream("GET", u, headers=headers) as r:
                            hist = list(r.history)
                            rec = {"status": r.status_code, "hops": len(hist),
                                   "types": [h.status_code for h in hist], "final": str(r.url)}
                    if rec["status"] not in (403, 429):
                        break
                    await asyncio.sleep(1.5 * (attempt + 1))
                except Exception as e:
                    rec["status"] = f"ERR:{type(e).__name__}"
                    await asyncio.sleep(1.0 * (attempt + 1))
            res[u] = rec
            stat[str(rec["status"])] += 1
            done += 1
            if done % 500 == 0:
                el = time.time() - t0
                print(f"[sweep]   {done}/{len(urls)} · {done/el*60:.0f}건/분 · "
                      f"남은 {(len(urls)-done)/(done/el)/60:.0f}분", flush=True)

    await asyncio.gather(*(one(u) for u in urls))
    return res, stat


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", action="append")
    ap.add_argument("--concurrency", type=int, default=16)
    ap.add_argument("--only-must", action="store_true", help="필수 감사 URL 만")
    args = ap.parse_args()
    sys.path.insert(0, HERE)
    from analyzer import build_request_headers
    import run_render_audit as R

    urls, owner = [], {}
    for cc in (args.country or COUNTRIES):
        got = R._load_must_audit(cc) if args.only_must else sample_for(cc)
        for u in got:
            if u not in owner:
                owner[u] = cc
                urls.append(u)
    print(f"[sweep] {len(urls)}건 · 동시성 {args.concurrency}", flush=True)

    res, stat = asyncio.run(sweep(urls, args.concurrency, build_request_headers()))
    old = {}
    if os.path.exists(OUT):
        try: old = json.load(open(OUT, encoding="utf-8"))
        except Exception: old = {}
    old.update(res)
    json.dump(old, open(OUT, "w", encoding="utf-8"), ensure_ascii=False)

    print(f"\n[sweep] 상태 분포: {dict(stat.most_common())}")
    perm = defaultdict(Counter)
    for u, r in res.items():
        if r["hops"]:
            perm[owner[u]]["301" if all(t in (301, 308) for t in r["types"]) else "302"] += 1
    print(f"[sweep] 리다이렉트: {sum(sum(c.values()) for c in perm.values())}건")
    for cc in sorted(perm):
        print(f"    {cc}: {dict(perm[cc])}")
    print(f"→ {OUT}")


if __name__ == "__main__":
    main()
