# 히로 (Hiro — Dotcom Readability Checker)

만든 사람 D2C디지털마케팅팀 · 운영: D2C마케팅담당

**[열기](https://my-geo-89ft.onrender.com)** — 새 탭에서 열립니다. 외부 사이트라 로그인 없이 열려요. 크롬 확장(KO/EN)도 있어요.

LG.com 페이지를 AI의 눈으로 읽고 채점하는 검수 에이전트예요. ChatGPT·Gemini·Perplexity 같은 AI 검색이 페이지를 잘 읽고 인용할 수 있는 구조인지(AI Readability · GEO 점수)를 항목별로 진단해요.

| 만든 사람 | 분류 | 접근 | 상태 |
| :-- | :-- | :-- | :-- |
| D2C디지털마케팅팀 | D2C마케팅담당 | 외부 서비스 · 크롬 확장 | 운영중 |

## 무엇을 하는 도구인가요

AI 검색(GEO, Generative Engine Optimization) 관점의 **페이지 가독성 검사기**예요. URL을 넣으면 사이트 성능·웹접근성·Basic SEO·스키마 마크업·고인용 콘텐츠·AI Crawlability 6개 카테고리, 39개 항목을 PASS/FAIL로 채점하고 100점 만점 종합 점수(Good · Need Improvement · Poor)를 보여줘요. 매월 전략 10개국(US·CA·UK·DE·ES·BR·MX·AU·VN·IN) LG.com 페이지를 페이지 유형별로 정기 감사하고, 그 결과는 GEO KPI 대시보드의 Readability 지표로 들어가요.

## 이런 분께 필요해요

- LG.com PDP·마이크로사이트를 새로 만들거나 고친 뒤 AI가 잘 읽는지 바로 확인하고 싶은 콘텐츠 담당자
- JSON-LD(Product·Offer·FAQPage·BreadcrumbList 등) 스키마가 제대로 들어갔는지 점검하는 웹 운영 담당자
- GEO KPI 대시보드의 Readability 수치가 왜 낮은지 원인 항목을 찾아야 하는 디지털 마케터
- 법인별 개선 과제를 뽑아 사업부·법인에 전달해야 하는 분

## 무엇을 할 수 있나요

1. **단일 URL 검사** — 페이지 하나를 넣으면 종합 점수, 카테고리별 점수, 항목별 PASS/FAIL과 실패 사유를 보여줘요.
2. **다중 URL 검사** — 한 줄에 하나씩 최대 50개 URL을 한꺼번에 검사하고 평균 GEO 점수와 페이지별 결과를 표로 봐요.
3. **스키마 검사** — 페이지에 들어 있는 JSON-LD 종류와 원문을 확인해요(Schema Only 모드).
4. **SSR/CSR 비교** — 본문 중 AI 크롤러가 자바스크립트 없이 읽을 수 있는 비율을 봐요.
5. **고인용 콘텐츠 판정** — AI가 그대로 인용하기 좋은 정의문·수치 문장이 본문에 있는지 판정해요.
6. **AI Crawlability** — robots.txt·llms.txt·메타 robots·X-Robots-Tag로 AI 봇 접근이 막혀 있지 않은지 확인해요.
7. **크롬 확장** — 지금 보고 있는 페이지를 브라우저에서 바로 채점해요(KO/EN 전환).

## 시작하기

1. 위 「열기」를 누르면 검사 화면이 열려요. 상단에서 **단일 URL** 또는 **다중 URL**을 고릅니다.
2. LG.com URL을 넣고 검사 카테고리를 고른 뒤 실행해요. `https://`가 없으면 자동으로 붙여요.
3. 종합 점수와 항목별 점수를 보고, FAIL 항목의 「상세 보기」에서 실패 사유와 측정값을 확인해요.
4. 페이지를 고친 뒤 다시 검사해 PASS로 바뀌었는지 확인합니다. 브라우저에서 바로 보려면 크롬 확장을 설치해 쓰세요.

## 알아두면 좋아요

- **점수 계산** — 카테고리 가중치 없이 `통과 항목 ÷ 전체 항목 × 100`이에요. 페이지 유형(PDP·마이크로사이트·트러블슈팅 등)에 따라 적용되는 항목이 달라요.
- **리다이렉트** — 따라간 뒤 최종 도착 페이지 내용으로 채점해요.
- **페이지를 못 가져올 때** — 접속이 막히면 항목이 "HTML 파싱 실패"로 표시돼요. 잠시 뒤 다시 검사하세요. 짧은 시간에 너무 많이 돌리면 차단될 수 있어요.
- **정기 감사** — 매월 5일 전략 10개국 LG.com 페이지를 정기 검사하고, 매월 10일 결과를 GEO 대시보드에 올려요. → [Readability 보기](https://my-geo-newsletter.onrender.com/p/GEO-KPI-Dashboard-KO-readability)
- **검수 기준** — 항목별 정의와 판정 기준은 [검수 기준 페이지](https://my-geo-newsletter.onrender.com/p/GEO-Readability-Criteria)에서 볼 수 있어요.

## 문의 · 함께 쓰면 좋은 도구

문의 · D2C디지털마케팅팀

- **GEO 에이전트 (GEO KPI Dashboard)** — ChatGPT·Gemini·Perplexity가 LG 제품을 얼마나 먼저 추천하는지(Visibility)와 Citation·Readability를 주차·국가·제품별로 추적해요. 히로 정기 감사 결과가 Readability 탭에 들어가요. → [열기](https://my-geo-newsletter.onrender.com/p/GEO-KPI-Dashboard-KO)
  - 대시보드에서 「취약」 제품을 찾고 → 히로로 해당 PDP의 FAIL 항목을 확인할 때

## 정보

| | |
| :-- | :-- |
| 만든 사람 | D2C디지털마케팅팀 |
| 분류 | D2C마케팅담당 |
| 접근 | 외부 서비스 · 크롬 확장 |
| 상태 | 운영중 |
| 주소 | https://my-geo-89ft.onrender.com |
| 검수 기준 | https://my-geo-newsletter.onrender.com/p/GEO-Readability-Criteria |

## 이런 말로 찾을 수 있어요

히로 · Hiro · GEO · AI 가독성 · Readability · 페이지 검사 · SEO · 스키마 · JSON-LD · 구조화 데이터 · SSR · CSR · robots.txt · llms.txt · 웹접근성 · PDP 진단 · 크롬 확장 · audit
