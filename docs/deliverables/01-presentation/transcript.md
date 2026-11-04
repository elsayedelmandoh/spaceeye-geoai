# Presentation transcript: مين يقول إيه، slide بعد slide

خطة الكلام للعرض أمام اللجنة في 14:30 دقيقة داخل slot مدته 20 دقيقة، فيفضل حوالي 5:30 للأسئلة (الـ team lead، 2026-11-04) ([presentation.pptx](presentation.pptx)، 20 slides). نص الـ rubric بيقول 12 دقيقة. أرقام الـ slides هنا هي نفس أرقام PowerPoint من 1 لـ 20. كل عضو يقدّم الجزء اللي بناه بنفسه (الـ owners من [02-team-roles-and-tasks.md](../../requirements/02-team-roles-and-tasks.md))، عشان يقدر يدافع عنه في الأسئلة. الأوقات هي أوقات الـ speaker notes في الـ deck ومجموعها 14:30. الكلام بالعربي، والمصطلحات المهمة تفضل بالإنجليزي زي ما هي مكتوبة على الشاشة والـ slides. السرعة حوالي 130 كلمة في الدقيقة (0:30 ≈ 65 كلمة)؛ قولها بأسلوبك، لكن الأرقام تفضل بالظبط.

قواعد للكل: codes بس (C18، عمرنا ما نقول اسم)؛ نقول "priority level" وعمرنا ما نقول "risk level"؛ عمرنا ما نوصف compound حقيقي بإنه "distressed"؛ K5 هو "months eligible for review" ومش غرامة؛ أي حاجة من Track B هي "generated, Synthetic - for training only".

## Running order

| Slide | العنوان | العضو | الوقت | Dashboard live |
| --- | --- | --- | --- | --- |
| 1 | SpaceEye GeoAI | السيد المندوه (lead) | 0:30 | - |
| 2 | Problem in numbers | فيرينا فؤاد | 0:30 | - |
| 3 | The question and the decision | السيد المندوه | 0:30 | - |
| 4 | As-is: how R7 is followed today | فيرينا فؤاد | 0:45 | - |
| 5 | To-be: the new process | السيد المندوه | 0:45 | - |
| 6 | Data | أحمد عبد الحميد | 0:30 | - |
| 7 | Seeing construction from space | سلمى مجدي | 0:30 | - |
| 8 | The Track A rule | أحمد عبد الحميد | 0:45 | - |
| 9 | Live demo (Track A) | ندى شادي | 1:00 | Priority map ← Compound file ← visit form |
| 10 | Search, filters and map click | السيد المندوه | 0:30 | search و filter و map click |
| 11 | Four screens, one path from alert to action | ندى شادي | 0:30 | - |
| 12 | Backtest: 1 of 6 and why | أحمد عبد الحميد | 1:15 | District view (C21 early signal) |
| 13 | Track B: generated data | فيرينا فؤاد | 0:45 | - |
| 14 | The observatory: one what-if scenario | السيد المندوه | 0:30 | Digital twin what if (Track B, S3 capacity) |
| 15 | Ask the project: the chatbot | سلمى مجدي | 0:45 | chatbot (💬) |
| 16 | What the chatbot knows, and its limits | سلمى مجدي | 0:30 | - |
| 17 | Value in EGP (3 settings) | فيرينا فؤاد | 1:15 | - |
| 18 | Risks and responsible use | سلمى مجدي | 1:00 | - |
| 19 | Launching in production | أحمد عبد الحميد | 0:45 | - |
| 20 | Decision, transition and next step | ندى شادي | 1:00 | - |
| | **Total** | **20 slides · 14:30** | **14:30** | |

لكل عضو: السيد 2:45 (الافتتاح، السؤال، الـ to-be، الـ search والـ filters، الـ what-if)، فيرينا 3:15 (المشكلة، الـ as-is، Track B، الـ value)، أحمد 3:15 (الـ data، الـ rule، الـ backtest، الـ production)، سلمى 2:45 (الـ satellites، الـ chatbot، الـ risks)، ندى 2:30 (الـ dashboard، القرار). المجموع 14:30.

## بطاقة كل عضو

كل واحد يحفظ الكارت بتاعه: الـ slides، اللي هيعرضه live، واللي يكون جاهز يفتحه لو اتسأل.

| العضو | Slides | الوقت | يعرض live على الـ dashboard | جاهز يفتحه في الأسئلة | يحضّر إيه |
| --- | --- | --- | --- | --- | --- |
| السيد المندوه | 1, 3, 5, 10, 14 | 2:45 | **Search and filters** (C1 ← 6 من 12، level filter، map click، Clear selection)؛ Digital twin what if ← **S3 · Capacity** (2 أو 6 بدل 4) | tabs **S1 · Cost shock** و **S2 · Collections drop** ("Nobody crosses a threshold")؛ `docs/deliverables/to-be.md` | أرقام الـ what-if (45 من 744)؛ يدير الأسئلة |
| فيرينا فؤاد | 2, 4, 13, 17 | 3:15 | - | District view (الـ activity spread و developer groups و delays للـ as-is)؛ `docs/deliverables/as-is.md`؛ District view ← **A false alarm against a missed case** (1 missed case ≈ 6.7 false alarms بالـ central assumptions) | أرقام الـ as-is (48 review في السنة، 18 لـ 33 شهر، median 25)؛ أرقام الـ recall@4 والـ baseline 0.335؛ أرقام الـ value الثلاثة |
| أحمد عبد الحميد | 6, 8, 12, 19 | 3:15 | District view: **An early signal: C21** و **When the solution fails** | Compound file ← الـ KPI tiles (K2، K3، K6، K5) لأي compound | الـ backtest بالأرقام (1 من 6، 0 من 6، target 5) |
| سلمى مجدي | 7, 15, 16, 18 | 2:45 | الـ chatbot (سؤال + follow-up) | Compound file ← **Satellite curves**؛ `chatbot/knowledge/SOURCES.csv` | تسأل الـ chatbot مرة قبل العرض |
| ندى شادي | 9, 11, 20 (والماوس في كل الـ live) | 2:30 | Priority map ← cycle cards ← CSV ← Compound file C18 ← Visit form | أي شاشة؛ هي اللي بتضغط | الأربع tabs متظبطين؛ نسخة rehearsal من الـ app data؛ slide 20 بالحرف |

## Timing checkpoints

العضو اللي عليه الدور الجاي ماسك الـ timer ويبص عليه عند كل checkpoint؛ لو متأخرين أكتر من 15 ثانية، المتكلم يختصر جملة.

| لما نوصل لآخر | الوقت المفروض |
| --- | --- |
| slide 5 (الـ to-be) | 3:00 |
| slide 8 (الـ rule) | 4:45 |
| slide 11 (الأربع شاشات) | 6:45 |
| slide 15 (الـ chatbot) | 10:00 |
| slide 18 (الـ risks) | 12:45 |
| slide 20 (القرار) | 14:30 |

## قبل ما نبدأ (بـ 10 دقايق)

- لابتوب واحد وشاشتين: PowerPoint في presenter view، و browser فيه الـ dashboard شغال (نشغّله بـ `start.ps1`؛ الـ dashboard على port 8501 والـ chatbot على 8001).
- أربع tabs في الـ browser، مفتوحين ومتظبطين قبلها (كل tab ليه session لوحده، فالـ track switch مش بيتنقل بينهم):
  1. Tab 1: **1 · Priority map**، Track A، في أول الصفحة، الـ search فاضي، مفيش filter، ومفيش compound متختار.
  2. Tab 2: **3 · District view**، عند "An early signal: C21".
  3. Tab 3: Track B، **4 · Digital twin what if**، على tab **S3 · Capacity**.
  4. Tab 4: الـ chatbot على http://127.0.0.1:8001/ (أو زرار 💬 في الـ dashboard). اسأل سؤال واحد قبل العرض عشان الـ embedding model يكون اتحمّل؛ أول سؤال بيبقى بطيء. على جهاز جديد أول تشغيل بينزّل الـ embedding model (intfloat/multilingual-e5-small)، فشغّله قبلها بيوم على نت كويس.
- التنقل: `Alt+Tab` من الـ slides للـ browser، و `Ctrl+1/2/3/4` للـ tab، و `Alt+Tab` للرجوع. اتمرّنوا عليه؛ لازم ياخد أقل من ثانيتين.
- الـ visit form: استخدموا نسخة rehearsal من فولدر الـ app data، لأن أي visit بيتحفظ بيبقى row حقيقي في ملف الـ visits.
- Backup: لو الـ dashboard أو الـ chatbot ما فتحش، اقف على الـ slide؛ slides 9 و 10 و 12 و 14 و 15 فيهم نفس الشاشات كـ screenshots. قول "دي نفس الشاشة" وكمّل. عمرنا ما نعمل debug قدام اللجنة.
- شخص واحد (ندى) ماسك الماوس في كل الأجزاء الـ live؛ اللي بيتكلم بيتكلم، وندى بتدوس على الإشارة (للسيد في slides 10 و 14، ولأحمد في slide 12، ولسلمى في slide 15).

## إزاي نسلّم لبعض (handover)

كل handover جملة واحدة: اسم اللي جاي والسؤال اللي هيجاوب عليه، والمتكلم الجديد يبدأ بالإجابة على طول، مش بـ "شكرًا". لما نفس الشخص بيكمّل بيبقى **Transition** مش handover. اللي خلّص يرجع خطوة، واللي جاي يكون واقف جنب الشاشة قبل ما الجملة تخلص. في slides 9 و 10 و 11 ندى فاضلة على الماوس، فالـ handover بين ندى والسيد من غير ما حد يتحرك من مكانه.

---

## الدور 1 · السيد المندوه (team lead، الافتتاح)

### Slide 1/20 · SpaceEye GeoAI (0:30)

**العضو:** السيد المندوه

**يقول:**
"صباح الخير. إحنا SpaceEye GeoAI: New Capital Radar، رادار لشركة بتمتلك مدينة. شكرًا لـ د. نديم عبدين على الإشراف. الفريق: السيد المندوه، وفيرينا فؤاد، وأحمد عبد الحميد، وندى شادي، وسلمى مجدي؛ وكل واحد هيقدّم الجزء اللي بناه. النهارده هنجاوب على سؤال واحد: أنهي compounds اللجنة تزورها الأول، وليه."

**على الـ dashboard:** على الـ slide بس. ابدأ والـ slide بالـ logos على الشاشة، وابص للجنة مش للشاشة.

**Handover:** "فيرينا هتبدأ بالمشكلة، بأرقام رئيس مجلس الإدارة نفسه."

---

## الدور 2 · فيرينا فؤاد (المشكلة)

### Slide 2/20 · Problem in numbers (0:30)

**العضو:** فيرينا فؤاد

**تقول:**
"دي أرقام رئيس مجلس الإدارة، مش أرقامنا: أكتر من 400 developer، وأكتر من 500 project، و field review كل 3 شهور، وحوالي 7 لـ 8% متأخرين تأخير كبير، و 6 mutual terminations. اللجنة مش هتقدر تزور كل حاجة في كل cycle. يبقى السؤال: أنهي compounds الأول؟ وإجابتنا: cycle list قصيرة، ومع كل compound سبب واضح."

**على الـ dashboard:** على الـ slide بس؛ شاوري على الـ stat callouts وإنتي بتقولي كل رقم. لو اتسأل "الأرقام دي منين؟": تصريحات رئيس مجلس الإدارة، مسجلة في `docs/requirements/01-specs.md` section 12.

**Handover:** "طب إيه السؤال بالظبط؟ السيد."

---

## الدور 3 · السيد المندوه (السؤال والقرار)

### Slide 3/20 · The question and the decision (0:30)

**العضو:** السيد المندوه

**يقول:**
"منطقة واحدة، R7: 12 compound بـ codes، والربع 2026Q3. السؤال: أنهي compounds اللجنة تزورها الأول في الـ cycle الجاي، وليه؟ الـ observatory بيرتّب، واللجنة هي اللي بتقرر. الإطار: preventive، و Buildings & Facilities، و normal conditions، والهدف stability. المتأثرين: المشترين، 6,474 وحدة في الخمس حالات المتأخرة. وليه دلوقتي؟ لأن C18 عدّى أول handover date اتعلن بـ 57 شهر."

**على الـ dashboard:** على الـ slide بس؛ شاور على الـ funnel (12 ← 4). الـ dashboard هيوريها live مع ندى بعد شوية، فقول: "وهتشوفوها live."

**Handover:** "طب الوضع النهارده شكله إيه؟ فيرينا."

---

## الدور 4 · فيرينا فؤاد (الـ as-is)

### Slide 4/20 · As-is: how R7 is followed today (0:45)

**العضو:** فيرينا فؤاد

**تقول:**
"الـ map دي من public sources وهنأكدها مع ACUD. نفس الـ field review كل 3 شهور لكل الـ compounds: 48 في السنة. 5 من 6 حالات public متأخرة 18 لـ 33 شهر، median 25. الأسباب: الـ effort مش على حسب الأولوية، والـ progress من كلام الـ developer، ومحدش بيقارن السرعة بالموعد. الدليل: C19 أعلن 70% و 28% بس من مساحته المبنية كانت 20 متر أو أعلى؛ سبب نزور، مش إثبات. و C14 أعلن 35% قبل ميعاده بـ 3 شهور وأجّله. والـ activity متوسطها 0.61، والمدى من 0.03 لـ 0.90."

**على الـ dashboard:** على الـ slide بس. لو اتسأل "الأرقام دي بتخبي إيه؟": District view بيوري الـ activity spread والـ developer groups والـ delays (`docs/deliverables/as-is.md`). وقولي إن الـ process map محتاجة تأكيد من ACUD.

**Handover:** "طب الشكل الجديد إيه؟ السيد."

---

## الدور 5 · السيد المندوه (الـ to-be)

### Slide 5/20 · To-be: the new process (0:45)

**العضو:** السيد المندوه

**يقول:**
"الـ public satellite data والـ developer statements بيدخلوا الـ pipeline والـ quality gates كل ربع، ويطلع priority list بـ levels 1 لـ 4 وسبب مكتوب، والـ capacity أربعة. اللجنة تقرر: field visit أو watch next quarter، والنتيجة بتتسجّل في الـ visit log. الـ target المقترح: كل compound في level 1 أو 2 يتزار؛ والـ capacity 4 غطّت ده في 31 من 31 ربع. ISO 37122 و U4SSC مفيهومش indicator مطابق، فالـ targets على data الـ R7؛ و S3 بيختبر حمل فوق الـ capacity. ده proposal، مش approved من ACUD."

**على الـ dashboard:** على الـ slide بس؛ امشي بإيدك على الـ loop من الشمال لليمين وارجع من تحت للـ visit log. قول: "والـ visit form اللي ندى هتوريه live هو بالظبط الـ result recorded ده." لو اتسأل عن الأدوار: الـ Track A owner بيشغّل الـ pipeline كل ربع مع reviewer تاني، والـ field visit lead بيسجّل progressing أو stalled أو complete أو not done، والـ ACUD data custodian ماسك الـ code-to-name mapping (`docs/deliverables/to-be.md`).

**Handover:** "الـ lists دي جاية منين؟ أحمد بنى الـ data والـ rule."

---

## الدور 6 · أحمد عبد الحميد (الـ data)

### Slide 6/20 · Data (0:30)

**العضو:** أحمد عبد الحميد

**يقول:**
"كل رقم ليه لون: أخضر real، أزرق derived، برتقاني generated. 1,009 من 1,026 documented facts عدّوا independent review. الـ public sources بتدخل في prepared release واحد فيه 84 frozen inputs، والـ dashboard بيقرا منه بس: 12 compound، و 516 compound-quarters، و 57 statement. اللي عند ACUD بس، زي الـ finance والـ supervisor reports، عاملينه generated ومفصول لوحده."

**على الـ dashboard:** على الـ slide بس. لو اتسأل عن الألوان: الـ sidebar pill في Track A مكتوب عليه `🟢 REAL · 🔵 DERIVED`، وفي Track B `🟠 GENERATED`؛ ندى تقدر توريه في ثانية من Tab 1.

**Handover:** "طب الـ satellite بيشوف إيه من فوق؟ سلمى."

---

## الدور 7 · سلمى مجدي (الـ satellites)

### Slide 7/20 · Seeing construction from space (0:30)

**العضو:** سلمى مجدي

**تقول:**
"Dynamic World بيدينا كل ربع احتمال إن الـ compound بيتبني: ده الـ activity score A. Open Buildings بيدي الارتفاع كـ context بس. Wayback بيدي صور before و after بتاريخها. الربع بيتحسب لو فيه 6 صور على الأقل و boundary متراجعة. الـ satellites بتشوف البناء، مش التشطيب من جوه، عشان كده عمرنا ما بندي completion percentage."

**على الـ dashboard:** على الـ slide بس (فيه screenshot للـ Compound file). لو اتسأل "شايفين إيه بالظبط؟": Compound file ← **Satellite curves** (Activity score A و Dynamic World built probability) و **More evidence** ← **Wayback timeline**.

**Handover:** "ودي بتتحول لـ priority level إزاي؟ أحمد."

---

## الدور 8 · أحمد عبد الحميد (الـ Track A rule)

### Slide 8/20 · The Track A rule (0:45)

**العضو:** أحمد عبد الحميد

**يقول:**
"تلات clocks. K2: عدد الأرباع من غير activity بعد ما البناء بدأ. K3: الشهور من أول handover date اتعلن. K6: الشهور من launch أو promise من غير ما البناء يبدأ. أسوأ clock هو اللي بيحدد الـ level، من غير weights. Level 1 inspect now، و 2 this cycle، و 3 document review، و 4 routine. لو الـ compound ممكن يكون خلص، الـ level بيقف عند 3؛ الربع ده ده حصل مع C03 و C12 و C21. المرجع القانوني Decree 2184/2022: 12 شهر grace، و 24 شهر لحق الـ refund. K5، الـ months eligible for review، عمره ما بيحدد level."

**على الـ dashboard:** على الـ slide بس. لو اتسأل "فين الـ clocks دي؟": Compound file ← الـ tiles **K2 no activity** و **K3 handover clock** و **K6 never started** و **K5**، وتحتها caption "worst of K2, K3, K6".

**Handover:** "ده الـ rule على الورق. ندى هتورّيه شغال، live."

---

## الدور 9 · ندى شادي (الـ dashboard)

### Slide 9/20 · Live demo (Track A) (1:00)

**العضو:** ندى شادي

**Switch:** `Alt+Tab` ← Tab 1 (Priority map، Track A).

| Click | تعرض | تقول |
| --- | --- | --- |
| 1 | الـ headline والأربع tiles فوق | "ده اللي اللجنة بتفتحه كل ربع. الـ headline بيجاوب على السؤال على طول: دي زيارات الـ cycle ده، وليه أول واحد هو الأول." |
| 2 | كروت "This cycle's visits" (C18 و C07 و C14 و C03) | "أربع compounds من 12، كل واحد بالـ level بتاعه والسبب وآخر satellite capture بتاريخها." |
| 3 | جدول الـ visit list وزرار **Cycle list (CSV)** | "الـ list بتنزل بضغطة واحدة، والسبب مكتوب بالعربي للجنة." |
| 4 | الـ sidebar ← **2 · Compound file**، C18 | "ليه ده؟ C18 عدّى أول handover date اتعلن بـ 57 شهر، ومن التاريخ ده الـ clock بيعدّ." |
| 5 | انزلي لـ **Visit form**: code C18، النتيجة، **Save visit** | "بعد الزيارة النتيجة بتتسجّل هنا، بالـ code بس. كل visit بيتحفظ بيبني الـ ground truth اللي مش موجودة النهارده." |

**على الـ dashboard:** الجدول فوق هو الـ live. وإنتي بتتنقلي قولي: "كل ده real أو derived؛ مفيش ولا رقم generated على الـ map دي."

**Switch:** الـ sidebar ← **1 · Priority map** (نفضل في Tab 1).

**Handover:** "طب لو اللجنة عايزة توصل لـ compound معيّن على طول؟ السيد بنى الـ search والـ filters."

---

## الدور 10 · السيد المندوه (الـ search والـ filters والـ map click)

### Slide 10/20 · Search, filters and map click (0:30)

**العضو:** السيد المندوه

Live على Tab 1، جزء **Search and filters** فوق الـ map. ندى بتضغط، والسيد بيتكلم. لو الـ dashboard بطيء، slide 10 فيه نفس الشاشتين كـ screenshots.

| Click (ندى) | تعرض | يقول (السيد) |
| --- | --- | --- |
| 1 | اكتبي **C1** في **Search code** | "Search box واحد للـ compound أو developer code. نكتب C1 فيفضل 6 من الـ 12 على الـ map، والـ legend بيعرض العدد لكل level." |
| 2 | اختاري level من **Priority level** (مثلًا level 1) | "Filters: الربع، والـ level، والـ developer، و minimum K2 و K3 و K6. الـ rank بيفضل نفس ترتيب الزيارات." |
| 3 | اضغطي على block في الـ map، وبعدين الـ panel بتاع **Selected compound** | "نضغط على block، والـ sidebar يفتح الـ compound بالـ stored values والـ drill-downs." |
| 4 | اضغطي **Clear selection**، وفضّي الـ search box | "Codes بس، و Clear selection بيرجّع كل حاجة." |

**على الـ dashboard:** الجدول فوق هو الـ live (Tab 1).

**Handover:** "ندى هتجمع الأربع شاشات في طريق واحد."

---

## الدور 11 · ندى شادي (الأربع شاشات)

### Slide 11/20 · Four screens, one path from alert to action (0:30)

**العضو:** ندى شادي

**Switch:** `Alt+Tab` ← الـ slides.

**تقول:**
"أربع شاشات، أربع أسئلة: مين الأول؟ ليه ده؟ السيستم بيدي إيه وإمتى بيفشل؟ ومين هيتغير لو الظروف اتغيرت؟ والطريق من الـ level لحد الـ recorded visit. الشاشات للجنة، والـ visit form للـ field visit lead، وشاشة 4 generated. زمايل في الفريق راجعوها وعدّلنا؛ والـ supervisor عمل ten-second test من غير ما يتسجّل؛ والـ test المسجّل مع عضو لجنة لسه هيتعمل."

**على الـ dashboard:** على الـ slide بس؛ شاوري على الأربع شاشات بالترتيب.

**Handover:** "هل بيمسك المشاريع المتأخرة بدري؟ أحمد هيعرض الـ backtest، والـ clock متجمّد."

---

## الدور 12 · أحمد عبد الحميد (الـ backtest)

### Slide 12/20 · Backtest: 1 of 6 and why (1:15)

**العضو:** أحمد عبد الحميد

**يقول (على الـ slide):**
"هنبدأ باللي فاتنا. جمّدنا الـ clock وأعدنا تشغيل 6 حالات حقيقية public في R7. الـ target، 5 من 6، اتحدد قبل الحساب، ما نزّلناهوش، وما وصلناهوش: الـ rule عمل early alert في حالة واحدة من 6 بعد البداية، و 0 من 6 point-in-time. ومعندناش false-alarm rate على الحالات الحقيقية، لأن الست كلهم كانوا متأخرين. وبالـ central assumptions الـ missed case الواحد يساوي حوالي 6.7 false alarms؛ ده calculator على inputs مفترضة."

**على الـ dashboard:** `Alt+Tab` ← Tab 2 (District view، "An early signal: C21").

**يعرض ويقول:**

- جزء الـ early signal: "دي الحالة الوحيدة اللي مسكناها، C21: ربع الـ alert واللي الـ satellite شافه وقتها."
- ندى تنزل لـ **When the solution fails**: "في الخمس حالات اللي فاتونا، الصور كانت كفاية، لكن المواقع كانت شغالة، فمكانش فيه stall نكتشفه. الـ rule بيقيس الـ stalls والمواعيد اللي عدّت، مش السرعة مقارنة بالـ plan. وحتى C21 جت جزئيًا من توقيت النشر، فمش بنقول إنها هتتكرر."

**Switch:** `Alt+Tab` ← الـ slides.

**يقول:** "الأرقام دي مش بتثبت سبب كل تأخير؛ ده محتاج سجلات ACUD."

**Handover:** "لو معانا data زي بتاعة ACUD، model يقدر يعمل أحسن؟ فيرينا جربت ده على generated data."

---

## الدور 13 · فيرينا فؤاد (Track B: generated data)

### Slide 13/20 · Track B: generated data (0:45)

**العضو:** فيرينا فؤاد

**تقول:**
"كل حاجة على الـ slide دي Synthetic - for training only. سألنا: هل الـ compound هيبقى distressed في الست شهور الجاية؟ 96 training rows، و 48 test rows، فيهم 4 distressed test cases بس. الـ chart بيوضح كل method حط كام واحد من الـ 4 دول في الـ top 4 بتاعه. الـ public rule جاب 3؛ والـ boosting على الـ satellite data جاب 4، لكن ده معتمد جزئيًا على الارتفاع، ومن غيره بيبقى 1. والـ random list متوسطها 0.335. بـ 4 حالات بس مش هنقدر نفرّق بين الـ methods. ده diagnostic، مش real accuracy."

**على الـ dashboard:** على الـ slide بس (الـ chart native). لو اتسأل: Track B بيظهر الـ orange banner `Synthetic - for training only` على كل شاشة، والـ map بتختفي فيه.

**Handover:** "وإيه اللي يحصل لو عدد زيارات اللجنة اتغير؟ السيد، scenario واحد، live."

---

## الدور 14 · السيد المندوه (الـ what-if)

### Slide 14/20 · The observatory: one what-if scenario (0:30)

**العضو:** السيد المندوه

**Switch:** `Alt+Tab` ← Tab 3 (Track B، Digital twin what if، S3 · Capacity). شاور على الـ orange banner الأول؛ ندى بتضغط.

**على الـ dashboard:** Digital twin what if ← **S3 · Capacity** (2 أو 6 بدل 4).

**يقول:**
"الـ orange banner معناه generated. لو اللجنة عندها زيارتين في الـ cycle، أو 6، بدل 4؟ على كل الأرباع، 45 من 744 row بيتغير فيهم الـ list membership، والـ level عمره ما بيتغير. أما الـ dollar shock وانخفاض التحصيل، S1 و S2، فمش بيغيروا أي حاجة في الـ list. وده result، مش missing value."

**Handover:** "وهل اللجنة تقدر ببساطة تسأل المشروع سؤال؟ سلمى، live."

---

## الدور 15 · سلمى مجدي (الـ chatbot)

### Slide 15/20 · Ask the project: the chatbot (0:45)

**العضو:** سلمى مجدي

**Switch:** `Ctrl+4` ← Tab 4 (الـ chatbot)، أو زرار 💬 في الـ dashboard.

| Click (ندى) | تعرض | تقول (سلمى) |
| --- | --- | --- |
| 1 | اكتبي سؤال، مثلًا "latest KPI for C18"، وابعتيه | "السؤال بيروح لـ router فيه 10 intents، وبعدين لنوعين retrieval: facts من الـ v7 release، و search في الـ statements والـ complaints والـ knowledge documents." |
| 2 | الإجابة والـ sources اللي بتعرضها | "الإجابة جاية بالـ sources بتاعتها، وبتوضح إيه published وإيه derived وإيه generated. الـ AI model بيتستخدم بس لما يكون approved وجوه الـ call budget؛ غير كده الإجابة local." |
| 3 | اسألي follow-up قصير من غير code، مثلًا "and the reason?" | "الـ follow-up بيفتكر آخر compound code، والحاجات الـ generated زي الـ complaints بتفضل مكتوب عليها synthetic." |

**على الـ dashboard:** الجدول فوق هو الـ live. بعدها `Alt+Tab` ← الـ slides. لو الـ chatbot بطيء، اقفليه وقولي "دي نفس الشاشة" على الـ slide.

**Transition:** "طب الـ assistant ده يعرف إيه، وحدوده فين؟"

### Slide 16/20 · What the chatbot knows, and its limits (0:30)

**العضو:** سلمى مجدي

**تقول:**
"بيعرف 9 sourced documents: موقع ACUD، و Decree 2184/2022، و Building Law 119، و Law 151/2020، و Dynamic World، و Open Buildings، و Esri Wayback، و ISO 37120 و 37122، والـ SLA note، وكمان data المشروع. اختبرناه بنفسنا: 8 من 8 intent tests و 5 من 5 retrieval checks، دي tests صغيرة مش accuracy claim. الـ model calls بموافقة صاحب المشروع وبحد أقصى 200 call، وبعدها local. Codes بس، ومش legal advice."

**على الـ dashboard:** على الـ slide بس. لو اتسأل "الـ sources دي فين؟": `chatbot/knowledge/SOURCES.csv`، والسيد يقدر يسأل الـ chatbot سؤال قانوني live في الأسئلة.

**Handover:** "طب كل ده يساوي كام بالفلوس؟ فيرينا."

---

## الدور 16 · فيرينا فؤاد (الـ value)

### Slide 17/20 · Value in EGP (3 settings) (1:15)

**العضو:** فيرينا فؤاد

**تقول:**
"السياسة الحالية بتزور الـ 12 كلهم. زيارة 4 في كل cycle معناها 16 field visit في السنة بدل 48 (12 × 4)، وده الوحدة التانية جنب الـ EGP. تحت الـ assumptions بتاعتنا الـ value من 0.007 لـ 0.102 million EGP في السنة. تلات settings: الزيارة بتتكلف 2,000 أو 3,000 أو 4,000 EGP، فريق من 3 بمرتب مهندس منشور زائد المواصلات. الـ operating cost والـ missed cases هم public proxies؛ وتكلفة الحالة المتأخرة placeholder قيمته 20,000 EGP. حتى الـ conservative setting موجب لكن صغير، وده مش measured saving. لسه مش قادرين نقيس تكلفة الـ false alarm قصاد الـ missed case؛ بالـ data بتاعة ACUD ده يبقى حقيقي."

**على الـ dashboard:** على الـ slide بس. جاهزة للأسئلة: District view ← **A false alarm against a missed case**: أربع inputs من `configs/cost_assumptions.yaml`؛ بالـ central assumptions (3,000 EGP للزيارة، 20,000 EGP للـ missed case) الـ missed case الواحد يساوي حوالي 6.7 false alarms.

**Handover:** "الـ value جانب؛ لكن هل آمن نستخدمه؟ سلمى."

---

## الدور 17 · سلمى مجدي (الـ risks)

### Slide 18/20 · Risks and responsible use (1:00)

**العضو:** سلمى مجدي

**تقول:**
"سبع risks، و control واحد، ولأغلب الـ risks owner role مكتوب في governance.md. الـ level مش finding: هو بيقول مين نزوره الأول، عمره ما بيعني مخالفة أو عقوبة. الـ unknown بيفضل unknown. الـ generated data عمرها ما بتتخلط بالـ real. الـ small samples بنعرضها counts، مش نسب مئوية. نص الـ complaints بيتعمله masking، والنص الحقيقي محتاج review. Law 151/2020 محتاج مراجعة الـ data custodian عندكم. والـ handover documents: technical guide، و user guide، و knowledge-transfer pack، و method card، و final checklist. عملنا clean-room run من fresh clone: 451 test عدّوا؛ لكن محدش برّه الفريق بنى الـ system من الأول. والـ control اللي بالأحمر: اللجنة هي اللي بتقرر، وكل visit result بيتسجّل."

**على الـ dashboard:** على الـ slide بس. لو اتسأل "الـ committee decides فين على الشاشة؟": تحت الـ visit list مكتوب "Suggested actions are proposals; the committee decides."

**Handover:** "طب ده هيشتغل إزاي جوه ACUD؟ أحمد."

---

## الدور 18 · أحمد عبد الحميد (الـ production)

### Slide 19/20 · Launching in production (0:45)

**العضو:** أحمد عبد الحميد

**يقول:**
"تلات حاجات: الـ dashboard، و quarterly data run واحد، والـ prepared release. Proposed، مش deployed: server جوه شبكة ACUD، فالـ data تفضل عند ACUD والـ exports بالـ codes بس. كل ربع: refresh، ثم quality gates، ثم list، ثم visits، ثم recorded results. أي STOP بيوقف الـ release؛ والـ fallback هو الـ K1 check الأبسط والـ prior release. والـ controls: الـ thresholds والـ capacity بتتغير بقرار متراجع بس، والـ chatbot model calls بحد أقصى 200 call وبموافقة، وكل visit result بيتسجّل في ops_visits."

**على الـ dashboard:** على الـ slide بس. لو اتسأل "إزاي بتشغلوه؟": `start.ps1` على Windows (dashboard على 8501 و chatbot على 8001)، والـ quarterly run بأمر واحد.

**Handover:** "وإيه اللي بنطلبه منكم النهارده؟ ندى هتختم بالقرار."

---

## الدور 19 · ندى شادي (القرار)

### Slide 20/20 · Decision, transition and next step (1:00)

**العضو:** ندى شادي

**تقول (بالراحة؛ بصّي للجنة، مش للشاشة):**
"طلبنا قرار واحد: استخدام الـ inspection priority list لاختيار أنهي compounds في R7 اللجنة تزورها الأول في الـ cycle الجاي. السيستم بيرشّح، واللجنة هي اللي بتقرر. تلات phases. Pilot cycle: اللجنة بتقرر والـ Track A owner بيجهّز الـ list، والـ risk إن الحالات قليلة. بعدها ACUD data: الـ data custodian عندكم، والـ risk إن الـ access مايتوافقش. بعدها quarterly operation: الـ Track A owner بيشغّل ومعاه reviewer، والـ risk إن الـ activity score يفشل. الـ training والـ gate criteria والتواريخ والـ owners هنتفق عليها مع ACUD، وبنعدّ كل ربع كام visit result اتسجّل من 12. الـ reviews الحالية مستمرة، فالرجوع أقصاه rerun واحد. الـ thresholds والـ capacity configuration؛ district تاني يحتاج boundaries و statements، و R7 بس اللي اتشغّل، ومفيش transfer متثبت. ده اللي الـ public data لوحدها تقدر تعمله. ادونا الـ data بتاعتكم، والأجزاء الـ demo تبقى real operation. شكرًا، وتحت أمركم في أي أسئلة."

**على الـ dashboard:** على الـ slide بس، وتفضل على الشاشة طول الأسئلة. ارجعي بجملة لسؤال البداية: "أنهي compounds الأول، وليه؟ دي الإجابة."

**Handover:** "السيد هياخد أسئلة حضراتكم."

**نهاية الـ 14:30.** سيبوا slide 20 على الشاشة وقت الأسئلة.

---

## الأسئلة والإجابات (بعد الـ 14:30، حوالي 5:30 للأسئلة)

السيد بياخد كل سؤال ويحوّله لصاحبه في جملة واحدة ("أحمد هو اللي بناه، اتفضل يا أحمد")، ويقفل لو محتاج. كل واحد بيجاوب عن اللي بناه، وده نفس اللي قدّمه. الإجابة جملة أو جملتين، بالرقم، من [expected-questions.md](../expected-questions.md).

| نوع السؤال | يجاوب | يعرض لو مفيد |
| --- | --- | --- |
| الـ data، الـ rule، الـ levels، الـ backtest، الـ production، "ليه مش score" | أحمد | District view، Compound file |
| المشكلة، الـ as-is، الـ generated data، الـ model، الـ complaints classifier، الفلوس | فيرينا | Slides 2 و 4 و 13 و 17، District view |
| الشاشات، الصياغة، الـ visit form، الـ cycle list | ندى | Tab 1 |
| الـ satellites، الـ chatbot (إزاي بيشتغل، معرفته والـ budget)، الـ KPIs، الـ risks، القانون، الـ governance، الـ data request | سلمى | Slides 7 و 15 و 16 و 18، Tab 4 |
| الـ AI، الـ to-be، الـ search والـ filters، الـ what-if، القرار، "محتاجين مننا إيه" | السيد | Slides 3 و 5 و 10 و 14، Tab 3 |

**لحظة الـ chatbot (سلمى، حوالي 30 ثانية، لما ييجي سؤال عن الـ rules أو القانون؛ السيد يحوّلها السؤال):**
شاوري على slide 15، وبعدين افتحي زرار 💬 في الـ dashboard (الـ chatbot على port 8001) واكتبي سؤال اللجنة نفسه، مثلًا "What does level 1 mean for C18?" أو "What does Decree 2184/2022 say about the handover grace period?". وقولي: "ده الـ assistant اللي في slide 15. بيجاوب من الـ data بتاعة المشروع والـ sourced documents بتاعته، وبيوضح كل إجابة جاية منين. مش legal advice، وبيستخدم الـ AI model بس جوه الـ budget اللي صاحب المشروع وافق عليه." لو بطيء، اقفليه وجاوبي بنفسك.

إجابات جاهزة في سطر:

- "هل ده real saving؟" ← "لأ، من 0.007 لـ 0.102 million EGP في السنة تحت assumptions معلنة؛ الـ data بتاعتكم هي اللي هتخليه measurable."
- "ليه 1 من 6 بس؟" ← "الـ rule بيكتشف الـ stalls والمواعيد اللي عدّت؛ الخمسة اللي فاتونا كانوا لسه بيبنوا، لكن ببطء. وحددنا الـ target قبل الحساب وما نزّلناهوش."
- "انتوا بتقولوا على developers إنهم distressed؟" ← "لأ. بنقول 'no building activity for N quarters' أو 'passed its first date by N months'، واللجنة هي اللي بتقرر."
- "محتاجين مننا إيه؟" ← "Coded export، نبدأ بـ dated inspection and handover outcomes، والـ contract register، والـ parcel geometry؛ والـ identity mapping تفضل عند ACUD."
- "نبدأ إزاي من غير risk؟" ← "Pilot cycle واحد والـ reviews كل 3 شهور مستمرة؛ الرجوع أقصاه rerun واحد."
- "الـ chatbot دقيق قد إيه؟" ← "مش بنقول accuracy: الـ 8 من 8 intent tests والـ 5 من 5 retrieval checks دي tests صغيرة عملناها بنفسنا."
- "إيه اللي بيحصل النهارده وإيه اللي هيتغير؟" (as-is / to-be) ← "النهارده كل compound بنفس الـ field review كل 3 شهور، 48 في السنة في R7؛ ومع الـ list اللجنة تزور الـ levels الأعلى الأول وتسجّل كل نتيجة."
- "ليه دلوقتي؟" ← "Decree 2184/2022 art. 5 بيسري على المشروعات الجارية، وفي R7 ساعتين شغالين: C18 عدّى أول موعد اتعلن بـ 57 شهر، و C14 أجّل ميعاده مرتين."
- "كام مشتري متأثر؟" ← "مش معروف بالظبط: الخمس حالات العامة المتأخرة فيها 6,474 وحدة (مباعة وغير مباعة)، والتأخير محسوب من الوعد المنشور مش من تاريخ العقد."
- "false alarm بكام قصاد missed case؟" ← "بالـ central assumptions الـ missed case الواحد يساوي حوالي 6.7 false alarms؛ ومفيش false-alarm rate حقيقي لأن الست حالات كلهم كانوا متأخرين."
- "هل يشتغل في district تاني؟" ← "مش متثبت: R7 بس اللي اتشغّل؛ district تاني يحتاج coded boundaries و dated statements و satellite windows، وبعدين نفس الـ checks."

## إزاي العرض يوصل

- **نفتح بأرقامهم، ونقفل بقرارهم.** أول slides بتقتبس رئيس مجلس الإدارة؛ وآخر slide بيطلب قرار واحد اللجنة تقدر تاخده الـ cycle الجاي.
- **نبدأ باللي فاتنا.** لما نقول "1 من 6، والـ target اتحدد الأول" قبل ما حد يسأل، ده بيكسب ثقة أكتر من أي رقم حلو.
- **كل واحد بيتكلم عن شغله.** اللي بنى الجزء هو اللي بيقدّمه، فلو اللجنة سألت، الإجابة جاهزة عنده.
- **Show, then say.** في الأجزاء الـ live: اضغط الأول، استنى ثانية، وبعدين اتكلم عن اللي على الشاشة.
- **ماوس واحد، صوت واحد.** ندى بتضغط في كل الأجزاء الـ live؛ اللي بيتكلم عمره ما يمد إيده على اللابتوب.
- **نفس كلام الشاشة.** قول "Inspect now" و "months eligible for review" و "Synthetic - for training only" بالظبط زي ما الـ dashboard كاتبها.
- **الوقت.** اتمرّنوا مرتين بـ timer (T-ALL-05). لو الوقت زاد، اختصروا تفاصيل slide 7 وقائمة slide 18 لتلات risks؛ لكن عمرنا ما نشيل القرار في slide 20.

## لحظات الـ wow (اللي اللجنة هتفتكرها)

1. **أول 30 ثانية:** السيد يقول السؤال الواحد ("أنهي compounds الأول، وليه؟")، وندى تقفل بيه في آخر جملة من slide 20. نفس السؤال في الأول وفي الآخر بيخلي القصة مقفولة.
2. **أرقامهم مش أرقامنا (slide 2):** نبدأ بتصريحات رئيس مجلس الإدارة؛ اللجنة بتسمع مشكلتها هي.
3. **الـ headline live (slide 9):** أول ما Tab 1 يفتح، ندى تسكت ثانيتين وتسيب اللجنة تقرا "Visit C18, C07, C14, C03 this cycle". الشاشة بتجاوب قبل ما حد يتكلم.
4. **C1 ← 6 من 12 (slide 10):** كتابة حرفين بتغير الـ map قدامهم. بيورّي إن الأداة سريعة ومش مجرد صور.
5. **الصراحة في الـ backtest (slide 12):** "1 من 6، والـ target اتحدد قبل الحساب". اللجان بتثق في الفريق اللي بيقول اللي فشل فيه قبل ما حد يسأله.
6. **الـ chatbot بسؤالهم (Q&A):** سلمى تكتب سؤال اللجنة نفسه، مش سؤال متحضّر.
7. **القرار في جملة (slide 20):** طلب واحد، والرجوع أقصاه rerun واحد. سهل يقولوا "آه".

## إزاي نجاوب على الأسئلة (5 خطوات)

1. **اسمع للآخر** ومتقاطعش، حتى لو عارف الإجابة.
2. **كرر السؤال في جملة قصيرة** ("السؤال عن الـ false alarms") عشان الكل يسمعه وتكسب ثانيتين.
3. **السيد يحوّل** للي بنى الجزء: "أحمد هو اللي بناه، اتفضل يا أحمد."
4. **جاوب بالرقم ومصدره** في جملة أو جملتين، من [expected-questions.md](../expected-questions.md). لو مش عارف: "مش عندنا الرقم ده دلوقتي، ودي من الحاجات اللي محتاجة data ACUD"، ومتخمنش أبدًا.
5. **اقفل بسؤال**: "ده جاوب على سؤال حضرتك؟"، ولو الشاشة بتوضح أكتر، ندى تفتحها.

جمل ممنوعة: "risk level"، "distressed" عن compound حقيقي، "غرامة" عن K5، "accuracy" عن الـ generated data أو الـ chatbot، وأي اسم compound أو developer.

## Plan B

| لو حصل | نعمل إيه |
| --- | --- |
| الـ dashboard ما فتحش أو وقف | نفضل على الـ slide؛ slides 9 و 10 و 12 و 14 و 15 فيها نفس الشاشات. "دي نفس الشاشة" ونكمل. |
| الـ chatbot بطيء أو مردّش | نقفله في ثانيتين، ونكمل على slide 15؛ في الأسئلة سلمى تجاوب بنفسها. |
| الـ map ما ظهرتش | نكمل من الـ cycle cards والـ visit list؛ الـ map context بس. |
| الوقت زاد | نختصر تفاصيل slide 7 وقائمة slide 18 لتلات risks؛ القرار في slide 20 عمره ما يتشال. |
| سؤال مالوش إجابة | "مش عندنا الرقم ده، وده من اللي محتاج data ACUD." |
| حد نسي جملته | اللي جاي في الدور يقول الـ handover بتاعه ويكمل. |

## بروفة اليوم اللي قبله

- [ ] `git pull` و `start.ps1` على لابتوب العرض نفسه، والـ chatbot يتسأل مرة (الـ embedding model يتنزل).
- [ ] الأربع tabs متظبطين، و `Ctrl+1/2/3/4` شغالين.
- [ ] نسخة rehearsal من الـ app data للـ visit form.
- [ ] بروفتين كاملتين بـ timer (T-ALL-05) على 14:30، والـ checkpoints متسجلة.
- [ ] كل عضو يقول الـ handover بتاعه من غير ورق.
- [ ] كل عضو يجاوب على 3 أسئلة من [expected-questions.md](../expected-questions.md) في جزئه.
- [ ] PowerPoint في presenter view، والـ notes ظاهرة للمتكلم بس.
- [ ] الوقوف بنفس ترتيب الكلام، عشان التسليم يبقى خطوة واحدة.
