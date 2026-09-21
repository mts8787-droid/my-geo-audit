# GEO Agent Readability 검수 기준

> 6개 카테고리 41개 채점 항목 + 9월 감사 시행 예정 4항목.
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
- **상태**: 9월 감사부터 추가 시행 (데이터 추출 및 검증 진행중)

### (예정) Agentic Browsing
- **정의**: AI Agent와 상호작용하기 위해 사이트가 얼마나 잘 구성되어 있는지 (구글 베타)
- **측정방법**: CLS · llms.txt · 에이전트 접근성 항목 평가
- **상태**: 9월 감사부터 추가 시행. WebMCP audit 3종은 대상 페이지가 Origin Trial 토큰을
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
| #25 | Product 풀세트 | name, description, sku, brand, offers.price, offers.availability, aggregateRating.ratingValue, Review | `ai_schema_product`, `ai_schema_offer` |
| #26 | ImageObject | url, name, description, uploadDate | `ai_schema_image` |
| #27 | VideoObject | url, name, description, thumbnailUrl | `ai_schema_video` |
| #28 | HowTo | HowToSupply / HowToStep | `ai_schema_howto` |
| #29 | Article | headline, author, publisher, articleBody | `ai_schema_article` |
| #49 | WebSite | — (체크리스트 문서에 대응 행 없음) | `ai_schema_website` |

> #25는 Product와 Offer 2개 항목으로 채점되어 스키마마크업 카테고리는 총 10개.

### 게이트 (2026-09 적용) — 해당 콘텐츠가 없는 페이지는 N/A로 분모 제외

콘텐츠가 없는 페이지까지 분모에 넣으면 통과율이 구조적으로 낮게 나와, 아래 항목은
**해당 콘텐츠가 있는 페이지만** 평가한다 (`applies_when` / `applies_to_page_types`).

| # | 게이트 조건 |
| :-: | :-- |
| #23 FAQPage | FAQ 섹션(클래스·헤딩) 존재 + `pdp`·`plp`·`buying_guide`·`microsite` 타입만 |
| #26 ImageObject | 본문 콘텐츠 이미지(figure·article·gallery 등 selector) 존재 — 페이지타입 제한 없음 |
| #27 VideoObject | video 태그 또는 youtube/vimeo iframe 존재 |
| #28 HowTo | 절차(순서 목록·단계 블록 3개 이상) 존재 + `support_troubleshoot` 타입만 |
| #29 Article | 기사 본문 구조(article 등) 존재 + `experience`·`buying_guide`·`microsite` 타입만 |

> 게이트 적용 후에도 #26·#27·#28·#29는 통과율 0% — 측정 문제가 아니라 실제로 4종
> 스키마를 전혀 쓰지 않는 것이며, LG 전달 리포트의 핵심 개선 항목이다.

---

## 고인용 콘텐츠

| # | 항목 | PASS | 측정방법 | check id |
| :-: | :-- | :-- | :-- | :-- |
| #32 | FAQ Block | 1개 이상 | FAQPage Schema, details/summary, Q&A 패턴 | `ai_faq_block` |
| #33 | Definition Paragraph | 1개 이상 | 정의문 패턴 15종(6개 언어), `dfn`, `abbr` — [패턴 목록](#매칭-패턴-기준) | `ai_definition` |
| #34 | Author/Source | 저자 또는 (출처+날짜) | **JSON-LD** `author` 또는 (`datePublished` + `publisher`/`sourceOrganization`/`source`) | `ai_author_source` |
| #35 | Summary Box | 1개 이상 | TL;DR, Key Takeaways, Highlights, Abstract | `ai_summary_box` |
| #36 | Citable Sentences | **5개 이상** | 인용 가능 패턴 22종에 걸리는 문장 수 — [패턴 목록](#매칭-패턴-기준) | `ai_citable` |

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
| #37 | (JS) HTML Text Ratio | 밀도 ≥ 60% | JS 렌더링 후 텍스트 대비 HTML Text 비중 | `ai_ssr_ratio` |
| #38 | (JS) HTML Resource | PDP 썸네일 1-3번째 이미지가 HTML에 존재 | PDP HTML 파싱 후 SSR 확인 | `ai_pdp_thumbnails` |
| #39 | (JS) 핵심 element | PDP 핵심 element가 HTML로 존재 | PDP HTML 파싱 후 SSR 확인 | `ai_core_element` |
| #40 | Image File Name | 브랜드·제품 키워드 포함 이미지 ≥ 30% | 파일명 키워드 검증 — logo·icon·sprite 등 장식 파일 제외 | `ai_image_filename` |
| #41 | Status Code (200) | 200 반환 | Status Code | `ai_status_200` |
| #42 | Status Code (Soft 404) | 200 응답 본문에 404 안내 문구 없음 | 문구 판정 (2026-09-17 전환 — LG 404 본문이 2,400~3,200자라 길이로는 판별 불가). 본문 200자 미만은 보조 신호 | `ai_soft_404` |
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

문장 단위로 아래 중 **하나라도** 걸리면 인용 가능으로 센다. 5개 이상이면 통과.

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

### #33 Definition Paragraph — 정의문 (15패턴)

문서 전체에서 아래 중 **하나라도** 걸리면 통과. `dfn`·`abbr` 태그가 있으면 그것으로도 통과.

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

### 채점에서 제외된 항목
- **#5 HTML < 100KB** — 측정은 정확하나 lg.com HTML 중앙값이 1,536KB라 실질 통과율 0.0%.
  통과 건의 대부분이 본문 0자인 빈 404 셸이라 지표 방향이 반대였음
- **#8 Render Blocking 0** — 통과율 2.3%로 변별력 없음
- **#44 Sitemap XML** — #19 Sitemap과 rule이 완전히 동일한 중복 (`ai_sitemap_domain`, `enabled: false`)
- **#20 Organization · #22 Speakable · #30 digitalDocument · #31 Recipe** — `enabled: false`

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
- **2026-09 오탐 수정 12건** — #10(main 필수 해제)·#11(역순만 실패)·#15(host 완화)·
  #19(국가별 sitemap 캐시 키)·#23/#26/#27/#28/#29(콘텐츠 게이트)·#32(피드백 위젯 제외)·
  #33(계사 제거)·#34(page_type 게이트)·#35(class 매칭 제거)·#36(개수 기준)·
  #40(장식 파일 제외)·#42(문구 판정). 각 항목 상세는 본문 해당 섹션 참조.

### 문서 번호와 채점 항목이 1:1이 아닌 곳
- **#17 Robots** — `seo_robots`(meta) + `seo_robots_hdr`(X-Robots-Tag), 두 개로 채점
- **#25 Product 풀세트** — `ai_schema_product` + `ai_schema_offer`, 두 개로 채점
- **#49 Schema: WebSite · #40 Summary Content SSR** — 채점은 되지만 체크리스트 문서에 대응 행 없음

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
