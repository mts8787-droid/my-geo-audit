"""사업부 삭제 요청 URL — 감사·집계에서 뺀다 (2026-10-26 사용자 지시).

구글 시트 "GEO Monthly Report" 의 'Appendix.Delet URL' 탭(요청자·일시·URL)을
reports/delete_urls.csv 로 내려받고, run_render_audit(감사 대상)·gen_dashboard_data
(집계)가 이 파일을 읽어 해당 URL 을 제외한다.

  /usr/bin/python3 delete_urls.py     # 시트 → reports/delete_urls.csv 갱신
"""
import csv
import os
import urllib.request

from build_hs_contents import SHEET_ID, norm_key

HERE = os.path.dirname(os.path.abspath(__file__))
GID = "1580952762"
EXPORT_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}"
OUT = os.path.join(HERE, "reports", "delete_urls.csv")

_cache = None


def load():
    """삭제 요청 URL 의 비교 키(norm_key) 집합. 파일이 없으면 빈 집합."""
    global _cache
    if _cache is None:
        try:
            with open(OUT, encoding="utf-8") as f:
                _cache = {norm_key(r["url"]) for r in csv.DictReader(f) if r.get("url")}
        except FileNotFoundError:
            _cache = set()
    return _cache


def is_deleted(url):
    return bool(url) and norm_key(url) in load()


def main():
    data = urllib.request.urlopen(EXPORT_URL, timeout=60).read().decode("utf-8")
    rows = [r for r in csv.DictReader(data.splitlines()) if (r.get("URL") or "").strip().startswith("http")]
    seen, recs = set(), []
    for r in rows:
        k = norm_key(r["URL"])
        if k in seen:
            continue
        seen.add(k)
        recs.append({"url": r["URL"].strip(), "requester": r.get("요청", ""), "date": r.get("일시", "")})
    with open(OUT, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["url", "requester", "date"])
        w.writeheader()
        w.writerows(recs)
    print(f"[delete-urls] 시트 {len(rows)}행 → {len(recs)}건 → {OUT}")


if __name__ == "__main__":
    main()
