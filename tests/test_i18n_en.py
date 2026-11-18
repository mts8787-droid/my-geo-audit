"""검사 화면 EN 모드 변환(i18n_en) — 판정 근거 문형이 영어로 바뀌는지."""
import re
import unittest

import i18n_en as T

_HANGUL = re.compile(r"[가-힣]")


class TestTr(unittest.TestCase):
    def test_patterns(self):
        cases = {
            "이 항목은 pdp 페이지에서만 평가됩니다 (현재: plp)": "Evaluated only on pdp pages (current: plp)",
            "@type='FAQPage' 노드 없음": "No @type='FAQPage' node",
            "23개 중 21개 'alt' 보유": "21 of 23 have 'alt'",
            "SSR 비율 47% — 60% 이상 필요": "SSR ratio 47% — 60% or more required",
            "HTTP/1.1 — HTTP/2 이상 필요": "HTTP/1.1 — HTTP/2 or more required",
            "국가 디렉토리(/us/sitemap.xml) lastmod=2026-11-02": "Country directory (/us/sitemap.xml) lastmod=2026-11-02",
        }
        for ko, en in cases.items():
            self.assertEqual(T.tr(ko), en)

    def test_model_reasons(self):
        self.assertEqual(T.tr("인용 가능 문장 1개 — 5개 이상 필요 (모델 제외 사유: 스펙표 조각, 법적 고지)"),
                         "1 citable sentence(s) — 5 or more required (model exclusion: spec-table fragment, legal notice)")
        # 모르는 사유는 빼고, 남는 게 없으면 일반 문구
        self.assertEqual(T.tr("정의문 0건 — 1건 이상 필요 (모델 제외 사유: 증상의 원인 설명(트러블슈팅))"),
                         "0 definition sentence(s) — 1 or more required (excluded by the sentence model)")

    def test_keywords_drop_korean(self):
        self.assertEqual(T.tr("키워드(faq, 자주 묻는, 자주묻는...)를 포함한 요소를 찾을 수 없습니다."),
                         "No element contains the keywords (faq...).")

    def test_non_korean_unchanged(self):
        for s in ("gzip", None, "", "Body text with Tính năng chính"):
            self.assertEqual(T.tr(s), s)


class TestTranslateResult(unittest.TestCase):
    def test_result_copy(self):
        r = {"page_type": {"id": "pdp", "label": "제품 상세 (PDP)"},
             "score": {"breakdown": {"seo": {"label": "Basic SEO", "items": {
                 "seo_title": {"label": "#13 Title 존재", "pass": False, "value": None, "hint": "'title' 요소를 찾을 수 없습니다."}}}}}}
        e = T.translate_result(r)
        self.assertEqual(e["page_type"]["label"], "Product detail (PDP)")
        it = e["score"]["breakdown"]["seo"]["items"]["seo_title"]
        self.assertEqual(it["label"], "#13 Title present")
        self.assertEqual(it["hint"], "Element 'title' not found.")
        self.assertEqual(r["page_type"]["label"], "제품 상세 (PDP)")  # 원본 유지

    def test_client_table_js_compatible(self):
        tb = T.client_table()
        for a, b in tb["patterns"]:
            re.compile(a)
            self.assertNotIn("\\1", b)
        self.assertFalse(any(_HANGUL.search(v) for v in tb["items"].values()))


if __name__ == "__main__":
    unittest.main()
