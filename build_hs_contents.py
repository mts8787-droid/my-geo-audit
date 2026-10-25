#!/usr/bin/env python3
"""HS(가전) 콘텐츠 URL 시트 → reports/hs_contents.csv + 감사 대상 반영.

사업부가 관리하는 구글 시트 "GEO Monthly Report" 의 'Appendix.HS Contents URL' 탭
(팀 · 컨텐츠 타입 1 · 채널 · 대상제품군 · GEO 대응 URL · Live 시점 · 컨텐츠 타입 2)을
정규화해 reports/hs_contents.csv 로 저장하고, 감사 국가의 must_audit/<cc>.csv 와
reports/lg_urls_<cc>.csv 에 없는 URL 을 덧붙인다 (2026-10-25 사용자 지시).

분류 규칙(사용자 결정 2026-10-25):
  - page_type: Award Banner·뱃지적용 Gallery → pdp(제품 상세의 어워드/뱃지 노출),
    Microsite → microsite, Experience Article → experience, buying guide → buying_guide,
    installation guide → installation_guide(신설). 시트가 URL 패턴 분류보다 우선한다
    (page_type.detect_page_type 의 hs_contents 오버라이드).
  - 콘텐츠 2뎁스(hs.content_type2): 시트 I열 그대로 — FAQ · LG AI · category page · 신뢰성 ·
    ice solution · fitmax · Experience Article · buying guide · Award Banner · installation guide ·
    뱃지적용 Gallery. HS 콘텐츠에만 있는 분류다.
  - 제품(hs.product): F열 표기를 통일 — WM(wm·wM·WM (F/L)·WM (T/L)) · REF · DW · VCC · Cooking ·
    Dryer · MWO(mwo) · Common. 원문은 product_raw 에 남긴다.

사용: python3 build_hs_contents.py [--csv <export.csv>] [--no-apply]
  기본은 시트의 공개 CSV export 를 내려받는다. --no-apply 는 hs_contents.csv 만 만든다.
"""
import argparse
import csv
import os
import re
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
SHEET_ID = "1v4V7ZsHNFXXqbAWqvyVkgNIeXx188hSZ9l7FDsRYy2Y"
GID = "1858607647"
EXPORT_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}"
OUT = os.path.join(HERE, "reports", "hs_contents.csv")

TYPE1_TO_PAGE_TYPE = {
    "award banner": "pdp",
    "뱃지적용 gallery": "pdp",
    "microsite": "microsite",
    "experience article": "experience",
    "buying guide": "buying_guide",
    "installation guide": "installation_guide",
}
PRODUCT_NORM = {
    "wm": "WM", "wm (f/l)": "WM", "wm (t/l)": "WM",
    "ref": "REF", "dw": "DW", "vcc": "VCC", "cooking": "Cooking",
    "dryer": "Dryer", "mwo": "MWO", "common": "Common",
}
SEG2CC = {"ca_en": "ca", "ca_fr": "ca", "be_fr": "be"}
# 감사 URL 목록·must_audit 을 관리하는 국가. 그 외 국가 URL 은 별도 감사 그룹 `hs`(HS-Others) 로 묶어
# 전부 측정한다(사용자 결정 2026-10-25): reports/lg_urls_hs.csv + must_audit/hs.csv 를 통째로 다시 쓴다.
AUDITED = ["us", "uk", "de", "es", "ca", "au", "br", "mx", "in", "vn", "be", "nl"]
HS_GROUP = "hs"

FIELDS = ["url", "key", "cc", "seg", "page_type", "content_type1", "content_type2",
          "product", "product_raw", "live_date"]


def norm_key(u: str) -> str:
    """비교용 키: https·www 통일, 쿼리/프래그먼트 제거, 끝 슬래시 제거, 소문자."""
    u = u.strip()
    u = re.sub(r"^(?:https?|ps|ttps):?//", "https://", u, flags=re.I)
    u = re.sub(r"^https://(?:www\.)?lg\.com", "https://www.lg.com", u, flags=re.I)
    u = u.split("#", 1)[0].split("?", 1)[0]
    return u.rstrip("/").lower()


def fix_url(u: str):
    """시트 URL 의 흔한 오타를 바로잡는다. lg.com 국가 URL 이 아니면 None."""
    u = u.strip()
    u = re.sub(r"^(?:https?|ps|ttps):?//", "https://", u, flags=re.I)
    u = re.sub(r"^https://(?:www\.)?lg\.com", "https://www.lg.com", u, flags=re.I)
    u = u.split("#", 1)[0].split("?", 1)[0]
    if not re.match(r"https://www\.lg\.com/[a-z_]+/", u, flags=re.I):
        return None
    return u


def seg_of(u: str) -> str:
    return re.match(r"https://www\.lg\.com/([a-z_]+)/", u, flags=re.I).group(1).lower()


def load_rows(path):
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def build(rows):
    out, seen, skipped = [], {}, []
    for r in rows:
        raw = (r.get("GEO 대응 URL") or "").strip()
        t1 = (r.get("컨텐츠 타입 1") or "").strip()
        url = fix_url(raw) if raw else None
        if not url:
            skipped.append((t1, raw))
            continue
        pt = TYPE1_TO_PAGE_TYPE.get(t1.lower())
        if not pt:
            skipped.append((t1, raw))
            continue
        key = norm_key(url)
        if key in seen:
            continue
        seg = seg_of(url)
        praw = (r.get("대상제품군") or "").strip()
        rec = {
            "url": url, "key": key, "cc": SEG2CC.get(seg, seg.split("_")[0]), "seg": seg,
            "page_type": pt, "content_type1": t1,
            "content_type2": (r.get("컨텐츠 타입 2") or "").strip() or t1,
            "product": PRODUCT_NORM.get(praw.lower(), praw or "Common"), "product_raw": praw,
            "live_date": (r.get("Live 시점") or "").strip().strip("."),
        }
        seen[key] = rec
        out.append(rec)
    return out, skipped


def _read_url_col(path):
    try:
        with open(path, encoding="utf-8") as f:
            return [l.strip() for l in f if l.strip() and l.strip() != "url"]
    except FileNotFoundError:
        return []


def apply(recs):
    """감사 국가의 lg_urls_<cc>.csv 와 must_audit/<cc>.csv 에 없는 HS URL 을 덧붙인다."""
    for cc in AUDITED:
        mine = [r for r in recs if r["cc"] == cc]
        if not mine:
            continue
        # URL 목록
        p = os.path.join(HERE, "reports", f"lg_urls_{cc}.csv")
        have = {norm_key(u) for u in _read_url_col(p)}
        add = [r["url"] for r in mine if r["key"] not in have]
        if add:
            with open(p, "a", encoding="utf-8") as f:
                if os.path.getsize(p) and not open(p, "rb").read()[-1:] == b"\n":
                    f.write("\n")
                f.write("\n".join(add) + "\n")
        # 필수 감사
        mp = os.path.join(HERE, "reports", "must_audit", f"{cc}.csv")
        rows = load_rows(mp) if os.path.exists(mp) else []
        mhave = {norm_key(r["url"]) for r in rows if r.get("url")}
        madd = [r for r in mine if r["key"] not in mhave]
        if madd:
            new = not os.path.exists(mp)
            with open(mp, "a", encoding="utf-8", newline="") as f:
                w = csv.DictWriter(f, fieldnames=["url", "product", "page_type_hint", "name"])
                if new:
                    w.writeheader()
                for r in madd:
                    w.writerow({"url": r["url"], "product": r["product"],
                                "page_type_hint": r["page_type"], "name": f"HS:{r['content_type2']}"})
        print(f"  {cc}: HS {len(mine)}건 → lg_urls +{len(add)} · must_audit +{len(madd)}")
    # 감사 국가 밖 → hs 그룹 (파생 파일이라 매번 통째로 다시 쓴다)
    others = [r for r in recs if r["cc"] not in AUDITED]
    with open(os.path.join(HERE, "reports", f"lg_urls_{HS_GROUP}.csv"), "w", encoding="utf-8") as f:
        f.write("url\n" + "".join(r["url"] + "\n" for r in others))
    with open(os.path.join(HERE, "reports", "must_audit", f"{HS_GROUP}.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["url", "product", "page_type_hint", "name"])
        w.writeheader()
        for r in others:
            w.writerow({"url": r["url"], "product": r["product"], "page_type_hint": r["page_type"],
                        "name": f"HS:{r['content_type2']}"})
    from collections import Counter
    print(f"  {HS_GROUP}(그 외 국가): {len(others)}건 → lg_urls_{HS_GROUP}.csv · must_audit/{HS_GROUP}.csv "
          f"({dict(Counter(r['seg'] for r in others).most_common(6))} …)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="", help="시트 CSV export 파일 (기본: 구글 시트에서 내려받음)")
    ap.add_argument("--no-apply", action="store_true")
    a = ap.parse_args()
    if a.csv:
        rows = load_rows(a.csv)
    else:
        data = urllib.request.urlopen(EXPORT_URL, timeout=60).read().decode("utf-8")
        rows = list(csv.DictReader(data.splitlines()))
    recs, skipped = build(rows)
    with open(OUT, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(recs)
    from collections import Counter
    print(f"[hs] 시트 {len(rows)}행 → {len(recs)}건 (중복·불량 {len(rows)-len(recs)}) → {OUT}")
    for t, u in skipped:
        print(f"  건너뜀: {t} | {u[:80]}")
    print("  page_type:", dict(Counter(r["page_type"] for r in recs)))
    print("  content_type2:", dict(Counter(r["content_type2"] for r in recs)))
    print("  product:", dict(Counter(r["product"] for r in recs)))
    aud = Counter(r["cc"] for r in recs if r["cc"] in AUDITED)
    print(f"  감사 국가 분량 {sum(aud.values())}건: {dict(aud)} · 그 외 국가 {len(recs)-sum(aud.values())}건")
    if not a.no_apply:
        apply(recs)


if __name__ == "__main__":
    main()
