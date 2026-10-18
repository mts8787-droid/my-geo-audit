#!/bin/bash
# 서포트 트러블슈팅(support_troubleshoot) 전수 비정기 감사 — 전략 10국, 로컬(이 Mac) + 문장 판정 모델.
# 사용자 결정(2026-10-19): 그림자 실행 뒤 트러블슈팅만 전수 조사한다.
# 출력: data/run_results/<cc>_ts_<date>_run_*.json  (--tag ts → 월간 run 과 분리, 대시보드 집계 제외)
# 재개: 같은 날짜에 다시 실행하면 처리한 URL 은 건너뛴다(run_render_audit resume).
# 사용: bash run_support_full_audit.sh [cc ...]   (인자 없으면 10국 전체)
set -u
cd /Users/dubaba/my-geo-project/my-geo-audit || exit 1
PY=/usr/bin/python3
COUNTRIES="${*:-us uk de es ca au br mx in vn}"
export AUDIT_MODEL_URL="${AUDIT_MODEL_URL:-http://127.0.0.1:11434}"
export LOCAL_AUDIT_CONCURRENCY="${LOCAL_AUDIT_CONCURRENCY:-5}"
export AUDIT_RUN_DATE="${AUDIT_RUN_DATE:-$(date -u +%Y-%m-%d)}"
STAMP=$(date +%Y%m%d_%H%M%S)
LOG="data/support_full_audit_${STAMP}.log"
echo "[support-full] start ${STAMP} countries=${COUNTRIES} model=${AUDIT_MODEL_URL}" >> "$LOG"
curl -sf "${AUDIT_MODEL_URL}/api/version" >/dev/null \
  && echo "[support-full] 판정 모델 연결 OK" >> "$LOG" \
  || echo "[support-full] WARN 올라마 미응답 — #33·#36 은 정규식으로 판정됨" >> "$LOG"
for c in $COUNTRIES; do
  echo "===== ${c} $(date +%H:%M:%S) =====" >> "$LOG"
  "$PY" run_render_audit.py "$c" --local --tag ts --types support_troubleshoot \
      --per-type 100000 --no-reuse >> "$LOG" 2>&1 \
    || echo "[support-full] ERROR ${c} 실패 — 다음 국가로 진행" >> "$LOG"
done
echo "[support-full] done $(date +%Y%m%d_%H%M%S)" >> "$LOG"
