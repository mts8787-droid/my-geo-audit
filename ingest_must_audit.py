#!/usr/bin/env python3
"""URL 목록을 국가별 must_audit CSV 로 편입한다.

사업부가 주는 필수 감사 URL 은 국가가 섞인 한 덩어리로 온다. 국가 코드를 URL 에서
뽑아 reports/must_audit/<cc>.csv 로 나눠 넣는다. 감사 대상이 아닌 국가는 건너뛴다.

사용: python3 ingest_must_audit.py <url목록파일> [--product TV] [--dry-run]
"""
import argparse
import csv
import os
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
# 감사 대상 10국 + Global. URL 경로 세그먼트 → 우리 국가 코드.
# ca 는 영어 사이트만 감사한다(사용자 결정) — ca_fr 은 대상 아님.
SITE_TO_CODE = {
    "us": "us", "uk": "uk", "de": "de", "es": "es", "ca_en": "ca",
    "au": "au", "br": "br", "mx": "mx", "in": "in", "vn": "vn", "global": "global",
}
FIELDS = ["url", "product", "page_type_hint", "name"]


def site_of(url):
    parts = url.split("/")
    return parts[3] if len(parts) > 3 else ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path", help="URL 목록 파일 (한 줄에 하나)")
    ap.add_argument("--product", default="")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    sys.path.insert(0, HERE)
    from page_type import detect_page_type

    urls, skipped = [], Counter()
    seen = set()
    for line in open(args.path, encoding="utf-8"):
        u = line.strip()
        if not u or not u.startswith("http") or u in seen:
            continue
        seen.add(u)
        code = SITE_TO_CODE.get(site_of(u))
        if not code:
            skipped[site_of(u)] += 1
            continue
        urls.append((code, u))

    by_cc = defaultdict(list)
    for code, u in urls:
        by_cc[code].append(u)

    print(f"[ingest] 입력 {len(seen)} · 편입 대상 {len(urls)} · 제외 국가 {sum(skipped.values())}")
    if skipped:
        print("[ingest] 감사 대상 아님:", dict(skipped.most_common()))

    for cc in sorted(by_cc):
        path = os.path.join(HERE, "reports", "must_audit", f"{cc}.csv")
        old = list(csv.DictReader(open(path, encoding="utf-8"))) if os.path.exists(path) else []
        have = {r["url"] for r in old}
        # URL 목록(CSV)에 실제로 있는지 — 없으면 감사는 하되 경고한다
        src = os.path.join(HERE, "reports", f"lg_urls_{cc}.csv")
        known = {r[0] for r in csv.reader(open(src, encoding="utf-8")) if r} if os.path.exists(src) else set()
        new, unknown = [], 0
        for u in by_cc[cc]:
            # 사이트가 끝 슬래시 없는 URL 을 301 로 슬래시 버전에 보낸다. 목록에 있는
            # 표기로 맞춰 두면 감사 때마다 리다이렉트 한 번을 아끼고, URL 목록과도
            # 같은 키로 대조된다.
            if u not in known and u + "/" in known:
                u = u + "/"
            elif u not in known and u.rstrip("/") in known:
                u = u.rstrip("/")
            if u in have:
                continue
            if u not in known:
                unknown += 1
            pt = detect_page_type(None, u).get("id") or ""
            new.append({"url": u, "product": args.product,
                        "page_type_hint": pt, "name": u.rstrip("/").split("/")[-1]})
        note = f" · URL목록에 없음 {unknown}" if unknown else ""
        print(f"  {cc}: 기존 {len(old)} + 신규 {len(new)} = {len(old)+len(new)}{note}")
        if args.dry_run:
            continue
        with open(path, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=FIELDS)
            w.writeheader()
            w.writerows(old + new)


if __name__ == "__main__":
    main()
