"""
룰 엔진 — 어드민에서 정의한 규칙을 실제로 평가합니다.

context dict:
  - soup: BeautifulSoup (HTML 파싱 결과)
  - page_data: dict (redirect_count, final_url 등)
  - jsonld_types: set[str] (소문자 변환된 모든 @type 값)
  - base_url: str (llms.txt 등 HTTP 체크용)
"""

import re
import operator as op
import httpx
from bs4 import BeautifulSoup

# ── 룰 타입 메타데이터 (어드민 UI에서 사용) ───────────────────────────────────

RULE_TYPES = {
    "css_exists": {
        "label": "CSS 요소 존재",
        "description": "CSS 셀렉터에 매칭되는 요소가 1개 이상 존재하는지 확인",
        "params": {"selector": {"label": "CSS 셀렉터", "type": "text", "placeholder": "#reviews_container"}},
    },
    "css_count": {
        "label": "CSS 요소 개수",
        "description": "CSS 셀렉터에 매칭되는 요소 개수를 비교",
        "params": {
            "selector": {"label": "CSS 셀렉터", "type": "text", "placeholder": "h1"},
            "operator": {"label": "비교 연산자", "type": "select", "options": ["==", ">=", "<=", ">", "<"]},
            "value":    {"label": "비교 값", "type": "number", "placeholder": "1"},
        },
    },
    "css_text_min_length": {
        "label": "요소 텍스트 최소 길이",
        "description": "CSS 셀렉터의 첫 요소 텍스트 길이가 최소값 이상인지 확인",
        "params": {
            "selector":   {"label": "CSS 셀렉터", "type": "text", "placeholder": "title"},
            "min_length": {"label": "최소 길이", "type": "number", "placeholder": "10"},
        },
    },
    "css_attr_exists": {
        "label": "속성값 존재",
        "description": "CSS 셀렉터의 요소에 특정 속성이 비어있지 않은 값으로 존재하는지 확인",
        "params": {
            "selector":   {"label": "CSS 셀렉터", "type": "text", "placeholder": 'meta[property="og:title"]'},
            "attr":       {"label": "속성명", "type": "text", "placeholder": "content"},
            "min_length": {"label": "최소 길이 (선택)", "type": "number", "placeholder": "0"},
        },
    },
    "css_all_have_attr": {
        "label": "모든 요소에 속성 존재",
        "description": "CSS 셀렉터에 매칭되는 모든 요소에 특정 속성이 존재하는지 확인 (0개면 통과)",
        "params": {
            "selector": {"label": "CSS 셀렉터", "type": "text", "placeholder": "img"},
            "attr":     {"label": "속성명", "type": "text", "placeholder": "alt"},
        },
    },
    "css_attr_not_contains": {
        "label": "속성에 텍스트 미포함",
        "description": "CSS 셀렉터 요소의 속성값에 특정 텍스트가 포함되지 않으면 통과 (요소 없으면 통과)",
        "params": {
            "selector": {"label": "CSS 셀렉터", "type": "text", "placeholder": 'meta[name="robots"]'},
            "attr":     {"label": "속성명", "type": "text", "placeholder": "content"},
            "value":    {"label": "미포함 텍스트", "type": "text", "placeholder": "noindex"},
        },
    },
    "class_id_contains": {
        "label": "class/id에 키워드 포함",
        "description": "요소의 class 또는 id 속성에 키워드가 포함되는지 확인",
        "params": {
            "keywords": {"label": "키워드 (쉼표 구분)", "type": "text", "placeholder": "faq,자주 묻는,accordion"},
            "tags":     {"label": "검색 태그 (쉼표 구분)", "type": "text", "placeholder": "div,section,aside"},
        },
    },
    "text_has_pattern": {
        "label": "텍스트 정규식 매칭",
        "description": "특정 태그들의 텍스트에서 정규식 패턴이 매칭되는 단어가 존재하는지 확인",
        "params": {
            "pattern": {"label": "정규식 패턴", "type": "text", "placeholder": "\\d"},
            "tags":    {"label": "검색 태그 (쉼표 구분)", "type": "text", "placeholder": "p,li,td,h1,h2,h3"},
        },
    },
    "http_status": {
        "label": "HTTP 상태 확인",
        "description": "특정 경로로 HTTP 요청을 보내 응답 상태 코드를 확인",
        "params": {
            "path":   {"label": "경로", "type": "text", "placeholder": "/llms.txt"},
            "status": {"label": "기대 상태코드", "type": "number", "placeholder": "200"},
        },
    },
    "schema_type_exists": {
        "label": "JSON-LD @type 존재",
        "description": "페이지의 JSON-LD 구조화 데이터에 특정 @type이 존재하는지 확인 (OR 조건: 쉼표로 여러 타입 지정 가능)",
        "params": {
            "type": {"label": "@type (쉼표 구분 시 OR 조건)", "type": "text", "placeholder": "Product,IndividualProduct"},
        },
    },
    "heading_order": {
        "label": "제목 논리적 순서",
        "description": "H1이 H2/H3/H4보다 먼저 나타나는지 확인",
        "params": {},
    },
    "redirect_max": {
        "label": "리다이렉트 최대 횟수",
        "description": "페이지 접근 시 리다이렉트 횟수가 최대값 이하인지 확인",
        "params": {
            "max_count": {"label": "최대 횟수", "type": "number", "placeholder": "3"},
        },
    },
}


# ── 평가 함수 ─────────────────────────────────────────────────────────────────

def evaluate_rule(rule: dict, context: dict) -> dict:
    """규칙을 평가하여 결과를 반환합니다."""
    rule_type = rule.get("type", "")
    params = rule.get("params", {})

    handler = _HANDLERS.get(rule_type)
    if not handler:
        return {"pass": False, "value": None, "hint": f"알 수 없는 규칙 타입: {rule_type}"}

    try:
        return handler(params, context)
    except Exception as e:
        return {"pass": False, "value": None, "hint": f"규칙 평가 오류: {str(e)}"}


def _eval_css_exists(params: dict, ctx: dict) -> dict:
    soup = ctx.get("soup")
    if not soup:
        return {"pass": False, "value": None, "hint": "HTML 파싱 실패"}
    selector = params.get("selector", "")
    els = soup.select(selector)
    found = len(els) > 0
    return {
        "pass": found,
        "value": f"{len(els)}개 발견" if found else None,
        "hint": None if found else f"'{selector}' 요소를 찾을 수 없습니다.",
    }


def _eval_css_count(params: dict, ctx: dict) -> dict:
    soup = ctx.get("soup")
    if not soup:
        return {"pass": False, "value": None, "hint": "HTML 파싱 실패"}
    selector = params.get("selector", "")
    operator_str = params.get("operator", ">=")
    target = int(params.get("value", 1))

    els = soup.select(selector)
    count = len(els)

    ops = {"==": op.eq, ">=": op.ge, "<=": op.le, ">": op.gt, "<": op.lt}
    compare = ops.get(operator_str, op.ge)
    passed = compare(count, target)

    return {
        "pass": passed,
        "value": f"{count}개",
        "hint": None if passed else f"'{selector}' {count}개 — {operator_str} {target} 필요",
    }


def _eval_css_text_min_length(params: dict, ctx: dict) -> dict:
    soup = ctx.get("soup")
    if not soup:
        return {"pass": False, "value": None, "hint": "HTML 파싱 실패"}
    selector = params.get("selector", "")
    min_length = int(params.get("min_length", 1))

    el = soup.select_one(selector)
    if not el:
        return {"pass": False, "value": None, "hint": f"'{selector}' 요소를 찾을 수 없습니다."}

    text = el.get_text(strip=True)
    passed = len(text) >= min_length

    return {
        "pass": passed,
        "value": text[:80] if text else None,
        "hint": None if passed else f"텍스트 길이 {len(text)} — {min_length}자 이상 필요",
    }


def _eval_css_attr_exists(params: dict, ctx: dict) -> dict:
    soup = ctx.get("soup")
    if not soup:
        return {"pass": False, "value": None, "hint": "HTML 파싱 실패"}
    selector = params.get("selector", "")
    attr = params.get("attr", "")
    min_length = int(params.get("min_length", 0))

    el = soup.select_one(selector)
    if not el:
        return {"pass": False, "value": None, "hint": f"'{selector}' 요소를 찾을 수 없습니다."}

    val = (el.get(attr) or "").strip()
    passed = bool(val) and len(val) >= max(min_length, 1)

    return {
        "pass": passed,
        "value": val[:120] if val else None,
        "hint": None if passed else f"'{attr}' 속성이 없거나 {min_length}자 미만입니다." if min_length else f"'{attr}' 속성이 없습니다.",
    }


def _eval_css_all_have_attr(params: dict, ctx: dict) -> dict:
    soup = ctx.get("soup")
    if not soup:
        return {"pass": False, "value": None, "hint": "HTML 파싱 실패"}
    selector = params.get("selector", "")
    attr = params.get("attr", "")

    els = soup.select(selector)
    if not els:
        return {"pass": True, "value": "해당 요소 없음", "hint": None}

    missing = [el for el in els if el.get(attr) is None]
    passed = len(missing) == 0

    return {
        "pass": passed,
        "value": f"{len(els)}개 중 {len(els) - len(missing)}개 '{attr}' 보유",
        "hint": None if passed else f"{len(missing)}개 요소에 '{attr}' 속성이 없습니다.",
    }


def _eval_css_attr_not_contains(params: dict, ctx: dict) -> dict:
    soup = ctx.get("soup")
    if not soup:
        return {"pass": False, "value": None, "hint": "HTML 파싱 실패"}
    selector = params.get("selector", "")
    attr = params.get("attr", "")
    bad_value = params.get("value", "").lower()

    el = soup.select_one(selector)
    if not el:
        return {"pass": True, "value": "태그 없음 (기본 허용)", "hint": None}

    attr_val = (el.get(attr) or "").strip()
    passed = bad_value not in attr_val.lower()

    return {
        "pass": passed,
        "value": attr_val or None,
        "hint": None if passed else f"'{bad_value}'가 포함되어 있습니다.",
    }


def _eval_class_id_contains(params: dict, ctx: dict) -> dict:
    soup = ctx.get("soup")
    if not soup:
        return {"pass": False, "value": None, "hint": "HTML 파싱 실패"}

    keywords_raw = params.get("keywords", "")
    if isinstance(keywords_raw, list):
        keywords = [k.strip().lower() for k in keywords_raw if k.strip()]
    else:
        keywords = [k.strip().lower() for k in keywords_raw.split(",") if k.strip()]

    tags_raw = params.get("tags", "")
    if isinstance(tags_raw, list):
        tags = [t.strip() for t in tags_raw if t.strip()]
    else:
        tags = [t.strip() for t in tags_raw.split(",") if t.strip()]

    if not keywords:
        return {"pass": False, "value": None, "hint": "키워드가 지정되지 않았습니다."}

    search_tags = tags if tags else True  # True = all tags

    for el in soup.find_all(search_tags):
        cls = " ".join(el.get("class", [])).lower()
        el_id = (el.get("id") or "").lower()
        combined = cls + " " + el_id
        for kw in keywords:
            if kw in combined:
                return {
                    "pass": True,
                    "value": f"<{el.name}> class/id에서 '{kw}' 발견",
                    "hint": None,
                }

    # heading 텍스트도 확인
    for heading in soup.find_all(["h1", "h2", "h3", "h4", "h5"]):
        text = heading.get_text(strip=True).lower()
        for kw in keywords:
            if kw in text:
                return {
                    "pass": True,
                    "value": f"<{heading.name}> 텍스트에서 '{kw}' 발견",
                    "hint": None,
                }

    # details 요소 3개 이상도 체크
    details = soup.find_all("details")
    if len(details) >= 3:
        return {"pass": True, "value": f"<details> {len(details)}개 발견", "hint": None}

    return {
        "pass": False,
        "value": None,
        "hint": f"키워드({', '.join(keywords[:3])}...)를 포함한 요소를 찾을 수 없습니다.",
    }


def _eval_text_has_pattern(params: dict, ctx: dict) -> dict:
    soup = ctx.get("soup")
    if not soup:
        return {"pass": False, "value": None, "hint": "HTML 파싱 실패"}

    pattern_str = params.get("pattern", r"\d")
    tags_raw = params.get("tags", "")
    if isinstance(tags_raw, list):
        tags = [t.strip() for t in tags_raw if t.strip()]
    else:
        tags = [t.strip() for t in tags_raw.split(",") if t.strip()]

    if not tags:
        tags = ["p", "li", "td", "h1", "h2", "h3", "h4", "h5", "h6"]

    text_parts = []
    for el in soup.find_all(tags):
        text_parts.append(el.get_text(strip=True))
    text = " ".join(text_parts)

    words = [w for w in re.split(r"\s+", text) if len(w) > 1]
    if not words:
        return {"pass": False, "value": "텍스트 없음", "hint": "분석할 텍스트가 없습니다."}

    pattern = re.compile(pattern_str)
    matched = [w for w in words if pattern.search(w)]
    passed = len(matched) > 0

    ratio = round(len(matched) / len(words) * 100, 1) if words else 0

    return {
        "pass": passed,
        "value": f"{len(matched)}개 매칭 ({ratio}%)" if passed else None,
        "hint": None if passed else f"패턴 '{pattern_str}'에 매칭되는 텍스트가 없습니다.",
    }


async def _eval_http_status(params: dict, ctx: dict) -> dict:
    base_url = ctx.get("base_url", "")
    path = params.get("path", "/")
    expected = int(params.get("status", 200))

    if not base_url:
        return {"pass": False, "value": None, "hint": "base_url이 없습니다."}

    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            r = await client.get(f"{base_url}{path}")
        passed = r.status_code == expected
        return {
            "pass": passed,
            "value": f"HTTP {r.status_code}",
            "hint": None if passed else f"HTTP {r.status_code} — {expected} 기대",
        }
    except Exception as e:
        return {"pass": False, "value": None, "hint": f"요청 실패: {str(e)}"}


def _eval_schema_type_exists(params: dict, ctx: dict) -> dict:
    jsonld_types = ctx.get("jsonld_types", set())
    type_raw = params.get("type", "")
    target_types = [t.strip().lower() for t in type_raw.split(",") if t.strip()]

    if not target_types:
        return {"pass": False, "value": None, "hint": "@type이 지정되지 않았습니다."}

    found = [t for t in target_types if t in jsonld_types]
    passed = len(found) > 0

    return {
        "pass": passed,
        "value": ", ".join(found) if found else None,
        "hint": None if passed else f"@type '{type_raw}'을(를) 찾을 수 없습니다.",
    }


def _eval_heading_order(params: dict, ctx: dict) -> dict:
    soup = ctx.get("soup")
    if not soup:
        return {"pass": False, "value": None, "hint": "HTML 파싱 실패"}

    seen_h1 = False
    logical = True
    for tag in soup.find_all(["h1", "h2", "h3", "h4"]):
        if tag.name == "h1":
            seen_h1 = True
        elif not seen_h1:
            logical = False
            break

    return {
        "pass": logical,
        "value": "논리적 순서 정상" if logical else None,
        "hint": None if logical else "H2/H3/H4가 H1보다 먼저 나타납니다.",
    }


def _eval_redirect_max(params: dict, ctx: dict) -> dict:
    page_data = ctx.get("page_data", {})
    max_count = int(params.get("max_count", 3))
    actual = page_data.get("redirect_count", 0)
    passed = actual <= max_count

    return {
        "pass": passed,
        "value": f"{actual}회 리다이렉트",
        "hint": None if passed else f"리다이렉트 {actual}회 — {max_count}회 이하 권장",
    }


# ── 핸들러 레지스트리 ─────────────────────────────────────────────────────────

_HANDLERS = {
    "css_exists":             _eval_css_exists,
    "css_count":              _eval_css_count,
    "css_text_min_length":    _eval_css_text_min_length,
    "css_attr_exists":        _eval_css_attr_exists,
    "css_all_have_attr":      _eval_css_all_have_attr,
    "css_attr_not_contains":  _eval_css_attr_not_contains,
    "class_id_contains":      _eval_class_id_contains,
    "text_has_pattern":       _eval_text_has_pattern,
    # http_status는 async — evaluate_rule_async에서 처리
    "schema_type_exists":     _eval_schema_type_exists,
    "heading_order":          _eval_heading_order,
    "redirect_max":           _eval_redirect_max,
}

# async 핸들러 (http_status)
_ASYNC_HANDLERS = {
    "http_status": _eval_http_status,
}


async def evaluate_rule_async(rule: dict, context: dict) -> dict:
    """동기 + 비동기 규칙을 모두 평가합니다."""
    rule_type = rule.get("type", "")
    params = rule.get("params", {})

    # async 핸들러 먼저 확인
    async_handler = _ASYNC_HANDLERS.get(rule_type)
    if async_handler:
        try:
            return await async_handler(params, context)
        except Exception as e:
            return {"pass": False, "value": None, "hint": f"규칙 평가 오류: {str(e)}"}

    # sync 핸들러
    return evaluate_rule(rule, context)
