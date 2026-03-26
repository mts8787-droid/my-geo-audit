import re
import asyncio
import httpx
from bs4 import BeautifulSoup
import json
from urllib.parse import urlparse

# Playwright 동시 실행 제한 (메모리 보호)
_playwright_sem = asyncio.Semaphore(2)

# 벌크 분석 시 동시 요청 제한
_bulk_sem = asyncio.Semaphore(5)

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
            seo_tags = _check_seo_tags(page_data)
            page_data["soup"] = None
            return {"url": url, "base_url": base_url, "scope": scope, "seo_tags": seo_tags}

        if scope == "faq":
            jsonld = _extract_json_ld(page_data)
            faq = _check_faq(page_data, jsonld)
            page_data["soup"] = None
            return {"url": url, "base_url": base_url, "scope": scope, "faq": faq}

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

    seo_tags  = _check_seo_tags(page_data)
    jsonld    = _extract_json_ld(page_data)
    faq       = _check_faq(page_data, jsonld)
    summary   = _check_summary_box(page_data)
    stats     = _check_stats_density(page_data)
    headings  = _check_heading_structure(page_data)
    reviews   = _check_reviews_ssr(page_data)
    pdp       = _detect_pdp(url)

    # SSR 글자수 계산 (soup 변조 없이)
    ssr_chars = 0
    if page_data["status"] == "ok" and page_data["soup"]:
        ssr_chars = _safe_visible_text(page_data["soup"])

    # soup 참조 해제 — 메모리 즉시 회수
    page_data["soup"] = None

    csr_ratio = _calc_csr_ratio(ssr_chars, csr_raw)

    score = _calculate_score(
        robots, llms, jsonld, seo_tags, faq, summary, stats, headings, reviews, csr_ratio
    )

    return {
        "url":               url,
        "base_url":          base_url,
        "scope":             "all",
        "pdp":               pdp,
        "robots_txt":        robots,
        "llms_txt":          llms,
        "json_ld":           jsonld,
        "seo_tags":          seo_tags,
        "faq":               faq,
        "summary_box":       summary,
        "stats_density":     stats,
        "heading_structure": headings,
        "reviews_ssr":       reviews,
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
    except Exception as e:
        return {"status": "error", "error": str(e)}


# ── Basic SEO Tags (20점, 10종 × 2점) ─────────────────────────────────────────

def _check_seo_tags(page_data: dict) -> dict:
    if page_data["status"] != "ok" or not page_data["soup"]:
        return {"status": "error", "passed": 0, "total": 10, "items": {}}

    soup  = page_data["soup"]
    items = {}

    # 1. Title
    title_tag  = soup.find("title")
    title_text = title_tag.get_text(strip=True) if title_tag else ""
    t_pass = bool(title_text and len(title_text) >= 10)
    items["title"] = {
        "label": "Title 태그",
        "pass":  t_pass,
        "value": title_text[:80] or None,
        "hint":  "Title이 없거나 10자 미만입니다." if not t_pass else None,
    }

    # 2. Meta Description
    meta_desc    = soup.find("meta", attrs={"name": re.compile(r"^description$", re.I)})
    desc_content = (meta_desc.get("content") or "").strip() if meta_desc else ""
    d_pass = bool(desc_content and len(desc_content) >= 50)
    items["meta_description"] = {
        "label": "Meta Description",
        "pass":  d_pass,
        "value": desc_content[:120] or None,
        "hint":  "Meta Description이 없거나 50자 미만입니다." if not d_pass else None,
    }

    # 3. Canonical
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
    h1s     = soup.find_all("h1")
    h1_pass = len(h1s) == 1
    items["h1_unique"] = {
        "label": "H1 고유성 (정확히 1개)",
        "pass":  h1_pass,
        "value": h1s[0].get_text(strip=True)[:80] if h1s else None,
        "hint":  ("H1 태그가 없습니다." if not h1s else f"H1이 {len(h1s)}개 — 1개여야 합니다.") if not h1_pass else None,
    }

    # 5. 이미지 Alt
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

    # 6. 리다이렉트 체인 (3회 이하)
    redirect_count = page_data.get("redirect_count", 0)
    r_pass = redirect_count <= 3
    items["redirect_chain"] = {
        "label": "리다이렉트 체인 (3회 이하)",
        "pass":  r_pass,
        "value": f"{redirect_count}회 리다이렉트",
        "hint":  f"리다이렉트 {redirect_count}회 — 3회 이하 권장" if not r_pass else None,
    }

    # 7. og:title
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
    return {"status": "ok", "passed": passed, "total": 10, "items": items}


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


def _visible_text(soup: BeautifulSoup) -> int:
    """script/style/noscript 제거 후 보이는 텍스트 글자수(공백 제외) 반환."""
    for tag in soup(["script", "style", "noscript", "svg", "path"]):
        tag.decompose()
    return len(re.sub(r'\s+', '', soup.get_text()))


async def _check_csr_chars(url: str) -> dict:
    """Playwright로 JS 실행 후 텍스트 글자수를 반환."""
    try:
        from playwright.async_api import async_playwright
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
                await context.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                    Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
                    Object.defineProperty(navigator, 'languages', { get: () => ['ko-KR', 'ko', 'en-US', 'en'] });
                    window.chrome = { runtime: {} };
                    const origQuery = window.navigator.permissions.query;
                    window.navigator.permissions.query = (params) =>
                      params.name === 'notifications'
                        ? Promise.resolve({ state: Notification.permission })
                        : origQuery(params);
                """)
                page = await context.new_page()

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
                        frame_texts.append(_visible_text(fs))
                    except Exception:
                        continue

                await context.close()
                await browser.close()

            csr_soup  = BeautifulSoup(main_html, "html.parser")
            main_chars = _visible_text(csr_soup)
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

def _calculate_score(robots: dict, llms: dict, jsonld: dict,
                     seo_tags: dict, faq: dict, summary: dict,
                     stats: dict, headings: dict, reviews: dict,
                     csr_ratio: dict) -> dict:
    score     = 0
    breakdown = {}

    # 1. 기본 SEO 태그 (20점): 10종 × 2점
    passed    = seo_tags.get("passed", 0)
    seo_score = passed * 2
    score    += seo_score
    breakdown["seo_tags"] = {"points": seo_score, "max": 20, "passed": passed, "total": 10}

    # 2. robots.txt AI 봇 허용 (10점)
    bots = robots.get("bots", {})
    if bots:
        allowed   = sum(1 for b in bots.values() if not b["blocked"])
        bot_score = round((allowed / len(bots)) * 10)
    else:
        bot_score = 10
    score    += bot_score
    breakdown["robots_txt"] = {"points": bot_score, "max": 10}

    # 3. JSON-LD (15점): 필수(8점) + 보조(7점)
    #    ※ FAQPage는 FAQ 섹션(항목 5)에서만 채점 — 여기서는 Product만 평가
    all_types        = set(jsonld.get("all_types", []))
    all_types_lower  = {t.lower() for t in all_types}

    has_product    = "product"       in all_types_lower or "individualproduct" in all_types_lower
    has_breadcrumb = "breadcrumblist" in all_types_lower
    has_org        = "organization"   in all_types_lower

    req_score    = 8 if has_product else 0
    sup_score    = 7 if (has_breadcrumb or has_org) else 0
    jsonld_score = req_score + sup_score
    score       += jsonld_score
    breakdown["json_ld"] = {
        "points":           jsonld_score,
        "max":              15,
        "required_score":   req_score,
        "supporting_score": sup_score,
        "has_product":      has_product,
        "has_breadcrumb":   has_breadcrumb,
        "has_org":          has_org,
        "all_types":        list(all_types),
    }

    # 4. llms.txt (5점)
    llms_score = 5 if llms["status"] == "found" else 0
    score     += llms_score
    breakdown["llms_txt"] = {"points": llms_score, "max": 5}

    # 5. FAQ 섹션 (15점): FAQPage 스키마(8점) + HTML 섹션(7점)
    faq_score = (8 if faq.get("has_faq_schema") else 0) + (7 if faq.get("has_faq_html") else 0)
    score    += faq_score
    breakdown["faq"] = {
        "points":     faq_score,
        "max":        15,
        "has_schema": faq.get("has_faq_schema", False),
        "has_html":   faq.get("has_faq_html",   False),
    }

    # 6. 서머리 박스 (5점)
    sum_score = 5 if summary.get("found") else 0
    score    += sum_score
    breakdown["summary_box"] = {
        "points": sum_score,
        "max":    5,
        "found":  summary.get("found", False),
        "method": summary.get("method"),
    }

    # 7. Heading 구조 (5점): H1 단일(2) + H2 복수(2) + 논리적 순서(1)
    h_score  = 0
    if headings.get("has_single_h1"):   h_score += 2
    if headings.get("has_multiple_h2"): h_score += 2
    if headings.get("logical_order"):   h_score += 1
    score   += h_score
    breakdown["heading_structure"] = {
        "points":          h_score,
        "max":             5,
        "has_single_h1":   headings.get("has_single_h1",   False),
        "has_multiple_h2": headings.get("has_multiple_h2", False),
        "logical_order":   headings.get("logical_order",   False),
    }

    # 8. 통계 데이터 (5점): 존재 유무
    stat_score = 5 if stats.get("has_stats") else 0
    score     += stat_score
    breakdown["stats_density"] = {"points": stat_score, "max": 5}

    # 9. 리뷰 데이터 SSR (10점): #reviews_container 서버사이드 렌더링 여부
    rev_score = 10 if reviews.get("found") else 0
    score    += rev_score
    breakdown["reviews_ssr"] = {
        "points":      rev_score,
        "max":         10,
        "found":       reviews.get("found",       False),
        "has_content": reviews.get("has_content", False),
    }

    # 10. CSR 비중 (10점): SSR 글자수 / CSR 글자수 비율
    csr_status = csr_ratio.get("status", "unavailable")
    ratio = csr_ratio.get("ratio")
    if csr_status == "skipped":
        # 벌크 분석 시 CSR 생략 — 페널티 없이 제외
        csr_score = 0
        csr_tier  = "skipped"
    elif csr_status == "blocked":
        # 봇 차단 시 페널티 없이 측정불가 처리
        csr_score = 0
        csr_tier  = "blocked"
    elif ratio is None:
        csr_score = 0
        csr_tier  = "unavailable"
    elif ratio >= 0.8:
        csr_score = 10
        csr_tier  = "excellent"
    elif ratio >= 0.5:
        csr_score = 7
        csr_tier  = "good"
    elif ratio >= 0.3:
        csr_score = 4
        csr_tier  = "partial"
    else:
        csr_score = 0
        csr_tier  = "poor"
    score += csr_score
    breakdown["csr_ratio"] = {
        "points":    csr_score,
        "max":       10,
        "ratio":     ratio,
        "tier":      csr_tier,
        "ssr_chars": csr_ratio.get("ssr_chars", 0),
        "csr_chars": csr_ratio.get("csr_chars", 0),
        "status":    csr_ratio.get("status", "unavailable"),
    }

    grade = (
        "Good"             if score >= 90 else
        "Need Improvement" if score >= 70 else
        "Poor"
    )

    return {"total": score, "max": 100, "grade": grade, "breakdown": breakdown}
