# GEO Agent Readability 검수 기준

> 6개 카테고리 41개 채점 항목 + 10월 감사 시행 예정 4항목.
> 점수·통과율은 제외한 **기준 정의 문서**입니다. 실측치는 Readability 대시보드에서 확인하세요.
> 원본: `data/readability/geo-agent-checklist.html` → `scripts/render-criteria.mjs` (별도 리포)
> 이 사본 갱신: 2026-09-20 (9월 오탐 수정 12건 반영)

## 카테고리

| 카테고리 | 채점 항목 | 무엇을 보는가 | scoring_config 키 |
| :-- | :-: | :-- | :-- |
| 사이트 성능 | 6 | 서버가 페이지를 얼마나 빠르고 안전하게 전달하는가 — 전송 계층 | `performance` |
| 웹접근성 | 4 | 사람과 기계가 문서 구조를 읽어낼 수 있는가 | `accessibility` |
| Basic SEO | 8 | 검색엔진이 페이지를 수집하고 표시할 수 있는가 | `seo` |
| 스키마마크업 | 10 | AI가 읽을 수 있는 구조화 데이터가 있는가 | `schema_markup` |
| 고인용 콘텐츠 | 5 | AI가 인용할 만한 서술이 본문에 있는가 | `citable_content` |
| AI Crawlability | 8 | AI 크롤러가 원문을 실제로 가져갈 수 있는가 | `ai_crawlability` |

> 총점은 카테고리 가중치 없이 `통과항목 / 전체항목 × 100`.

---

## 사이트 성능

### #1 — TTFB
- **정의**: 서버 요청 후 첫 번째 응답이 전달되기까지 걸리는 시간
- **PASS**: < 600ms
- **측정방법**: PageSpeed Insights(Lighthouse) `server-response-time`
- **check id**: `perf_ttfb`

### #2 — Compression
- **정의**: 페이지 전송 용량을 줄이기 위한 HTTP 응답 압축 적용 여부
- **PASS**: gzip/br/deflate · **측정방법**: Content-Encoding 헤더 · **check id**: `perf_compression`

### #3 — HTTP Protocol
- **정의**: 페이지 전송에 사용되는 HTTP 통신 프로토콜 버전
- **PASS**: HTTP/2 이상 · **측정방법**: Alt-Svc, :status 헤더 · **check id**: `perf_http_protocol`

### #4 — Cache-Control
- **정의**: 브라우저가 리소스를 일정 기간 저장·재사용할 수 있도록 하는 캐시 유효기간
- **PASS**: max-age 설정 (0 포함) · **측정방법**: Cache-Control 헤더 · **check id**: `perf_cache_control`

### #6 — Redirect Chain
- **정의**: 최종 페이지에 도달하기 전 거치는 URL 리다이렉트 횟수
- **PASS**: ≤ 1회 · **측정방법**: redirectChain 메타데이터 · **check id**: `perf_redirect`

### #7 — Mixed Content
- **정의**: HTTPS 페이지 내 비보안(HTTP) 리소스 포함 여부
- **PASS**: 0개 · **측정방법**: http:// 리소스 탐지 · **check id**: `perf_mixed_content`

### (예정) LCP · CLS · INP
- **PASS**: LCP ≤ 4,000ms / CLS ≤ 0.25 / INP ≤ 500ms
- **측정방법**: PageSpeed Insights (INP는 CrUX 실사용자 데이터)
- **상태**: 10월 감사부터 추가 예정 (데이터 추출 및 검증 진행중)

### (예정) Agentic Browsing
- **정의**: AI Agent와 상호작용하기 위해 사이트가 얼마나 잘 구성되어 있는지 (구글 베타)
- **측정방법**: CLS · llms.txt · 에이전트 접근성 항목 평가
- **상태**: 10월 감사부터 추가 예정. WebMCP audit 3종은 대상 페이지가 Origin Trial 토큰을
  서빙해야 평가되며, 2026-08-26 확인 시 www.lg.com 은 토큰·구현 모두 없어 N/A로 남는다.

---

## 웹접근성

| # | 항목 | PASS | 측정방법 | check id |
| :-: | :-- | :-- | :-- | :-- |
| #9 | Image Alt | 누락 0개 | img[alt] 체크 | `a11y_image_alt` |
| #10 | Semantic HTML | 헤딩+랜드마크 합계 8개 이상 | main(role=main 인정)·nav·header·footer·article·section·aside + h1~h6 합산. `<main>` 필수 아님 (2026-09-19 완화, 유무는 value에 보존) | `a11y_semantic` |
| #11 | Heading Hierarchy | 본문 헤딩 역순 0건 | 첫 헤딩보다 상위 레벨이 뒤에 오는 역순만 실패. GNB·푸터·스티키 바 헤딩 제외, 레벨 점프(h1→h3)는 허용 (2026-09-17 완화) | `a11y_heading_hier` |
| #12 | ARIA Labels | 누락 < 10% | button, input, a 접근성 텍스트 | `a11y_aria_labels` |

---

## Basic SEO

| # | 항목 | PASS | check id |
| :-: | :-- | :-- | :-- |
| #13 | Title | 존재 (30~60자) | `seo_title` |
| #14 | Meta Description | 존재 (120~160자) | `seo_meta_desc` |
| #15 | Canonical | 존재 + 동일 host | `seo_canonical` |
| #16 | H1 | 정확히 1개 | `seo_h1` |
| #17 | Robots | Indexing 허용 | `seo_robots`, `seo_robots_hdr` |
| #18 | Open Graph | og:title + og:image | `seo_open_graph` |
| #19 | Sitemap | 1개월 내 최신화된 Sitemap XML 존재 | `seo_sitemap` |

> #17은 meta robots(`seo_robots`)와 X-Robots-Tag 헤더(`seo_robots_hdr`) 2개로 채점.
>
> **#15는 2026-09-17에 경로 일치(self-referencing)에서 host 일치로 완화**했다 (사용자 결정).
> 같은 제품군 여러 페이지가 대표 1개를 정본으로 선언하는 형태(9/16 실측 434건)는 의도된
> 정규화일 수 있어 감점하지 않는다. canonical 태그가 없거나 외부 도메인이면 여전히 FAIL.

---

## 스키마마크업

> 공통 PASS 조건: JSON-LD 필수요소 모두 존재, 파싱 성공

| # | 스키마 | 필수 요소 | check id |
| :-: | :-- | :-- | :-- |
| #21 | BreadcrumbList | itemListElement, item, name, position | `ai_schema_breadcrumb` |
| #23 | FAQPage | mainEntity | `ai_schema_faq` |
| #24 | CollectionPage | itemList, ListItem | `ai_schema_collection` |
| #25 | Product 풀세트 | name, description, **sku 또는 mpn/gtin13/gtin**, brand, offers.price, offers.availability (ProductGroup+hasVariant 인정) | `ai_schema_product`, `ai_schema_offer` |
| #26 | ImageObject | **url 또는 contentUrl**, **name 또는 caption**, description (uploadDate 요구 삭제 — 이미지에 업로드일은 비표준). **Review·Comment 안의 이미지는 제외** | `ai_schema_image` |
| #27 | VideoObject | **url 또는 contentUrl/embedUrl**, name, description, thumbnailUrl. **Review·Comment 안의 영상은 제외** | `ai_schema_video` |
| #28 | HowTo | HowToSupply / HowToStep | `ai_schema_howto` |
| #29 | Article | headline, author, publisher, articleBody — `support_troubleshoot` 에도 적용(2026-10-24) | `ai_schema_article` |
| #44 | AggregateRating 또는 Review (PDP) | 둘 중 하나라도 JSON-LD 에 존재 — Product 에 연결되지 않은 별도 블록이어도 인정(2026-10-26 사용자 확인). 2026-10-24 활성(사용자 결정, LG PDP 3,147건에 Review 추가됨) | `ai_schema_rating_or_review` |
| #49 | WebSite | — (체크리스트 문서에 대응 행 없음) | `ai_schema_website` |

> #25는 Product와 Offer 2개 항목으로 채점되어 스키마마크업 카테고리는 총 10개.
>
> **대체 필드(2026-10-24)**: 필수 필드는 `sku|mpn|gtin13` 처럼 `|` 로 묶으면 하나만 있어도 충족. schema.org·Google 모두 식별자(sku/mpn/gtin)와
> 영상 주소(url/contentUrl/embedUrl)를 동등하게 보는데, 한 이름만 요구해 LG 가 10월에 추가한 Product 4,045건(mpn 96%)·VideoObject 2,721건(contentUrl 100%)이
> 전부 누락 판정됐다. 사용자 승인으로 4개 룰(#25·#26·#27·#29) 보정.
>
> **리뷰 위젯 오탐 수정(2026-10-26)**: LG PDP 의 Bazaarvoice 리뷰는 `@type` 없는 별도 JSON-LD 블록(`{"review": [...]}`)으로 들어가고,
> 리뷰마다 고객 사진(ImageObject)·영상(VideoObject)이 붙어 있다. 룰이 페이지 전체에서 노드를 찾다 보니 ① #26 통과 PDP **전부**(9개국 2,473건)가
> 고객 리뷰 사진으로 통과했고(Product 의 `image` 는 URL 문자열), ② #27 은 94건이 리뷰 영상만으로 통과했다(나머지는 LG 제품 영상으로 정상).
> → #26·#27 은 Review·Comment 하위 노드 제외(`exclude_within`). 리뷰 자체를 보는 #44 는 별도 블록이어도 인정(사용자 확인).
> 10월 run 은 저장된 JSON-LD 로 재채점(대시보드 §5).

### 게이트 (2026-09 적용) — 해당 콘텐츠가 없는 페이지는 N/A로 분모 제외

콘텐츠가 없는 페이지까지 분모에 넣으면 통과율이 구조적으로 낮게 나와, 아래 항목은
**해당 콘텐츠가 있는 페이지만** 평가한다 (`applies_when` / `applies_to_page_types`).

| # | 게이트 조건 |
| :-: | :-- |
| #23 FAQPage | FAQ 섹션(클래스·헤딩) 존재 + `pdp`·`plp`·`buying_guide`·`microsite` 타입만 |
| #26 ImageObject | 본문 콘텐츠 이미지(figure·article·gallery 등 selector) 존재 — 페이지타입 제한 없음 |
| #27 VideoObject | video 태그 또는 youtube/vimeo iframe 존재 |
| #28 HowTo | 절차(순서 목록·단계 블록 3개 이상) 존재 + `support_troubleshoot` 타입만 |
| #29 Article | 기사 본문 구조(article 등) 존재 + `experience`·`buying_guide`·`microsite`·`support_troubleshoot` 타입 (트러블슈팅은 2026-10-24 추가 — LG 가 help-library 1,908건에 Article 을 넣음) |

> 게이트 적용 후에도 #26·#27·#28·#29는 통과율 0% — 측정 문제가 아니라 실제로 4종
> 스키마를 전혀 쓰지 않는 것이며, LG 전달 리포트의 핵심 개선 항목이다.

---

## 고인용 콘텐츠

| # | 항목 | PASS | 측정방법 | check id |
| :-: | :-- | :-- | :-- | :-- |
| #32 | FAQ Block | 1개 이상 | FAQPage Schema, details/summary, Q&A 패턴 | `ai_faq_block` |
| #33 | Definition Paragraph | 1개 이상 | 정의문 패턴 15종(6개 언어), `dfn`, `abbr` — [패턴 목록](#매칭-패턴-기준). 모델 연결 시 패턴 매칭 문장을 모델이 확인하고, 0건이면 본문 40문장을 모델로 탐색 — [문장 판정 모델](#문장-판정-모델-33-36) | `ai_definition` |
| #34 | Author/Source | 저자 또는 (출처+날짜) | **JSON-LD** `author` 또는 (`datePublished` + `publisher`/`sourceOrganization`/`source`) | `ai_author_source` |
| #35 | Summary Box | 1개 이상 | TL;DR, Key Takeaways, Highlights, Abstract | `ai_summary_box` |
| #36 | Citable Sentences | **5개 이상** · 트러블슈팅·PLP 는 **3개 이상** | 인용 가능 패턴 22종에 걸리는 문장 수 — [패턴 목록](#매칭-패턴-기준). 모델 연결 시 패턴 후보를 모델이 확인한 문장만 센다 — [문장 판정 모델](#문장-판정-모델-33-36). 타입별 기준은 [아래](#36-citable-sentences--인용-가능-문장-22패턴) | `ai_citable` |

> **#34 주의**: HTML `meta author`·본문 byline은 판정에 **사용하지 않는다**. AI가 파싱 가능한
> 구조화 데이터를 요구하는 기준이다. 따라서 통과율 0%는 "저자 표기가 없다"가 아니라
> "JSON-LD에 author/발행정보가 없다"로 읽어야 하고, 개선 액션은 Article/NewsArticle 스키마에
> `author`·`datePublished`·`publisher`를 추가하는 것이다.
>
> #34는 byline 개념이 성립하는 `newsroom`·`press_media` page_type에만 적용되며,
> 그 외 페이지타입은 N/A로 분모에서 빠진다 (2026-09 오탐 수정 — 종전에는
> `experience`·`buying_guide` 628건이 무조건 실패로 잡혀 55.6%였고, 게이트 적용 후 98.4%).

---

## AI Crawlability

| # | 항목 | PASS | 측정방법 | check id |
| :-: | :-- | :-- | :-- | :-- |
| #37 | (JS) HTML Text Ratio | 밀도 ≥ 60% | JS 렌더링 후 텍스트 대비 HTML Text 비중. **Shadow DOM SSR(`<template shadowrootmode>`)은 분자에서 제외** — 비JS 파서 다수(BS·DOMParser·trafilatura)가 본문으로 안 치며(CNX 실측, html5lib만 인식) ChatGPT·Claude류 해석은 비공개라 보수 기준 유지 (2026-10-05 결정). 경량 감사에서는 국가×페이지타입 baseline(`data/csr_baseline.json`)을 넣는다 — 트러블슈팅 baseline 은 2026-10-24 기사 페이지 15건(허브 제외)으로 재측정 | `ai_ssr_ratio` |
| #38 | (JS) HTML Resource | PDP 썸네일 1-3번째 이미지가 HTML에 존재 | PDP HTML 파싱 후 SSR 확인 | `ai_pdp_thumbnails` |
| #39 | (JS) 핵심 element | PDP 핵심 element가 HTML로 존재 | PDP HTML 파싱 후 SSR 확인 | `ai_core_element` |
| #40 | Image File Name | 브랜드·제품 키워드 포함 이미지 ≥ 30% | 파일명 키워드 검증 — logo·icon·sprite 등 장식 파일 제외 | `ai_image_filename` |
| #41 | Status Code (200) | 200 반환 | Status Code | `ai_status_200` |
| #42 | Status Code (Soft 404) | 200 응답 본문에 404 안내 문구 없음 | 문구 판정 (2026-09-17 전환 — LG 404 본문이 2,400~3,200자라 길이로는 판별 불가). 본문 200자 미만은 보조 신호. 독일어 'nicht gefunden werden' 은 'Seite' 와 함께일 때만(2026-10-26 — 트러블슈팅 본문 '채널을 찾지 못할 수 있음' 오탐) | `ai_soft_404` |
| #43 | llms.txt | 존재 | 각 국가별 llms.txt 검증 | `ai_llms_txt` |
| #40* | Summary Content SSR | — (체크리스트 문서에 대응 행 없음) | | `ai_summary_ssr` |


---

## 매칭 패턴 기준

일부 항목은 스키마나 HTML 구조가 아니라 **본문 텍스트·클래스명 패턴**으로 판정한다.
패턴 매칭은 문맥을 보지 못하므로 아래 한계를 전제로 읽어야 한다.

- 판정 대상 텍스트에서 **GNB·헤더·푸터·쿠키 배너·브레드크럼은 제외**한다.
  모든 페이지에 동일하게 들어가 분모를 부풀리기 때문이다.
- 검수 대상이 다국어라 **영어·스페인어·독일어·포르투갈어·베트남어·한국어**를 함께 처리한다.
  (2026-08 확인: 한국어 전용 패턴만 있던 시기에 #33 통과율이 US 외 전 국가 0% 였다)

### #36 Citable Sentences — 인용 가능 문장 (22패턴)

문장 단위로 아래 중 **하나라도** 걸리면 인용 가능으로 센다. 5개 이상이면 통과. **트러블슈팅(`support_troubleshoot`)과
PLP(`plp`)는 3개 이상이면 통과**(룰 파라미터 `min_count_by_type`, 2026-10-26 사용자 결정, 10월 감사부터 적용).

> **트러블슈팅·PLP 를 3개로 두는 이유** — 5개 기준은 PDP 와 에디토리얼 아티클(익스피어리언스·바잉가이드·뉴스룸)처럼
> 본문이 길고 사실·수치·근거가 여러 단락에 걸쳐 나오는 콘텐츠를 전제로 잡은 값이다. 트러블슈팅은 **증상 → 원인 → 해결책**
> 세 요소를 설명하면 끝나는 짧은 콘텐츠이고, 나머지 본문은 조작 안내("버튼을 누르세요")라 인용 대상이 아니다. PLP 는 본문이
> 카테고리 설명문 몇 줄과 상품 목록이라 역시 설명문이 적은 구성이다. 이 두 타입에 5개를 대면 설명문이 제대로 있는 페이지도
> 떨어져, "설명문이 있는 페이지"와 "UI 텍스트만 있는 페이지"를 구분하지 못한다. 3개는 트러블슈팅에서 증상·원인·해결책 각
> 1문장, PLP 에서 카테고리 정의·특징·용도 각 1문장에 해당한다. 10월 재측정(트러블슈팅 7국 2,014페이지) 기준으로 3개 통과율은
> 32~61% 로 다른 타입(56~71%)을 넘지 않는다. AI 답변 엔진이 트러블슈팅·카테고리 페이지를 인용할 때도 2~3문장 스니펫이 보통이다.

| 분류 | 잡는 것 | 예 |
| :-- | :-- | :-- |
| 퍼센트 | 백분율 | `42.7%` |
| 통화 | 금액 | `$3,399.99` · `₩1,200,000` |
| 연도 | 4자리 연도 / 한국어 연도 | `2025` · `2013-2024` · `2025년` |
| 큰 수 | 1,000 이상 | `24,999` |
| 배수 | 배수 표현 | `2x` · `3배` · `2 times` · `veces` · `fach` · `lần` |
| 대규모 수 | 백만·억 단위 | `1 million` · `500만` · `milhões` · `triệu` |
| 물리 단위 | 치수·전기·디스플레이 | `65 inch` · `34"`(인치 축약) · `165Hz` · `kWh` · `°C` · `dB` · `nits` |
| 출처 표현 | 근거 인용문 | `according to` · `~에 따르면` · `según` · `laut` · `theo nghiên cứu` |
| 순위·최초 | 1위/최초 주장 | `world's first` · `No.1` · `top 3` · `đầu tiên` |
| 해상도·화면비 | 픽셀·비율 | `3840 × 2160` · `16:9` |
| 평점 | 별점·점수 | `4.5/5` · `4.5 stars` · `★4.5` |
| 용량·규격 | 저장·전송·성능 | `cu. ft.` · `mAh` · `Mbps` · `fps` · `lbs` · `인치` |
| 기간·주기 | 보증·기간 | `10-year warranty` · `24 months` · `5년 보증` |
| 인증·표준 | 규격 식별자 + 제3자 인증·업계 표준 (2026-09-20 확장) | `ISO 9001` · `ENERGY STAR` · `IP68` · `HDR10+` · `Wi-Fi 6` · `Dolby Vision/Atmos` · `DTS:X` · `FreeSync` · `G-SYNC` · `VESA` · `ClearMR` · `Intertek` · `SGS` · `NSF` · `PROCEL` · `ISEER` · `eARC` · `VRR` — LG 자사 기술명(ThinQ 등)은 변별력 훼손이라 제외 |
| 비교·증감 | 수치 동반 비교 | `up to 30%` · `hasta` · `bis zu` · `40% 더 빠른` |
| 수상·선정 | 어워드 | `CES Innovation Award` · `iF Design Award` · `Red Dot` |
| **EEAT·경험** | 실측·시험 수행 서술 | `we tested` · `tested by/under` · `independently tested` · `probado por` · `getestet von` · `được kiểm nghiệm` |
| **EEAT·전문성** | 특허·공동 개발 | `patented` · `developed in collaboration with` · `patentado` · `특허` |
| **EEAT·권위** | 전문가·기관·연구 | `recommended by dermatologists` · `trusted by` · `official partner` · `research shows` · `según un estudio` |
| **EEAT·신뢰** | 임상·과학 입증 | `clinically proven` · `proven to reduce` · `dermatologist-tested` · `klinisch getestet` |

> **과대 집계 주의.** 문맥을 보지 않으므로 `Copyright © 2012–2025` 같은 저작권 표기,
> 제품명에 포함된 `65 inch`, 가격표 나열도 인용 가능으로 잡힌다. 특히 PDP 는 제품명·
> 스펙·가격이 본문에 반복돼 유리하다. 이 항목은 "구체적 수치가 본문에 5개 이상 있는가"
> 수준의 느슨한 신호로 읽어야 하며, 인용 가치를 직접 보증하지 않는다.
>
> 2026-09-17 에 비율(≥10%) 기준에서 개수(≥5개) 기준으로 바꿨다. 비율은 본문이 길수록
> 불리해 긴 서포트 문서가 짧은 PLP 보다 낮게 나왔기 때문이다.
>
> **EEAT 확장 4패턴(2026-09-20)** 은 숫자 없는 검증·권위 서술을 잡는다. 코퍼스
> (양성 27/음성 23 — 재현율 100%·오탐 0)와 실측 게이트를 거쳐 등재했으며, 절차는
> [citable-pattern-methodology.md](citable-pattern-methodology.md) 참조. 현재 LG SSR
> 본문에 이런 서술이 드물어(세탁기류 Intertek 시험 각주가 대표 사례) 점수 영향은
> 없고, EEAT 콘텐츠가 늘면 즉시 측정에 반영된다.
>
> **노이즈 제외 보강(2026-10-17)** — 사람 판정(그림자 모드 1차, 65문항)에서 규칙만 고른
> 문장 10개 중 8개가 오탐이었다. 무이자 할부(`0% interest`)·쿠폰/바우처·베트남어 할부·증정
> (`trả góp`, `tặng … trị giá`)·할인(`% off`, `descuento`, `dto`)·보도자료 연락처(이메일,
> `Media Contacts`)·공유 버튼(`Share this content`)·JavaScript 안내·상표 고지를 노이즈로
> 뺐다. 판정 정답 기준 정밀도 41% → 88%(정답 문장 손실 0), 실측 80페이지 #36 PASS 48 → 42.
> 같은 날 문서 선언(doctype)과 `<title>` 이 본문 첫 문장으로 섞이던 버그도 고쳤다(199/200 페이지).

### #33 Definition Paragraph — 정의문 (15패턴)

문서 전체에서 아래 중 **하나라도** 걸리면 통과. `dfn`·`abbr` 태그가 있으면 그것으로도 통과.
약관·결제·상표 고지 문장(#36 노이즈 목록과 동일)과 지시대명사 주어(`This is a…`, `Đây là một…`)는
2026-10-17 부터 정의문으로 세지 않는다 — 판정 정답 기준 정밀도 20% → 50%, 실측 80페이지 PASS 46 → 35.

| 언어 | 문형 |
| :-- | :-- |
| 한국어 | `X는 ~이다` · `X란 ~를 말한다` · `~를 의미한다` · `~를 가리킨다` · `~의 약자이다` |
| 영어 | `X is/are a…` · `refers to` · `means` · `stands for` · `is defined as` · `can be defined as` · `consists of` · `is a type of` · `also known as` |
| 영어(동격) | `X, also called Y` · `X (also known as Y)` · `a.k.a.` |
| 스페인어 | `se define como` · `se conoce como` · `consiste en` · `es un tipo de` · `hace referencia a` · `se trata de` |
| 독일어 | `wird als … bezeichnet` · `steht für` · `besteht aus` · `handelt es sich um` · `versteht man` |
| 포르투갈어 | `é um tipo de` · `consiste em` · `é conhecido como` · `trata-se de` · `designa` · `corresponde a` |
| 베트남어 | `là một/các…` · `được gọi là` · `được định nghĩa là` · `viết tắt của` |
| 공통 | 약어 정의 `HDR (High Dynamic Range)` · 질문형 `What is X?` · `Was ist` · `¿Qué es` |

> 독일어·스페인어·포르투갈어의 계사 '기본형'(`ist ein` · `es la` · `é a`)은 2026-09-19에
> **제거**했다. 계사는 일반 문장(`Im letzten Zimmer ist ein…` · `Cuál es la…`)에도 흔해
> 정의문이 아닌 것을 대량으로 잡았다 (오탐 수정으로 58.3% → 47.5%). 확장형·질문형·약어
> 정의는 유지.

### 문장 판정 모델 (#33 · #36)

2026-10-18 도입. #33 정의문·#36 인용 문장은 정규식만으로는 사람 기준과 크게 어긋나서(정규식 #36 의 사람 기준 F1 36),
문장 판정 모델 히로(`hiro`, 올라마)가 최종 판정한다. 문장 하나를 받아 `citable` / `definition` / `summary`
각 y·n 과 판정 이유(한국어 30자)를 돌려준다.

**우선순위 — DOM/셀렉터 규칙이 절대 규칙이다.** #35처럼 특정 요소·class·셀렉터를 지정한 규칙은
모델이 개입하지 않는다. 모델은 텍스트 패턴(정규식)만으로 판정하던 #33·#36 에서만 쓴다.

#### 구축 경위 (2026-10, 10/19 기준)

| 단계 | 내용 | 산출물 |
| :-- | :-- | :-- |
| 1. 기준·조건 정의 | 인용(#36)·정의(#33)·요약(#35)의 y/n 기준과 예외를 **Claude Fable 5.1 과 함께 문서로 정의**. 일반 페이지 기준 + 검수자 보정 2회(배치 1 검수, 모델 불일치 검수 186문장 중 132 재라벨)로 엄격화 | `reports/shadow_llm/train/GUIDELINE.md` |
| 2. 1차 추출·라벨·검수 | 파일럿 200페이지(10국 × 10 페이지타입)에서 5,264문장 추출 → Fable 이 기준대로 라벨 → 검수자가 328문장(불일치 중심) 검수·정정. 기능 설명·권장·스펙 조각·각주·보도자료 상투구는 모두 n | `dataset_v1.jsonl`, `claude_labels.json`, `compare_corrected.txt` |
| 3. 올라마 모델 구성·학습 | Qwen2.5-3B-Instruct 를 mlx LoRA 로 미세조정(v1 라벨만, v2 라벨+이유 → v2 채택). 어댑터를 병합해 올라마 `hiro`(q8_0, 3.3GB, 구 이름 geo-audit-3b) 로 등록. ChatML 템플릿은 `.Messages` 만 사용, `repeat_penalty 1.0`(기본 1.1 은 반복 "n" 억제로 재현율 붕괴). q4_K_M 은 정의 F1 90→80 이라 제외 | `Modelfile.v2`, `lora_q25_3b_v2/`, `ollama_v2/eval.txt` |
| 4. 룰 엔진 결합·그림자 실행 | #33·#36 핸들러에 모델 확인 단계 추가(미연결 시 정규식 폴백). 파일럿 200페이지 그림자 실행: #36 정규식 PASS 93 → 모델 35(통과→실패 58, 역방향 0), #33 80 → 55(양방향). 오류 0 | `shadow_model_run.py`, `reports/shadow_llm/model_shadow.jsonl` |
| 5. 트러블슈팅 재감사 | 리포트 집계분 10국 × 100 페이지 재감사. 모델 효과 평균 −1.5점(UK −6.6, VN −6.5, IN −3.2 — 정규식 100% 통과가 허수였음). 숨은 모달 문장이 본문에 섞이는 오탐 발견·수정 | `run_support_ts_audit.sh`, `data/run_results/<cc>_ts_*.json` |
| 6. 트러블슈팅 기준 추가 | 트러블슈팅 문장(조작 지시·오류코드·원인 설명)에 맞춘 별도 기준을 검수자가 정의(유형 코드 D1·D2·C1·C2·C3·N1·N2·I-A~I-I). 집계분 300페이지에서 2,931문장 추출 → Fable 라벨 → 검수 → v3 학습 예정 | `GUIDELINE_TS.md`, `pool_ts.json`, `batches_ts/`, `out_ts/` |
| 7. 기준 정합화·v3b 학습 | 트러블슈팅 2,931문장을 Fable 라벨 → 검수자 2회 검수(418문장, 라벨 y의 84% 뒤집힘)로 확정. 일반 페이지 전면 재라벨은 검수분 블라인드 대조에서 사람 판정과 맞지 않아(인용 F1 18·67 < 기존 라벨 기반 v2 77) 폐기. 대신 검수자 판정이 엇갈리던 4개 유형을 검수자가 결정(각주 n · 상단 핵심기능 단어 나열 n · 수치 없는 기술 작동 설명 y · 용량 안내 y)하고, 해당 유형만 태깅해 270문장 수정. v3(재라벨 없음)·v3b(결정 반영)를 같은 정답으로 비교 | `dataset_v3.jsonl`, `out_tag/`, `lora_data_v3b/`, `GUIDELINE.md` 끝 "검수자 결정" |
| 8. v3·v3b 평가 → v2 유지 | 같은 정답으로 비교. 사람 검수 문장(일반 268)에서 인용 F1 v2 67 · v3 59 · v3b 61, 정의 F1 60 · 46 · 51. 트러블슈팅 검수 99문장 인용 F1 63 · 23 · 62. v3b는 결정 4유형 문장에서는 앞서지만(정의 F1 80 vs 74) 일반 문장에서 기능 설명을 정의문으로 과잉 판정(정의 예측 y 38 vs 정답 10) → 오탐 위험으로 배포 보류, 운영 모델은 v2(`hiro`) 그대로 | `compare_v3.txt`, `score_v3.py` |

#### 판정 기준 요약

- 공통 전제(인용): **자기완결**(지시어로 시작해 대상을 알 수 없으면 n), **구체성**(수치·조건·메뉴·설정값), **LG 고유성**(범용 상식은 n).
- 인용 y: 기술·기능명과 검증 가능한 구체 사실, 오류코드·표시등의 의미, 제품·증상·구체 원인이 한 문장에 있는 원인 설명, 지원·호환 범위의 완결 진술, 제품·목적·버튼/메뉴/수치가 모두 있는 조작 지시.
- 인용 n: 홍보 문구, 기능 혜택 설명, 권장, 스펙 조각, 각주·시험 조건, 할부·보증·가격, 상담 안내, 대상 없는 단계·범용 지시·연결 조각, 제목·날짜·버튼 텍스트.
- 정의 y: 대상명이 문장 안에 있고 "무엇인지/무엇을 하는지"를 서술(기능·서비스·부품·오류코드·표시등). 회사 소개·각주 붙은 기능 설명·지시어 시작은 n.
- 요약: 트러블슈팅은 항상 n(요약은 #35 DOM 규칙이 판정). 그 외 페이지도 본문 "key features" 목록은 요약이 아니다.
- 각주(*·번호)는 시험·인증 근거가 있어도 n. 제품 페이지 상단 핵심 기능 블록이 단어 나열이면 n. 이름 붙은 기술의 작동 설명은 수치가 없어도 인용·정의 y. 가구·용도별 용량 안내는 인용 y(2026-10-20 검수자 결정).
- 애매하면 n(정밀도 우선).

#### 운영

| 항목 | 모델 연결 시 | 모델 미연결 시 |
| :-- | :-- | :-- |
| #36 | 정규식 후보 문장을 모델이 먼저 확인하고, `min_count` 를 못 채우면 나머지 본문 앞 `model_scan_max`(40)문장도 모델로 훑는다(2026-10-24 — 숫자 없는 원인·증상 설명문이 후보에 안 걸려 모델에 보이지도 않던 문제). y 인 것만 세고 채우면 즉시 중단. 실패 시 hint 에 모델 제외 사유 표시 | 정규식 판정 그대로, value 에 `정규식(모델 미연결)` 표시 |
| #33 | 정규식 매칭 문장을 모델이 확인. 매칭 0건이면 본문 앞 `model_scan_max`(40)문장을 모델로 훑어 정의문 탐색(정규식 OR 모델). `dfn`/`abbr` 이 기준을 채우면 모델 호출 없음 | 정규식 판정 그대로 |

- 활성 조건: 환경변수 `AUDIT_MODEL_URL`(예 `http://127.0.0.1:11434`) + 룰 파라미터 `model: yes`(기본). 모델명 `AUDIT_MODEL_NAME`(기본 `hiro`). 2026-10-19 부터 월간·비정기 감사 모두 이 Mac 로컬에서 모델과 함께 실행한다(Render 미사용).
- 평가셋 1,052문장(사람 검수 268 포함, 엄격 기준) F1: 인용 88.7 · 정의 89.9. 올라마 q8_0 은 mlx 와 1,047/1,052 일치.
- 비용: 문장당 약 1.5초, `OLLAMA_NUM_PARALLEL=8` 로 초당 1.1문장(16 으로 늘려도 동일 — GPU 포화, 2026-10-24 실측). 트러블슈팅 페이지는 평균 25회 호출(정규식 0건 → 40문장 탐색). 정의문이 있으면 5문장 안에 발견된다.
- #36 본문 탐색은 #33 과 같은 앞 40문장이라 메모(같은 문장 재판정 생략)로 추가 비용이 대부분 상쇄된다. 40문장 뒤의 인용문은 여전히 놓친다.
- 같은 문장이 Shadow DOM 과 일반 DOM 양쪽에서 추출되면 한 번만 센다(2026-10-24).
- **트러블슈팅 인용 기준(2026-10-24 사용자 결정)**: 증상의 원인 설명문·증상(동작) 설명문은 인용 y. 버튼·메뉴 지시문은 그대로 n. `GUIDELINE_TS.md` 끝 절.
- 본문 문장 추출에서 nav/header/footer·쿠키·프로모 배너·숨은 모달(`modal`/`dialog`)을 제외한다. US help-library 의 브라우저 안내 모달 문장이 #33 을 67/100 허위 통과시킨 사례(2026-10-19).

### 클래스·선택자 매칭 항목

본문이 아니라 **HTML class/id 또는 CSS 선택자**로 판정하는 항목이다.
마크업이 바뀌면 통과율이 함께 흔들리므로, 급변 시 사이트 개편을 먼저 의심할 것.

| # | 항목 | 매칭 대상 | check id |
| :-: | :-- | :-- | :-- |
| #32 | FAQ Block | class/id 에 `faq` · `q&a` · `qna` · `accordion` · `frequently asked` · `자주 묻는` · `질문` · `answer` — 단, 하단 피드백 위젯(`Was this information helpful?` 등 8개 언어 문구)은 FAQ로 치지 않는다 (2026-09 오탐 수정: 1,596건) | `ai_faq_block` |
| #35 | Summary Box | 둘 중 하나 — ① 헤딩 텍스트에 `At a Glance` · `요약` · `한눈에` 등 ② 요약 블록 selector `p.info-desc, p.description` (아래 참조). ~~class/id 키워드~~ 경로는 2026-09 제거 — 스펙 테이블에도 `class="summary"`가 붙어 오탐 (48.5% → 15.7%) | `ai_summary_box` |
| #39 | PDP Thumbnails | `img[src*=PDPGalleryThumbnail]` · `[class*=Product-ImageGrid] img` · 구 AEM `.c-*` fallback | `ai_pdp_thumbnails` |
| #40 | Core Element | 제품명·가격·이미지 등 선택자 그룹 중 3개 이상 존재 | `ai_core_element` |
| #44 | Image Filename | `img` 파일명에 브랜드·제품 키워드(`lg` · `oled` · `gram` · `thinq` 등 40여 종) 포함 비율 ≥ 30% — `logo` · `icon` · `sprite` 등 장식 파일은 분자·분모 모두 제외 (2026-09: `logo-lg-100-44.svg` 반복 삽입 오탐 수정) | `ai_image_filename` |

> **#35 는 두 경로 중 하나만 걸리면 통과한다.** (class/id 키워드 경로는 2026-09 제거 —
> 스펙 테이블·푸터 등 요약이 아닌 요소에도 `summary` 계열 클래스가 붙어 오탐이 많았다)
>
> | 경로 | 예 |
> | :-- | :-- |
> | 헤딩·라벨 텍스트 | `<h2 class="tit">At a Glance</h2>` — 클래스명과 무관하게 h1~h6·b·strong·dt 텍스트를 본다. `label_tags: p` 로 `<p>Key features</p>` 같은 라벨 태그도 스캔 — **US PDP(MUI 템플릿) 전용 패턴**이라 키워드는 `key features`(영어)만 추가 (2026-09-20). 타 국가 PDP는 자체 템플릿의 진짜 헤딩(`<h3>resumo</h3>` 등)으로 잡힌다. 번역어(`características principales` 등)는 ES/BR 스펙 섹션 헤딩과 겹쳐 오탐 위험이 있어 넣지 않음 |
> | 요약 블록 selector | `<p class="info-desc">` 80자 이상 · `div.c-floating-features`(구 AEM PDP의 Key features 블록 — 라벨이 현지어 `Principais recursos`·`Hauptmerkmale`·`Tính năng chính` 등이라 키워드 대신 selector 로 잡는다, 2026-09-20) |
>
> `At a Glance` 는 2026-09-17 에 다국어(`한눈에`·`de un vistazo`·`auf einen Blick`·
> `em resumo`·`tổng quan`)와 함께 추가했다. 헤딩만 있고 요약 단락 형식이 다른 문서를
> 잡기 위한 것으로, US 트러블슈팅 실측 50% → 66.7% 로 올랐다.
>
> **요약 블록 selector** — LG 서포트 문서는 요약을 `<h2>At a Glance</h2>` 아래
> `<p class="info-desc">` 또는 `<p class="description">` 에 넣는다(두 클래스가 한 요소에
> 같이 붙기도 한다). 클래스명이 `summary` 계열이 아니라 키워드로는 안 잡혀 2026-09-17 에
> selector 판정을 추가했다. 같은 클래스가 요약이 아닌 곳에도 쓰이므로 세 가지로 거른다:
>
> | 필터 | 거르는 것 |
> | :-- | :-- |
> | `idt` 클래스 제외 | `➔ Setting for [2022 WebOS22]` 같은 단계 라벨 |
> | 80자 이상 | `Step 1. Preheating to warm up the indoor unit` (44자) |
>
> (줄 수 필터는 1줄로 완화 — 80자 이상 단문 요약도 인정. `block_min_lines: 1`)
>
> **이 블록이 SSR로 제공되는 곳은 US 트러블슈팅 템플릿뿐이다.** 초기(9/17)에는 "타 국가
> 템플릿에 요약이 없다"고 판단했으나, 2026-09-18 재실측에서 정정됐다: **타 국가도 요약은
> 서버 응답에 들어 있다.** 다만 JSON 이스케이프 형태(`<p class=\"info-desc\"`)라 JS 실행
> 후에만 DOM에 들어간다. UA 5종(Googlebot·GPTBot·ClaudeBot 포함) × 캐시 우회 3방식
> 모두 SSR `<p>` 0개. 2026-09-20 CA·BR 재확인(각 15건 + 봇 UA 3종 18회)에서도 동일.
> 즉 "요약이 없다"가 아니라 **"SSR이 아니라 AI가 못 읽는다"** — 개선 액션은 요약 블록의
> SSR 전환(US 파이프라인과 동일하게)이다.

> #32·#35 는 클래스명에 더해 **heading·강조 태그의 텍스트**(h1~h6, b, strong, dt, summary,
> caption, legend · 60자 이하)도 본다. 클래스명 없이 제목 문구만으로 구성된 블록을
> 놓치던 문제를 2026-08 에 보완했다.

---

## 예외 처리

### 채점에서 제외된 항목 (TBD)

일부 항목은 TBD 로 분류했다 — 자가 콘텐츠 분석 및 기준 세분화, 검수 에이전트
기능 고도화 후 항목 추가 예정.
- **#5 HTML < 100KB** — 측정은 정확하나 lg.com HTML 중앙값이 1,536KB라 실질 통과율 0.0%.
  통과 건의 대부분이 본문 0자인 빈 404 셸이라 지표 방향이 반대였음
- **#8 Render Blocking 0** — 통과율 2.3%로 변별력 없음
- **#44 Sitemap XML** — #19 Sitemap과 rule이 완전히 동일한 중복 (`ai_sitemap_domain`, `enabled: false`)
- **#20 Organization · #22 Speakable · #30 digitalDocument · #31 Recipe** — `enabled: false`

### 트러블슈팅 Shadow DOM SSR 정책 (2026-10-05)

LG CS 는 트러블슈팅 본문 SSR 을 Declarative Shadow DOM 방식으로 전환 중이다
(10/5 실측 롤아웃: AU·BR·CA·IN·VN 배포 / DE·ES·MX·UK·US 미배포).

- **콘텐츠 룰(#32~#36)**: 섀도 본문을 읽어 콘텐츠 존재는 **인정**한다.
- **#37 SSR 비중**: 섀도 본문은 분자에서 **제외**한다 (보수 기준 — 위 #37 비고).
- 두 경우 모두 해당 페이지 판정 근거(value)에 **"Shadow DOM SSR — 주요 AI 크롤러
  미인식 가능(일반 DOM 전환 필요)"** 를 적시한다. 개선 요구 방향은 에이전시(CNX)
  권고와 동일 — 일반 DOM 출력.

### 집계 대상에서 빠지는 페이지
- **B2B(사업자) · 프로모션/약관** — GEO 대상이 아니라 점수·통과율·URL 카운트 전부에서 제외
- **비-200 페이지** (404 · 500 · fetch 실패) — 전 체크가 cascade-FAIL 이라 개선 대상이 아님
- **분류불가(unknown) · 홈페이지(home)** — 측정 의미 없음
- **회사소개(about)** — GEO 검수 대상이 아니라 감사 자체를 하지 않음 (2026-08-28 결정)
- **서포트-일반(support)** — 아웃데이트된 URL이 많아 집계·감사 모두 제외 (2026-09-20 결정).
  트러블슈팅(`support_troubleshoot`)은 별개 타입으로 계속 감사·집계
- **단종/비활성 PDP** — PLP 상품 API(Coveo) 활성 목록(`reports/plp/<cc>.txt`,
  `plp_discover.py` 수집) 밖의 PDP 는 단종·판매종료로 보고 집계·샘플링 모두 제외
  (2026-09-21 결정). 판정 근거: US 는 후보 전수에 DISCONTINUED 배지가 확인됐고,
  AEM(비US)은 단종을 페이지에 표기하지 않아 목록 대조가 유일한 신호다. JSON-LD
  `availability` 는 66%가 미제공 + 재고없음과 뒤섞여 쓸 수 없다. 활성 목록이 없는
  국가는 판정하지 않으며, `must_audit` 지정 URL 은 샘플링 제외에서 예외다.
- **악세사리 PDP** — 필터·리모컨·설치키트 등은 콘텐츠가 빈약해 PDP 평균을 왜곡
  (실측 -2.7, US -5.8). Coveo 카테고리(`reports/plp/<cc>_cat.json`의 Accessories/
  Accesorios/Peças e Acessórios 세그먼트)와 URL 키워드의 **합집합**으로 판정해
  집계·샘플링 모두 제외 (2026-09-21 결정). 두 신호는 상호 보완 — 카테고리는 DE 처럼
  URL 에 표가 없는 케이스를, URL 은 CA/US 처럼 Coveo 카테고리가 상위 계층뿐인
  케이스를 잡는다.

### 측정 기준이 바뀐 항목
- **#1 TTFB** — 어딧 크롤러 자체 측정값이 동시 크롤 큐잉에 오염돼 실제보다 6~200배 크게 잡혔음
  (UK 크롤러 1,088ms vs PSI 11ms). PageSpeed Insights의 `server-response-time`을 정본으로 교체.
  임계값 600ms (2026-08-28 실측 1,462건 기준 통과율 96.1%, 중앙값 223ms)
- **#4 Cache-Control** — 원래 룰이 `no-cache`/`no-store`가 섞이면 `max-age` 값과 무관하게 즉시
  FAIL 처리했음. `max-age` 디렉티브가 설정돼 있으면(0 포함) 통과로 완화
- **#34 Author 또는 출처+날짜** — `newsroom`·`press_media` page_type에만 적용,
  그 외는 N/A (분모 제외)
- **#36 Citable Sentences 트러블슈팅·PLP 3개**(2026-10-26, 10월 감사부터) — 증상·원인·해결책으로 끝나는 트러블슈팅과
  카테고리 설명문 몇 줄이 전부인 PLP 는 PDP·에디토리얼 아티클(5개)과 콘텐츠 분량이 다르다. 사유 상세는 #36 섹션.
- **2026-09 오탐 수정 12건** — #10(main 필수 해제)·#11(역순만 실패)·#15(host 완화)·
  #19(국가별 sitemap 캐시 키)·#23/#26/#27/#28/#29(콘텐츠 게이트)·#32(피드백 위젯 제외)·
  #33(계사 제거)·#34(page_type 게이트)·#35(class 매칭 제거)·#36(개수 기준)·
  #40(장식 파일 제외)·#42(문구 판정). 각 항목 상세는 본문 해당 섹션 참조.

### 문서 번호와 채점 항목이 1:1이 아닌 곳
- **#17 Robots** — `seo_robots`(meta) + `seo_robots_hdr`(X-Robots-Tag), 두 개로 채점
- **#25 Product 풀세트** — `ai_schema_product` + `ai_schema_offer`, 두 개로 채점
- **#49 Schema: WebSite · #40 Summary Content SSR** — 채점은 되지만 체크리스트 문서에 대응 행 없음

---

## 대시보드 집계 기준 (하류 공유용)

> 월간 감사 결과가 `reports/dashboard_data.json` 의 숫자가 되기까지의 규칙. 하류 대시보드·리포트는
> 이 섹션을 기준으로 숫자를 해석한다. 구현: 표본은 `run_render_audit.py`, 집계는 `gen_dashboard_data.py`.

### 1. 표본 (감사 단계)
- 국가별 URL 목록(`reports/lg_urls_<cc>.csv`, 사이트맵 수집)을 URL 패턴으로 page_type 사전 분류한 뒤
  **타입별 최대 100페이지**를 감사한다. PDP 만 최대 500 — 핵심 제품군 10종(TV·오디오·모니터·냉장고·
  세탁·식기세척기·공조·공기청정·조리·청소기)에 각 50 이상을 먼저 배정하고 남는 자리를 라운드로빈으로 채운다.
  PLP 도 카테고리 균등 배분.
- 트러블슈팅·뉴스룸·프레스는 발행일 내림차순(최신 문서 우선). 날짜를 모르는 URL 은 뒤로 보낸다.
- 사업부 지정 필수 URL(`reports/must_audit/<cc>.csv`)은 타입 정원 안에서 먼저 자리를 차지하고, 정원을
  넘는 분량은 정원 밖에 덧붙여 **전부 감사**한다(트러블슈팅은 국가당 128~432건). 2026-10-25 사용자 결정:
  집계 대상인 트러블슈팅은 줄이지 않는다.
- 감사 자체를 하지 않는 타입: 분류불가(unknown)·회사소개(about)·서포트-일반(support), 그리고 2026-10-25 부터
  대시보드 집계 제외 타입인 B2B(business)·프로모션(promotion)·홈(home). 단종/비활성·악세사리 PDP 는 표본에서 제외
  ("집계 대상에서 빠지는 페이지" 참조).
- 매월 전부 새로 측정한다. 이전 run 결과 재사용 없음(2026-10-23 사용자 규칙).
- **사업부 삭제 요청 URL**(구글 시트 'Appendix.Delet URL' → `delete_urls.py` → `reports/delete_urls.csv`)은
  감사하지 않고(샘플·필수 감사 모두) 집계에서도 뺀다(제외 사유 `delete_request`, 2026-10-26 사용자 지시).
  월간 감사 시작 때 시트를 다시 받는다. 첫 요청 71건은 전부 트러블슈팅(9개국)이라 타입 정원 100 이 다른 페이지로 채워졌다.
- **HS(가전) 콘텐츠 시트**(사업부 관리 구글 시트 'Appendix.HS Contents URL' → `build_hs_contents.py` →
  `reports/hs_contents.csv`)의 URL 은 감사 국가 분량 전부를 필수 감사로 편입한다(2026-10-25 사용자 지시).
  타입 정원(100)은 필수 URL 이 먼저 차지하므로 그만큼 기존 표본 URL 이 밀려난다. 분류는 아래 "HS 콘텐츠 분류".

### 2. 페이지 점수
- 활성 채점 항목(현재 39개) 중 그 페이지에 **적용되는 항목**만 분모로 쓴다. 콘텐츠 게이트·page_type 게이트로
  N/A 가 된 항목은 분모에서 빠진다.
- 페이지 점수 = 통과 항목 / 적용 항목 × 100 (정수 반올림). 카테고리 가중치 없음.
- 임계값이 page_type 에 따라 다른 항목: **#36 인용 가능 문장**은 기본 5개, 트러블슈팅·PLP 는 3개(짧은 콘텐츠 — 사유는
  [#36 섹션](#36-citable-sentences--인용-가능-문장-22패턴)). 10월 감사부터 적용.
- 등급: Good ≥ 90 · Need Improvement ≥ 70 · Poor < 70 (`scoring_config.json` grade).
- 카테고리 점수 = 그 카테고리 안에서 통과 / 적용 × 100.

### 3. 집계 대상 페이지 (대시보드 단계, `counted_results`)
1. **제외**: business · promotion · unknown · home · about · support 타입, 단종/비활성 PDP(Coveo 활성 목록 밖),
   악세사리 PDP, 비-200 페이지(fetch 실패·404·500, #41 실패). 세부는 "집계 대상에서 빠지는 페이지".
2. **리다이렉트 중복 제거**: 여러 구 URL 이 같은 도착지로 모이면 도착지 기준 1건만 남긴다.
3. **타입별 상한 100** (PDP 는 상한 없음, 감사 단계 500): 국가마다 타입 비중이 다르면(US 트러블슈팅 34% vs DE 13%)
   국가 점수가 표본 구성을 반영하게 되므로 같은 구성으로 맞춘다. 100건 선별은 **URL sha1 해시 순** —
   무작위지만 매 실행 같은 결과(멱등). 상위 점수 선별은 채택하지 않았다(개선해도 점수가 안 움직임).
   그래서 `sample_size` 는 국가당 약 750~950, 제외 사유별 건수는 `excluded` 에 남는다.

### 4. 국가 점수와 전체 점수
- 국가 점수(`total_avg`) = 집계 대상 페이지의 페이지 점수 **단순 평균**. 카테고리 `points_avg` 는 페이지별
  카테고리 점수 평균, 항목 `pass_rate` = 통과 페이지 / 적용 페이지(`applicable_n`).
- 전체(`overall.total_avg_weighted`) = Σ(국가 점수 × sample_size) / Σ sample_size. 대상 13개 사이트:
  US · UK · DE · ES · CA · AU · BR · MX · IN · VN · BE · NL · Global-Site (BE·NL 은 월간 자동 감사 대상이 아니라
  마지막 측정분이 유지됨). **HS-Others**(`hs`, 감사 국가 밖 HS 콘텐츠 URL 595건 묶음, 2026-10-25 신설)는 행으로는
  보이지만 모집단이 달라 전체 가중평균에는 넣지 않는다.
- 국가별로 **가장 최신의 완료된 run 1개**만 쓴다(`status: ok`). 진행 중·중단된 run 은 집계하지 않으며,
  같은 날짜에 완료본이 여럿이면 성공 건수가 많은 쪽. 날짜 키는 UTC(`AUDIT_RUN_DATE`).

### 5. 저장 run 의 재채점
저장된 run 을 그대로 합산하지 않고 `scoring_config.json` 의 **현재 기준**으로 다시 채점한다. 과거 run 을 다시 돌리지
않고도 기준 변경이 대시보드에 반영되게 하기 위함이다(그래서 9월·10월 값도 현재 기준으로 다시 계산된 숫자다).
- 비활성 항목(#5·#8 등)은 분모에서 제외. 항목 ID 로 현재 6개 카테고리에 재매핑.
- `applies_to_page_types` 가 있는 항목(#34 등)은 해당 타입에서만 평가.
- #1 TTFB 는 PSI 캐시(`data/psi_cache.json`)의 **감사 날짜 이후 측정값**만 쓴다. 미측정 URL 은 같은 page_type
  실측 중앙값으로 추정 보정(`psi_coverage` 에 실측/추정 건수).
- 임계값만 바뀐 항목(#4 등)은 저장된 value 문자열로 재판정. #17 은 meta·헤더 판정을 OR 로 합성.
- #36 은 저장된 인용 문장 개수로 현재 임계값에 다시 판정한다. 모델 판정값("모델 확인 N/…")도 N 이 실측 개수다(단, 측정 당시
  임계를 채우면 중단하므로 N 은 그 임계에서 잘린다 → 임계를 **낮출** 때만 재판정, 높일 때는 저장 pass 사용). 트러블슈팅·PLP
  3개 기준(2026-10-26)은 이 경로로 10월 run 전체에 적용됐다.
- #26·#27 은 저장된 JSON-LD 원본(`json_ld.raw`)으로 현재 룰을 다시 돌린다(리뷰 위젯 오탐 수정, 2026-10-26).
- 그 외는 저장된 pass 를 그대로 쓴다. #33 모델 판정도 저장값 사용(재감사 없이는 바뀌지 않음).

### 5-1. HS(가전) 콘텐츠 분류 (2026-10-25)
사업부 시트에 올라온 HS 콘텐츠 URL 은 시트의 분류가 URL 패턴 분류보다 우선한다(`page_type.detect_page_type`,
`matched_by: hs_contents`). 결과의 `page_type.hs` 에 아래 두 분류가 붙고, 대시보드 `countries[cc].hs` 에 집계된다.

| 시트 '컨텐츠 타입 1' | page_type | 비고 |
| :-- | :-- | :-- |
| Award Banner · 뱃지적용 Gallery | `pdp` | 제품 상세에 어워드/뱃지가 노출된 페이지. HS 지정 PDP 는 단종·악세사리 제외를 적용하지 않는다 |
| Microsite | `microsite` | |
| Experience Article | `experience` | |
| buying guide | `buying_guide` | |
| installation guide | `installation_guide` | **신설 타입** "설치 가이드". URL 패턴 `installation-guide` · `pruvodce-instalaci` · `huong-dan-lap-dat` 도 보조 매칭 |

- **콘텐츠 2뎁스**(`hs.content_type2`, 시트 I열, HS 콘텐츠에만 존재): Experience Article · FAQ · buying guide · LG AI ·
  Award Banner · installation guide · category page · 신뢰성 · ice solution · 뱃지적용 Gallery · fitmax.
- **제품**(`hs.product`, 시트 F열 통일): WM(F/L·T/L 포함) · REF · DW · VCC · Cooking · Dryer · MWO · Common. 원문은 `product_raw`.
- 2026-10-25 기준 시트 1,029행 → 유효 1,015건(중복 12·URL 아닌 행 2). 감사 국가 분량 420건(AU 103 · IN 85 · UK 78 ·
  VN 34 · MX 33 · CA 24 · BR 17 · ES 16 · DE 14 · BE 11 · NL 4 · US 1), 그 외 국가(SA·CZ·IT·TW·CO·CL·TH·PH·EG·HK 등 40여 곳) 595건은
  별도 감사 그룹 `hs`(HS-Others, `reports/lg_urls_hs.csv` · `must_audit/hs.csv`, 전부 필수 감사)로 측정한다(사용자 결정 2026-10-25).
  이 국가들은 PLP 활성 목록·CSR baseline 이 없어 단종 판정은 하지 않고 #37 baseline 은 다른 국가 같은 타입 평균으로 추정한다.

### 6. 산출물
- `reports/dashboard_data.json`: `countries[cc]` → `total_avg` · `sample_size` · `excluded{사유:건수}` · `grade_dist` ·
  `breakdown[카테고리]{points_avg, pass_rate, items_n}` · `items[항목id]{label, category, pass_rate, applicable_n}` ·
  `psi_coverage` · `hs{n, total_avg, by_content_type2, by_product, by_page_type}` · `date` · `run_file`; `overall` → `total_avg_weighted` · `sample_total` · `excluded_breakdown` · `missing`;
  `criteria` → 카테고리별 항목 수.
- 월간 감사가 끝나면 자동 생성·커밋·푸시된다(`run_monthly_audit.sh`). 하류는 git 의 이 파일 또는
  MCP `geo-audit-dashboard` 도구(get_overall · get_scorecard · get_item_passrates · get_raw · list_countries)로 읽는다.
- 원시 결과(`data/run_results/<cc>_<date>_run_*.json`, 페이지별 항목 pass/value/hint)는 git 에 올리지 않는다.

---

## 감사 대상 국가

전략 10국 + Global-Site, 총 11개.

| 코드 | 표시명 | 비고 |
| :-- | :-- | :-- |
| us, uk, de, es, ca, au, br, mx, in, vn | 국가 코드 대문자 | CA는 `ca_en`(영문)만. 불어(`ca_fr`)는 제외 |
| global | **Global-Site** | `lg.com/global/newsroom` — 전량 `newsroom` page_type |

> `newsroom` 은 Global 전용이다. 국가별 보도자료는 별도 page_type **`press_media`**
> (프레스앤미디어)로 분류한다 — 경로 명칭이 국가마다 다르다:
> `press-and-media`(CA/AU/MX/IN) · `press-media`(UK/BR) · `press-release`(US) · `newsroom`(DE).
>
> `newsroom` · `press_media` · `support_troubleshoot` 세 타입은 **발행일 내림차순**으로
> 100개를 뽑는다. 계속 새 문서가 나오는 타입이라 URL 정렬순으로 자르면 오래된 문서만
> 반복 감사하게 된다 (`reports/page_dates.json`).

감사는 **page_type별 최대 100개 샘플**이다. URL 목록은 사이트맵 + PLP 상품 API(Coveo)의
활성 제품을 합쳐 구성한다(`build_url_csv.py` → `plp_discover.py`).
