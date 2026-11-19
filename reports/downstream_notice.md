<!-- notice run=2026-11-04 since=c445e19 head=1c4ca3c -->
# 상류 → 하류 알림: 2026-11-04 감사 집계 확정

- 생성: 2026-11-20 05:54 · 상류 기준 커밋 `1c4ca3c` (my-geo-audit)
- 스냅샷 날짜(run 날짜, UTC): **2026-11-04**
- 가중평균 **83.97** · 표본 9,700 · 채점 39항목

## 상류 확정 수치 (대조 기준)

| 코드 | 사이트 | run 날짜 | 총점 | 표본 | run 파일 (`data/run_results/`) |
| :-- | :-- | :-- | --: | --: | :-- |
| us | US | 2026-11-04 | 78.57 | 837 | `us_2026-11-04_run_0d6ebeb5122b.json` |
| uk | UK | 2026-11-04 | 84.15 | 960 | `uk_2026-11-04_run_4525d0e0db95.json` |
| de | DE | 2026-11-04 | 85.73 | 769 | `de_2026-11-04_run_9040df11f2dc.json` |
| es | ES | 2026-11-04 | 86.74 | 650 | `es_2026-11-04_run_5bb737eb5bf1.json` |
| ca | CA | 2026-11-04 | 85.54 | 758 | `ca_2026-11-04_run_600e38ec7f50.json` |
| au | AU | 2026-11-04 | 83.87 | 877 | `au_2026-11-04_run_2cab05f082cb.json` |
| br | BR | 2026-11-04 | 85.44 | 868 | `br_2026-11-04_run_d36245f2fc72.json` |
| mx | MX | 2026-11-04 | 86.34 | 762 | `mx_2026-11-04_run_f222623e217e.json` |
| in | IN | 2026-11-04 | 84.87 | 888 | `in_2026-11-04_run_6b73a50a29a5.json` |
| vn | VN | 2026-11-04 | 85.92 | 750 | `vn_2026-11-04_run_44ce100cf7e8.json` |
| be | BE | 2026-09-29 (이전 run 유지) | 80.29 | 690 | `be_2026-09-29_run_6ff488a49b94.json` |
| nl | NL | 2026-09-29 (이전 run 유지) | 80.84 | 792 | `nl_2026-09-29_run_11f2fdd8c5f7.json` |
| global | Global-Site | 2026-11-04 | 81.43 | 99 | `global_2026-11-04_run_564493c5008b.json` |
| hs | HS-Others | 2026-11-04 | 85.1 | 365 | `hs_2026-11-04_run_cd5659bb3b04.json` |

## 직전 알림 이후 상류 변경 (`c445e19..1c4ca3c`, 집계 영향 파일만)

- `96d3b8e` 2026-11-12 feat(audit): 11월 #33·#36 v5c 재판정 + 일반 페이지 인용 기준 확장 + #37 PDP 카테고리 baseline
  - audit_model.py, data/csr_baseline.json, data/item_overrides.json, docs/audit-criteria.md, gen_dashboard_data.py, rule_engine.py, run_render_audit.py
- `b1c5a37` 2026-11-13 fix(audit): US PDP 기능 소개(__NEXT_DATA__)를 #33·#36 문장에 포함 + 수집 상한 4MB
  - analyzer.py, data/item_overrides.json, docs/audit-criteria.md, rule_engine.py

## 하류 처리 절차

1. 위 커밋을 `git -C /Users/dubaba/my-geo-project/my-geo-audit show <커밋>` 으로 읽고, 점수·표본·분류에 영향 있는 규칙을 `scripts/aggregate-readability.mjs` 에 이식한다(테스트 추가). 배경은 상류 `docs/release-notes.md` 맨 위 단위와 `docs/audit-criteria.md` 의 "대시보드 집계 기준 (하류 공유용)".
2. `node scripts/aggregate-readability.mjs --date 2026-11-04 --staging`
3. 위 표와 대조한다 — 국가별 총점 ±0.6점 · 표본 ±10건 안이면 수렴. 벗어나면 빠진 규칙을 찾아 1로 돌아간다.
4. `npx vitest run` 통과 후 커밋 — 제목에 이식한 상류 커밋을 적는다("상류 <커밋> 이식").
5. 공개 승격은 하지 않는다 — 사용자가 `/admin/readability` 에서 검수 후 직접 승격한다.

상류 수치와 맞지 않는데 원인이 상류 쪽이면(분류 오류 등) 고치지 말고 사용자에게 보고한다.
