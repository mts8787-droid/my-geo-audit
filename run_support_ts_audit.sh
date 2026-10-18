#!/bin/bash
# 서포트 트러블슈팅(support_troubleshoot) 비정기 재감사 — 전략 10국, 로컬(이 Mac) + 문장 판정 모델.
# 사용자 결정(2026-10-19): 전수가 아니라 **리포트에 올라간 페이지만** 다시 잰다.
#   대상 = 대시보드가 쓰는 국가별 최신 정식 run(gen_dashboard_data.pick_latest_runs)에서
#   실제 집계에 들어간(counted_results: 제외 규칙 + 타입 상한 100) support_troubleshoot 페이지.
#   사이트맵 재샘플링을 하지 않으므로 정규식 판정(이전 run)과 모델 판정(이번 run)을
#   같은 페이지끼리 비교할 수 있다.
# 출력: data/run_results/<cc>_ts_<date>_run_*.json  (--tag ts → 월간 run 과 분리, 대시보드 집계 제외)
# 재개: 같은 날짜에 다시 실행하면 처리한 URL 은 건너뛴다(run_render_audit resume).
# 사용: bash run_support_ts_audit.sh [cc ...]   (인자 없으면 10국 전체)
set -u
cd /Users/dubaba/my-geo-project/my-geo-audit || exit 1
PY=/usr/bin/python3
COUNTRIES="${*:-us uk de es ca au br mx in vn}"
export AUDIT_MODEL_URL="${AUDIT_MODEL_URL:-http://127.0.0.1:11434}"
export LOCAL_AUDIT_CONCURRENCY="${LOCAL_AUDIT_CONCURRENCY:-5}"
export AUDIT_RUN_DATE="${AUDIT_RUN_DATE:-$(date -u +%Y-%m-%d)}"
STAMP=$(date +%Y%m%d_%H%M%S)
LOG="data/support_ts_audit_${STAMP}.log"
URLDIR=$(mktemp -d)
echo "[support-ts] start ${STAMP} countries=${COUNTRIES} model=${AUDIT_MODEL_URL} urls=${URLDIR}" >> "$LOG"
curl -sf "${AUDIT_MODEL_URL}/api/version" >/dev/null \
  && echo "[support-ts] 판정 모델 연결 OK" >> "$LOG" \
  || echo "[support-ts] WARN 올라마 미응답 — #33·#36 은 정규식으로 판정됨" >> "$LOG"
for c in $COUNTRIES; do
  echo "===== ${c} $(date +%H:%M:%S) =====" >> "$LOG"
  # 리포트(최신 정식 run)에 수록된 support_troubleshoot URL 추출
  "$PY" - "$c" "$URLDIR/$c.txt" >> "$LOG" 2>&1 <<'PYEOF' || { echo "[support-ts] ERROR ${c} URL 추출 실패" >> "$LOG"; continue; }
import json, os, sys
from gen_dashboard_data import pick_latest_runs, counted_results, current_page_type, RUNS
cc, out = sys.argv[1], sys.argv[2]
date, fn = pick_latest_runs()[cc]
doc = json.load(open(os.path.join(RUNS, fn)))
results, _ = counted_results(doc)          # 대시보드 집계에 실제 들어간 페이지(타입 상한 100 적용 후)
urls = [r["url"] for r in results if current_page_type(r) == "support_troubleshoot"]
open(out, "w").write("\n".join(dict.fromkeys(urls)) + "\n")
print(f"[support-ts] {cc}: 리포트 run {fn} ({date}) 집계분 support_troubleshoot {len(urls)}건")
PYEOF
  "$PY" run_render_audit.py "$c" --local --tag ts --urls-file "$URLDIR/$c.txt" --no-reuse >> "$LOG" 2>&1 \
    || echo "[support-ts] ERROR ${c} 실패 — 다음 국가로 진행" >> "$LOG"
done
echo "[support-ts] done $(date +%Y%m%d_%H%M%S)" >> "$LOG"
