"""비 PDP 콘텐츠의 제품라인 추정 (2026-11-25 사용자 요청).

PDP 는 SKU 로 제품이 정해지지만 Experience, Buying Guide, Microsite,
Troubleshooting, Installation Guide 는 페이지마다 다룬 제품을 따로 매핑해야 한다.
LG 카테고리 ID 를 아직 모르므로 제품라인 키(PDP 표본의
run_render_audit.REQUIRED_PDP_CATEGORIES 와 같은 키 + 보조 키)로 추정한다.

근거 우선순위: HS 콘텐츠 시트 product → 제목 앞 대괄호([LG TV] …) → 제목 →
URL 경로 → 제목과 URL 공통.

사용자 결정(2026-11-25)
1. 특정 제품이 없는 페이지 = "제품 무관"(none). 단 Troubleshooting 은 항상 제품이 있으므로
   단서가 없으면 "미분류" + "정밀 검수 필요".
2. 두 제품라인 이상이 걸리면 대표 제품 하나로 넣는다 — 제목에서 "LG TV"처럼 LG 바로 뒤에
   나온 제품, 없으면 제목에서 먼저 나온 제품, 제목에 없으면 URL 에서 같은 순서.
3. 스타일러, 노트북/PC, 프로젝터는 각각 별도 제품라인.

Troubleshooting URL 의 cs-CTxxxxxxxx 코드는 제품 카테고리가 아니다(같은 코드에
청소기, 세탁기, 냉장고가 섞임, 11월 감사 56개 코드 확인) — 쓰지 않는다.
"""
import re
from typing import Optional

# 제품라인 매핑 대상 page_type. PDP 는 SKU 로 매핑하므로 제외.
TARGET_PAGE_TYPES = {"experience", "buying_guide", "microsite",
                     "support_troubleshoot", "installation_guide"}

LABELS = {
    "tv": "TV", "audio": "사운드바/오디오", "monitor": "모니터", "laptop": "노트북/PC",
    "projector": "프로젝터", "mobile": "휴대폰", "refrigerator": "냉장고",
    "washer": "세탁기/건조기", "styler": "스타일러", "dishwasher": "식기세척기",
    "aircon": "에어컨", "aircare": "공기청정기/제습기", "water_purifier": "정수기",
    "vacuum": "청소기", "cooking": "조리기기", "none": "제품 무관",
}
UNKNOWN_LABEL = "미분류"

# 자동 근거 없이 정한 페이지 표시 — 책임이 직접 확인한다(2026-11-25 사용자 지정 문구).
REVIEW = "정밀 검수 필요"

# 순서 = 우선순위. 앞에서 걸린 부분은 지우고 다음 패턴을 본다(dishwasher 안의 washer 등).
# 패턴의 '-' 는 공백/하이픈 구분자로 바꿔 쓴다(_norm 이 구분자를 공백으로 통일).
_LINES = [
    ("styler", r"styler"),
    ("audio", r"soundbar|sound-?bar|barra-de-sonido|speaker|altavoz|lautsprecher|alto-?falante|\bloa\b|earbud|earphone|headphone|tai-?nghe|xboom|tone-?free|tonfrei|\blg tone\b|som de lg sem tom|\bfones\b|auricular|ohrh[öo]rer|subwoofer|caixa-de-som|\baudio\b|home-?theat|soundsuite|sound suite"),
    ("projector", r"projector|proyector|projetor|projektor|beamer|m[áa]y-?chi[ếe]u|cinebeam"),
    ("monitor", r"oled-?monitor|monitor|m[àa]n-?h[ìi]nh-?m[áa]y-?t[íi]nh|m[àa]n-?h[ìi]nh-?lg|m[àa]n-?h[ìi]nh-?(cong|ph[ẳa]ng)|t[ấa]m-?n[ềe]n|ultragear|ultrafine|ultrawide|onscreen-?control|\bosc\b"),
    ("laptop", r"laptop|\bgram\b|notebook|port[áa]til|m[áa]y-?t[íi]nh|\bpc\b|chromebook|touchpad|\bbios\b|microsoft-?edge|\bwindows\b"),
    ("mobile", r"\blg g\d\b|\blgm\d|\blgk\d|\bx screen|face unlock|face recognition"),
    ("tv", r"\btvs?\b|television|televis|fernseh|webos|\boled\b|qned|nanocell|smart-?tv|magic-?remote|controle smart magic|\btivi\b|stanbyme|lg-channels|hgig|ai sound pro|auto-?tu?rning|k[êe]nh truy[ềe]n h[ìi]nh"),
    ("dishwasher", r"dishwasher|lavavajillas|lava-?lou[çc]as|geschirrsp[üu]l|m[áa]y-?r[ửu]a-?(b[áa]t|ch[ée]n)|lavaplatos|\bdw\b"),
    ("washer", r"washer|(?<!hand )washing|front-?load|top-?load|loader|dryer|lavadora|secadora|lava-?e-?seca|m[áa]quina-de-lavar|waschmaschine|waschger|frontlader|trockner|m[áa]y-?gi[ặa]t|m[áa]y-?s[ấa]y|tumble|laundry|lavanderia|wash-?tower|\bwm\b|lavado|clothes|ropa|roupa|\bdrum\b|spin cycle|turbowash|\bai dd\b|ciclo de secagem"),
    ("refrigerator", r"refrigerat|fridge|frigor[íi]fico|frigor|\bfrig\b|nevera|refrigerador|geladeira|k[üu]hl|gefriersc|gem[üu]sebox|vegetable box|t[ủu]-?l[ạa]nh|freezer|ice-?maker|\bice\b|congelador|instaview|\bref\b|wine|vino"),
    ("aircon", r"heater|calefac|aquecedor|air-?condition|aire-?acondicionado|ar-?condicionado|klima|[đd]i[ềe]u-?h[òo]a|mini-?split|heat-?pump|bomba-de-calor|w[äa]rmepumpe|\bac\b|dualcool|artcool|hvac|\brac\b|heating-?cooling|outdoor unit|unidade externa|unidad exterior|au[ßs]eneinheit"),
    ("aircare", r"air-?purif|purificador-de-a(ire|r)|luftreiniger|m[áa]y-?l[ọo]c-?kh[ôo]ng-?kh[íi]|dehumidif|deshumidif|desumidif|luftentfeucht|h[úu]t-?[ẩa]m|aerocat|puricare|humidif|aerotower"),
    ("water_purifier", r"\bro\b|uv purif|purification|water-?purif|purifiers? .*water|water science|purificador-de-agua|wasserspender|m[áa]y-?l[ọo]c-?n[ưu][ớo]c|water-?dispenser"),
    ("vacuum", r"vacuum|aspirador|aspiradora|staubsauger|m[áa]y-?h[úu]t-?b[ụu]i|cordzero|cyking|robot|hombot|steam-?cleaner|dampfreiniger|limpiador a vapor|torre todo en uno|th[áa]p t[ấa]t c[ảa]|all-?in-?one tower|bedding"),
    ("cooking", r"microwave|oven|ofen\b|lichtwellen|cooktop|indu[ck]|horno|forno|microondas|micro-?ondas|mikrowelle|gasherd|kochfeld|\bherd\b|l[òo]-?vi-?s[óo]ng|l[òo]-?n[ưu][ớo]ng|b[ếe]p|\bhob\b|\brange\b|cooking|cocina|kitchen|k[üu]che|neochef|infravermelho|infrarrojos"),
]
_LC = [(k, re.compile(p.replace("-?", " ?").replace("-", " "), re.I)) for k, p in _LINES]

# HS 콘텐츠 시트(reports/hs_contents.csv) product 값 → 키. Common(공통)은 제목, URL 로 다시 본다.
_HS = {"WM": "washer", "Dryer": "washer", "REF": "refrigerator", "DW": "dishwasher",
       "VCC": "vacuum", "Cooking": "cooking", "MWO": "cooking"}


def _norm(s: str) -> str:
    return " " + re.sub(r"[-_/|:,()\[\]]+", " ", (s or "").lower()) + " "


def _hits(text: str) -> list:
    """[(키, 처음 나온 위치)] — LG 바로 뒤 제품 먼저, 그다음 위치 순. 걸린 부분은 같은 길이 공백으로 지워 위치를 보존."""
    t, out, txt = _norm(text), [], {}
    for k, p in _LC:
        m = p.search(t)
        if m:
            out.append((k, m.start()))
            txt[k] = m.group()
            t = p.sub(lambda x: " " * len(x.group()), t)
    # 히트펌프 건조기(Heat Pump vs. Condenser Dryers) — 건조기와 함께 나온 히트펌프는 에어컨이 아니다.
    if "washer" in txt and re.match(r"heat ?pump|bomba de calor|w[äa]rmepumpe", txt.get("aircon", ""), re.I):
        out = [x for x in out if x[0] != "aircon"]
    # 대표 제품 선택용: 바로 앞이 "lg " 인 제품(… on your LG TV)을 먼저, 그다음 먼저 나온 순.
    orig = _norm(text)
    return sorted(out, key=lambda x: (not orig[max(0, x[1] - 3):x[1]].endswith("lg "), x[1]))


def detect_product_line(url: str, title: str = "", hs_product: str = "",
                        page_type_id: Optional[str] = None) -> dict:
    """{"id": 키|"none"|None, "label": 표시명, "basis": 근거, "review": "정밀 검수 필요"|None}.

    basis: hs | title | url | url+title | 대표(복수 감지) | none
    """
    def res(k, basis, review=None):
        return {"id": k, "label": LABELS.get(k, UNKNOWN_LABEL), "basis": basis, "review": review}

    if hs_product in _HS:
        return res(_HS[hs_product], "hs")
    path = re.sub(r"^https?://[^/]+/[^/]+/", "", url or "")
    path = re.sub(r"cs-ct\d+-\d+\w*", " ", path, flags=re.I)
    u, ti = _hits(path), _hits(title)
    b = re.match(r"\s*\[([^\]]+)\]", title or "")
    if b:
        bh = _hits(b.group(1))
        if bh:
            return res(bh[0][0], "title" if len(bh) == 1 else "대표(복수 감지)")
    uk, tk = {k for k, _ in u}, {k for k, _ in ti}
    if len(tk) == 1:
        return res(ti[0][0], "title")
    if len(uk) == 1 and not tk:
        return res(u[0][0], "url")
    common = [k for k, _ in ti if k in uk]
    if len(set(common)) == 1:
        return res(common[0], "url+title")
    if ti:      # 결정 2: 제목에서 "LG 제품명"으로 나온 제품, 없으면 먼저 나온 제품
        return res(ti[0][0], "대표(복수 감지)")
    if u:
        return res(u[0][0], "대표(복수 감지)")
    # 결정 1: 특정 제품 없음. Troubleshooting 은 제품이 있어야 하므로 미분류로 남긴다.
    if page_type_id == "support_troubleshoot":
        return res(None, "none", REVIEW)
    return res("none", "none")


def product_line_for(page_type_id: Optional[str], url: str, title: str = "",
                     hs_product: str = "") -> Optional[dict]:
    """매핑 대상 page_type 이면 detect_product_line 결과, 아니면 None."""
    if page_type_id not in TARGET_PAGE_TYPES:
        return None
    return detect_product_line(url, title, hs_product, page_type_id)
