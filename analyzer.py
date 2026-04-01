import re
import asyncio
import httpx
from bs4 import BeautifulSoup
import json
import os
import copy
from typing import Optional
from urllib.parse import urlparse
from rule_engine import evaluate_rule, evaluate_rule_async, RULE_TYPES

# Playwright 동시 실행 제한 (메모리 보호)
_playwright_sem = asyncio.Semaphore(2)

# 벌크 분석 시 동시 요청 제한
_bulk_sem = asyncio.Semaphore(5)

# ── 채점 설정 관리 ──────────────────────────────────────────────────────────────

_CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scoring_config.json")

_DEFAULT_CONFIG = None  # scoring_config.json에서 로드, 없으면 파일 기본값 사용

def _load_default_config():
    """소스 코드에 하드코딩하지 않고, scoring_config.json의 초기 상태를 기본값으로 사용."""
    return {
        "seo_tags": {"max": 20, "label": "SEO Tags", "description": "기본 SEO 태그 검사", "criteria": [
            {"id": "title", "name": "Title 태그", "points": 2, "enabled": True, "rule": {"type": "css_text_min_length", "params": {"selector": "title", "min_length": 10}}},
            {"id": "desc", "name": "Meta Description", "points": 2, "enabled": True, "rule": {"type": "css_attr_exists", "params": {"selector": "meta[name='description' i]", "attr": "content", "min_length": 50}}},
            {"id": "canonical", "name": "Canonical 태그", "points": 2, "enabled": True, "rule": {"type": "css_attr_exists", "params": {"selector": "link[rel~='canonical']", "attr": "href"}}},
            {"id": "h1", "name": "H1 고유성", "points": 2, "enabled": True, "rule": {"type": "css_count", "params": {"selector": "h1", "operator": "==", "value": 1}}},
            {"id": "img_alt", "name": "이미지 Alt", "points": 2, "enabled": True, "rule": {"type": "css_all_have_attr", "params": {"selector": "img", "attr": "alt"}}},
            {"id": "redirect", "name": "리다이렉트 체인", "points": 2, "enabled": True, "rule": {"type": "redirect_max", "params": {"max_count": 3}}},
            {"id": "og_title", "name": "og:title", "points": 2, "enabled": True, "rule": {"type": "css_attr_exists", "params": {"selector": "meta[property='og:title']", "attr": "content"}}},
            {"id": "og_desc", "name": "og:description", "points": 2, "enabled": True, "rule": {"type": "css_attr_exists", "params": {"selector": "meta[property='og:description']", "attr": "content"}}},
            {"id": "og_image", "name": "og:image", "points": 2, "enabled": True, "rule": {"type": "css_attr_exists", "params": {"selector": "meta[property='og:image']", "attr": "content"}}},
            {"id": "robots", "name": "Meta Robots (noindex 아님)", "points": 2, "enabled": True, "rule": {"type": "css_attr_not_contains", "params": {"selector": "meta[name='robots' i]", "attr": "content", "value": "noindex"}}},
        ]},
        "robots_txt": {"max": 10, "label": "robots.txt AI 봇 허용", "description": "AI 크롤러 봇 허용 비율 (특수 로직)", "criteria": [], "special": "robots_ratio"},
        "json_ld": {"max": 15, "label": "JSON-LD 구조화 데이터", "description": "필수 스키마 + 보조 스키마", "criteria": [
            {"id": "product", "name": "필수: Product 스키마", "points": 8, "enabled": True, "rule": {"type": "schema_type_exists", "params": {"type": "product,individualproduct"}}},
            {"id": "breadcrumb", "name": "보조: BreadcrumbList/Organization", "points": 7, "enabled": True, "rule": {"type": "schema_type_exists", "params": {"type": "breadcrumblist,organization"}}},
        ]},
        "llms_txt": {"max": 5, "label": "llms.txt", "description": "llms.txt 파일 존재 여부", "criteria": [
            {"id": "exists", "name": "llms.txt 파일", "points": 5, "enabled": True, "rule": {"type": "http_status", "params": {"path": "/llms.txt", "status": 200}}},
        ]},
        "faq": {"max": 15, "label": "FAQ 섹션", "description": "FAQPage 스키마 + HTML FAQ 섹션", "criteria": [
            {"id": "schema", "name": "FAQPage 스키마", "points": 8, "enabled": True, "rule": {"type": "schema_type_exists", "params": {"type": "faqpage"}}},
            {"id": "html", "name": "HTML FAQ 섹션", "points": 7, "enabled": True, "rule": {"type": "class_id_contains", "params": {"keywords": "faq,자주 묻는,자주묻는,frequently asked,q&a,qna,questions,질문,answer,accordion", "tags": "div,section,aside,article"}}},
        ]},
        "summary_box": {"max": 5, "label": "서머리 박스", "description": "요약 박스 존재 여부", "criteria": [
            {"id": "found", "name": "요약 박스 감지", "points": 5, "enabled": True, "rule": {"type": "class_id_contains", "params": {"keywords": "summary,요약,tldr,tl;dr,abstract,핵심,정리,key-point,keypoint,highlight,takeaway,key feature,key-feature,주요 기능,주요기능,주요 특징,주요특징,핵심 기능,핵심기능,제품 특징,제품특징,특장점,benefit,overview,product overview", "tags": "div,section,aside,article,blockquote,p"}}},
        ]},
        "heading_structure": {"max": 5, "label": "Heading 구조", "description": "제목 태그 구조 분석", "criteria": [
            {"id": "single_h1", "name": "H1 단일", "points": 2, "enabled": True, "rule": {"type": "css_count", "params": {"selector": "h1", "operator": "==", "value": 1}}},
            {"id": "multiple_h2", "name": "H2 복수", "points": 2, "enabled": True, "rule": {"type": "css_count", "params": {"selector": "h2", "operator": ">=", "value": 2}}},
            {"id": "logical_order", "name": "논리적 순서", "points": 1, "enabled": True, "rule": {"type": "heading_order", "params": {}}},
        ]},
        "stats_density": {"max": 5, "label": "통계 데이터", "description": "수치/통계 데이터 존재 여부", "criteria": [
            {"id": "has_stats", "name": "통계 데이터 존재", "points": 5, "enabled": True, "rule": {"type": "text_has_pattern", "params": {"pattern": "\\d", "tags": "p,li,td,h1,h2,h3,h4,h5,h6"}}},
        ]},
        "reviews_ssr": {"max": 10, "label": "리뷰 SSR", "description": "리뷰 컨테이너 서버사이드 렌더링", "criteria": [
            {"id": "found", "name": "리뷰 컨테이너 SSR", "points": 10, "enabled": True, "rule": {"type": "css_exists", "params": {"selector": "#reviews_container"}}},
        ]},
        "csr_ratio": {"max": 10, "label": "CSR 비중", "description": "SSR/CSR 비율 (특수 로직)", "criteria": [
            {"id": "excellent", "name": "Excellent", "points": 10, "enabled": True, "rule": {"type": "csr_tier", "params": {"min_ratio": 0.8}}},
            {"id": "good", "name": "Good", "points": 7, "enabled": True, "rule": {"type": "csr_tier", "params": {"min_ratio": 0.5}}},
            {"id": "partial", "name": "Partial", "points": 4, "enabled": True, "rule": {"type": "csr_tier", "params": {"min_ratio": 0.3}}},
        ], "special": "csr_tiers"},
        "grade": {"good": 90, "need_improvement": 70},
    }

_scoring_config: Optional[dict] = None


def load_scoring_config() -> dict:
    """설정 파일에서 채점 설정을 로드합니다. 없으면 기본값 반환."""
    global _scoring_config
    try:
        with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
            _scoring_config = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        _scoring_config = _load_default_config()
    return _scoring_config


def save_scoring_config(config: dict) -> None:
    """채점 설정을 파일에 저장합니다."""
    global _scoring_config
    _scoring_config = config
    with open(_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def get_scoring_config() -> dict:
    """현재 메모리에 로드된 설정을 반환합니다."""
    if _scoring_config is None:
        return load_scoring_config()
    return _scoring_config


def get_default_config() -> dict:
    """기본 채점 설정을 반환합니다."""
    return _load_default_config()


# 서버 시작 시 설정 로드
load_scoring_config()

AI_BOTS = {
    "GPTBot":          "OpenAI GPT",
    "ChatGPT-User":    "ChatGPT",
    "Google-Extended": "Google Gemini",
    "CCBot":           "Common Crawl (AI 학습)",
    "anthropic-ai":    "Claude (Anthropic)",
    "Claude-Web":      "Claude Web",
    "PerplexityBot":   "Perplexity AI",
    "Bytespider":      "ByteDance AI",
    "cohere-ai":       "Cohere AI",
    "YouBot":          "You.com",
}


def _normalize_url(url: str) -> tuple[str, str]:
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    parsed   = urlparse(url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"
    return url, base_url


def _safe_visible_text(soup: BeautifulSoup) -> int:
    """soup를 변조하지 않고 보이는 텍스트 글자수를 계산합니다."""
    text_parts = []
    for element in soup.find_all(string=True):
        if element.parent and element.parent.name in ("script", "style", "noscript", "svg", "path"):
            continue
        text_parts.append(element)
    return len(re.sub(r'\s+', '', ''.join(text_parts)))


async def analyze_url(url: str, lightweight: bool = False, scope: str = "all") -> dict:
    """URL 분석.

    lightweight=True: 벌크 분석용 경량 모드 (Playwright CSR 분석 생략, 메모리 절약)
    scope: 'all' | 'schema' | 'seo' | 'faq' — 특정 항목만 분석
    """
    url, base_url = _normalize_url(url)

    # scope별 필요한 분석만 수행
    if scope != "all":
        page_data = await _fetch_page(url)

        if scope == "schema":
            jsonld = _extract_json_ld(page_data)
            page_data["soup"] = None
            return {"url": url, "base_url": base_url, "scope": scope, "json_ld": jsonld}

        if scope == "seo":
            context = {"soup": page_data.get("soup"), "page_data": page_data, "jsonld_types": set(), "base_url": base_url}
            score = await _calculate_score(context, {"bots": {}}, {"status": "skipped"})
            page_data["soup"] = None
            return {"url": url, "base_url": base_url, "scope": scope, "score": score}

        if scope == "faq":
            jsonld = _extract_json_ld(page_data)
            context = {"soup": page_data.get("soup"), "page_data": page_data, "jsonld_types": {t.lower() for t in jsonld.get("all_types", [])}, "base_url": base_url}
            score = await _calculate_score(context, {"bots": {}}, {"status": "skipped"})
            page_data["soup"] = None
            return {"url": url, "base_url": base_url, "scope": scope, "score": score}

    if lightweight:
        # 벌크: Playwright(CSR) 생략 — httpx만 사용
        async with _bulk_sem:
            robots, llms, page_data = await asyncio.gather(
                _check_robots_txt(base_url),
                _check_llms_txt(base_url),
                _fetch_page(url),
            )
        csr_raw = {"status": "skipped", "csr_chars": 0}
    else:
        robots, llms, page_data, csr_raw = await asyncio.gather(
            _check_robots_txt(base_url),
            _check_llms_txt(base_url),
            _fetch_page(url),
            _check_csr_chars(url),
        )

    jsonld    = _extract_json_ld(page_data)
    pdp       = _detect_pdp(url)

    # SSR 글자수 계산 (soup 변조 없이)
    ssr_chars = 0
    if page_data["status"] == "ok" and page_data["soup"]:
        ssr_chars = _safe_visible_text(page_data["soup"])

    csr_ratio = _calc_csr_ratio(ssr_chars, csr_raw)

    # 룰 엔진 context 구성
    all_types = set(jsonld.get("all_types", []))
    context = {
        "soup":         page_data.get("soup"),
        "page_data":    page_data,
        "jsonld_types": {t.lower() for t in all_types},
        "base_url":     base_url,
    }

    score = await _calculate_score(context, robots, csr_ratio)

    # soup 참조 해제 — 메모리 즉시 회수
    page_data["soup"] = None

    return {
        "url":               url,
        "base_url":          base_url,
        "scope":             "all",
        "pdp":               pdp,
        "robots_txt":        robots,
        "json_ld":           jsonld,
        "csr_ratio":         csr_ratio,
        "score":             score,
    }


# ── Page Fetch ────────────────────────────────────────────────────────────────

async def _fetch_page(url: str) -> dict:
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; GEOAudit/1.0; +https://geoaudit.dev)",
            "Accept":     "text/html,application/xhtml+xml",
        }
        async with httpx.AsyncClient(timeout=15, follow_redirects=True, max_redirects=10) as client:
            r = await client.get(url, headers=headers)

        redirect_count = len(r.history)
        content_type = r.headers.get("content-type", "")

        # HTML 본문이 있으면 상태코드와 관계없이 파싱 (일부 사이트는 404/403이지만 콘텐츠 정상)
        if "text/html" in content_type and len(r.text) > 500:
            soup = BeautifulSoup(r.text, "html.parser")
            return {
                "status":         "ok",
                "soup":           soup,
                "http_status":    r.status_code,
                "final_url":      str(r.url),
                "redirect_count": redirect_count,
            }

        if r.status_code != 200:
            return {"status": "error", "http_status": r.status_code,
                    "soup": None, "redirect_count": redirect_count}

        soup = BeautifulSoup(r.text, "html.parser")
        return {
            "status":         "ok",
            "soup":           soup,
            "final_url":      str(r.url),
            "redirect_count": redirect_count,
        }
    except httpx.TimeoutException:
        return {"status": "error", "error": "요청 시간 초과 (15초)", "soup": None, "redirect_count": 0}
    except httpx.ConnectError:
        return {"status": "error", "error": "서버에 연결할 수 없습니다", "soup": None, "redirect_count": 0}
    except httpx.TooManyRedirects:
        return {"status": "error", "error": "리다이렉트가 너무 많습니다", "soup": None, "redirect_count": 0}
    except Exception as e:
        return {"status": "error", "error": str(e), "soup": None, "redirect_count": 0}


# ── robots.txt ────────────────────────────────────────────────────────────────

async def _check_robots_txt(base_url: str) -> dict:
    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            r = await client.get(f"{base_url}/robots.txt")
        if r.status_code != 200:
            return {"status": "not_found", "bots": {}, "raw": ""}
        content = r.text
        return {"status": "found", "bots": _parse_robots_for_ai_bots(content), "raw": content[:3000]}
    except Exception as e:
        return {"status": "error", "error": str(e), "bots": {}}


def _parse_robots_for_ai_bots(content: str) -> dict:
    rules: dict[str, list[str]] = {}
    current_agents: list[str]   = []

    for raw_line in content.splitlines():
        line = raw_line.strip()
        if line.startswith("#"):
            continue
        if not line:
            current_agents = []
            continue
        lower = line.lower()
        if lower.startswith("user-agent:"):
            agent = line.split(":", 1)[1].strip()
            current_agents.append(agent)
            rules.setdefault(agent, [])
        elif lower.startswith("disallow:"):
            path = line.split(":", 1)[1].strip()
            for agent in current_agents:
                rules.setdefault(agent, []).append(path)

    bot_status: dict[str, dict] = {}
    for bot_key, bot_name in AI_BOTS.items():
        blocked      = False
        matched_rule = None
        for agent, disallows in rules.items():
            if agent.lower() in (bot_key.lower(), "*"):
                for disallow in disallows:
                    if disallow in ("/", "/*"):
                        blocked      = True
                        matched_rule = f"User-agent: {agent}  →  Disallow: {disallow}"
                        break
            if blocked:
                break
        bot_status[bot_key] = {"name": bot_name, "blocked": blocked, "rule": matched_rule}

    return bot_status


# ── llms.txt ──────────────────────────────────────────────────────────────────

async def _check_llms_txt(base_url: str) -> dict:
    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            r = await client.get(f"{base_url}/llms.txt")
        if r.status_code == 200:
            content = r.text
            return {
                "status":          "found",
                "content_preview": content[:1200],
                "size_bytes":      len(content.encode()),
            }
        return {"status": "not_found", "http_status": r.status_code}
    except httpx.TimeoutException:
        return {"status": "error", "error": "요청 시간 초과"}
    except httpx.HTTPError as e:
        return {"status": "error", "error": f"네트워크 오류: {type(e).__name__}"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


# ── Basic SEO Tags (20점, 10종 × 2점) ─────────────────────────────────────────

def _check_seo_tags(page_data: dict) -> dict:
    if page_data["status"] != "ok" or not page_data["soup"]:
        return {"status": "error", "passed": 0, "total": 10, "items": {}}

    cfg = get_scoring_config()
    seo_cfg = cfg.get("seo_tags", {})
    criteria = {c["id"]: c for c in seo_cfg.get("criteria", []) if c.get("enabled", True)}

    soup  = page_data["soup"]
    items = {}

    # 1. Title
    if "title" in criteria:
        cr = criteria["title"]
        min_len = cr.get("threshold", {}).get("min_length", 10)
        title_tag  = soup.find("title")
        title_text = title_tag.get_text(strip=True) if title_tag else ""
        t_pass = bool(title_text and len(title_text) >= min_len)
        items["title"] = {
            "label": "Title 태그",
            "pass":  t_pass,
            "value": title_text[:80] or None,
            "hint":  f"Title이 없거나 {min_len}자 미만입니다." if not t_pass else None,
        }

    # 2. Meta Description
    if "desc" in criteria:
        cr = criteria["desc"]
        min_len = cr.get("threshold", {}).get("min_length", 50)
        meta_desc    = soup.find("meta", attrs={"name": re.compile(r"^description$", re.I)})
        desc_content = (meta_desc.get("content") or "").strip() if meta_desc else ""
        d_pass = bool(desc_content and len(desc_content) >= min_len)
        items["meta_description"] = {
            "label": "Meta Description",
            "pass":  d_pass,
            "value": desc_content[:120] or None,
            "hint":  f"Meta Description이 없거나 {min_len}자 미만입니다." if not d_pass else None,
        }

    # 3. Canonical
    if "canonical" in criteria:
        canonical = soup.find("link", rel=lambda v: v and "canonical" in v)
        can_href  = (canonical.get("href") or "").strip() if canonical else ""
        c_pass = bool(can_href)
        items["canonical"] = {
            "label": "Canonical 태그",
            "pass":  c_pass,
            "value": can_href or None,
            "hint":  "Canonical 태그가 없습니다." if not c_pass else None,
        }

    # 4. H1 고유성 (정확히 1개)
    if "h1" in criteria:
        h1s     = soup.find_all("h1")
        h1_pass = len(h1s) == 1
        items["h1_unique"] = {
            "label": "H1 고유성 (정확히 1개)",
            "pass":  h1_pass,
            "value": h1s[0].get_text(strip=True)[:80] if h1s else None,
            "hint":  ("H1 태그가 없습니다." if not h1s else f"H1이 {len(h1s)}개 — 1개여야 합니다.") if not h1_pass else None,
        }

    # 5. 이미지 Alt
    if "img_alt" in criteria:
        images           = soup.find_all("img")
        imgs_missing_alt = [img for img in images if img.get("alt") is None]
        if not images:
            img_pass, img_value, img_hint = True, "이미지 없음", None
        else:
            img_pass  = len(imgs_missing_alt) == 0
            img_value = f"{len(images)}개 중 {len(images) - len(imgs_missing_alt)}개 alt 보유"
            img_hint  = f"{len(imgs_missing_alt)}개 이미지에 alt 속성이 없습니다." if not img_pass else None
        items["image_alt"] = {
            "label": "이미지 Alt 속성",
            "pass":  img_pass,
            "value": img_value,
            "hint":  img_hint,
        }

    # 6. 리다이렉트 체인
    if "redirect" in criteria:
        cr = criteria["redirect"]
        max_count = cr.get("threshold", {}).get("max_count", 3)
        redirect_count = page_data.get("redirect_count", 0)
        r_pass = redirect_count <= max_count
        items["redirect_chain"] = {
            "label": f"리다이렉트 체인 ({max_count}회 이하)",
            "pass":  r_pass,
            "value": f"{redirect_count}회 리다이렉트",
            "hint":  f"리다이렉트 {redirect_count}회 — {max_count}회 이하 권장" if not r_pass else None,
        }

    # 7. og:title
    if "og_title" in criteria:
        og_title = soup.find("meta", property="og:title")
        og_t     = (og_title.get("content") or "").strip() if og_title else ""
        ot_pass  = bool(og_t)
        items["og_title"] = {
            "label": "og:title",
            "pass":  ot_pass,
            "value": og_t[:80] or None,
            "hint":  "og:title 태그가 없습니다." if not ot_pass else None,
        }

    # 8. og:description
    if "og_desc" in criteria:
        og_desc = soup.find("meta", property="og:description")
        og_d    = (og_desc.get("content") or "").strip() if og_desc else ""
        od_pass = bool(og_d)
        items["og_description"] = {
            "label": "og:description",
            "pass":  od_pass,
            "value": og_d[:120] or None,
            "hint":  "og:description 태그가 없습니다." if not od_pass else None,
        }

    # 9. og:image
    if "og_image" in criteria:
        og_img  = soup.find("meta", property="og:image")
        og_i    = (og_img.get("content") or "").strip() if og_img else ""
        oi_pass = bool(og_i)
        items["og_image"] = {
            "label": "og:image",
            "pass":  oi_pass,
            "value": og_i[:100] or None,
            "hint":  "og:image 태그가 없습니다." if not oi_pass else None,
        }

    # 10. Meta Robots (noindex 체크)
    if "robots" in criteria:
        meta_robots    = soup.find("meta", attrs={"name": re.compile(r"^robots$", re.I)})
        robots_content = (meta_robots.get("content") or "").strip() if meta_robots else ""
        is_noindex     = bool(meta_robots and "noindex" in robots_content.lower())
        mr_pass        = not is_noindex
        items["meta_robots"] = {
            "label": "Meta Robots (noindex 아님)",
            "pass":  mr_pass,
            "value": robots_content if robots_content else "태그 없음 (기본: index/follow)",
            "hint":  "noindex가 설정되어 검색 엔진에서 제외됩니다." if is_noindex else None,
        }

    passed = sum(1 for v in items.values() if v["pass"])
    total  = len(criteria)
    return {"status": "ok", "passed": passed, "total": total, "items": items}


# ── JSON-LD ───────────────────────────────────────────────────────────────────

def _extract_json_ld(page_data: dict) -> dict:
    if page_data["status"] != "ok" or not page_data["soup"]:
        return {"status": "error", "schemas": [], "count": 0, "all_types": [], "raw_sources": []}

    soup        = page_data["soup"]
    scripts     = soup.find_all("script", type="application/ld+json")
    schemas     = []
    raw_datas   = []
    raw_sources = []

    for script in scripts:
        try:
            data = json.loads(script.string or "")
            schemas.append(_parse_schema(data))
            raw_datas.append(data)
            raw_sources.append(json.dumps(data, ensure_ascii=False, indent=2)[:5000])
        except Exception:
            pass

    # 1차: 파싱된 스키마에서 타입 수집
    all_types = _get_all_schema_types(schemas)

    # 2차: 원본 JSON을 재귀적으로 스캔하여 중첩된 @type까지 수집
    #      (e.g. LG의 AggregateRating > itemReviewed > @type: "IndividualProduct")
    for raw in raw_datas:
        _collect_raw_types(raw, all_types)

    return {
        "status":      "found" if schemas else "not_found",
        "count":       len(schemas),
        "schemas":     schemas,
        "all_types":   list(all_types),
        "raw_sources": raw_sources,
    }


def _collect_raw_types(data, types: set):
    """원본 JSON-LD에서 모든 @type 값을 재귀적으로 추출."""
    if isinstance(data, dict):
        t = data.get("@type")
        if t:
            if isinstance(t, list):
                types.update(str(v) for v in t)
            else:
                types.add(str(t))
        for val in data.values():
            _collect_raw_types(val, types)
    elif isinstance(data, list):
        for item in data:
            _collect_raw_types(item, types)


def _parse_schema(data) -> dict:
    """JSON-LD 데이터를 파싱.

    처리 구조:
    - List                     → @graph 취급
    - Dict with @graph key     → { "@context": "...", "@graph": [...] } 패턴
    - Dict with @type          → 일반 스키마 오브젝트
    """
    if isinstance(data, list):
        return {"type": "@graph", "items": [_parse_schema(item) for item in data]}

    if not isinstance(data, dict):
        return {"type": "unknown"}

    if "@graph" in data and "@type" not in data:
        graph = data["@graph"]
        items = [_parse_schema(item) for item in graph] if isinstance(graph, list) else []
        return {"type": "@graph", "items": items}

    return {
        "type":        data.get("@type", "Unknown"),
        "name":        data.get("name", ""),
        "description": str(data.get("description", ""))[:200],
        "keys":        [k for k in data.keys() if not k.startswith("@")],
    }


def _schema_has_type(schema: dict, type_name: str) -> bool:
    t = schema.get("type", "")
    if isinstance(t, list):
        if type_name in t:
            return True
    elif t == type_name:
        return True
    for item in schema.get("items", []):
        if _schema_has_type(item, type_name):
            return True
    return False


def _get_all_schema_types(schemas: list) -> set:
    types: set[str] = set()
    for schema in schemas:
        _collect_types(schema, types)
    return types


def _collect_types(schema: dict, types: set):
    skip = {"@graph", "unknown", "Unknown", ""}
    t = schema.get("type", "")
    if isinstance(t, list):
        types.update(v for v in t if v not in skip)
    elif t not in skip:
        types.add(t)
    for item in schema.get("items", []):
        _collect_types(item, types)


# ── FAQ Section (15점) ────────────────────────────────────────────────────────

def _check_faq(page_data: dict, jsonld: dict) -> dict:
    has_faq_schema = any(
        _schema_has_type(s, "FAQPage")
        for s in jsonld.get("schemas", [])
    )

    has_faq_html = False
    if page_data["status"] == "ok" and page_data["soup"]:
        soup   = page_data["soup"]
        faq_kw = ["faq", "자주 묻는", "자주묻는", "frequently asked", "q&a", "qna",
                  "questions", "질문", "answer", "accordion"]

        for tag in soup.find_all(True):
            cls = " ".join(tag.get("class", [])).lower()
            iid = tag.get("id", "").lower()
            if any(kw in cls or kw in iid for kw in faq_kw):
                has_faq_html = True
                break

        if not has_faq_html:
            for tag in soup.find_all(["h1", "h2", "h3", "h4", "h5"]):
                if any(kw in tag.get_text(strip=True).lower() for kw in faq_kw):
                    has_faq_html = True
                    break

        if not has_faq_html:
            if len(soup.find_all("details")) >= 3:
                has_faq_html = True

    return {"status": "ok", "has_faq_schema": has_faq_schema, "has_faq_html": has_faq_html}


# ── Summary Box (5점) ─────────────────────────────────────────────────────────

def _check_summary_box(page_data: dict) -> dict:
    if page_data["status"] != "ok" or not page_data["soup"]:
        return {"status": "error", "found": False, "method": None, "source_html": None}

    soup = page_data["soup"]
    kw   = ["summary", "요약", "tldr", "tl;dr", "abstract", "핵심", "정리",
            "key-point", "keypoint", "highlight", "takeaway",
            # 제품 특징/기능 (PDP 서머리 박스)
            "key feature", "key-feature", "keyfeature",
            "key spec", "key-spec", "keyspec",
            "feature highlight", "product feature", "product highlight",
            "주요 기능", "주요기능", "주요 특징", "주요특징", "핵심 기능", "핵심기능",
            "제품 특징", "제품특징", "특장점",
            # 혜택/장점 요약
            "benefit", "why choose", "at a glance", "quick summary",
            "overview", "product overview", "spec summary"]

    for tag in soup.find_all(["div", "section", "aside", "article", "blockquote", "p"]):
        cls = " ".join(tag.get("class", [])).lower()
        iid = tag.get("id", "").lower()
        if any(k in cls or k in iid for k in kw):
            return {"status": "ok", "found": True, "method": "class/id",
                    "source_html": str(tag)[:3000]}

    for tag in soup.find_all(["h1", "h2", "h3", "h4"]):
        if any(k in tag.get_text(strip=True).lower() for k in kw):
            # 제목 + 바로 아래 형제 블록까지 소스 캡처
            siblings = []
            for sib in tag.next_siblings:
                if hasattr(sib, 'name') and sib.name in ("ul", "ol", "div", "p", "section"):
                    siblings.append(str(sib)[:1000])
                    if len(siblings) >= 3:
                        break
            source = str(tag) + "".join(siblings)
            return {"status": "ok", "found": True, "method": "heading",
                    "source_html": source[:3000]}

    summary_tag = soup.find("summary")
    if summary_tag:
        parent = summary_tag.parent
        return {"status": "ok", "found": True, "method": "html5-summary",
                "source_html": str(parent)[:3000] if parent else str(summary_tag)[:500]}

    return {"status": "ok", "found": False, "method": None, "source_html": None}


# ── Stats Density (5점, 존재 유무) ────────────────────────────────────────────

def _check_stats_density(page_data: dict) -> dict:
    if page_data["status"] != "ok" or not page_data["soup"]:
        return {"status": "error", "has_stats": False, "ratio": 0.0,
                "stat_words": 0, "total_words": 0}

    soup         = page_data["soup"]
    content_tags = soup.find_all(["p", "li", "td", "h1", "h2", "h3", "h4", "h5", "h6"])
    text         = " ".join(tag.get_text() for tag in content_tags)
    words        = [w for w in re.split(r'\s+', text) if len(w) > 1]

    if not words:
        return {"status": "ok", "has_stats": False, "ratio": 0.0,
                "stat_words": 0, "total_words": 0}

    stat_words = [w for w in words if re.search(r'\d', w)]
    ratio_pct  = round(len(stat_words) / len(words) * 100, 1)
    has_stats  = len(stat_words) > 0

    return {
        "status":      "ok",
        "has_stats":   has_stats,
        "ratio":       ratio_pct,
        "stat_words":  len(stat_words),
        "total_words": len(words),
    }


# ── Heading Structure (5점) ───────────────────────────────────────────────────

def _check_heading_structure(page_data: dict) -> dict:
    empty = {
        "status": "error", "h1_count": 0, "h2_count": 0,
        "h3_count": 0, "h4_count": 0,
        "logical_order": False, "has_single_h1": False,
        "has_multiple_h2": False, "no_level_gap": False,
        "h1_texts": [], "h2_texts": [],
    }
    if page_data["status"] != "ok" or not page_data["soup"]:
        return empty

    soup = page_data["soup"]
    h1s  = soup.find_all("h1")
    h2s  = soup.find_all("h2")
    h3s  = soup.find_all("h3")
    h4s  = soup.find_all("h4")

    logical_order = True
    seen_h1       = False
    for tag in soup.find_all(["h1", "h2", "h3", "h4"]):
        if tag.name == "h1":
            seen_h1 = True
        elif not seen_h1:
            logical_order = False
            break

    no_level_gap = not (h3s and not h2s)

    return {
        "status":          "ok",
        "h1_count":        len(h1s),
        "h2_count":        len(h2s),
        "h3_count":        len(h3s),
        "h4_count":        len(h4s),
        "logical_order":   logical_order,
        "has_single_h1":   len(h1s) == 1,
        "has_multiple_h2": len(h2s) >= 2,
        "no_level_gap":    no_level_gap,
        "h1_texts":        [h.get_text(strip=True)[:100] for h in h1s[:3]],
        "h2_texts":        [h.get_text(strip=True)[:80]  for h in h2s[:6]],
    }


# ── Reviews SSR (10점) ────────────────────────────────────────────────────────

def _check_reviews_ssr(page_data: dict) -> dict:
    """#reviews_container 요소가 서버사이드 렌더링으로 존재하는지 확인."""
    if page_data["status"] != "ok" or not page_data["soup"]:
        return {"status": "error", "found": False, "has_content": False}

    soup = page_data["soup"]
    el   = soup.find(id="reviews_container")

    if el is None:
        return {"status": "ok", "found": False, "has_content": False}

    content     = el.get_text(strip=True)
    has_content = len(content) > 10

    return {
        "status":      "ok",
        "found":       True,
        "has_content": has_content,
    }


# ── CSR Ratio ─────────────────────────────────────────────────────────────────

async def _ensure_chromium() -> bool:
    """Chromium 바이너리가 없으면 자동 설치. 성공 시 True."""
    import sys
    python = sys.executable or "python"
    for cmd in [
        [python, "-m", "playwright", "install", "chromium", "--with-deps"],
        [python, "-m", "playwright", "install", "chromium"],
    ]:
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await asyncio.wait_for(proc.communicate(), timeout=180)
            if proc.returncode == 0:
                return True
        except Exception:
            continue
    return False


async def _check_csr_chars(url: str) -> dict:
    """Playwright로 JS 실행 후 텍스트 글자수를 반환."""
    try:
        from playwright.async_api import async_playwright
        from playwright_stealth import stealth_async
    except ImportError:
        return {"status": "unavailable", "csr_chars": 0}

    async with _playwright_sem:
        try:
            async with async_playwright() as p:
                launch_args = [
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                ]
                try:
                    browser = await p.chromium.launch(
                        headless=True,
                        args=launch_args,
                    )
                except Exception as launch_err:
                    if "Executable doesn't exist" in str(launch_err):
                        ok = await _ensure_chromium()
                        if not ok:
                            return {"status": "error",
                                    "error": "Chromium 설치 실패 — Render 대시보드에서 Build Command를 확인하세요.",
                                    "csr_chars": 0}
                        browser = await p.chromium.launch(
                            headless=True,
                            args=launch_args,
                        )
                    else:
                        raise

                context = await browser.new_context(
                    viewport={"width": 1280, "height": 720},
                    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                    locale="ko-KR",
                    timezone_id="Asia/Seoul",
                    extra_http_headers={
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
                        "Accept-Encoding": "gzip, deflate, br",
                        "Sec-Fetch-Dest": "document",
                        "Sec-Fetch-Mode": "navigate",
                        "Sec-Fetch-Site": "none",
                        "Sec-Fetch-User": "?1",
                        "Upgrade-Insecure-Requests": "1",
                    },
                )
                page = await context.new_page()
                await stealth_async(page)

                resp = await page.goto(url, wait_until="networkidle", timeout=30000)
                final_url = page.url
                http_status = resp.status if resp else None

                # 봇 차단 감지 (403/406) — 본문이 충분하면 정상 파싱 시도
                if http_status and http_status in (403, 406):
                    await page.wait_for_timeout(2000)
                    quick_text = await page.inner_text("body")
                    body_chars = len(re.sub(r'\s+', '', quick_text))
                    if body_chars < 10000:
                        await context.close()
                        await browser.close()
                        is_bot_block = any(kw in quick_text.lower() for kw in
                                           ["access denied", "robot", "captcha", "blocked",
                                            "not allowed", "permission"])
                        return {
                            "status": "blocked",
                            "csr_chars": 0,
                            "error": f"사이트가 헤드리스 브라우저를 차단합니다 (HTTP {http_status})"
                                     if is_bot_block else
                                     f"HTTP {http_status} 응답",
                            "debug": {
                                "final_url": final_url,
                                "http_status": http_status,
                                "page_title": quick_text[:100],
                                "text_preview": quick_text[:300],
                            },
                        }
                    # 본문이 200자 이상이면 계속 진행 (403이지만 콘텐츠 정상인 경우)

                # JS 프레임워크 렌더링 완료 대기
                await page.wait_for_timeout(3000)

                # 메인 프레임 콘텐츠
                main_html = await page.content()
                title = await page.title()

                # iframe 내부 콘텐츠도 수집
                frame_count = len(page.frames) - 1
                frame_texts = []
                for frame in page.frames:
                    if frame == page.main_frame:
                        continue
                    try:
                        fc = await frame.content()
                        fs = BeautifulSoup(fc, "html.parser")
                        frame_texts.append(_safe_visible_text(fs))
                    except Exception:
                        continue

                await context.close()
                await browser.close()

            csr_soup  = BeautifulSoup(main_html, "html.parser")
            main_chars = _safe_visible_text(csr_soup)
            iframe_chars = sum(frame_texts)
            csr_chars = main_chars + iframe_chars

            return {
                "status": "ok",
                "csr_chars": csr_chars,
                "debug": {
                    "final_url": final_url,
                    "http_status": http_status,
                    "page_title": title,
                    "main_chars": main_chars,
                    "iframe_count": frame_count,
                    "iframe_chars": iframe_chars,
                    "html_length": len(main_html),
                },
            }
        except asyncio.TimeoutError:
            return {"status": "error", "error": "브라우저 렌더링 시간 초과", "csr_chars": 0}
        except Exception as e:
            return {"status": "error", "error": str(e), "csr_chars": 0}


def _calc_csr_ratio(ssr_chars: int, csr_raw: dict) -> dict:
    """SSR 글자수와 CSR 글자수를 비교하여 비율과 상태를 반환."""
    status    = csr_raw.get("status", "unavailable")
    csr_chars = csr_raw.get("csr_chars", 0)
    error     = csr_raw.get("error")
    debug     = csr_raw.get("debug")

    if status != "ok" or csr_chars == 0:
        return {
            "status":    status,
            "ssr_chars": ssr_chars,
            "csr_chars": csr_chars,
            "ratio":     None,
            "error":     error,
            "debug":     debug,
        }

    ratio = round(ssr_chars / csr_chars, 3) if csr_chars > 0 else 1.0
    ratio = min(ratio, 1.0)  # CSR는 항상 SSR 이상
    return {
        "status":    "ok",
        "ssr_chars": ssr_chars,
        "csr_chars": csr_chars,
        "ratio":     ratio,
        "error":     None,
        "debug":     debug,
    }


# ── PDP Detection ─────────────────────────────────────────────────────────────

def _detect_pdp(url: str) -> dict:
    parsed   = urlparse(url)
    path     = parsed.path.strip("/")
    segments = [s for s in path.split("/") if s]
    is_pdp   = len(segments) >= 3
    return {
        "is_pdp":        is_pdp,
        "path_segments": segments,
        "pattern":       "/".join(segments) if segments else "",
        "segment_count": len(segments),
    }


# ── Score (총합 100점) ────────────────────────────────────────────────────────

async def _calculate_score(context: dict, robots: dict, csr_ratio: dict) -> dict:
    """룰 엔진 기반 채점. context에 soup, page_data, jsonld_types, base_url 포함."""
    cfg       = get_scoring_config()
    score     = 0
    breakdown = {}

    cat_keys = ["seo_tags", "robots_txt", "json_ld", "llms_txt", "faq",
                "summary_box", "heading_structure", "stats_density", "reviews_ssr", "csr_ratio"]

    for cat_key in cat_keys:
        c = cfg.get(cat_key, {})
        cat_max  = c.get("max", 0)
        special  = c.get("special")
        criteria = [cr for cr in c.get("criteria", []) if cr.get("enabled", True)]

        # ── 특수 로직: robots_txt (비율 계산) ──
        if special == "robots_ratio":
            bots = robots.get("bots", {})
            if bots:
                allowed   = sum(1 for b in bots.values() if not b["blocked"])
                cat_score = round((allowed / len(bots)) * cat_max)
            else:
                cat_score = cat_max
            score += cat_score
            breakdown[cat_key] = {"points": cat_score, "max": cat_max}
            continue

        # ── 특수 로직: CSR 티어 ──
        if special == "csr_tiers":
            csr_status = csr_ratio.get("status", "unavailable")
            ratio = csr_ratio.get("ratio")
            csr_score = 0
            csr_tier  = "poor"

            if csr_status in ("skipped", "blocked"):
                csr_score = 0; csr_tier = csr_status
            elif ratio is None:
                csr_score = 0; csr_tier = "unavailable"
            else:
                for cr in criteria:
                    min_r = cr.get("rule", {}).get("params", {}).get("min_ratio", 1.0)
                    if ratio >= float(min_r):
                        csr_score = min(cr.get("points", 0), cat_max)
                        csr_tier  = cr.get("id", "unknown")
                        break

            score += csr_score
            breakdown[cat_key] = {
                "points": csr_score, "max": cat_max,
                "ratio": ratio, "tier": csr_tier,
                "ssr_chars": csr_ratio.get("ssr_chars", 0),
                "csr_chars": csr_ratio.get("csr_chars", 0),
                "status": csr_ratio.get("status", "unavailable"),
            }
            continue

        # ── 범용 룰 엔진 평가 ──
        cat_score = 0
        items = {}
        for cr in criteria:
            rule = cr.get("rule")
            if not rule:
                continue
            result = await evaluate_rule_async(rule, context)
            passed = result.get("pass", False)
            if passed:
                cat_score += cr.get("points", 0)
            items[cr["id"]] = {
                "label": cr.get("name", cr["id"]),
                "pass":  passed,
                "value": result.get("value"),
                "hint":  result.get("hint"),
                "rule_type": rule.get("type"),
            }

        cat_score = min(cat_score, cat_max)
        score += cat_score
        passed_count = sum(1 for v in items.values() if v["pass"])
        breakdown[cat_key] = {
            "points": cat_score,
            "max": cat_max,
            "passed": passed_count,
            "total": len(criteria),
            "items": items,
        }

    # 등급
    g = cfg.get("grade", {})
    total_max = sum(cfg.get(k, {}).get("max", 0) for k in cat_keys)
    grade = (
        "Good"             if score >= g.get("good", 90) else
        "Need Improvement" if score >= g.get("need_improvement", 70) else
        "Poor"
    )

    return {"total": score, "max": total_max, "grade": grade, "breakdown": breakdown}
