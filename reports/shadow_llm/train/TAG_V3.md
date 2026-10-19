# v3 유형 태깅 지시 (2026-10-20)

검수자가 정한 4개 유형(GUIDELINE.md 끝 "검수자 결정" 섹션)에 해당하는 문장만 찾아낸다. 다른 문장의 라벨은 바꾸지 않는다.
각 문장에 tag 하나를 붙인다.

- footnote : 별표(*)·번호("1)", "10.", "²", "4 ")로 시작하거나 문장 끝/중간이 각주 주석인 문장. 시험 조건, 인증, 규정, 적용 모델, "이미지는 연출" 등.
- kf_list  : 제품 페이지 상단 핵심 기능 블록(Key Features, Características principales, Principais recursos, Hauptmerkmale, Tính năng chính 등)이거나
             제품명 + 기능명/스펙의 단어 나열로 된 조각. 서술어가 있는 완결 문장이 아니다.
- mechanism: 이름 붙은 기술·기능·부품·코스(NanoCell, Inverter DD, Air Fry, Gold Fin+, DoorCooling+, alpha 11 프로세서 등)가 문장 안에 있고,
             그것이 어떻게 작동하는지(무엇을 감지·측정·조절·순환·여과·분사하는지, 어떤 구조·재질로 무엇을 하는지)를 서술한다. 수치 유무는 상관없다.
             결과·편의만 말하면(냄새를 줄여 준다, 연결할 수 있다, 쉽게 닦인다, 최적 설정을 선택한다) mechanism 이 아니라 none.
- capacity : 가구 규모·용도·세탁물 양 등에 따른 권장 용량(kg, L, cu.ft, BTU 등)을 수치로 안내하는 문장.
- none     : 위 어디에도 해당하지 않음. 대부분의 문장은 none 이다.

우선순위: footnote > kf_list > capacity > mechanism > none. (각주로 시작하는 작동 설명은 footnote.)
유형이 support_troubleshoot 인 페이지의 문장은 모두 none 으로 둔다(별도 기준 적용).

출력: 문장마다 JSON 한 줄 {"id": "...", "tag": "footnote|kf_list|mechanism|capacity|none", "why": "<한국어 30자 이내, tag 가 none 이 아닐 때 결정 근거; none 이면 빈 문자열>"}
