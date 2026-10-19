# Sentence labeling guideline (LG.com GEO audit — training data)

You label sentences taken from the main content of LG.com pages (10 countries; English, Spanish, Portuguese,
German, Vietnamese). Judge the sentence in its original language (translate mentally to English first).
A Korean reviewer will check your work using your Korean translation, so the translation must be faithful.

For EACH sentence output three labels, each exactly "y" or "n" (no "maybe"), plus a Korean translation and a very short reason.

## citable (#36 — 고인용 문장)
y = an AI assistant could quote this sentence on its own as a concrete, verifiable FACT about a product, technology
    or company: a spec/number with its meaning, a named standard/certification, a measured or tested result,
    an award/ranking with source, a dated factual statement, a concrete technical explanation.
n = marketing slogans, vague praise, calls to action, navigation/menu/UI text run together, promotions, prices,
    discounts, financing/installment/warranty-period terms, coupons, contact details, legal boilerplate, questions,
    usage instructions, company history/boilerplate ("...was established in 1997 in India" = n).
Reviewer calibration — judged y:
  - Dolby Vision realza cada detalle, y el FILMAKER Mode elimina el procesamiento innecesario para ofrecer una experiencia auténtica con calidad de estudio.
  - *Die Angabe zur Reaktionszeit von 0,03 ms (GtG) bezieht sich auf LG UlraGear-Modelle mit OLED.
  - Imbatible en gaming: hasta 50 veces más rápido que el mejor TV LED del mercado (tiempo de respuesta 0,1ms) 8 , máxima fluidez VRR 165Hz, compatible y certificado con nVidia G-sync/AMD Freesync Premium y cloud gaming 9 .
  - 4 Variable refresh rate (VRR) is supported on models 17Z90R and 16Z90R with GPU option only.
  - Prueba esto Los modelos lanzados en 2022 (webOS 22) y posteriores no son compatibles con la función Time Machine.
  - Plasmaster ™ Ionizer++ Loại bỏ vi khuẩn bám dính tới 99,9% Thanh lọc không khí trong phòng.
Reviewer calibration — judged n:
  - LG UNVEILS TWO GROUNDBREAKING SMARTPHONES Corporate 02/24/2019 Print Share this content.
  - Sign in Join us Welcome coupon New LG Members can use the Welcome Coupon towards their next purchase over $500.
  - Browse LG’s Range of Speakers & Sound Systems Now Ventajas de comprar en LG Iniciar sesión Registrarse Hasta 10% de descuento 5% dto por primera compra en el pago.
  - Tặng Bộ sản phẩm chuyên dụng LG trị giá 950.000 VNĐ khi mua Máy rửa bát LG LDT14BGA3, LDT14SVA4, LDT14BLA4.
  - Bạn có thể kích hoạt tính năng này từ mọi nơi trong nhà, vì tính năng có sẵn từ cả bảng điều khiển tủ lạnh và ứng dụng LG ThinQ.
  - html 22kg Lavadora de Carga Frontal Lavadoras y Secadoras-WM22WV26SR | LG México Parece que JavaScript está desactivado en tu navegador.
  - Cerrar Environmental Handing Fee (EHF) EHFs vary by product and province.
  - The credit product is provided by Klarna Bank AB (publ).

## definition (#33 — 정의문)
y = the sentence explains WHAT a term, technology, feature, product category or concept IS, for a reader who
    does not know it: "X is a ...", "X means ...", "X refers to ...". A product/service definition like
    "LG Channels es un servicio gratuito de LG que transmite televisión en directo" = y.
n = company profile / "About LG" boilerplate ("LG Electronics, Inc.", "LG India is a wholly owned subsidiary..."),
    a product name followed by a list of features/specs, page titles, headlines, breadcrumbs, benefit claims,
    instructions, questions, legal/payment/registration notices, sentences whose subject is "this/it/there".
Reviewer calibration — judged y:
  - El sistema True Wireless se basa en la validación NVIDIA G-Sync compatible para la reducción de la fragmentación, la baja demora de entrada y el rendimiento sin
  - LG is committed to customer-centric innovation, providing solutions that directly address the evolving needs of the food and hospitalit
  - LG is a world-leading producer of TVs, refrigerators, air conditioners, washing machines and mobile devices, including premium LG SIGNATURE and LG ThinQ products featuring artificial intelligence.
  - When it is about time to replace the water purifier filter, the filter replacement indicator on the [Dispense] button lights up in orange instead of blue.
Reviewer calibration — judged n:
  - All other trademarks are the property of their respective owners.
  - PayPal Credit is a regulated credit agreement.
  - Finding the perfect gift for her—whether it’s for a girlfriend or any special woman—blends style, functionality, and cutting-edge innovation.
  - Đây là một cách dễ dàng để theo dõi mặt hàng đặc biệt mà bạn đã để mắt đến hoặc để lưu ý tưởng quà tặng cho bạn bè và gia đình.
  - LG Electronics, Inc.
  - LG Electronics India Pvt. Ltd., a wholly owned subsidiary of LG Electronics, South Korea was established in January 1997 in India.
  - Big Sound Made to move with you xboom Mini delivers rich, powerful sound from a compact, portable design.
  - Ihre E-Mail wurde erfolgreich registriert.

## summary (#35 — 요약 블록)
y = the sentence is (part of) a block that summarizes the page or lists its key points/features with CONCRETE
    content: a "Key Features / Características principales / Hauptmerkmale" list whose items carry specs or
    specific features, an "In this article" overview, a lead paragraph that states what the whole page covers.
n = a page title or headline, breadcrumb, menu, a single generic intro sentence, a key-features list whose items
    are only vague marketing words, body paragraphs, FAQ questions, press-release datelines.
Reviewer calibration — judged y:
  - [Video] How to use the 4-way screen split function in LG Monitor Product Usage Computing Device 05/08/2026 Print Share Share This Content.
  - Step-by-Step-Anleitung In diesem offiziellen Leitfaden findest du leicht nachvollziehbare Anleitungen und Antworten im Zusammenhang mit der Nutzung der LG Sound Suite.
  - Key Features 27-inch 4K UHD (3840x2160) IPS display VESA DisplayHDR™ 400 180Hz refresh rate 1ms (GtG) response time NVIDIA® G-SYNC® Compatible / VESA Certified AdaptiveSync / AMD FreeSync™ Premium More
  - Principais recursos Tela UltraFine 4K UHD (3840x2160) de 32" Cores Ricas com HDR10 com DCI-P3 90% (Typ.) Dynamic Action Sync / Black Stabilizer Alto-falante estéreo com MaxxAudio® Inclinação ajustável Mais
Reviewer calibration — judged n:
  - Làm thế nào để đảm bảo ngôi nhà của bạn sẵn sàng cho mùa hè
  - <p> 텍스트: key features
  - p.info-desc, p.description, div.c-floating-features 1줄: Tính năng chính Giặt sạch, thông minh vớ
  - p.info-desc, p.description, div.c-floating-features 1줄: Principais recursos INVERTER LG com 24.0
  - p.info-desc, p.description, div.c-floating-features 1줄: Key Features Support up to 4K Resolution
  - p.info-desc, p.description, div.c-floating-features 1줄: Key Features TurboClean3D™ Powerful & Fa


## Reviewer corrections after batch 1 (2026-10-18) — apply these
citable:
  - Asterisk/footnote disclaimers and test-method notes are NOT citable even when they name a standard or model:
    "*Prueba de laboratorio interna de LG basada en EN 60456:2016 con F6V7RWP1WE." = n, "*AI DD có trong 3 chu trình." = n.
  - UI/operation notes about what the device does in a situation ("※ Si es la primera vez que intentas grabar en USB, el televisor realiza una comprobación…") = n.
  - A sentence that explains concretely what a feature/technology does and its effect IS citable even if it starts with "This":
    "This stronger contrast allows bright highlights to stand out more clearly… especially in night scenes" = y.
  - A feature description with a concrete fact ("…el motor Inverter Direct Drive brinda un control preciso y durabilidad con hasta 10 años de garantía") = y.
definition:
  - The reviewer treats a sentence that names a feature/technology and says what it does/provides as a definition:
    "Motor Inverter DD … el motor Inverter Direct Drive brinda un control preciso y durabilidad…" = y.
  - A PDP header block "product name + Key Features list" with concrete feature names (Dual Inverter Compressor, plasmaster ion filter…) = definition y AND citable y.
summary:
  - "Key Features" block = y only when items are concrete features/specs; if items are vague benefits
    ("Solución perfecta para cargas pequeñas… Motor Inverter… Dimensiones") = n.
  - Article header + dateline + one-line teaser ("…HOME APPLIANCES 11/01/2025 …aprende seus hábitos e economiza.") = n.

## Output format
One JSON object per line (JSONL), same order as input, exactly these keys:
{"id": "<id>", "citable": "y|n", "definition": "y|n", "summary": "y|n", "ko": "<faithful Korean translation, max ~150 chars; truncate long run-together nav text with …>", "why": "<Korean, ≤30 chars, the decisive reason>"}
Do not skip, merge or reorder items. Do not add commentary outside the JSONL.

## Reviewer corrections after model-disagreement review (2026-10-18, 186 eval sentences, 132 relabeled)
The reviewer applied a STRICTER standard than batch 1/2 labels. Dominant direction: citable y→n (74), definition y→n (50), summary y→n (11).
citable / definition = n (this overrides the "feature + what it does = definition y" note above):
  - Feature-benefit descriptions ("X helps/lets you/reduces/circulates hot air for even cooking", "The door can be changed…") are NOT citable and NOT definitions.
  - Recommendations ("8–9 kg is recommended for an average family") = n.
  - Spec fragments / attribute strings (tilt -5~25°, dimensions W600×H850, "32\" 3840x2160 VA 16:9…") = citable n, summary n.
  - Footnotes, test-condition notes, model-applicability notes ("*4K 144Hz applies to 83/77/65\" OLED M5") = n (reaffirmed).
  - Support/troubleshoot behaviour notes ("2017 and later: turns off after 10 minutes", "cannot delete the app on webOS 6.0+") = n.
  - Press-release boilerplate, datelines, survey statistics in PR copy, booth/event announcements = n.
  - Company/partner profiles ("About the Energy Saving Trust…", "LG Pro Dealers are independent contractors…") = definition n.
citable / definition = y (kept or added):
  - Sentence naming a technology AND stating a concrete, verifiable claim: "R1 Compressor reduces up to 4dB of noise" = definition y;
    "LG OLED evo: self-lit OLED pixels, infinite contrast, AI 4K upscaling" = citable y, definition y.
  - PDP header with concrete feature names (Multi-Air Flow, Smart Diagnosis, ENERGY STAR) = citable y.
summary: article-body "key features" lists and PDP spec headers are NOT summary (summary is decided by the #35 DOM rule in production).
Note: the reviewer's calls are not perfectly consistent (e.g. "Air Fry circulates hot air…" = n but "AI engine analyses every frame" = y); when in doubt choose n.

## [WITHDRAWN 2026-10-20 — do not apply] v3 relabel — consolidated strict standard
> Withdrawn: a blind relabel of the 328 human-reviewed sentences with this section reached only 10 % citable recall (F1 18 vs. v2 model 79). It wrongly extended troubleshoot-page strictness to all pages. Superseded by the calibrated section below.
Derived from three reviewer passes (batch-1 review, 186-sentence model-disagreement review, 418-sentence troubleshoot review).
In every pass the reviewer flipped most y labels to n. The reviewer's real question is:
**"Would an AI answer engine copy this sentence verbatim as a FACT about a specific LG product, technology, spec, standard or error code?"**
If not clearly yes → n. Expected rates on LG.com body text: citable y ≈ 4–10 %, definition y ≈ 2–5 %.

citable = y ONLY when the sentence is self-contained (subject named in the sentence, not "it/this/these") AND carries at least one of:
  - a spec/number with its meaning (capacity, temperature range, pressure, size, response time, refresh rate, energy rating, % result with test basis in the same sentence)
  - a named standard / certification / compatibility (NVIDIA G-SYNC Compatible, ENERGY STAR, VESA DisplayHDR 400, webOS 22+ only)
  - a model-year / model-range applicability stated as a full sentence ("Time Machine is supported only on models released before 2021")
  - an error code / indicator with its meaning ("CH04 indicates a drain problem caused by …")
  - a concrete technical mechanism of a named LG technology with a verifiable claim ("R1 Compressor reduces noise by up to 4 dB")
citable = n (always), even if well written:
  - feature-benefit / what-it-lets-you-do descriptions ("X lets you control…", "X helps keep food fresh", "enjoy immersive sound")
  - recommendations, usage tips, how-to steps, button presses, menu paths, settings instructions (unless the sentence states a product spec/installation spec number)
  - hedged causes ("may be", "usually because", "could be") and generic causes
  - spec fragments / attribute strings without a predicate, key-feature lists run together, product name + spec list
  - footnotes, asterisk notes, test-condition notes, "results may vary", model-applicability footnotes
  - press-release boilerplate, datelines, quotes from executives, survey stats in PR copy, event/booth announcements, awards without source
  - prices, promotions, financing, warranty, delivery, coupons, membership, contacts, legal, cookie/JS notices, navigation, titles, questions
definition = y ONLY when the sentence names the thing and states WHAT IT IS ("X is a … / X refers to … / X는 ~이다 / X es un …"),
  or what a named code/indicator MEANS. Includes general (non-LG) term definitions (set-top box, MAC address) — those are definition y but citable n.
definition = n: what a feature does or enables, benefits, company profiles ("LG is a world-leading …", "About LG …"), sequences/step lists,
  sentences whose subject is "this/it/there", product name + features.
summary = n for everything except a genuine page-level overview sentence ("This guide explains how to …", "In this article: …").
  Key-feature lists, PDP spec headers, article lists, titles = n (summary is decided by the #35 DOM rule in production).
For page type support_troubleshoot also apply reports/shadow_llm/train/GUIDELINE_TS.md including its "검수자 보정" section.
When unsure → n.


## v3 calibrated standard (2026-10-20, derived from the reviewer's own labels) — THIS SECTION OVERRIDES EVERYTHING ABOVE
Derived from the reviewer's actual y/n decisions on 328 reviewed sentences. On general pages (PDP, PLP, experience, buying guide,
microsite, business, press, promotion, home) the reviewer is strict about BENEFIT TALK but accepts concrete TECHNICAL content.
For page type support_troubleshoot apply GUIDELINE_TS.md (with its "검수자 보정" section) instead — that page type is much stricter.

### citable = y when the sentence states at least one of these, with its subject named in the sentence:
  1. A named LG technology / product / feature AND how it works or a measurable effect:
     "The R1 Compressor works to reduce up to 4dB of noise and vibration" · "NanoCell technology delivers a broad colour spectrum by filtering out impurities"
     · "Der neue Algorithmus des alpha 11 AI Processor Gen3 liefert hellere Highlights" · "Adaptiver Kontrast regelt die Stromstärke abhängig von der Helligkeit des Bildes"
     · "O DoorCooling+ mantém a temperatura estável nas prateleiras da porta, enquanto o LinearCooling reduz variações internas"
  2. A spec / number with its meaning: "0.03ms response time and up to 240Hz refresh rate" · "bis zu 24 bit / 192 kHz" · "Pixelabstand von 1,56 Millimetern"
     · "4 a 6 veces más calor por cada kW" · "8 kg für Einzelpersonen, 9 kg für kleine Familien, 10,5 kg …" (capacity-to-household table)
  3. A requirement / compatibility / applicability: "Compatible smartphone with Android 4.1.2 or later or iOS 9 or later required for LG ThinQ app"
     · "Dolby Atmos: H7, M7 support it natively; M5 …" · "the UVnano filter box is an optional accessory for the mid static UMN models"
  4. A test result, certification or award WITH its source: "UL verified for Perfect Black, measured per IDMS 11.5" · "im Test bei Konsolenfan '5 von 5'"
     · "World's first OLED gaming monitors with 240Hz"
  5. A glossary-style definition of a display/technology term: "8K Ultra HD — eight times the resolution of Full HD" · "Full HD (1080p) — …"
  6. A PDP header / key-features block whose items are concrete specs or named technologies
     ("Laser-Beamer mit nativer 4K-UHD-Auflösung von 3.840 x 2.160 Pixeln …", "MULTI V S, 5 HP, R32 … Menor GWP …").
  7. A press sentence announcing a dated, concrete product fact ("Sydney, September 2023 – LG Electronics Australia announced the local availability of its 1:1 ducted … range").

### citable = n:
  - Benefit / convenience talk without a mechanism or number: "The Air Fry circulates hot air for the perfect, even cook" · "AI technology selects optimal dry motions"
    · "The Pet Care cycle helps reduce odours" · "Smudge Resistant finish wipes clean" · "works with Google Assistant and Alexa" · "The door can be changed from right to left swing"
    · "Ambient Mode lets announcements come through" · "Com o Switching Hub, você conecta mouse e teclado" · "Fusion Lighting: customise backlight colours"
  - Feature lines carrying a footnote number ("10) Der LG AI TV erkennt deine Stimme…", "21) Game Dashboard …") and feature-tagline lists in articles
    ("Some of its key features include: Flexible Curved Display … '1 screen, 20 curves'").
  - Spec attribute strings without a predicate (tilt -5~15°, "Exibição - Tamanho 32\" Resolução 3840x2160 …"), simulated-image notes, "*Sold separately".
  - Recommendations ("8–9 kg is recommended for an average family"), survey statistics in PR, company boilerplate, marketing awards quotes without the fact.
  - Prices, promotions, financing, warranty, delivery, contacts, legal, navigation, titles, questions.

### definition = y when a NAMED term / technology / feature / product is explained by what it is or how it works:
  "The R1 Compressor works to reduce up to 4dB…" · "NanoCell … by filtering out impurities" · "ClearMR 10000 minimiert Bewegungsunschärfen"
  · "Auto Clean+ se activa después de usar el aire, detecta la humedad y sopla aire para eliminarla" · "8K Ultra HD — eight times the resolution of Full HD"
  · "The SmartDiagnosis feature helps the service center diagnose problems over the phone or with an app" · "the UVnano filter box is an optional accessory for UMN models".
### definition = n: benefit talk ("Air Fry circulates hot air…", "AI selects optimal motions"), company profiles ("LG Electronics is a global innovator…"),
  "X lets you / you can …" convenience sentences, footnoted feature lines, generic category claims ("Smart TVs allow voice control…").

### summary: n for almost everything (decided by the #35 DOM rule). y only for a page-level overview sentence or a PDP key-features block with concrete items.

### Calibration: on these reviewed sentences the reviewer marked citable y on ~29 % and definition y on ~12 % — a general-page batch with < 5 % y means you are too strict.

### why: write a SPECIFIC reason for each sentence naming the decisive element (e.g. "R1 압축기 4dB 소음 저감 수치", "혜택 서술, 작동 원리 없음", "각주 번호 붙은 기능 문구").
  Do not reuse the same why text for more than 5 sentences in a batch.

## 검수자 결정 (2026-10-20) — 판정이 엇갈리던 4개 유형. 위 모든 섹션보다 우선
1. 각주(별표 *, 번호 "1)" "10." 로 시작하는 주석)는 시험·인증·규정 근거를 담고 있어도 citable n, definition n.
   예: "*LG OLED 패널은 UL 인증을 받았습니다" n · "2) 에너지 등급은 EU 2019/2014 기준" n · "10. 독립 제3자 시험 기준…" n.
2. 제품 페이지 상단 핵심 기능(Key Features / Características principales / Hauptmerkmale / Tính năng chính) 블록이
   제품명·기능명·스펙의 단어 나열이면 citable n, definition n, summary n. 예: "UltraGear 27G810A 4K UHD, Dual-Mode (Max 360Hz), 1ms GtG, HDMI 2.1 …" n.
3. 이름 붙은 기술·기능·부품이 어떻게 작동하는지 설명하는 문장은 수치가 없어도 citable y, definition y.
   예: "NanoCell 기술은 색 스펙트럼의 불순물을 걸러 넓은 색을 낸다" y · "Inverter DD 모터는 에너지 손실이 적어 전력 소비를 줄인다" y
   · "Gold Fin+ 의 두꺼운 핀과 친수 코팅이 내구성을 높인다" y · "Air Fry 는 뜨거운 공기를 고속 순환시켜 고르게 조리한다" y.
   단, 작동 방식 없이 결과·편의만 말하면 n: "Pet Care 코스는 냄새를 줄여 준다" n · "Google Assistant 와 함께 쓸 수 있다" n · "부드러운 천으로 쉽게 닦인다" n.
4. 용량 안내(가구 규모·용도별 권장 용량 수치)는 citable y. 예: "8kg는 1인, 9kg는 소가족, 10.5kg는 일반 가정" y · "일반 가정에는 8~9kg 권장" y.
