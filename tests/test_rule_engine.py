"""
rule_engine 단위 테스트.

서버를 띄우지 않고 픽스처 HTML/JSON-LD/headers를 직접 컨텍스트에 주입해
각 룰 핸들러의 PASS/FAIL을 검증한다.

실행:
    python3 -m unittest tests.test_rule_engine -v
"""
import os
import sys
import asyncio
import unittest
import httpx
from bs4 import BeautifulSoup

# 프로젝트 루트를 path에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rule_engine import (  # noqa: E402
    evaluate_rule, evaluate_rule_async, _HANDLERS, _ASYNC_HANDLERS, RULE_TYPES,
    _detect_country_dir, _CITABLE_NOISE, _CITABLE_PATTERNS, _visible_text,
)


def _ctx(html="<html><head></head><body></body></html>", **page_data_overrides):
    """기본 컨텍스트 빌더."""
    soup = BeautifulSoup(html, "html.parser")
    page_data = {
        "status":         "ok",
        "soup":           soup,
        "http_status":    200,
        "final_url":      "https://example.com/",
        "redirect_count": 0,
        "headers":        {},
        "http_version":   "HTTP/2",
        "html_bytes":     len(html.encode("utf-8")),
        "ttfb_ms":        300,
        "raw_html":       html,
    }
    page_data.update(page_data_overrides)
    return {
        "soup":            soup,
        "page_data":       page_data,
        "jsonld_types":    set(),
        "jsonld_raw":      [],
        "base_url":        "https://example.com",
        "current_url":     page_data["final_url"],
        "csr_ratio_dict":  {"status": "unavailable", "ratio": None},
    }


def _eval(rule_type, params, ctx):
    return evaluate_rule({"type": rule_type, "params": params}, ctx)


# ── Performance / HTTP ────────────────────────────────────────────────────────

class TestPerformanceRules(unittest.TestCase):
    def test_compression_pass(self):
        ctx = _ctx(headers={"content-encoding": "gzip"})
        r = _eval("header_value_in", {"header": "content-encoding", "values": "gzip,br,deflate"}, ctx)
        self.assertTrue(r["pass"])

    def test_compression_fail(self):
        ctx = _ctx(headers={"content-encoding": "identity"})
        r = _eval("header_value_in", {"header": "content-encoding", "values": "gzip,br,deflate"}, ctx)
        self.assertFalse(r["pass"])

    def test_compression_missing_header(self):
        ctx = _ctx(headers={})
        r = _eval("header_value_in", {"header": "content-encoding", "values": "gzip,br,deflate"}, ctx)
        self.assertFalse(r["pass"])

    def test_cache_max_age_pass(self):
        ctx = _ctx(headers={"cache-control": "public, max-age=3600"})
        r = _eval("header_max_age_min", {"min_seconds": 1}, ctx)
        self.assertTrue(r["pass"])
        self.assertIn("3600", r["value"])

    def test_cache_max_age_no_store_fail(self):
        ctx = _ctx(headers={"cache-control": "no-store"})
        r = _eval("header_max_age_min", {"min_seconds": 1}, ctx)
        self.assertFalse(r["pass"])

    def test_x_robots_no_noindex_pass(self):
        ctx = _ctx(headers={"x-robots-tag": "all"})
        r = _eval("header_no_value", {"header": "x-robots-tag", "token": "noindex"}, ctx)
        self.assertTrue(r["pass"])

    def test_x_robots_noindex_fail(self):
        ctx = _ctx(headers={"x-robots-tag": "noindex, nofollow"})
        r = _eval("header_no_value", {"header": "x-robots-tag", "token": "noindex"}, ctx)
        self.assertFalse(r["pass"])

    def test_ttfb_pass(self):
        ctx = _ctx(ttfb_ms=300)
        r = _eval("ttfb_under_ms", {"max_ms": 600}, ctx)
        self.assertTrue(r["pass"])

    def test_ttfb_fail(self):
        ctx = _ctx(ttfb_ms=900)
        r = _eval("ttfb_under_ms", {"max_ms": 600}, ctx)
        self.assertFalse(r["pass"])

    def test_http_protocol_h2_pass(self):
        ctx = _ctx(http_version="HTTP/2")
        r = _eval("http_protocol_min", {"min_version": "HTTP/2"}, ctx)
        self.assertTrue(r["pass"])

    def test_http_protocol_h11_fail(self):
        ctx = _ctx(http_version="HTTP/1.1")
        r = _eval("http_protocol_min", {"min_version": "HTTP/2"}, ctx)
        self.assertFalse(r["pass"])

    def test_html_size_under_pass(self):
        ctx = _ctx(html_bytes=50000)
        r = _eval("html_size_under_kb", {"max_kb": 100}, ctx)
        self.assertTrue(r["pass"])

    def test_html_size_over_fail(self):
        ctx = _ctx(html_bytes=200000)
        r = _eval("html_size_under_kb", {"max_kb": 100}, ctx)
        self.assertFalse(r["pass"])

    def test_status_code_pass(self):
        ctx = _ctx(http_status=200)
        r = _eval("status_code_eq", {"code": 200}, ctx)
        self.assertTrue(r["pass"])

    def test_status_code_fail(self):
        ctx = _ctx(http_status=404)
        r = _eval("status_code_eq", {"code": 200}, ctx)
        self.assertFalse(r["pass"])

    def test_soft_404_pass_normal_page(self):
        long_text = "본문 " * 200
        html = f"<html><body>{long_text}</body></html>"
        ctx = _ctx(html=html, http_status=200)
        r = _eval("soft_404_check", {"min_text_length": 200}, ctx)
        self.assertTrue(r["pass"])

    def test_soft_404_fail_thin_page(self):
        html = "<html><body>oops</body></html>"
        ctx = _ctx(html=html, http_status=200)
        r = _eval("soft_404_check", {"min_text_length": 200}, ctx)
        self.assertFalse(r["pass"])

    def test_soft_404_german_phrase_needs_seite(self):
        filler = "Inhalt " * 60
        ok = f"<html><body>{filler} Einige Kanäle könnten nicht gefunden werden.</body></html>"
        r = _eval("soft_404_check", {"min_text_length": 200}, _ctx(html=ok, http_status=200))
        self.assertTrue(r["pass"])
        bad = f"<html><body>{filler} Die Seite konnte leider nicht gefunden werden.</body></html>"
        r = _eval("soft_404_check", {"min_text_length": 200}, _ctx(html=bad, http_status=200))
        self.assertFalse(r["pass"])

    def test_soft_404_skip_when_not_200(self):
        ctx = _ctx(http_status=404)
        r = _eval("soft_404_check", {"min_text_length": 200}, ctx)
        # 404는 검증 대상이 아니므로 PASS 처리
        self.assertTrue(r["pass"])


# ── Accessibility ─────────────────────────────────────────────────────────────

class TestAccessibilityRules(unittest.TestCase):
    def test_landmark_count_pass(self):
        html = """
        <html><body>
          <header>head</header>
          <nav>nav</nav>
          <main>main</main>
          <footer>foot</footer>
        </body></html>"""
        r = _eval("landmark_count_min", {"min_landmarks": 3, "require_main": "yes"}, _ctx(html))
        self.assertTrue(r["pass"])

    def test_landmark_count_fail_no_main(self):
        html = "<html><body><nav></nav><header></header><footer></footer></body></html>"
        r = _eval("landmark_count_min", {"min_landmarks": 3, "require_main": "yes"}, _ctx(html))
        self.assertFalse(r["pass"])

    def test_landmark_count_fail_too_few(self):
        html = "<html><body><main></main></body></html>"
        r = _eval("landmark_count_min", {"min_landmarks": 3, "require_main": "yes"}, _ctx(html))
        self.assertFalse(r["pass"])

    def test_heading_no_jump_pass(self):
        html = "<h1>1</h1><h2>2</h2><h3>3</h3><h2>2</h2>"
        r = _eval("heading_no_jump", {}, _ctx(html))
        self.assertTrue(r["pass"])

    def test_heading_no_jump_fail(self):
        html = "<h1>1</h1><h3>3</h3>"  # h2 건너뜀
        r = _eval("heading_no_jump", {}, _ctx(html))
        self.assertFalse(r["pass"])

    def test_aria_missing_pass(self):
        html = """
        <button aria-label="close">X</button>
        <a href="/" title="home">Home</a>
        <input type="submit" value="Send">
        """
        r = _eval("aria_missing_ratio_max", {"max_ratio": 0.1}, _ctx(html))
        self.assertTrue(r["pass"])

    def test_aria_missing_fail(self):
        html = "<button></button>" * 5 + "<a href='/'></a>" * 5
        r = _eval("aria_missing_ratio_max", {"max_ratio": 0.1}, _ctx(html))
        self.assertFalse(r["pass"])


# ── SEO / 콘텐츠 ──────────────────────────────────────────────────────────────

class TestSEORules(unittest.TestCase):
    def test_canonical_self_pass(self):
        html = '<link rel="canonical" href="https://example.com/page">'
        ctx = _ctx(html, final_url="https://example.com/page")
        r = _eval("canonical_self", {}, ctx)
        self.assertTrue(r["pass"])

    def test_canonical_self_pass_relative(self):
        html = '<link rel="canonical" href="/page">'
        ctx = _ctx(html, final_url="https://example.com/page")
        r = _eval("canonical_self", {}, ctx)
        self.assertTrue(r["pass"])

    def test_canonical_self_fail_different(self):
        html = '<link rel="canonical" href="https://other.com/page">'
        ctx = _ctx(html, final_url="https://example.com/page")
        r = _eval("canonical_self", {}, ctx)
        self.assertFalse(r["pass"])

    def test_canonical_missing(self):
        ctx = _ctx("<html></html>")
        r = _eval("canonical_self", {}, ctx)
        self.assertFalse(r["pass"])

    def test_mixed_content_zero_pass(self):
        html = '<img src="https://example.com/a.jpg"><script src="/x.js"></script>'
        ctx = _ctx(html, final_url="https://example.com/")
        r = _eval("mixed_content_zero", {}, ctx)
        self.assertTrue(r["pass"])

    def test_mixed_content_zero_fail(self):
        html = '<img src="http://example.com/a.jpg">'
        ctx = _ctx(html, final_url="https://example.com/")
        r = _eval("mixed_content_zero", {}, ctx)
        self.assertFalse(r["pass"])

    def test_render_blocking_zero_pass(self):
        html = '<head><script src="/x.js" defer></script><script src="/y.js" async></script></head>'
        r = _eval("render_blocking_zero", {}, _ctx(html))
        self.assertTrue(r["pass"])

    def test_render_blocking_zero_fail(self):
        html = '<head><script src="/blocking.js"></script></head>'
        r = _eval("render_blocking_zero", {}, _ctx(html))
        self.assertFalse(r["pass"])

    def test_og_required_pass(self):
        html = """
        <meta property="og:title" content="Title">
        <meta property="og:image" content="https://example.com/img.jpg">
        """
        r = _eval("og_required_pairs", {"required": "title,image"}, _ctx(html))
        self.assertTrue(r["pass"])

    def test_og_required_fail_missing_image(self):
        html = '<meta property="og:title" content="Title">'
        r = _eval("og_required_pairs", {"required": "title,image"}, _ctx(html))
        self.assertFalse(r["pass"])
        self.assertIn("image", r["hint"])


# ── AI Readiness — JSON-LD ────────────────────────────────────────────────────

class TestSchemaRules(unittest.TestCase):
    def _ctx_with_jsonld(self, jsonld_data):
        ctx = _ctx()
        ctx["jsonld_raw"] = jsonld_data if isinstance(jsonld_data, list) else [jsonld_data]
        return ctx

    def test_organization_required_pass(self):
        data = {
            "@type": "Organization",
            "contactPoint": {"@type": "ContactPoint", "telephone": "+1"},
            "address": {"streetAddress": "123 Main"},
            "geo": {"latitude": 0, "longitude": 0},
            "hasMap": "https://maps.google.com/?q=...",
        }
        r = _eval("schema_required_fields",
                  {"type": "Organization", "fields": "contactPoint,address,geo,hasMap"},
                  self._ctx_with_jsonld(data))
        self.assertTrue(r["pass"])

    def test_organization_required_fail_missing(self):
        data = {"@type": "Organization", "contactPoint": {}, "address": {}}
        r = _eval("schema_required_fields",
                  {"type": "Organization", "fields": "contactPoint,address,geo,hasMap"},
                  self._ctx_with_jsonld(data))
        self.assertFalse(r["pass"])
        self.assertIn("geo", r["hint"])

    def test_product_dotted_path(self):
        data = {
            "@type": "Product",
            "name": "Test", "description": "D", "sku": "X1", "brand": {"@type": "Brand", "name": "LG"},
            "offers": {"@type": "Offer", "price": "999", "availability": "InStock"},
            "aggregateRating": {"@type": "AggregateRating", "ratingValue": "4.5"},
            "review": [{"@type": "Review", "reviewRating": {"ratingValue": "5"}}],
        }
        r = _eval("schema_required_fields",
                  {"type": "Product", "fields": "name,description,sku,brand,offers.price,offers.availability,aggregateRating.ratingValue,review"},
                  self._ctx_with_jsonld(data))
        self.assertTrue(r["pass"])

    def test_product_dotted_path_missing_nested(self):
        data = {
            "@type": "Product",
            "name": "Test", "description": "D", "sku": "X1", "brand": {"@type": "Brand", "name": "LG"},
            "offers": {"@type": "Offer", "price": "999"},  # availability 누락
        }
        r = _eval("schema_required_fields",
                  {"type": "Product", "fields": "name,description,sku,brand,offers.price,offers.availability"},
                  self._ctx_with_jsonld(data))
        self.assertFalse(r["pass"])
        self.assertIn("offers.availability", r["hint"])

    def test_faqpage_pass(self):
        data = {
            "@type": "FAQPage",
            "mainEntity": [{"@type": "Question", "name": "Q1", "acceptedAnswer": {"text": "A"}}],
        }
        r = _eval("schema_required_fields",
                  {"type": "FAQPage", "fields": "mainEntity"},
                  self._ctx_with_jsonld(data))
        self.assertTrue(r["pass"])

    def test_schema_alternative_fields(self):
        # sku|mpn|gtin13 — LG PDP 는 sku 대신 mpn 을 쓴다. 하나만 있어도 충족.
        data = {"@type": "Product", "name": "OLED65C4", "mpn": "OLED65C4PUA",
                "offers": {"@type": "Offer", "price": "1999", "availability": "InStock"}}
        r = _eval("schema_required_fields",
                  {"type": "Product", "fields": "name,sku|mpn|gtin13,offers.price"},
                  self._ctx_with_jsonld(data))
        self.assertTrue(r["pass"])
        # 대체 필드가 전부 없으면 누락으로 보고 그룹 전체를 hint 에 남긴다
        r = _eval("schema_required_fields",
                  {"type": "Product", "fields": "name,sku|gtin13"},
                  self._ctx_with_jsonld(data))
        self.assertFalse(r["pass"])
        self.assertIn("sku|gtin13", r["hint"])
        # VideoObject: url 대신 contentUrl (schema.org 표준)
        video = {"@type": "VideoObject", "name": "v", "description": "d", "thumbnailUrl": "t.jpg",
                 "contentUrl": "https://example.com/v.mp4"}
        r = _eval("schema_required_fields",
                  {"type": "VideoObject", "fields": "url|contentUrl|embedUrl,name,description,thumbnailUrl"},
                  self._ctx_with_jsonld(video))
        self.assertTrue(r["pass"])

    def test_schema_no_match_type(self):
        data = {"@type": "Article", "headline": "..."}
        r = _eval("schema_required_fields",
                  {"type": "Product", "fields": "name"},
                  self._ctx_with_jsonld(data))
        self.assertFalse(r["pass"])
        self.assertIn("Product", r["hint"])


# ── AI Readiness — Content ────────────────────────────────────────────────────

class TestContentRules(unittest.TestCase):
    def test_definition_pattern_pass(self):
        html = "<p>GEO는 검색 엔진 최적화를 말한다.</p><dfn>RAG</dfn>"
        r = _eval("definition_pattern_min", {"min_count": 1}, _ctx(html))
        self.assertTrue(r["pass"])

    def test_definition_pattern_fail(self):
        html = "<p>그냥 일반 문장입니다.</p>"
        r = _eval("definition_pattern_min", {"min_count": 1}, _ctx(html))
        self.assertFalse(r["pass"])

    def test_citable_density_pass(self):
        # 3문장 중 2문장에 패턴 → 66%
        html = "<p>매출이 30% 증가했다. 2024년 보고서에 따르면 좋다. 그냥 일반 문장.</p>"
        r = _eval("citable_density_min", {"min_ratio": 0.3}, _ctx(html))
        self.assertTrue(r["pass"])

    def test_citable_density_fail(self):
        html = "<p>좋아요. 멋져요. 훌륭해요. 환상적입니다. 완벽합니다.</p>"
        r = _eval("citable_density_min", {"min_ratio": 0.1}, _ctx(html))
        self.assertFalse(r["pass"])

    def test_citable_inch_abbreviation_pass(self):
        # 인치 축약(34")도 물리 단위로 인정 — \b 는 따옴표 뒤에서 성립하지 않아
        # 죽은 조항이었다 (2026-09-20, US PDP 실측)
        html = ('<p>Enjoy a 32" UHD display on a rolling stand. '
                'See more on a large 34" curved ultrawide smart display.</p>')
        r = _eval("citable_density_min", {"min_count": 2}, _ctx(html))
        self.assertTrue(r["pass"])

    def test_schema_media_inside_review_excluded(self):
        # 리뷰 위젯의 고객 사진은 페이지 ImageObject 로 세지 않는다 (2026-10-26)
        img = {"@type": "ImageObject", "contentUrl": "https://x/a.jpg", "name": "n", "description": "d"}
        raw = [{"review": [{"@type": "Review", "name": "r", "image": [img]}]},
               {"@type": "Product", "name": "p", "image": "https://x/p.jpg"}]
        params = {"type": "ImageObject", "fields": "url|contentUrl,name|caption,description",
                  "exclude_within": "Review,Comment"}
        self.assertFalse(_eval("schema_required_fields", params, {"jsonld_raw": raw})["pass"])
        raw.append({"@type": "ImageObject", "contentUrl": "https://x/b.jpg", "name": "n", "description": "d"})
        self.assertTrue(_eval("schema_required_fields", params, {"jsonld_raw": raw})["pass"])

    def test_citable_min_count_by_type(self):
        # 트러블슈팅·PLP 는 짧은 콘텐츠라 3개 (2026-10-26). 다른 타입은 min_count 그대로.
        html = "<p>매출이 30% 증가했다. 2024년 보고서에 따르면 좋다. 무게는 12kg 이다. 그냥 일반 문장.</p>"
        params = {"min_count": 5, "min_count_by_type": "support_troubleshoot:3,plp:3"}
        ctx = _ctx(html); ctx["page_type"] = {"id": "support_troubleshoot"}
        self.assertTrue(_eval("citable_density_min", params, ctx)["pass"])
        ctx["page_type"] = {"id": "plp"}
        self.assertTrue(_eval("citable_density_min", params, ctx)["pass"])
        ctx["page_type"] = {"id": "pdp"}
        r = _eval("citable_density_min", params, ctx)
        self.assertFalse(r["pass"])
        self.assertIn("5개 이상", r["hint"])

    def test_summary_label_tag_pass(self):
        # US PDP(MUI)의 <p>Key features</p> 라벨 — label_tags: p 로 잡는다
        html = '<p class="MuiTypography-body2">Key features</p><ul><li>32" UHD</li></ul>'
        r = _eval("class_id_contains",
                  {"keywords": "summary,key features", "match_class": "no",
                   "label_tags": "p"}, _ctx(html))
        self.assertTrue(r["pass"])

    def test_citable_certification_names_pass(self):
        # 숫자 없는 제3자 인증·표준 문장도 인용 가능으로 센다 (2026-09-20 확장)
        html = ("<p>This TV supports Dolby Vision and Dolby Atmos. "
                "Certified by Intertek for hygiene performance. "
                "FreeSync Premium eliminates screen tearing.</p>")
        r = _eval("citable_density_min", {"min_count": 3}, _ctx(html))
        self.assertTrue(r["pass"])

    def test_summary_aem_floating_features_pass(self):
        # 구 AEM PDP(비US)의 Key features 블록 — 라벨이 현지어(Principais recursos·
        # Hauptmerkmale 등)라 키워드로는 못 잡고 selector 로 잡는다 (2026-09-20)
        html = ('<div class="c-floating-features"><div><p class="tit">Hauptmerkmale</p>'
                '<ul><li>Intellowave und Grillfunktion</li><li>28 Liter Kapazität</li>'
                '<li>16 Automatikprogramme</li><li>Eco-On-Energiesparfunktion</li></ul>'
                '</div></div>')
        r = _eval("class_id_contains",
                  {"keywords": "summary", "match_class": "no",
                   "block_selector": "p.info-desc, p.description, div.c-floating-features",
                   "block_min_chars": 80, "block_min_lines": 1}, _ctx(html))
        self.assertTrue(r["pass"])

    def test_citable_dutch_patterns_pass(self):
        # 네덜란드어 지원 (베네룩스 추가, 2026-09-30)
        html = ("<p>Volgens een onderzoek verbruikt dit model 3 keer minder energie. "
                "Getest door onafhankelijke instituten. Meer dan 2 miljoen huishoudens.</p>")
        r = _eval("citable_density_min", {"min_count": 3}, _ctx(html))
        self.assertTrue(r["pass"])

    def test_definition_dutch_pass(self):
        html = "<p>OLED staat voor Organic Light Emitting Diode.</p>"
        r = _eval("definition_pattern_min", {"min_count": 1}, _ctx(html))
        self.assertTrue(r["pass"])

    def test_notification_banner_excluded_from_citable(self):
        # NL 전 페이지 프로모 스트립 — 보일러플레이트로 제거돼야 한다 (2026-09-30 실측:
        # 트러블슈팅 #36 이 100% 허수). sr-only 카루셀 라벨도 본문이 아니다.
        html = ('<div class="c-notification-banner__text"><p>Wordt LG Member en krijg '
                '2% korting op je eerste aankoop! Altijd gratis verzending.</p></div>'
                '<span class="sr-only">Vorige dia 2025</span>'
                '<p>Gewone tekst zonder cijfers hier.</p>')
        r = _eval("citable_density_min", {"min_count": 1}, _ctx(html))
        self.assertFalse(r["pass"])

    def test_hidden_modal_excluded_from_body(self):
        # US help-library 전 페이지의 브라우저 지원 안내 모달이 본문 첫 문장으로 잡혀
        # #33 모델 탐색을 허위 통과시켰다(2026-10-19, 67/100). 모달/다이얼로그는 본문이 아니다.
        html = ('<div class="modal-contentainer"><div class="modal-body"><p>LG.com utilizes '
                'responsive design to provide a convenient experience.</p></div></div>'
                '<div role="dialog" class="c-dialog"><p>OLED is a display technology.</p></div>'
                '<p>Press the power button.</p>')
        self.assertEqual(_visible_text(_ctx(html)["soup"], strip_boilerplate=True),
                         "Press the power button.")

    def test_summary_label_tag_off_by_default(self):
        # label_tags 미지정이면 <p> 라벨은 스캔하지 않는다 (#32 오탐 방지)
        html = '<p>Key features</p>'
        r = _eval("class_id_contains",
                  {"keywords": "summary,key features", "match_class": "no"}, _ctx(html))
        self.assertFalse(r["pass"])

    def test_image_filename_keyword_pass(self):
        html = '<img src="/products/lg-oled-c4.jpg"><img src="/products/lg-gram-pro.png">'
        r = _eval("image_filename_keyword", {"keywords": "lg,oled,gram", "min_ratio": 0.5}, _ctx(html))
        self.assertTrue(r["pass"])

    def test_image_filename_keyword_fail(self):
        html = '<img src="/img/IMG_1234.jpg"><img src="/img/photo_5678.png">'
        r = _eval("image_filename_keyword", {"keywords": "lg,oled,gram", "min_ratio": 0.5}, _ctx(html))
        self.assertFalse(r["pass"])

    def test_author_meta_pass(self):
        html = '<meta name="author" content="홍길동">'
        r = _eval("author_or_source", {}, _ctx(html))
        self.assertTrue(r["pass"])

    def test_author_byline_pass(self):
        html = '<div class="byline">By 김기자</div>'
        r = _eval("author_or_source", {}, _ctx(html))
        self.assertTrue(r["pass"])

    def test_author_date_plus_source_pass(self):
        html = '<time datetime="2026-01-01">2026-01-01</time><cite>LG Research</cite>'
        r = _eval("author_or_source", {}, _ctx(html))
        self.assertTrue(r["pass"])

    def test_author_fail(self):
        html = "<p>그냥 글</p>"
        r = _eval("author_or_source", {}, _ctx(html))
        self.assertFalse(r["pass"])

    def test_ssr_text_ratio_pass(self):
        ctx = _ctx()
        ctx["csr_ratio_dict"] = {"status": "ok", "ratio": 0.8}
        r = _eval("ssr_text_ratio_min", {"min_ratio": 0.6}, ctx)
        self.assertTrue(r["pass"])

    def test_ssr_text_ratio_fail(self):
        ctx = _ctx()
        ctx["csr_ratio_dict"] = {"status": "ok", "ratio": 0.3}
        r = _eval("ssr_text_ratio_min", {"min_ratio": 0.6}, ctx)
        self.assertFalse(r["pass"])

    def test_ssr_text_ratio_unavailable(self):
        ctx = _ctx()
        ctx["csr_ratio_dict"] = {"status": "unavailable", "ratio": None}
        r = _eval("ssr_text_ratio_min", {"min_ratio": 0.6}, ctx)
        self.assertFalse(r["pass"])


# ── Sitemap 국가 디렉토리 감지 ────────────────────────────────────────────────

class TestCitableEEATCorpus(unittest.TestCase):
    """#36 E-E-A-T 확장 패턴의 코퍼스 게이트 (2026-09-20).

    패턴 추가·수정 시 이 코퍼스가 항상 지켜져야 한다:
      양성(EEAT 관점 인용 가치 문장, 숫자 없음) → 반드시 매칭
      음성(마케팅 플러프·UI·법률 문구)        → 절대 비매칭
    방법론: docs/citable-pattern-methodology.md
    """
    POSITIVES = [
        # 경험(E) — 실측·시험
        "We tested the washer under heavy-load conditions and found no vibration issues.",
        "In our lab, the compressor remained below audible noise thresholds.",
        "The filter was independently tested by an external laboratory.",
        "Real-world tested across humid climates for durability.",
        "Der Motor wurde geprüft von unabhängigen Instituten.",
        "Probado por laboratorios independientes para garantizar su rendimiento.",
        "Testado por institutos independentes de qualidade.",
        "Sản phẩm được kiểm nghiệm bởi viện nghiên cứu độc lập.",
        "내구성 시험 결과 이상이 발견되지 않았습니다.",
        # 전문성(X) — 특허·공동 개발
        "The patented Direct Drive system reduces mechanical wear.",
        "Developed in collaboration with professional sound engineers.",
        "Tecnología patentada que protege el tambor.",
        "Motor patenteado que reduz o ruído.",
        "특허 받은 인버터 기술이 적용되었습니다.",
        # 권위(A) — 전문가·기관·연구
        "Recommended by dermatologists for sensitive skin.",
        "Trusted by professional chefs worldwide.",
        "Research shows steam cycles remove common allergens.",
        "Official partner of the national football league.",
        "Empfohlen von unabhängigen Prüfinstituten.",
        "Recomendado por expertos en cuidado de la ropa.",
        "Sản phẩm được các chuyên gia khuyên dùng.",
        # 신뢰(T) — 임상·과학적 입증
        "Clinically proven to reduce allergens in bedding.",
        "The steam function is proven to kill common bacteria.",
        "Dermatologist-tested for gentle fabric care.",
        "Klinisch getestet für empfindliche Haut.",
        "Clínicamente probado para pieles sensibles.",
        "Clinicamente comprovado no cuidado com tecidos.",
    ]
    NEGATIVES = [
        "Designed to elevate your everyday life.",
        "Experience immersive entertainment like never before.",
        "Discover a new world of possibilities.",
        "Engineered for those who demand more.",
        "Style that speaks for itself.",
        "Sign in to your account to continue shopping.",
        "Add to cart and check out today.",
        "Find a store near you.",
        "Compare products side by side.",
        "Subscribe to our newsletter for exclusive offers.",
        "Free delivery on eligible orders.",
        "This model is currently out of stock.",
        "Erleben Sie Unterhaltung auf einem neuen Niveau.",
        "Descubre un nuevo mundo de entretenimiento.",
        "Descubra um novo padrão de conforto.",
        "Trải nghiệm giải trí đỉnh cao.",
        "당신의 일상을 바꿔줄 프리미엄 디자인.",
        "We are committed to your satisfaction.",
        "Our design philosophy embraces simplicity.",
        "Trusted quality since day one.",
        "Recommended for large families.",
        "Proven design language.",
        "Tested styles for every home.",
    ]

    def test_positives_all_match(self):
        from rule_engine import _CITABLE_PATTERNS
        missed = [s for s in self.POSITIVES
                  if not any(p.search(s) for p in _CITABLE_PATTERNS)]
        self.assertEqual(missed, [], f"양성 미탐 {len(missed)}건")

    def test_negatives_none_match(self):
        from rule_engine import _CITABLE_PATTERNS
        fp = [s for s in self.NEGATIVES
              if any(p.search(s) for p in _CITABLE_PATTERNS)]
        self.assertEqual(fp, [], f"음성 오탐 {len(fp)}건")


class TestSitemapCountryDetection(unittest.TestCase):
    def test_country_kr(self):
        self.assertEqual(_detect_country_dir("https://www.lg.com/kr/products/oled"), "kr")

    def test_country_us(self):
        self.assertEqual(_detect_country_dir("https://www.lg.com/us/tvs/123"), "us")

    def test_locale_en_us(self):
        self.assertEqual(_detect_country_dir("https://www.lg.com/en-us/about"), "en-us")

    def test_no_country_root_path(self):
        self.assertIsNone(_detect_country_dir("https://www.lg.com/products"))

    def test_no_country_for_static_paths(self):
        self.assertIsNone(_detect_country_dir("https://example.com/js/app.js"))
        self.assertIsNone(_detect_country_dir("https://example.com/css/main.css"))
        self.assertIsNone(_detect_country_dir("https://example.com/api/v1/x"))

    def test_no_country_for_long_first_segment(self):
        self.assertIsNone(_detect_country_dir("https://example.com/products"))


# ── 기존 sync 룰 (css_*, schema_type_exists 등) ───────────────────────────────

class TestLegacyRules(unittest.TestCase):
    def test_css_exists_pass(self):
        r = _eval("css_exists", {"selector": "h1"}, _ctx("<h1>t</h1>"))
        self.assertTrue(r["pass"])

    def test_css_exists_fail(self):
        r = _eval("css_exists", {"selector": "h1"}, _ctx("<p>t</p>"))
        self.assertFalse(r["pass"])

    def test_css_count_eq_pass(self):
        r = _eval("css_count", {"selector": "h1", "operator": "==", "value": 1}, _ctx("<h1>a</h1>"))
        self.assertTrue(r["pass"])

    def test_css_count_eq_fail(self):
        r = _eval("css_count", {"selector": "h1", "operator": "==", "value": 1}, _ctx("<h1>a</h1><h1>b</h1>"))
        self.assertFalse(r["pass"])

    def test_css_text_min_length(self):
        r = _eval("css_text_min_length", {"selector": "title", "min_length": 1},
                  _ctx("<title>Hello</title>"))
        self.assertTrue(r["pass"])

    def test_css_attr_exists_pass(self):
        html = '<meta name="description" content="some content">'
        r = _eval("css_attr_exists",
                  {"selector": "meta[name='description' i]", "attr": "content", "min_length": 1},
                  _ctx(html))
        self.assertTrue(r["pass"])

    def test_css_attr_not_contains_pass(self):
        html = '<meta name="robots" content="all">'
        r = _eval("css_attr_not_contains",
                  {"selector": "meta[name='robots' i]", "attr": "content", "value": "noindex"},
                  _ctx(html))
        self.assertTrue(r["pass"])

    def test_css_attr_not_contains_fail(self):
        html = '<meta name="robots" content="noindex">'
        r = _eval("css_attr_not_contains",
                  {"selector": "meta[name='robots' i]", "attr": "content", "value": "noindex"},
                  _ctx(html))
        self.assertFalse(r["pass"])

    def test_css_all_have_attr_pass(self):
        html = '<img src="a" alt="a"><img src="b" alt="b">'
        r = _eval("css_all_have_attr", {"selector": "img", "attr": "alt"}, _ctx(html))
        self.assertTrue(r["pass"])

    def test_css_all_have_attr_fail(self):
        html = '<img src="a" alt="a"><img src="b">'
        r = _eval("css_all_have_attr", {"selector": "img", "attr": "alt"}, _ctx(html))
        self.assertFalse(r["pass"])

    def test_class_id_contains(self):
        html = '<div class="faq-section">…</div>'
        r = _eval("class_id_contains", {"keywords": "faq", "tags": "div"}, _ctx(html))
        self.assertTrue(r["pass"])

    def test_text_has_pattern(self):
        html = "<p>매출 500억원 달성</p>"
        r = _eval("text_has_pattern", {"pattern": "\\d", "tags": "p"}, _ctx(html))
        self.assertTrue(r["pass"])

    def test_schema_type_exists_or(self):
        ctx = _ctx()
        ctx["jsonld_types"] = {"individualproduct"}
        r = _eval("schema_type_exists", {"type": "Product, IndividualProduct"}, ctx)
        self.assertTrue(r["pass"])

    def test_schema_type_exists_fail(self):
        ctx = _ctx()
        ctx["jsonld_types"] = {"article"}
        r = _eval("schema_type_exists", {"type": "Product"}, ctx)
        self.assertFalse(r["pass"])

    def test_heading_order_pass(self):
        r = _eval("heading_order", {}, _ctx("<h1>a</h1><h2>b</h2>"))
        self.assertTrue(r["pass"])

    def test_heading_order_fail(self):
        r = _eval("heading_order", {}, _ctx("<h2>b</h2><h1>a</h1>"))
        self.assertFalse(r["pass"])

    def test_redirect_max_pass(self):
        ctx = _ctx(redirect_count=1)
        r = _eval("redirect_max", {"max_count": 1}, ctx)
        self.assertTrue(r["pass"])

    def test_redirect_max_fail(self):
        ctx = _ctx(redirect_count=3)
        r = _eval("redirect_max", {"max_count": 1}, ctx)
        self.assertFalse(r["pass"])

    def test_aria_excludes_hidden_input_and_anchor_target(self):
        # type=hidden 과 href 없는 a는 인터랙티브 카운트에서 제외 (#10)
        html = '<input type="hidden" name="csrf"><a name="anchor"></a>'
        r = _eval("aria_missing_ratio_max", {"max_ratio": 0.1}, _ctx(html))
        self.assertTrue(r["pass"])


# ── async 룰: sitemap_recent (httpx MockTransport) ────────────────────────────

class TestSitemapRecent(unittest.TestCase):
    """httpx MockTransport로 외부 호출 없이 sitemap_recent 동작을 검증."""

    def _run(self, params, ctx, transport):
        import rule_engine as re_mod
        original = httpx.AsyncClient
        def patched(*a, **kw):
            kw["transport"] = transport
            return original(*a, **kw)
        re_mod.httpx.AsyncClient = patched
        try:
            return asyncio.run(evaluate_rule_async(
                {"type": "sitemap_recent", "params": params}, ctx))
        finally:
            re_mod.httpx.AsyncClient = original

    def test_recent_lastmod_pass(self):
        from datetime import datetime, timezone
        recent = datetime.now(timezone.utc).date().isoformat()
        body = f"<urlset><url><loc>x</loc><lastmod>{recent}</lastmod></url></urlset>"
        def handler(req):
            return httpx.Response(200, text=body)
        ctx = _ctx()
        ctx["base_url"] = "https://example.com"
        ctx["current_url"] = "https://example.com/"
        r = self._run({"path": "/sitemap.xml", "max_days": 30, "auto_country": "no"}, ctx,
                      httpx.MockTransport(handler))
        self.assertTrue(r["pass"])

    def test_old_lastmod_fail(self):
        body = "<urlset><url><loc>x</loc><lastmod>2020-01-01</lastmod></url></urlset>"
        def handler(req):
            return httpx.Response(200, text=body)
        ctx = _ctx()
        ctx["base_url"] = "https://example.com"
        ctx["current_url"] = "https://example.com/"
        r = self._run({"path": "/sitemap.xml", "max_days": 30, "auto_country": "no"}, ctx,
                      httpx.MockTransport(handler))
        self.assertFalse(r["pass"])

    def test_country_dir_priority(self):
        """국가 디렉토리(/kr/sitemap.xml)를 우선 시도하는지 확인."""
        from datetime import datetime, timezone
        recent = datetime.now(timezone.utc).date().isoformat()
        seen_paths = []
        def handler(req):
            seen_paths.append(req.url.path)
            if req.url.path == "/kr/sitemap.xml":
                return httpx.Response(200, text=f"<urlset><url><lastmod>{recent}</lastmod></url></urlset>")
            return httpx.Response(404)
        ctx = _ctx()
        ctx["base_url"] = "https://example.com"
        ctx["current_url"] = "https://example.com/kr/products/x"
        r = self._run({"path": "/sitemap.xml", "max_days": 30, "auto_country": "yes"}, ctx,
                      httpx.MockTransport(handler))
        self.assertTrue(r["pass"])
        self.assertEqual(seen_paths[0], "/kr/sitemap.xml")
        self.assertIn("국가 디렉토리", r["value"])


# ── 핸들러 / RULE_TYPES 일관성 ────────────────────────────────────────────────

class TestRegistryConsistency(unittest.TestCase):
    def test_all_rule_types_have_handlers(self):
        all_handlers = set(_HANDLERS.keys()) | set(_ASYNC_HANDLERS.keys())
        for rt in RULE_TYPES:
            self.assertIn(rt, all_handlers, f"룰 타입 '{rt}'에 핸들러 미등록")

    def test_all_handlers_in_rule_types(self):
        all_handlers = set(_HANDLERS.keys()) | set(_ASYNC_HANDLERS.keys())
        for h in all_handlers:
            self.assertIn(h, RULE_TYPES, f"핸들러 '{h}'가 RULE_TYPES에 미정의")

    def test_scoring_config_rules_resolvable(self):
        import json as _json
        with open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                               "scoring_config.json"), "r", encoding="utf-8") as f:
            cfg = _json.load(f)
        all_handlers = set(_HANDLERS.keys()) | set(_ASYNC_HANDLERS.keys())
        for cat_key, cat in cfg.items():
            if not isinstance(cat, dict) or "criteria" not in cat:
                continue
            for cr in cat["criteria"]:
                rt = cr.get("rule", {}).get("type", "")
                if rt:
                    self.assertIn(rt, all_handlers,
                                  f"{cat_key}.{cr['id']}: 룰 타입 '{rt}' 핸들러 없음")


class TestJudgedCorpusR1(unittest.TestCase):
    """2026-10-17 사용자 판정(그림자 모드 1차)에서 '아니오'/'예'로 확정된 문장."""
    NEG_36 = [
        "Sign in Join us Welcome coupon New LG Members can use the Welcome Coupon towards their next purchase over $500.",
        "Browse LG’s Range of Speakers & Sound Systems Now Ventajas de comprar en LG Iniciar sesión Registrarse Hasta 10% de descuento 5% dto por primera compra en el pago.",
        "0% interest for: 12 months: Single purchase value of over £1,000.",
        "Quy định chung: Thời gian trả góp: 3, 6, 9 và 12 tháng.",
        "Tặng Bộ sản phẩm chuyên dụng LG trị giá 950.000 VNĐ khi mua Máy rửa bát LG LDT14BGA3, LDT14SVA4, LDT14BLA4.",
        "Media Contacts: LG Electronics USA Taryn Brucia 201 816 2187 taryn.brucia@lge.com Related Content October 16, 2026",
        "LG UNVEILS TWO GROUNDBREAKING SMARTPHONES Corporate 02/24/2019 Print Share this content.",
    ]
    POS_36 = [
        "*Die Angabe zur Reaktionszeit von 0,03 ms (GtG) bezieht sich auf LG UlraGear-Modelle mit OLED.",
        "4 Variable refresh rate (VRR) is supported on models 17Z90R and 16Z90R with GPU option only.",
        "Prueba esto Los modelos lanzados en 2022 (webOS 22) y posteriores no son compatibles con la función Time Machine.",
        "Plasmaster ™ Ionizer++ Loại bỏ vi khuẩn bám dính tới 99,9% Thanh lọc không khí trong phòng.",
    ]

    def _cit(self, s):
        return not _CITABLE_NOISE.search(s) and any(p.search(s) for p in _CITABLE_PATTERNS)

    def test_neg_36(self):
        for s in self.NEG_36:
            self.assertFalse(self._cit(s), s)

    def test_pos_36(self):
        for s in self.POS_36:
            self.assertTrue(self._cit(s), s)

    def test_doctype_and_title_not_body(self):
        soup = BeautifulSoup("<!DOCTYPE html><html><head><title>22kg Washer | LG</title></head>"
                             "<body><p>Hello world.</p></body></html>", "html.parser")
        self.assertEqual(_visible_text(soup, strip_boilerplate=True), "Hello world.")

    def _def(self, body):
        return _HANDLERS["definition_pattern_min"]({"min_count": 1}, _ctx(f"<html><body><p>{body}</p></body></html>"))["pass"]

    def test_definition_rejects_notices_and_demonstratives(self):
        self.assertFalse(self._def("PayPal Credit is a regulated credit agreement."))
        self.assertFalse(self._def("All other trademarks are the property of their respective owners."))
        self.assertFalse(self._def("Đây là một cách dễ dàng để theo dõi mặt hàng đặc biệt."))

    def test_definition_keeps_real_definition(self):
        self.assertTrue(self._def("LG is a world-leading producer of TVs, refrigerators and air conditioners."))


if __name__ == "__main__":
    unittest.main(verbosity=2)


class TestModelBackedRules(unittest.TestCase):
    """#33·#36 모델 결합 — audit_model.label_sentence 를 가짜로 바꿔 검증한다."""

    def setUp(self):
        import audit_model
        self.am = audit_model
        self._url, self._fn = audit_model.MODEL_URL, audit_model.label_sentence
        audit_model.MODEL_URL = "http://model.test"

    def tearDown(self):
        self.am.MODEL_URL, self.am.label_sentence = self._url, self._fn

    def _fake(self, rule):
        calls = []
        async def fake(sentence, client):
            calls.append(sentence)
            return rule(sentence)
        self.am.label_sentence = fake
        return calls

    def _run(self, rule_type, params, ctx):
        from rule_engine import evaluate_rule_async
        return asyncio.run(evaluate_rule_async({"type": rule_type, "params": params}, ctx))

    CITABLE_HTML = ("<p>Sales grew 30% in 2024. The 2023 report says 45% rose. "
                    "It measures 120 cm wide. It weighs 25 kg. Just a plain sentence.</p>")

    def test_citable_model_confirms_subset(self):
        # 정규식 후보 4문장 중 모델이 2문장만 y → min_count 3 FAIL, 제외 사유가 hint 에 남는다
        calls = self._fake(lambda s: {"citable": "y" if "grew" in s or "report" in s else "n",
                                      "why": "단순 치수"})
        # 후보로 못 채우면 나머지 본문("Just a plain sentence.")도 모델로 훑는다 → 5회 호출
        r = self._run("citable_density_min", {"min_count": 3}, _ctx(self.CITABLE_HTML))
        self.assertFalse(r["pass"])
        self.assertTrue(r["value"].startswith("모델 확인 2/5"))
        self.assertIn("본문 1문장 추가 탐색", r["value"])
        self.assertIn("단순 치수", r["hint"])
        self.assertEqual(len(calls), 5)

    def test_citable_body_scan_counts_non_regex_sentences(self):
        # 숫자 없는 원인 설명문(트러블슈팅)이 정규식 후보가 아니어도 모델이 y 면 센다
        html = ("<p>The LAN cable may be loose, disconnected, or damaged. "
                "Dust buildup on the filter can reduce air purification performance. "
                "Sales grew 30% in 2024.</p>")
        calls = self._fake(lambda s: {"citable": "y"})
        r = self._run("citable_density_min", {"min_count": 3}, _ctx(html))
        self.assertTrue(r["pass"])
        self.assertEqual(len(calls), 3)
        self.assertIn("본문 2문장 추가 탐색", r["value"])
        # model_scan_max 로 본문 탐색 범위를 제한할 수 있다
        calls = self._fake(lambda s: {"citable": "y" if "%" in s else "n"})
        r = self._run("citable_density_min", {"min_count": 3, "model_scan_max": 1}, _ctx(html))
        self.assertFalse(r["pass"])
        self.assertEqual(len(calls), 2)

    def test_citable_dedupes_repeated_sentences(self):
        # Shadow DOM + 일반 DOM 중복 추출 문장은 한 번만 센다
        html = "<p>Sales grew 30% in 2024.</p><div><p>Sales grew 30% in 2024.</p></div>"
        calls = self._fake(lambda s: {"citable": "y"})
        r = self._run("citable_density_min", {"min_count": 2}, _ctx(html))
        self.assertFalse(r["pass"])
        self.assertEqual(len(calls), 1)

    def test_citable_model_early_stop(self):
        calls = self._fake(lambda s: {"citable": "y"})
        r = self._run("citable_density_min", {"min_count": 2}, _ctx(self.CITABLE_HTML))
        self.assertTrue(r["pass"])
        self.assertEqual(len(calls), 2)

    def test_citable_model_unavailable_falls_back_to_regex(self):
        async def down(sentence, client):
            raise self.am.ModelUnavailable("connection refused")
        self.am.label_sentence = down
        r = self._run("citable_density_min", {"min_count": 3}, _ctx(self.CITABLE_HTML))
        self.assertTrue(r["pass"])           # 정규식 후보 4개 ≥ 3
        self.assertIn("정규식(모델 미연결)", r["value"])

    def test_citable_model_param_no_uses_regex(self):
        calls = self._fake(lambda s: {"citable": "n"})
        r = self._run("citable_density_min", {"min_count": 3, "model": "no"}, _ctx(self.CITABLE_HTML))
        self.assertTrue(r["pass"])
        self.assertEqual(calls, [])

    def test_definition_model_rejects_regex_match(self):
        html = "<p>GEO는 검색 엔진 최적화를 말한다.</p>"
        self._fake(lambda s: {"definition": "n", "why": "막연한 서술"})
        r = self._run("definition_pattern_min", {"min_count": 1}, _ctx(html))
        self.assertFalse(r["pass"])
        self.assertIn("막연한 서술", r["hint"])

    def test_definition_model_scans_when_regex_finds_nothing(self):
        # 패턴 0건이면 본문 문장을 모델로 훑어 정의문을 찾는다 (정규식 OR 모델)
        html = ("<p>The R1 Compressor reduces noise by up to 4dB in homes and offices. "
                "Another plain sentence about nothing in particular here.</p>")
        calls = self._fake(lambda s: {"definition": "y" if "Compressor" in s else "n"})
        r = self._run("definition_pattern_min", {"min_count": 1}, _ctx(html))
        self.assertTrue(r["pass"])
        self.assertIn("모델 탐색", r["value"])
        self.assertEqual(len(calls), 1)      # 첫 문장에서 조기 종료

    def test_definition_dfn_counts_without_model_call(self):
        html = "<p>Plain text only here with enough length.</p><dfn>RAG</dfn>"
        calls = self._fake(lambda s: {"definition": "n"})
        r = self._run("definition_pattern_min", {"min_count": 1}, _ctx(html))
        self.assertTrue(r["pass"])
        self.assertEqual(calls, [])
