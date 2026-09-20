# #36 Citable Sentences — 패턴 확장·일치도 검증 방법론

> 2026-09-20 제정. E-E-A-T 확장 4패턴 등재 때 처음 적용했다.
> 패턴을 추가·수정하려면 아래 두 게이트를 모두 통과해야 한다.

## 원칙

1. **인용 가치 = 검증 가능한 사실 신호.** 수치·단위·제3자 인증·시험/연구 서술처럼
   AI가 근거로 옮겨 적을 수 있는 것만 잡는다.
2. **자사 마케팅 용어 금지.** LG 기술명(ThinQ·QNED 등)이나 `designed to`·
   `engineered for` 류 플러프는 전 페이지에 깔려 있어 변별력을 없앤다.
   이런 표현은 반드시 음성 코퍼스에 넣어 오탐이 아님을 증명해야 한다.
3. **문장 구조로 패턴화.** 키워드 단독이 아니라 "누가/무엇으로 검증했는가"가
   드러나는 구문을 잡는다. 예: `tested` 단독(×) → `tested by|under|against`(○),
   `recommended` 단독(×) → `recommended by <전문가 명사>`(○),
   `proven` 단독(×) → `proven to <효과 동사>`(○).

## 게이트 1 — 코퍼스 일치도 (오프라인, 상시 회귀)

**절차**

1. E-E-A-T 축별로 **양성 예시 문장**을 작성한다 — 경험(실측·시험), 전문성(특허·
   공동개발), 권위(전문가·기관 추천, 연구 인용), 신뢰(임상·과학적 입증).
   - 감사 대상 6개 언어(en·es·de·pt·vi·ko)를 커버한다.
   - **숫자·연도를 넣지 않는다** — 기존 수치 패턴에 얹혀 통과하면 신규 패턴의
     기여를 측정할 수 없다.
2. **음성 예시 문장**을 작성한다 — 마케팅 플러프, UI/커머스 문구, 법률 문구,
   그리고 양성과 한 끗 차이인 함정 문장(`Trusted quality`·`Recommended for
   large families`·`Proven design language`·`Tested styles`).
3. 일치도 측정:
   - **양성 재현율 100%** — 미탐 0건이어야 통과.
   - **음성 오탐 0건** — 신규 패턴뿐 아니라 기존 전체 패턴으로도 0이어야 한다.
4. 통과한 코퍼스는 `tests/test_rule_engine.py::TestCitableEEATCorpus`에 넣어
   **상시 회귀 게이트**로 만든다. 이후 누가 패턴을 조여도/풀어도 테스트가 잡는다.

**2026-09-20 측정 기록**: 양성 27/27 (100%) · 음성 0/23 (기존 18패턴 기준으로도 0).

## 게이트 2 — 실측 검증 (실제 페이지)

코퍼스는 합성 문장이라 실제 LG 본문에서의 동작을 보증하지 않는다. 반드시 실측한다.

**절차**

1. **플립 밴드 표본**: 직전 감사에서 매칭 2~4개(기준 5개 직전)인 페이지를
   국가·타입 섞어 30건 내외 재fetch → 신규 패턴 단독 매칭(기존 패턴 비적중 문장)
   건수와 PASS 전환(플립) 수를 센다. → **점수 영향 추정치.**
2. **양성 대조군** (함정 7): 패턴에 가장 유리한 카테고리를 표적으로 별도 표본.
   일반 표본에서 0이 나와도 대조군 없이 "패턴이 안 먹힌다"고 결론내지 않는다.
   - EEAT 확장 때: TV/모니터 일반 표본 34건은 0이었지만, 세탁기·위생 제품군
     10건에서 14건 적중("Probado por Intertek" 각주) — 패턴은 유효했고
     해당 서술이 특정 카테고리에만 존재하는 것이었다.
3. **정밀도 육안 검증**: 실측에서 잡힌 문장을 전수 출력해 사람이 읽는다.
   인용 가치 없는 문장이 섞이면 해당 alternation을 조이고 1번부터 다시.
4. **노이즈 스팟 체크**: 흔한 UI·법률 문장 시료를 패턴에 직접 통과시켜 확인.
5. 표본 규칙 (함정 6): 국가당 5건 미만 표본으로 국가별 결론을 내지 않는다.
   fetch는 동시성 ≤3 + 지연 1초 이상 (velocity 차단, 함정 2).

**2026-09-20 측정 기록**

| 표본 | 결과 |
| :-- | :-- |
| 플립 밴드 26건 (pdp·support·experience·microsite) | 신규 매칭 0 · 플립 0 |
| 리치(5+ 통과) PDP 8건 | 신규 매칭 0 |
| 표적: 세탁기·공기청정기·스타일러 PDP 10건 | **14건 적중, 전부 정상** (Intertek 시험 각주 — ES/MX/IN) |

## 사후 검증

다음 정기 감사(매월 25일) 후 판정 근거 마이닝으로 재확인한다:
`value` 문자열(`n/total`)을 항목 × 페이지타입으로 집계해 이상 급등·급락을 본다
(`/tmp/fpscan.py` 방식 — HANDOFF §2 참조). 특정 타입 통과율이 갑자기 뛰면
신규 패턴의 오탐을 먼저 의심한다.

## 등재된 E-E-A-T 확장 4패턴 (2026-09-20)

| 축 | 잡는 구조 | 실측 예 |
| :-- | :-- | :-- |
| 경험 E | 실측·시험 수행 — `we tested`·`tested by/under`·`independently tested`·`probado por`·`getestet von`·`testado por`·`được kiểm nghiệm`·`시험 결과` | `*Probado por la entidad independiente Intertek.` |
| 전문성 X | 특허·공동 개발 — `patented`·`patent-pending`·`developed in collaboration with`·`patentado`·`특허` | `The patented Direct Drive system…` |
| 권위 A | 전문가·기관·연구 — `recommended by <전문가>`·`trusted by`·`official partner`·`research shows`·`según un estudio`·`연구에 따르면` | `Recommended by dermatologists…` |
| 신뢰 T | 임상·과학 입증 — `clinically proven`·`proven to <효과>`·`dermatologist-tested`·`klinisch getestet`·`clínicamente probado`·`임상적으로 입증` | `Clinically proven to reduce allergens…` |

**점수 영향**: 현 시점 ~0 (플립 0). LG.com SSR 본문에 EEAT 서술이 세탁기류 시험
각주 외에 거의 없기 때문 — 이것 자체가 콘텐츠 개선 권고 소재다(EEAT 서술을
본문에 늘리면 인용 가능성이 올라가고, 이 지표가 그 개선을 즉시 측정한다).
