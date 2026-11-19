#!/usr/bin/env python3
"""하류(my-geo-newsletter) 전달 알림 생성 → reports/downstream_notice.md

정기 감사·재판정이 끝나 reports/dashboard_data.json 이 확정되면 실행한다
(run_monthly_audit.sh 가 끝에서 자동 실행, 재판정 뒤에는 수동 실행).
하류 세션은 이 파일 하나만 읽고 스냅샷 집계를 이어간다.

담는 것: 확정 수치(국가별 총점·표본·run 파일) + 직전 알림 이후 집계에 영향 있는 상류 커밋.
커밋 범위: 같은 run 날짜로 다시 만들면 직전 알림의 시작점을 유지하고(재판정 누적),
run 날짜가 바뀌면 직전 알림 시점부터. 처음이거나 범위를 바꾸려면 --since <커밋>.
"""
import argparse
import json
import os
import re
import subprocess
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
DASH = os.path.join(HERE, "reports", "dashboard_data.json")
OUT = os.path.join(HERE, "reports", "downstream_notice.md")

# 하류 집계(aggregate-readability.mjs)가 따라와야 하는 상류 파일
WATCH = [
    "gen_dashboard_data.py", "rule_engine.py", "analyzer.py", "page_type.py",
    "audit_model.py", "run_render_audit.py", "delete_urls.py", "csr_baseline.py",
    "scoring_config.json", "data/item_overrides.json", "data/csr_baseline.json",
    "reports/delete_urls.csv", "docs/audit-criteria.md",
]


def git(*args):
    return subprocess.run(["git", *args], cwd=HERE, check=True,
                          capture_output=True, text=True).stdout.strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", help="이 커밋 이후의 상류 변경을 싣는다 (기본: 직전 알림 기준)")
    args = ap.parse_args()

    with open(DASH, encoding="utf-8") as f:
        dash = json.load(f)
    countries = dash["countries"]
    run_date = max(c["date"] for c in countries.values())

    prev = {}
    if os.path.exists(OUT):
        with open(OUT, encoding="utf-8") as f:
            m = re.search(r"<!-- notice run=(\S+) since=(\S+) head=(\S+) -->", f.read())
        if m:
            prev = dict(zip(("run", "since", "head"), m.groups()))
    since = args.since or (prev.get("since") if prev.get("run") == run_date else prev.get("head"))
    if not since:
        raise SystemExit("직전 알림이 없습니다 — --since <하류가 마지막으로 이식한 상류 커밋> 을 주세요")
    head = git("rev-parse", "--short", "HEAD")

    commits = []
    log = git("log", "--reverse", "--date=short", "--format=%h|%ad|%s", f"{since}..HEAD", "--", *WATCH)
    for line in filter(None, log.splitlines()):
        h, date, subject = line.split("|", 2)
        files = git("show", "--name-only", "--format=", h, "--", *WATCH).split()
        commits.append((h, date, subject, files))

    ov = dash["overall"]
    out = [
        f"<!-- notice run={run_date} since={since} head={head} -->",
        f"# 상류 → 하류 알림: {run_date} 감사 집계 확정",
        "",
        f"- 생성: {datetime.now():%Y-%m-%d %H:%M} · 상류 기준 커밋 `{head}` (my-geo-audit)",
        f"- 스냅샷 날짜(run 날짜, UTC): **{run_date}**",
        f"- 가중평균 **{ov['total_avg_weighted']}** · 표본 {ov['sample_total']:,} · "
        f"채점 {dash['criteria']['scored_items']}항목",
        "",
        "## 상류 확정 수치 (대조 기준)",
        "",
        "| 코드 | 사이트 | run 날짜 | 총점 | 표본 | run 파일 (`data/run_results/`) |",
        "| :-- | :-- | :-- | --: | --: | :-- |",
    ]
    for cc, c in countries.items():
        stale = "" if c["date"] == run_date else " (이전 run 유지)"
        out.append(f"| {cc} | {c.get('label', cc)} | {c['date']}{stale} | {c['total_avg']} | "
                   f"{c['sample_size']:,} | `{c.get('run_file', '')}` |")

    out += ["", f"## 직전 알림 이후 상류 변경 (`{since}..{head}`, 집계 영향 파일만)", ""]
    if commits:
        for h, date, subject, files in commits:
            out.append(f"- `{h}` {date} {subject}")
            out.append(f"  - {', '.join(files)}")
    else:
        out.append("- 없음 — 규칙 이식 없이 집계만 하면 된다.")

    out += [
        "",
        "## 하류 처리 절차",
        "",
        "1. 위 커밋을 `git -C /Users/dubaba/my-geo-project/my-geo-audit show <커밋>` 으로 읽고, 점수·표본·분류에 "
        "영향 있는 규칙을 `scripts/aggregate-readability.mjs` 에 이식한다(테스트 추가). "
        "배경은 상류 `docs/release-notes.md` 맨 위 단위와 `docs/audit-criteria.md` 의 "
        "\"대시보드 집계 기준 (하류 공유용)\".",
        f"2. `node scripts/aggregate-readability.mjs --date {run_date} --staging`",
        "3. 위 표와 대조한다 — 국가별 총점 ±0.6점 · 표본 ±10건 안이면 수렴. 벗어나면 빠진 규칙을 찾아 1로 돌아간다.",
        "4. `npx vitest run` 통과 후 커밋 — 제목에 이식한 상류 커밋을 적는다(\"상류 <커밋> 이식\").",
        "5. 공개 승격은 하지 않는다 — 사용자가 `/admin/readability` 에서 검수 후 직접 승격한다.",
        "",
        "상류 수치와 맞지 않는데 원인이 상류 쪽이면(분류 오류 등) 고치지 말고 사용자에게 보고한다.",
        "",
    ]
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    print(f"[downstream-notice] {OUT} — run {run_date}, 상류 변경 {len(commits)}건 ({since}..{head})")


if __name__ == "__main__":
    main()
