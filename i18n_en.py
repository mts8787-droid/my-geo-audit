"""분석 응답 영문 변환 — 검사 화면 EN 모드(`lang=en`) 전용.

채점·감사 결과(run_results)는 한국어 그대로 두고, /analyze·/analyze-bulk 응답을
돌려주기 직전에만 항목명·판정 근거(value/hint)·페이지 타입·카테고리를 영어로 바꾼다.
판정 근거는 rule_engine/analyzer 의 f-string 이 만든 문장이라 문형 정규식 → 고정 문구
순으로 치환한다. 문장 모델이 붙이는 '모델 제외 사유'는 아는 사유만 옮기고 나머지는 뺀다.
"""
import copy
import re

_HANGUL = re.compile(r"[가-힣]")

CATEGORY_LABELS = {
    "performance": "Site Performance",
    "accessibility": "Web Accessibility",
    "seo": "Basic SEO",
    "schema_markup": "Schema Markup",
    "citable_content": "Citable Content",
    "ai_crawlability": "AI Crawlability",
    "ai_readiness": "AI Readiness",
}

ITEM_NAMES = {
    "perf_ttfb": "#1 TTFB < 600ms (PSI Lab)",
    "perf_compression": "#2 Compression",
    "perf_http_protocol": "#3 HTTP/2+",
    "perf_cache_control": "#4 Cache-Control max-age set",
    "perf_html_size": "#5 HTML < 100KB",
    "perf_redirect": "#6 Redirect ≤ 1",
    "perf_mixed_content": "#7 Mixed Content 0",
    "perf_render_block": "#8 Render Blocking 0",
    "perf_lcp": "#9 LCP ≤ 4000ms (PSI)",
    "perf_cls": "#10 CLS ≤ 0.25 (PSI)",
    "perf_inp": "#11 INP ≤ 500ms (PSI)",
    "a11y_image_alt": "#9 Image Alt missing 0",
    "a11y_semantic": "#10 Semantic HTML",
    "a11y_heading_hier": "#11 Heading Hierarchy",
    "a11y_aria_labels": "#12 ARIA missing < 10%",
    "seo_title": "#13 Title present",
    "seo_meta_desc": "#14 Meta Description",
    "seo_canonical": "#15 Canonical (same host)",
    "seo_h1": "#16 Exactly one H1",
    "seo_indexable": "#17 Indexing allowed (meta robots or X-Robots-Tag)",
    "seo_robots": "#17 Indexing allowed",
    "seo_robots_hdr": "#17 No X-Robots-Tag noindex",
    "seo_open_graph": "#18 Open Graph (title+image)",
    "seo_sitemap": "#19 Sitemap (updated within 1 month)",
    "ai_schema_product": "#25 Schema: Product full set (PDP)",
    "ai_faq_block": "#32 FAQ Block (content)",
    "ai_definition": "#33 Definition Paragraph",
    "ai_author_source": "#34 Author or source + date",
    "ai_summary_box": "#35 Summary Box (content)",
    "ai_citable": "#36 Citable Sentences ≥ 5 (Troubleshooting·PLP: 3)",
    "ai_ssr_ratio": "#37 JS HTML Text Ratio ≥ 60%",
    "ai_pdp_thumbnails": "#38 PDP thumbnails ≥ 3 in SSR",
    "ai_core_element": "#39 PDP core elements in SSR (3 of 5 areas)",
    "ai_image_filename": "#40 Image file name includes brand",
    "ai_status_200": "#41 Status Code 200",
    "ai_soft_404": "#42 No Soft 404",
    "ai_llms_txt": "#43 llms.txt present",
    "ai_summary_ssr": "#40 Summary Content SSR",
    "ai_sitemap_domain": "#45 Sitemap (domain, within 1 month)",
}

PAGE_TYPES = {
    "home": "Home",
    "pdp": "Product detail (PDP)",
    "plp": "Product category (PLP)",
    "support_troubleshoot": "Support - Troubleshooting",
    "support": "Support",
    "business": "B2B (Business)",
    "experience": "Experience",
    "newsroom": "Newsroom (Global)",
    "press_media": "Press & Media",
    "promotion": "Promotion/Terms",
    "about": "Company/About",
    "installation_guide": "Installation guide",
    "buying_guide": "Buying guide",
    "microsite": "Microsite/Campaign",
    "unknown": "Unclassified",
}

# 문장 모델 제외 사유 (자주 나오는 것만 — 나머지는 생략)
REASONS = {
    "UI 텍스트": "UI text", "인용할 구체 사실 없음": "no concrete fact to cite",
    "내비게이션 메뉴 나열": "navigation menu list", "스펙표 텍스트 뭉침": "spec-table text blob",
    "질문": "question", "질문형 제목": "question-style heading", "제목형 질문": "heading-style question",
    "할인 조건": "discount terms", "결제 안내": "payment notice", "메뉴 경로": "menu path",
    "내비게이션 텍스트": "navigation text", "내비게이션/UI 텍스트": "navigation/UI text",
    "대상 제품 없는 주의 문구": "caution text without a target product", "면책 고지": "disclaimer",
    "각주 면책 고지": "footnote disclaimer", "잘린 문장 조각": "truncated fragment",
    "법적 고지": "legal notice", "각주 고지": "footnote notice", "마케팅 문구": "marketing copy",
    "알림": "notification", "기능명 없음": "no feature name", "상담 안내": "contact notice",
    "모호한 마케팅 문구": "vague marketing copy", "지원 안내": "support notice",
    "문장 조각": "sentence fragment", "별표 인증 각주": "asterisk certification footnote",
    "행동 유도 문구": "call to action", "수수료 고지": "fee notice", "일반론": "generic statement",
    "지시어": "demonstrative reference", "제품명 없음": "no product name",
    "가격 면책 고지": "price disclaimer", "증상 제목": "symptom heading",
    "제품 사실 아님": "not a product fact", "프로모션 약관": "promotion terms",
    "인용 발언": "quote", "인증 각주": "certification footnote", "매뉴얼 참조 안내": "manual reference",
    "스펙표 조각": "spec-table fragment", "모델별 상이 일반 안내": "generic model-dependent notice",
    "비교표 텍스트 뭉침": "comparison-table text blob", "안내 문구": "notice text",
    "일반적 서술": "generic description", "일반 서술": "generic description",
    "내비게이션 메뉴": "navigation menu", "잘린 조각": "truncated fragment",
    "범용 지시": "generic instruction", "보증 조건": "warranty terms", "모델 범위": "model scope",
    "일반 도입": "generic intro", "서비스 약관": "terms of service", "모호한 홍보 문구": "vague promo copy",
    "프로모션 문구": "promo copy", "스펙표 텍스트 조각": "spec-table text fragment",
    "주어 불명": "unclear subject", "제목형 문장": "heading-style sentence", "사용 안내": "usage notice",
    "지원 내비게이션 텍스트": "support navigation text", "지시어 시작": "starts with a reference word",
    "정보 없음": "no information", "주석 조각": "annotation fragment", "배송 안내": "shipping notice",
    "참조 안내": "reference notice", "마케팅 주장": "marketing claim", "일반 도입 문장": "generic intro sentence",
    "모호한 주장": "vague claim", "별표 각주": "asterisk footnote", "내비게이션 나열": "navigation list",
    "내비게이션 메시지": "navigation message", "등록된 상표 고지": "trademark notice",
    "디자인 홍보 문구": "design promo copy", "회사 소개 보일러플레이트": "company boilerplate",
    "제목 없음": "no heading", "질문형 문장": "question sentence", "홍보 문구": "promo copy",
    "회사 보일러플레이트": "company boilerplate", "보도자료 인용": "press-release quote",
    "슬로건": "slogan", "프로모션 조건": "promotion terms", "구체 정보 없음": "no concrete information",
    "모호": "vague", "마케팅": "marketing", "헤드라인": "headline", "각주": "footnote",
}

# 문형 정규식 — 위에서부터 차례로 적용 (구체적인 것 먼저)
_P = [
    (r"이 항목은 (.+?) 페이지에서만 평가됩니다 \(현재: (.+?)\)", r"Evaluated only on \1 pages (current: \2)"),
    (r"@type='([^']*)' 노드 없음", r"No @type='\1' node"),
    (r"@type=(\S+) 필수 필드 OK", r"@type=\1 required fields OK"),
    (r"@type '([^']*)'을\(를\) 찾을 수 없습니다\.", r"@type '\1' not found."),
    (r"@type 후보 (\d+)개", r"\1 @type candidate(s)"),
    (r"리다이렉트 (\d+)회 — (\d+)회 이하 권장", r"\1 redirect(s) — \2 or fewer recommended"),
    (r"(\d+)회 리다이렉트", r"\1 redirect(s)"),
    (r"(\d+)개 중 (\d+)개 '([^']*)' 보유", r"\2 of \1 have '\3'"),
    (r"(\d+)/(\d+) 누락 \(([\d.]+)%\)", r"\1/\2 missing (\3%)"),
    (r"누락 ([\d.]+)% — ([\d.]+)% 미만 필요", r"Missing \1% — under \2% required"),
    (r"국가 디렉토리\(([^)]*)\) lastmod 없음", r"Country directory (\1): no lastmod"),
    (r"(\d+)개 헤딩, 첫 레벨 h(\d), 역순 (\d+)건", r"\1 headings, first level h\2, \3 inversion(s)"),
    (r"헤딩 역순 (\d+)건 — 첫 헤딩\(h(\d)\)보다 상위 레벨이 뒤에 등장",
     r"\1 heading inversion(s) — a higher level appears after the first heading (h\2)"),
    (r"(\d+)개 og 메타 발견", r"\1 og meta tags found"),
    (r"본문 (\d+)자 — 내용 없는 200 응답 \((\d+)자 미만\)", r"Body \1 chars — empty 200 response (under \2 chars)"),
    (r"본문 (\d+)자", r"Body \1 chars"),
    (r"헤딩=(\d+), 랜드마크=(\d+), 합계=(\d+), main=([OX])", r"headings=\1, landmarks=\2, total=\3, main=\4"),
    (r"헤딩 (\d+) \+ 랜드마크 (\d+) = (\d+) — 의미 구조 (\d+)\+ 필요",
     r"headings \1 + landmarks \2 = \3 — semantic structure \4+ required"),
    (r"main (\d+)개 · role=main (\d+)개 — main 랜드마크 필요", r"main \1 · role=main \2 — a main landmark is required"),
    (r"모델 확인 (\d+)/(\d+) \(정규식 후보 (\d+)/(\d+)문장", r"Model-confirmed \1/\2 (regex candidates \3/\4 sentences"),
    (r", 본문 (\d+)문장 추가 탐색\)", r", \1 more body sentences scanned)"),
    (r"dfn/abbr (\d+)개 \+ 모델 확인 정의문 (\d+)건", r"dfn/abbr \1 + \2 model-confirmed definition(s)"),
    (r"dfn/abbr (\d+)개 \+ 패턴 (\d+)건", r"dfn/abbr \1 + \2 pattern match(es)"),
    (r"패턴 (\d+)건 → 본문 (\d+)문장 모델 탐색", r"\1 pattern match(es) → model scanned \2 body sentences"),
    (r"(\d+)문장 판정\)", r"\1 sentences judged)"),
    (r"정의문 (\d+)건 — (\d+)건 이상 필요", r"\1 definition sentence(s) — \2 or more required"),
    (r"인용 가능 문장 (\d+)개 — (\d+)개 이상 필요", r"\1 citable sentence(s) — \2 or more required"),
    (r"인용 가능 밀도 ([\d.]+)% — ([\d.]+)% 이상 필요", r"Citable density \1% — \2% or more required"),
    (r"(\d+)/(\d+) 영역", r"\1/\2 areas"),
    (r"서술적 파일명 (\d+)/(\d+) \(([\d.]+)%\) — ([\d.]+)% 이상 필요",
     r"Descriptive file names \1/\2 (\3%) — \4% or more required"),
    (r"SSR 비율 ([\d.]+)% — ([\d.]+)% 이상 필요", r"SSR ratio \1% — \2% or more required"),
    (r"키워드\((.*?)\)를 포함한 요소를 찾을 수 없습니다\.", r"No element contains the keywords (\1)."),
    (r"types (\[.*?\]) 중 하나도 JSON-LD에 없음 \(둘 중 하나 필요\)", r"None of types \1 in JSON-LD (one is required)"),
    (r"^(.+?) 모두 없음$", r"None of \1 found"),
    (r"'([^']*)' (\d+)개 — (\S+) (\d+) 필요", r"'\1' count \2 — \3 \4 required"),
    (r"(\d+)개 요소에 '([^']*)' 속성이 없습니다\.", r"\1 element(s) missing the '\2' attribute."),
    (r"'([^']*)' 속성이 없거나 (\d+)자 미만입니다\.", r"'\1' attribute missing or shorter than \2 chars."),
    (r"'([^']*)' 속성이 없습니다\.", r"'\1' attribute is missing."),
    (r"'([^']*)' 요소를 찾을 수 없습니다\.", r"Element '\1' not found."),
    (r"'([^']*)' 선언으로 색인이 차단됩니다\.", r"Indexing is blocked by the '\1' directive."),
    (r"'([^']*)' 헤더가 (.*?) 중 하나여야 합니다\.", r"'\1' header must be one of \2."),
    (r"'([^']*)'에 '([^']*)'이 포함되어 있습니다\.", r"'\1' contains '\2'."),
    (r"'([^']*)'가 포함되어 있습니다\.", r"Contains '\1'."),
    (r"패턴 '(.*?)'에 매칭되는 텍스트가 없습니다\.", r"No text matches pattern '\1'."),
    (r"<(\w+)> class/id에서 '([^']*)' 발견", r"'\2' found in <\1> class/id"),
    (r"<(\w+)> 텍스트에서 '([^']*)' 발견", r"'\2' found in <\1> text"),
    (r"<(\w+)> 텍스트: ", r"<\1> text: "),
    (r"질문 (\d+)개 \+ '([^']*)': ", r"\1 question(s) + '\2': "),
    (r"매칭: \[(.*?)\] · 누락: \[(.*?)\] · 최소 (\d+)개 필요", r"Matched: [\1] · Missing: [\2] · at least \3 required"),
    (r"HTTP (\d+) — (\d+) 기대", r"HTTP \1 — expected \2"),
    (r"HTTP (\S+) \(Soft 404 검증 대상 아님\)", r"HTTP \1 (not subject to Soft 404 check)"),
    (r"HTTP (\d+) 후 재시도 #(\d+)", r"Retry #\2 after HTTP \1"),
    (r"HTTP (\d+) 응답", r"HTTP \1 response"),
    (r"사이트가 헤드리스 브라우저를 차단합니다 \(HTTP (\d+)\)", r"The site blocks headless browsers (HTTP \1)"),
    (r"요청 시간 초과 \((\d+)초\)", r"Request timed out (\1 s)"),
    (r"마지막 갱신 (\S+) — (\d+)일 이내 필요", r"Last updated \1 — within \2 days required"),
    (r"max-age=(\d+) — (\d+)초 이상 필요", r"max-age=\1 — at least \2 seconds required"),
    (r"텍스트 길이 (\d+) — (\d+)자 이상 필요", r"Text length \1 — \2+ chars required"),
    (r"canonical='([^']*)' — 다른 도메인을 가리킵니다", r"canonical='\1' — points to a different domain"),
    (r"canonical='([^']*)' ≠ 현재 URL", r"canonical='\1' ≠ current URL"),
    (r"page_type=(\S+) / 모든 expected_schemas 발견: ", r"page_type=\1 / all expected_schemas found: "),
    (r"page_type=(\S+) / 발견 (.*?) / 누락 ", r"page_type=\1 / found \2 / missing "),
    (r"이 페이지 타입\((\S+)\)에서 기대되는 schema (.*?)가 JSON-LD에 없음",
     r"Schema \2 expected for this page type (\1) is missing from JSON-LD"),
    (r"(\S+): 검증할 expected_schemas 없음 \(자동 PASS\)", r"\1: no expected_schemas to verify (auto PASS)"),
    (r"(\S+) 가 200 이지만 내용이 llms.txt 형식이 아닙니다 \(soft 404 의심\)",
     r"\1 returns 200 but is not in llms.txt format (suspected soft 404)"),
    (r"(\S+): 날짜 정보 없음", r"\1: no date info"),
    (r"(\S+): 오류\((\w+)\)", r"\1: error (\2)"),
    (r"PSI 응답에 (\S+) 없음", r"No \1 in the PSI response"),
    (r"audit '([^']*)' 결과 없음", r"No result for audit '\1'"),
    (r"http:// 리소스 (\d+)개: ", r"\1 http:// resource(s): "),
    (r"head 내 blocking script (\d+)개", r"\1 blocking script(s) in head"),
    (r"page_type='([^']*)' 표본 평균 \(실측 아님\)", r"page_type='\1' sample average (not measured)"),
    (r"(\d+)개 매칭 \(([\d.]+)%\)", r"\1 matched (\2%)"),
    (r"(\d+)개 경로 시도", r"\1 paths tried"),
    (r"(\d+)개 노드", r"\1 nodes"),
    (r"(\d+)개 발견", r"\1 found"),
    (r"(\d+)줄: ", r"\1 lines: "),
    # 일반 임계 문형
    (r"— (\S+) 미만 필요", r"— under \1 required"),
    (r"— (\S+) 이상 필요", r"— \1 or more required"),
    (r"(\d+)\s?개", r"\1"),
    (r"(\d+)\s?건", r"\1"),
]
PATTERNS = [(re.compile(a), b) for a, b in _P]

# 고정 문구 (긴 것부터 치환)
PHRASES = {
    "영상이 없는 페이지라 VideoObject 스키마 평가 대상이 아닙니다.": "No video on this page — VideoObject schema not applicable.",
    "FAQ 섹션(클래스·헤딩)이 없는 페이지라 FAQPage 스키마 평가 대상이 아닙니다.": "No FAQ section (class/heading) on this page — FAQPage schema not applicable.",
    "기사 본문 구조가 없는 페이지라 Article 스키마 평가 대상이 아닙니다.": "No article body structure on this page — Article schema not applicable.",
    "절차(순서 목록·단계 블록)가 없는 페이지라 HowTo 스키마 평가 대상이 아닙니다.": "No procedure (ordered list/step block) on this page — HowTo schema not applicable.",
    "본문 콘텐츠 이미지가 없어 ImageObject 평가 대상이 아닙니다.": "No body content images — ImageObject not applicable.",
    "GNB·푸터·로고·아이콘을 제외하면 판정할 img 가 없어 평가 대상이 아닙니다.": "No images to judge after excluding GNB, footer, logos and icons — not applicable.",
    "로고·아이콘을 제외하면 판정할 img 가 없습니다.": "No images to judge after excluding logos and icons.",
    "요약 블록(헤딩 문구·selector)을 찾지 못했습니다.": "No summary block (heading text or selector) found.",
    "PSI 미수집 — psi_collect.py 로 수집 후 평가됩니다.": "PSI data not collected yet — evaluated after collection.",
    "Shadow DOM SSR — 주요 AI 크롤러 미인식 가능(일반 DOM 전환 필요)": "Shadow DOM SSR — major AI crawlers may not read it (move to regular DOM)",
    "JSON-LD author 또는 (datePublished+publisher) 조합 없음": "No JSON-LD author or (datePublished+publisher) combination",
    "JSON-LD datePublished+publisher 조합 발견": "JSON-LD datePublished+publisher combination found",
    "JSON-LD 노드 없음 (author/source 스키마 검증 불가)": "No JSON-LD nodes (cannot verify author/source schema)",
    "JSON-LD author 발견": "JSON-LD author found",
    "국가 sitemap 에 <lastmod> 가 없어 갱신 여부 판별 불가": "Country sitemap has no <lastmod> — cannot tell when it was updated",
    "대상 페이지가 WebMCP Origin Trial 토큰을 서빙하지 않아 평가 불가": "The page does not serve a WebMCP Origin Trial token — cannot evaluate",
    "200 응답인데 본문에 404 문구가 있습니다 — Soft 404": "200 response but the body contains 404 wording — Soft 404",
    "CSR 비율 측정 불가 (Playwright 미설치 또는 차단)": "Cannot measure CSR ratio (Playwright missing or blocked)",
    "H2/H3/H4가 H1보다 먼저 나타납니다.": "H2/H3/H4 appear before H1.",
    "HTTPS 페이지 아님 (검증 대상 외)": "Not an HTTPS page (not checked)",
    "본문 영역에 헤딩 태그가 없습니다.": "No heading tags in the body area.",
    "Cache-Control 헤더가 없습니다.": "No Cache-Control header.",
    "max-age 디렉티브가 없습니다.": "No max-age directive.",
    "@type이 지정되지 않았습니다.": "No @type specified.",
    "base_url이 없습니다.": "No base_url.",
    "키워드가 지정되지 않았습니다.": "No keywords specified.",
    "분석할 문장이 없습니다.": "No sentences to analyze.",
    "분석할 텍스트가 없습니다.": "No text to analyze.",
    "인용 가능 문장이 없습니다.": "No citable sentences.",
    "선행 조건을 만족하지 않아 평가 대상이 아닙니다.": "Prerequisite not met — not applicable.",
    "해당 콘텐츠가 없어 평가 대상이 아닙니다.": "No relevant content — not applicable.",
    "페이지 응답에 HTML 본문이 없거나 너무 짧습니다 (500자 미만).": "The response has no HTML body or it is too short (under 500 chars).",
    "봇 차단(Cloudflare/CAPTCHA), 타임아웃, 또는 비-HTML 응답일 수 있습니다. 브라우저에서 해당 URL이 정상 열리는지 확인하세요.":
        "Possibly bot blocking (Cloudflare/CAPTCHA), a timeout, or a non-HTML response. Check that the URL opens normally in a browser.",
    "사이트 전체 평균 (page_type 표본 부족, 실측 아님)": "Site-wide average (too few page_type samples, not measured)",
    "Chromium 설치 실패 — Render 대시보드에서 Build Command를 확인하세요.": "Chromium install failed — check the Build Command on Render.",
    "스텔스 모드(Playwright) 로딩 실패": "Stealth mode (Playwright) failed to load",
    "브라우저 렌더링 시간 초과": "Browser rendering timed out",
    "리다이렉트가 너무 많습니다": "Too many redirects",
    "서버에 연결할 수 없습니다": "Cannot connect to the server",
    "요청 시간 초과": "Request timed out",
    "페이지 로딩 실패": "Page failed to load",
    "playwright 미설치": "Playwright not installed",
    "선언 없음(기본 허용)": "No directive (allowed by default)",
    "태그 없음 (기본 허용)": "No tag (allowed by default)",
    "본문 없음(노이즈만)": "No body (noise only)",
    "정규식(모델 미연결)": "regex (model not connected)",
    "정규식 후보 확인": "regex candidates checked",
    "논리적 순서 정상": "Logical order OK",
    "본문 이미지 없음": "No body images",
    "콘텐츠 이미지 없음": "No content images",
    "인터랙티브 요소 없음": "No interactive elements",
    "본문 헤딩 없음": "No body headings",
    "canonical 태그 없음": "No canonical tag",
    "프로토콜 정보 없음": "No protocol info",
    "HTML 크기 측정 불가": "Cannot measure HTML size",
    "TTFB 측정 불가": "Cannot measure TTFB",
    "HTML 파싱 실패": "HTML parsing failed",
    "본문 파싱 실패": "Body parsing failed",
    "status code 없음": "No status code",
    "sitemap 부재": "No sitemap",
    "해당 요소 없음": "No matching element",
    "텍스트 없음": "No text",
    "문장 없음": "No sentences",
    "키워드 미지정": "No keywords specified",
    "필수 og 키 미지정": "No required og keys specified",
    "types 파라미터 비어있음": "types parameter is empty",
    "type 또는 fields 미지정": "type or fields not specified",
    "max_value 설정 오류": "max_value config error",
    "head 없음": "No head",
    "헤더 없음": "No header",
    "base_url 없음": "No base_url",
    "fetch 실패": "Fetch failed",
    "필수 필드 누락: ": "Missing required fields: ",
    "PSI 수집 실패: ": "PSI collection failed: ",
    "규칙 평가 오류: ": "Rule evaluation error: ",
    "알 수 없는 규칙 타입: ": "Unknown rule type: ",
    "요청 실패: ": "Request failed: ",
    "네트워크 오류: ": "Network error: ",
    "누락: ": "Missing: ",
    "발견: ": "Found: ",
    " (도메인 평균)": " (domain average)",
    "국가 디렉토리(": "Country directory (",
    "도메인 루트(": "Domain root (",
    "국가 디렉토리": "Country directory",
    "도메인 루트": "Domain root",
    "AI 학습": "AI training",
    # #39 PDP 핵심 영역 라벨
    "제품명": "Product name", "갤러리": "Gallery", "가격": "Price", "사양": "Specs", "리뷰": "Reviews",
    "없음": "none",
}
_PHRASES = sorted(PHRASES.items(), key=lambda kv: -len(kv[0]))

_REASON_RX = re.compile(r" ?\(모델 제외 사유: (.*)\)\s*$")


_KW_RX = re.compile(r"키워드\((.*?)\.\.\.\)를 포함한 요소를 찾을 수 없습니다\.")


def _keywords(m):
    # 키워드 목록의 한국어 키워드(자주 묻는 등)는 영문 화면에서 뺀다
    kws = [k for k in m.group(1).split(", ") if not _HANGUL.search(k)]
    return f"No element contains the keywords ({', '.join(kws)}...)."


def _reasons(m):
    parts = [REASONS.get(p.strip()) for p in m.group(1).split(", ")]
    parts = [p for p in parts if p]
    return f" (model exclusion: {', '.join(parts)})" if parts else " (excluded by the sentence model)"


def tr(s):
    """한국어 판정 문장 → 영어. 한글이 없으면 그대로."""
    if not isinstance(s, str) or not _HANGUL.search(s):
        return s
    s = _REASON_RX.sub(_reasons, s)
    s = _KW_RX.sub(_keywords, s)
    for ko, en in _PHRASES:
        if len(ko) >= 12 and ko in s:
            s = s.replace(ko, en)
    for rx, rep in PATTERNS:
        s = rx.sub(rep, s)
    for ko, en in _PHRASES:
        if ko in s:
            s = s.replace(ko, en)
    return s


def translate_result(result):
    """/analyze 응답 1건을 영문으로 (원본은 건드리지 않음)."""
    if not isinstance(result, dict):
        return result
    r = copy.deepcopy(result)
    pt = r.get("page_type")
    if isinstance(pt, dict) and pt.get("id"):
        pt["label"] = PAGE_TYPES.get(pt["id"], tr(pt.get("label")))
    pe = r.get("page_error")
    if isinstance(pe, dict):
        for k in ("message", "hint"):
            pe[k] = tr(pe.get(k))
    elif isinstance(pe, str):
        r["page_error"] = tr(pe)
    for bot in ((r.get("robots_txt") or {}).get("bots") or {}).values():
        if isinstance(bot, dict):
            bot["name"] = tr(bot.get("name"))
    csr = r.get("csr_ratio")
    if isinstance(csr, dict):
        for k, v in list(csr.items()):
            if isinstance(v, str):
                csr[k] = tr(v)
    for cat_key, cat in ((r.get("score") or {}).get("breakdown") or {}).items():
        if not isinstance(cat, dict):
            continue
        if "label" in cat:
            cat["label"] = CATEGORY_LABELS.get(cat_key, tr(cat["label"]))
        for item_id, it in (cat.get("items") or {}).items():
            if not isinstance(it, dict):
                continue
            if "label" in it:
                it["label"] = ITEM_NAMES.get(item_id) or tr(it["label"])
            for k in ("value", "hint"):
                it[k] = tr(it.get(k))
    return r


def client_table():
    """검사 화면(static/index.html)이 같은 규칙으로 브라우저에서 변환하도록 내려주는 표.
    정규식은 JS 와 호환되는 문법만 쓴다 — 치환 그룹 \\1 은 $1 로 바꿔 보낸다."""
    return {
        "categories": CATEGORY_LABELS,
        "items": ITEM_NAMES,
        "page_types": PAGE_TYPES,
        "reasons": REASONS,
        "patterns": [[a, re.sub(r"\\(\d)", r"$\1", b)] for a, b in _P],
        "phrases": _PHRASES,
    }
