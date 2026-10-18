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
