# Presentation transcript: مين يقول إيه، slide بعد slide

خطة الكلام للعرض أمام اللجنة في 12 دقيقة ([presentation.pptx](presentation.pptx)، 18 slides). كل عضو يقدّم الجزء اللي بناه بنفسه (الـ owners من [02-team-roles-and-tasks.md](../../requirements/02-team-roles-and-tasks.md))، عشان يقدر يدافع عنه في الأسئلة. الأوقات هي أوقات الـ speaker notes في الـ deck ومجموعها 12:00. الكلام بالعربي، والمصطلحات المهمة تفضل بالإنجليزي زي ما هي مكتوبة على الشاشة والـ slides. السرعة حوالي 130 كلمة في الدقيقة (0:30 ≈ 65 كلمة)؛ قولها بأسلوبك، لكن الأرقام تفضل بالظبط.

قواعد للكل: codes بس (C18، عمرنا ما نقول اسم)؛ نقول "priority level" وعمرنا ما نقول "risk level"؛ عمرنا ما نوصف compound حقيقي بإنه "distressed"؛ K5 هو "months eligible for review" ومش غرامة؛ أي حاجة من Track B هي "generated, Synthetic - for training only".

## Running order

| # | العضو | Slides | الوقت | Dashboard live |
| --- | --- | --- | --- | --- |
| 1 | السيد المندوه (lead) | 0 | 0:15 | - |
| 2 | سلمى مجدي | 1, 2 | 1:00 | - |
| 3 | أحمد عبد الحميد | 3, 4, 5 | 1:45 | - |
| 4 | ندى شادي | 6 | 1:00 | Priority map ← Compound file ← visit form |
| 5 | السيد المندوه | 6b | 0:45 | search و filter و map click |
| 6 | ندى شادي | 6c | 0:30 | - |
| 7 | أحمد عبد الحميد | 7 | 1:00 | District view (C21 early signal) |
| 8 | فيرينا فؤاد | 8, 8b | 1:15 | Digital twin what if (Track B, S3 capacity) |
| 9 | السيد المندوه | 8c | 0:45 | chatbot (💬) |
| 10 | سلمى مجدي | 8d, 9, 10 | 2:30 | - |
| 11 | أحمد عبد الحميد | 10b | 0:30 | - |
| 12 | سلمى مجدي | 11 | 0:45 | - |
| | **Total** | **18 slides** | **12:00** | |

لكل عضو (وبنى إيه): سلمى 4:15 (KPIs، value، governance، الـ presentation)، أحمد 3:15 (Track A، الـ backtest، الـ monitoring)، السيد 1:45 (الافتتاح، الـ search والـ filters والـ map click، الـ chatbot)، ندى 1:30 (الـ dashboard)، فيرينا 1:15 (Track B والـ what-if). المجموع 12:00.

## بطاقة كل عضو

كل واحد يحفظ الكارت بتاعه: الـ slides، اللي هيعرضه live، واللي يكون جاهز يفتحه لو اتسأل.

| العضو | Slides | الوقت | يعرض live على الـ dashboard | جاهز يفتحه في الأسئلة | يحضّر إيه |
| --- | --- | --- | --- | --- | --- |
| السيد المندوه | 0, 6b, 8c | 1:45 | **Search and filters** (C1 ← 6 من 12، level filter، map click، Clear selection)؛ الـ chatbot (سؤال + follow-up) | الـ chatbot بسؤال اللجنة نفسه | يتأكد إن الـ chatbot اتسأل مرة قبل العرض؛ يدير الأسئلة |
| سلمى مجدي | 1, 2, 8d, 9, 10, 11 | 4:15 | - | District view ← **A false alarm against a missed case** (1 missed case ≈ 6.7 false alarms بالـ central assumptions) | slide 11 بالحرف؛ أرقام الـ value الثلاثة |
| أحمد عبد الحميد | 3, 4, 5, 7, 10b | 3:15 | District view: **An early signal: C21** و **When the solution fails** | Compound file ← الـ KPI tiles (K2، K3، K6، K5) لأي compound | الـ backtest بالأرقام (1 من 6، 0 من 6، target 5) |
| ندى شادي | 6, 6c (والماوس في كل الـ live) | 1:30 | Priority map ← cycle cards ← CSV ← Compound file C18 ← Visit form | أي شاشة؛ هي اللي بتضغط | الأربع tabs متظبطين؛ نسخة rehearsal من الـ app data |
| فيرينا فؤاد | 8, 8b | 1:15 | Digital twin what if ← **S3 · Capacity** (2 أو 6 بدل 4) | tabs **S1 · Cost shock** و **S2 · Collections drop** ("Nobody crosses a threshold") | أرقام الـ recall@4 والـ baseline 0.335 |

## Timing checkpoints

العضو اللي عليه الدور الجاي ماسك الـ timer ويبص عليه عند كل checkpoint؛ لو متأخرين أكتر من 15 ثانية، المتكلم يختصر جملة.

| لما نوصل لآخر | الوقت المفروض |
| --- | --- |
| slide 2 (المشكلة والقرار) | 1:15 |
| slide 5 (الـ rule) | 3:00 |
| slide 6c (الـ dashboard) | 5:15 |
| slide 8c (الـ chatbot) | 8:15 |
| slide 10 (الـ risks) | 10:45 |
| slide 11 (القرار) | 12:00 |

## قبل ما نبدأ (بـ 10 دقايق)

- لابتوب واحد وشاشتين: PowerPoint في presenter view، و browser فيه الـ dashboard شغال (نشغّله بـ `start.ps1`؛ الـ dashboard على port 8501 والـ chatbot على 8001).
- أربع tabs في الـ browser، مفتوحين ومتظبطين قبلها (كل tab ليه session لوحده، فالـ track switch مش بيتنقل بينهم):
  1. Tab 1: **1 · Priority map**، Track A، في أول الصفحة، الـ search فاضي، مفيش filter، ومفيش compound متختار.
  2. Tab 2: **3 · District view**، عند "An early signal: C21".
  3. Tab 3: Track B، **4 · Digital twin what if**، على tab **S3 · Capacity**.
  4. Tab 4: الـ chatbot على http://127.0.0.1:8001/ (أو زرار 💬 في الـ dashboard). اسأل سؤال واحد قبل العرض عشان الـ embedding model يكون اتحمّل؛ أول سؤال بيبقى بطيء. على جهاز جديد أول تشغيل بينزّل الـ embedding model (intfloat/multilingual-e5-small)، فشغّله قبلها بيوم على نت كويس.
- التنقل: `Alt+Tab` من الـ slides للـ browser، و `Ctrl+1/2/3/4` للـ tab، و `Alt+Tab` للرجوع. اتمرّنوا عليه؛ لازم ياخد أقل من ثانيتين.
- الـ visit form: استخدموا نسخة rehearsal من فولدر الـ app data، لأن أي visit بيتحفظ بيبقى row حقيقي في ملف الـ visits.
- Backup: لو الـ dashboard أو الـ chatbot ما فتحش، اقف على الـ slide؛ slides 6 و 6b و 7 و 8b و 8c فيهم نفس الشاشات كـ screenshots. قول "دي نفس الشاشة" وكمّل. عمرنا ما نعمل debug قدام اللجنة.
- شخص واحد (ندى) ماسك الماوس في كل الأجزاء الـ live؛ اللي بيتكلم بيتكلم، وندى بتدوس على الإشارة (للسيد في slides 6b و 8c، ولأحمد في slide 7، ولفيرينا في slide 8b).

## إزاي نسلّم لبعض (handover)

كل handover جملة واحدة: اسم اللي جاي والسؤال اللي هيجاوب عليه، والمتكلم الجديد يبدأ بالإجابة على طول، مش بـ "شكرًا". اللي خلّص يرجع خطوة، واللي جاي يكون واقف جنب الشاشة قبل ما الجملة تخلص. في slides 6 و 6b و 6c ندى فاضلة على الماوس، فالـ handover بين ندى والسيد من غير ما حد يتحرك من مكانه.

---

## 1. السيد المندوه (team lead، الـ AI component)

### Slide 0 · SpaceEye GeoAI (0:15)

**يقول:**
"صباح الخير. إحنا SpaceEye GeoAI: New Capital Radar، رادار لشركة بتمتلك مدينة. شكرًا لـ د. نديم عبدين على الإشراف. النهارده هنجاوب على سؤال واحد: أنهي compounds اللجنة تزورها الأول، وليه."

**على الـ dashboard:** على الـ slide بس. ابدأ والـ slide بالـ logos على الشاشة، وابص للجنة مش للشاشة.

**Handover:** "سلمى هتبدأ بالمشكلة، بأرقام رئيس مجلس الإدارة نفسه."

---

## 2. سلمى مجدي (المشكلة وصياغة القرار)

### Slide 1 · Problem in numbers (0:30)

**تقول:**
"دي أرقام رئيس مجلس الإدارة، مش أرقامنا: أكتر من 400 developer، وأكتر من 500 project، و field review كل 3 شهور، وحوالي 7 لـ 8% متأخرين تأخير كبير، و 6 mutual terminations. اللجنة مش هتقدر تزور كل حاجة في كل cycle. يبقى السؤال: أنهي compounds الأول؟ وإجابتنا: cycle list قصيرة، ومع كل compound سبب واضح."

**على الـ dashboard:** على الـ slide بس؛ شاوري على الـ stat callouts وإنتي بتقولي كل رقم. لو اتسأل "الأرقام دي منين؟": تصريحات رئيس مجلس الإدارة، مسجلة في `docs/requirements/01-specs.md` section 12.

### Slide 2 · The question and the decision (0:30)

**تقول:**
"منطقة واحدة، R7: 12 compound بـ codes، والربع 2026Q3. النهارده كل compound بياخد نفس الـ review كل 3 شهور. بكرة: list فيها 4 بالكتير في كل cycle، وكل واحد معاه reason sentence، ومن غير أي label على developer. الـ observatory بيرتّب، واللجنة هي اللي بتقرر. ACUD ما شاركتش أوقات الزيارات، فتكلفة النهارده مش متقاسة."

**على الـ dashboard:** على الـ slide بس؛ شاوري على الـ funnel (12 ← 4). الـ dashboard هيوريها live مع ندى بعد دقيقتين، فقولي: "وهتشوفوها live حالًا."

**Handover:** "الـ lists دي جاية منين؟ أحمد بنى الـ data والـ rule."

---

## 3. أحمد عبد الحميد (Track A: satellites و rule)

### Slide 3 · Data (0:30)

**يقول:**
"كل رقم ليه لون: أخضر real، أزرق derived، برتقاني generated. 1,009 من 1,026 documented facts عدّوا independent review. الـ public sources بتدخل في prepared release واحد فيه 84 frozen inputs، والـ dashboard بيقرا منه بس: 12 compound، و 516 compound-quarters، و 57 statement. اللي عند ACUD بس، زي الـ finance والـ supervisor reports، عاملينه generated ومفصول لوحده."

**على الـ dashboard:** على الـ slide بس. لو اتسأل عن الألوان: الـ sidebar pill في Track A مكتوب عليه `🟢 REAL · 🔵 DERIVED`، وفي Track B `🟠 GENERATED`؛ ندى تقدر توريه في ثانية من Tab 1.

### Slide 4 · Seeing construction from space (0:30)

**يقول:**
"Dynamic World بيدينا كل ربع احتمال إن الـ compound بيتبني: ده الـ activity score A. Open Buildings بيدي الارتفاع كـ context بس. Wayback بيدي صور before و after بتاريخها. الربع بيتحسب لو فيه 6 صور على الأقل و boundary متراجعة. الـ satellites بتشوف البناء، مش التشطيب من جوه، عشان كده عمرنا ما بندي completion percentage."

**على الـ dashboard:** على الـ slide بس (فيه screenshot للـ Compound file). لو اتسأل "شايفين إيه بالظبط؟": Compound file ← **Satellite curves** (Activity score A و Dynamic World built probability) و **More evidence** ← **Wayback timeline**.

### Slide 5 · The Track A rule (0:45)

**يقول:**
"تلات clocks. K2: عدد الأرباع من غير activity بعد ما البناء بدأ. K3: الشهور من أول handover date اتعلن. K6: الشهور من launch أو promise من غير ما البناء يبدأ. أسوأ clock هو اللي بيحدد الـ level، من غير weights. Level 1 inspect now، و 2 this cycle، و 3 document review، و 4 routine. لو الـ compound ممكن يكون خلص، الـ level بيقف عند 3؛ الربع ده ده حصل مع C03 و C12 و C21. المرجع القانوني Decree 2184/2022: 12 شهر grace، و 24 شهر لحق الـ refund. K5، الـ months eligible for review، عمره ما بيحدد level."

**على الـ dashboard:** على الـ slide بس. لو اتسأل "فين الـ clocks دي؟": Compound file ← الـ tiles **K2 no activity** و **K3 handover clock** و **K6 never started** و **K5**، وتحتها caption "worst of K2, K3, K6".

**Handover:** "ده الـ rule على الورق. ندى هتورّيه شغال، live."

---

## 4. ندى شادي (الـ dashboard)

### Slide 6 · Live demo, Track A (1:00)

**Switch:** `Alt+Tab` ← Tab 1 (Priority map، Track A).

| Click | تعرض | تقول |
| --- | --- | --- |
| 1 | الـ headline والأربع tiles فوق | "ده اللي اللجنة بتفتحه كل ربع. الـ headline بيجاوب على السؤال على طول: دي زيارات الـ cycle ده، وليه أول واحد هو الأول." |
| 2 | كروت "This cycle's visits" (C18 و C07 و C14 و C03) | "أربع compounds من 12، كل واحد بالـ level بتاعه والسبب وآخر satellite capture بتاريخها." |
| 3 | جدول الـ visit list وزرار **Cycle list (CSV)** | "الـ list بتنزل بضغطة واحدة، والسبب مكتوب بالعربي للجنة." |
| 4 | الـ sidebar ← **2 · Compound file**، C18 | "ليه ده؟ C18 عدّى أول handover date اتعلن بـ 57 شهر، ومن التاريخ ده الـ clock بيعدّ." |
| 5 | انزلي لـ **Visit form**: code C18، النتيجة، **Save visit** | "بعد الزيارة النتيجة بتتسجّل هنا، بالـ code بس. كل visit بيتحفظ بيبني الـ ground truth اللي مش موجودة النهارده." |

**تقول وهي بتتنقل:** "كل ده real أو derived؛ مفيش ولا رقم generated على الـ map دي."

**Switch:** الـ sidebar ← **1 · Priority map** (نفضل في Tab 1).

**Handover:** "طب لو اللجنة عايزة توصل لـ compound معيّن على طول؟ السيد بنى الـ search والـ filters."

---

## 5. السيد المندوه (الـ search والـ filters والـ map click)

### Slide 6b · Search, filters and map click (0:45)

Live على Tab 1، جزء **Search and filters** فوق الـ map. ندى بتضغط، والسيد بيتكلم. لو الـ dashboard بطيء، slide 6b فيه نفس الشاشتين كـ screenshots.

| Click (ندى) | تعرض | يقول (السيد) |
| --- | --- | --- |
| 1 | اكتبي **C1** في **Search code** | "Search box واحد بياخد compound code أو developer code، وأول الحروف كفاية. لما نكتب C1 بيفضل 6 من الـ 12 compound على الـ map، والـ legend بيعرض العدد لكل level." |
| 2 | اختاري level من **Priority level** (مثلًا level 1) | "الـ filters: الربع، والـ level، والـ developer، و minimum K2 و K3 و K6، أو الـ cycle list بس. الـ rank بيفضل نفس ترتيب زيارات الربع." |
| 3 | اضغطي على block في الـ map | "اضغط على block، والـ sidebar يفتح الـ compound ده بالـ stored values والـ drill-downs بتاعته." |
| 4 | الـ panel بتاع **Selected compound** في الـ sidebar | "Codes بس، من غير أسماء. وزرار واحد بيفتح الـ compound file بتاعه." |
| 5 | اضغطي **Clear selection**، وفضّي الـ search box | "و Clear selection بيرجّع كل حاجة." |

**Handover:** "ندى هتجمع الأربع شاشات في طريق واحد."

---

## 6. ندى شادي (الأربع شاشات)

### Slide 6c · Four screens, one path from alert to action (0:30)

**Switch:** `Alt+Tab` ← الـ slides.

**تقول (على الـ slide):**
"أربع شاشات، أربع أسئلة: مين الأول؟ ليه ده؟ السيستم بيدي إيه، وإمتى بيفشل؟ والأخيرة generated: مين هيتغير لو التكاليف أو التحصيل أو الـ capacity اتغيرت؟ والطريق: level، ثم cycle list، ثم compound file، ثم visit form، ثم recorded visit. الـ reviews بتاعة زمايلنا غيّرت الشاشات؛ والـ ten-second test مع عضو من اللجنة لسه هيتعمل."

**Handover:** "هل بيمسك المشاريع المتأخرة بدري؟ أحمد هيعرض الـ backtest، والـ clock متجمّد."

---

## 7. أحمد عبد الحميد (الـ backtest)

### Slide 7 · Backtest: 1 of 6 and why (1:00)

**يقول (على الـ slide):**
"هنبدأ باللي فاتنا. جمّدنا الـ clock وأعدنا تشغيل 6 حالات حقيقية public في R7. الـ target، 5 من 6، اتحدد قبل الحساب، ما نزّلناهوش، وما وصلناهوش: الـ rule عمل early alert في حالة واحدة من 6."

**Switch:** `Alt+Tab` ← Tab 2 (District view، "An early signal: C21").

**يعرض ويقول:**

- جزء الـ early signal: "دي الحالة الوحيدة اللي مسكناها، C21: ربع الـ alert واللي الـ satellite شافه وقتها."
- ندى تنزل لـ **When the solution fails**: "في الخمس حالات اللي فاتونا، الصور كانت كفاية، لكن المواقع كانت شغالة، فمكانش فيه stall نكتشفه. الـ rule بيقيس الـ stalls والمواعيد اللي عدّت، مش السرعة مقارنة بالـ plan. وحتى C21 جت جزئيًا من توقيت النشر، فمش بنقول إنها هتتكرر."

**Switch:** `Alt+Tab` ← الـ slides.

**يقول:** "الأرقام دي مش بتثبت سبب كل تأخير؛ ده محتاج سجلات ACUD."

**Handover:** "لو معانا data زي بتاعة ACUD، model يقدر يعمل أحسن؟ فيرينا جربت ده على generated data."

---

## 8. فيرينا فؤاد (Track B: generated data و what-if)

### Slide 8 · Track B: generated data (0:45)

**تقول:**
"كل حاجة على الـ slide دي Synthetic - for training only. سألنا: هل الـ compound هيبقى distressed في الست شهور الجاية؟ 96 training rows، و 48 test rows، فيهم 4 distressed test cases بس. الـ chart بيوضح كل method حط كام واحد من الـ 4 دول في الـ top 4 بتاعه. الـ public rule جاب 3؛ والـ boosting على الـ satellite data جاب 4، لكن ده معتمد جزئيًا على الارتفاع، ومن غيره بيبقى 1. والـ random list متوسطها 0.335. بـ 4 حالات بس مش هنقدر نفرّق بين الـ methods. ده diagnostic، مش real accuracy."

**على الـ dashboard:** على الـ slide بس (الـ chart native). لو اتسأل: Track B بيظهر الـ orange banner `Synthetic - for training only` على كل شاشة، والـ map بتختفي فيه.

**تقول وهي بتتنقل:** "وإيه اللي يحصل لو عدد زيارات اللجنة اتغير؟ scenario واحد، live."

### Slide 8b · The observatory: one what-if scenario (0:30)

**Switch:** `Alt+Tab` ← Tab 3 (Track B، Digital twin what if، S3 · Capacity). شاوري على الـ orange banner الأول.

**تعرض وتقول:**
"الـ orange banner معناه generated. لو اللجنة عندها زيارتين في الـ cycle، أو 6، بدل 4؟ على كل الأرباع، 45 من 744 row بيتغير فيهم الـ list membership، والـ level عمره ما بيتغير. أما الـ dollar shock وانخفاض التحصيل، S1 و S2، فمش بيغيروا أي حاجة في الـ list. وده result، مش missing value."

**Handover:** "وهل اللجنة تقدر ببساطة تسأل المشروع سؤال؟ السيد، live."

---

## 9. السيد المندوه (الـ chatbot)

### Slide 8c · Ask the project: the chatbot (0:45)

**Switch:** `Ctrl+4` ← Tab 4 (الـ chatbot)، أو زرار 💬 في الـ dashboard.

| Click (ندى) | تعرض | يقول (السيد) |
| --- | --- | --- |
| 1 | اكتبي سؤال، مثلًا "latest KPI for C18"، وابعتيه | "السؤال بيروح لـ router فيه 10 intents، وبعدين لنوعين retrieval: facts من الـ v7 release، و search في الـ statements والـ complaints والـ knowledge documents." |
| 2 | الإجابة والـ sources اللي بتعرضها | "الإجابة جاية بالـ sources بتاعتها، وبتوضح إيه published وإيه derived وإيه generated. الـ AI model بيتستخدم بس لما يكون approved وجوه الـ call budget؛ غير كده الإجابة local." |
| 3 | اسألي follow-up قصير من غير code، مثلًا "and the reason?" | "الـ follow-up بيفتكر آخر compound code، والحاجات الـ generated زي الـ complaints بتفضل مكتوب عليها synthetic." |

**Switch:** `Alt+Tab` ← الـ slides. لو الـ chatbot بطيء، اقفله وقول "دي نفس الشاشة" على الـ slide.

**Handover:** "الـ assistant ده يعرف إيه، وحدوده فين؟ سلمى."

---

## 10. سلمى مجدي (حدود الـ chatbot، والـ value، والـ risks)

### Slide 8d · What the chatbot knows, and its limits (0:45)

**تقول:**
"بيعرف 9 sourced documents: موقع ACUD، و Decree 2184/2022، و Building Law 119، و Law 151/2020، و Dynamic World، و Open Buildings، و Esri Wayback، و ISO 37120 و 37122، و الـ SLA note بتاعتنا، وكمان الـ data بتاعة المشروع. اختبرناه بنفسنا: 8 من 8 intent tests، و 5 من 5 retrieval checks نجحوا. دي tests صغيرة، مش accuracy claim. الـ model calls محتاجة موافقة صاحب المشروع، وبحد أقصى 200 call، وبعدها الإجابات local. Codes بس، ومش legal advice."

**على الـ dashboard:** على الـ slide بس. لو اتسأل "الـ sources دي فين؟": `chatbot/knowledge/SOURCES.csv`، والسيد يقدر يسأل الـ chatbot سؤال قانوني live في الأسئلة.

**تقول وهي بتتنقل:** "طب كل ده يساوي كام بالفلوس؟"

### Slide 9 · Value in EGP, 3 settings (1:00)

**تقول:**
"السياسة الحالية بتزور الـ 12 كلهم. زيارة 4 في كل cycle معناها 16 visit في السنة. تحت الـ assumptions بتاعتنا الـ value من 0.007 لـ 0.102 million EGP في السنة. تلات settings: الزيارة بتتكلف 2,000 أو 3,000 أو 4,000 EGP، فريق من 3 بمرتب مهندس منشور زائد المواصلات. الـ operating cost والـ missed cases هم public proxies؛ وتكلفة الحالة المتأخرة placeholder قيمته 20,000 EGP. حتى الـ conservative setting موجب لكن صغير، وده مش measured saving. لسه مش قادرين نقيس تكلفة الـ false alarm قصاد الـ missed case؛ بالـ data بتاعة ACUD ده يبقى حقيقي."

**على الـ dashboard:** على الـ slide بس. جاهزة للأسئلة: District view ← **A false alarm against a missed case**: أربع inputs من `configs/cost_assumptions.yaml`؛ بالـ central assumptions (3,000 EGP للزيارة، 20,000 EGP للـ missed case) الـ missed case الواحد يساوي حوالي 6.7 false alarms.

**تقول وهي بتتنقل:** "الـ value جانب؛ لكن هل آمن نستخدمه؟"

### Slide 10 · Risks and responsible use (0:45)

**تقول:**
"سبع risks، و control واحد. الـ level مش finding: هو بيقول مين نزوره الأول، عمره ما بيعني مخالفة أو عقوبة. الـ unknown بيفضل unknown. الـ generated data عمرها ما بتتخلط بالـ real data. الـ small samples بنعرضها كـ counts، عمرها ما تبقى نسب مئوية. نص الـ complaints بيتعمله masking، والنص الحقيقي محتاج review زيادة. Law 151/2020 محتاج مراجعة الـ data custodian عندكم. والـ handover pack موجود في الـ repository. والـ control اللي بالأحمر: اللجنة هي اللي بتقرر، وكل visit result بيتسجّل."

**على الـ dashboard:** على الـ slide بس. لو اتسأل "الـ committee decides فين على الشاشة؟": تحت الـ visit list مكتوب "Suggested actions are proposals; the committee decides."

**Handover:** "طب ده هيشتغل إزاي جوه ACUD؟ أحمد."

---

## 11. أحمد عبد الحميد (الـ production)

### Slide 10b · Launching in production (0:30)

**يقول:**
"تلات حاجات: الـ dashboard، و quarterly data run واحد، والـ prepared release. Proposed، مش deployed: server جوه شبكة ACUD، فالـ data تفضل عند ACUD والـ exports بالـ codes بس. كل ربع: refresh، ثم quality gates، ثم list، ثم visits، ثم recorded results. أي STOP بيوقف الـ release؛ والـ fallback هو الـ K1 check الأبسط والـ prior release."

**على الـ dashboard:** على الـ slide بس. لو اتسأل "إزاي بتشغلوه؟": `start.ps1` على Windows (dashboard على 8501 و chatbot على 8001)، والـ quarterly run بأمر واحد.

**Handover:** "وإيه اللي بنطلبه منكم النهارده؟ سلمى هتختم بالقرار."

---

## 12. سلمى مجدي (القرار)

### Slide 11 · Decision, transition and next step (0:45)

**تقول (بالراحة؛ بصّي للجنة، مش للشاشة):**
"طلبنا قرار واحد: استخدام الـ inspection priority list لاختيار أنهي compounds في R7 اللجنة تزورها الأول في الـ cycle الجاي. السيستم بيرشّح، واللجنة هي اللي بتقرر. تلات phases: pilot cycle واحد والـ reviews الحالية مستمرة، فالرجوع مش بيكلف حاجة؛ وبعدها verified sample صغير من data ACUD؛ وبعدها quarterly operation. ده اللي الـ public data لوحدها تقدر تعمله. ادونا الـ data بتاعتكم، والأجزاء الـ demo تبقى real operation. شكرًا، وتحت أمركم في أي أسئلة."

**على الـ dashboard:** على الـ slide بس، وتفضل على الشاشة طول الأسئلة. ارجعي بجملة لسؤال البداية: "أنهي compounds الأول، وليه؟ دي الإجابة."

**نهاية الـ 12:00.** سيبوا slide 11 على الشاشة وقت الأسئلة.

---

## الأسئلة والإجابات (بعد الـ 12 دقيقة)

السيد بياخد كل سؤال ويحوّله لصاحبه في جملة واحدة ("أحمد هو اللي بناه، اتفضل يا أحمد")، ويقفل لو محتاج. كل واحد بيجاوب عن اللي بناه، وده نفس اللي قدّمه. الإجابة جملة أو جملتين، بالرقم، من [expected-questions.md](../expected-questions.md).

| نوع السؤال | يجاوب | يعرض لو مفيد |
| --- | --- | --- |
| الـ data، الـ satellites، الـ rule، الـ levels، الـ backtest، الـ production، "ليه مش score" | أحمد | District view، Compound file |
| الـ generated data، الـ model، الـ what-if، الـ complaints classifier | فيرينا | Tab 3 (what-if) |
| الشاشات، الصياغة، الـ visit form، الـ cycle list | ندى | Tab 1 |
| الفلوس، الـ KPIs، الـ risks، القانون، الـ governance، الـ data request، معرفة الـ chatbot والـ budget | سلمى | Slides 8d و 9 و 10 |
| الـ AI، الـ search والـ filters، الـ chatbot بيشتغل إزاي، "محتاجين مننا إيه" | السيد | Slides 6b و 8c، Tab 4 |

**لحظة الـ chatbot (السيد، حوالي 30 ثانية، لما ييجي سؤال عن الـ rules أو القانون):**
شاور على slide 8c، وبعدين افتح زرار 💬 في الـ dashboard (الـ chatbot على port 8001) واكتب سؤال اللجنة نفسه، مثلًا "What does level 1 mean for C18?" أو "What does Decree 2184/2022 say about the handover grace period?". وقول: "ده الـ assistant اللي في slide 8c. بيجاوب من الـ data بتاعة المشروع والـ sourced documents بتاعته، وبيوضح كل إجابة جاية منين. مش legal advice، وبيستخدم الـ AI model بس جوه الـ budget اللي صاحب المشروع وافق عليه." لو بطيء، اقفله وجاوب بنفسك.

إجابات جاهزة في سطر:

- "هل ده real saving؟" ← "لأ، من 0.007 لـ 0.102 million EGP في السنة تحت assumptions معلنة؛ الـ data بتاعتكم هي اللي هتخليه measurable."
- "ليه 1 من 6 بس؟" ← "الـ rule بيكتشف الـ stalls والمواعيد اللي عدّت؛ الخمسة اللي فاتونا كانوا لسه بيبنوا، لكن ببطء. وحددنا الـ target قبل الحساب وما نزّلناهوش."
- "انتوا بتقولوا على developers إنهم distressed؟" ← "لأ. بنقول 'no building activity for N quarters' أو 'passed its first date by N months'، واللجنة هي اللي بتقرر."
- "محتاجين مننا إيه؟" ← "Coded export، نبدأ بـ dated inspection and handover outcomes، والـ contract register، والـ parcel geometry؛ والـ identity mapping تفضل عند ACUD."
- "نبدأ إزاي من غير risk؟" ← "Pilot cycle واحد والـ reviews كل 3 شهور مستمرة؛ الرجوع أقصاه rerun واحد."
- "الـ chatbot دقيق قد إيه؟" ← "مش بنقول accuracy: الـ 8 من 8 intent tests والـ 5 من 5 retrieval checks دي tests صغيرة عملناها بنفسنا."

## إزاي العرض يوصل

- **نفتح بأرقامهم، ونقفل بقرارهم.** أول slide بيقتبس رئيس مجلس الإدارة؛ وآخر slide بيطلب قرار واحد اللجنة تقدر تاخده الـ cycle الجاي.
- **نبدأ باللي فاتنا.** لما نقول "1 من 6، والـ target اتحدد الأول" قبل ما حد يسأل، ده بيكسب ثقة أكتر من أي رقم حلو.
- **كل واحد بيتكلم عن شغله.** اللي بنى الجزء هو اللي بيقدّمه، فلو اللجنة سألت، الإجابة جاهزة عنده.
- **Show, then say.** في الأجزاء الـ live: اضغط الأول، استنى ثانية، وبعدين اتكلم عن اللي على الشاشة.
- **ماوس واحد، صوت واحد.** ندى بتضغط في كل الأجزاء الـ live؛ اللي بيتكلم عمره ما يمد إيده على اللابتوب.
- **نفس كلام الشاشة.** قول "Inspect now" و "months eligible for review" و "Synthetic - for training only" بالظبط زي ما الـ dashboard كاتبها.
- **الوقت.** اتمرّنوا مرتين بـ timer (T-ALL-05). لو الوقت زاد، اختصروا تفاصيل slide 4 وقائمة slide 10 لتلات risks؛ لكن عمرنا ما نشيل القرار في slide 11.

## لحظات الـ wow (اللي اللجنة هتفتكرها)

1. **أول 15 ثانية:** السيد يقول السؤال الواحد ("أنهي compounds الأول، وليه؟")، وسلمى تقفل بيه في آخر جملة. نفس السؤال في الأول وفي الآخر بيخلي القصة مقفولة.
2. **أرقامهم مش أرقامنا (slide 1):** نبدأ بتصريحات رئيس مجلس الإدارة؛ اللجنة بتسمع مشكلتها هي.
3. **الـ headline live (slide 6):** أول ما Tab 1 يفتح، ندى تسكت ثانيتين وتسيب اللجنة تقرا "Visit C18, C07, C14, C03 this cycle". الشاشة بتجاوب قبل ما حد يتكلم.
4. **C1 ← 6 من 12 (slide 6b):** كتابة حرفين بتغير الـ map قدامهم. بيورّي إن الأداة سريعة ومش مجرد صور.
5. **الصراحة في الـ backtest (slide 7):** "1 من 6، والـ target اتحدد قبل الحساب". اللجان بتثق في الفريق اللي بيقول اللي فشل فيه قبل ما حد يسأله.
6. **الـ chatbot بسؤالهم (Q&A):** السيد يكتب سؤال اللجنة نفسه، مش سؤال متحضّر.
7. **القرار في جملة (slide 11):** طلب واحد، والرجوع مش بيكلف حاجة. سهل يقولوا "آه".

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
| الـ dashboard ما فتحش أو وقف | نفضل على الـ slide؛ slides 6 و 6b و 7 و 8b و 8c فيها نفس الشاشات. "دي نفس الشاشة" ونكمل. |
| الـ chatbot بطيء أو مردّش | نقفله في ثانيتين، ونكمل على slide 8c؛ في الأسئلة السيد يجاوب بنفسه. |
| الـ map ما ظهرتش | نكمل من الـ cycle cards والـ visit list؛ الـ map context بس. |
| الوقت زاد | نختصر تفاصيل slide 4 وقائمة slide 10 لتلات risks؛ القرار في slide 11 عمره ما يتشال. |
| سؤال مالوش إجابة | "مش عندنا الرقم ده، وده من اللي محتاج data ACUD." |
| حد نسي جملته | اللي جاي في الدور يقول الـ handover بتاعه ويكمل. |

## بروفة اليوم اللي قبله

- [ ] `git pull` و `start.ps1` على لابتوب العرض نفسه، والـ chatbot يتسأل مرة (الـ embedding model يتنزل).
- [ ] الأربع tabs متظبطين، و `Ctrl+1/2/3/4` شغالين.
- [ ] نسخة rehearsal من الـ app data للـ visit form.
- [ ] بروفتين كاملتين بـ timer (T-ALL-05)، والـ checkpoints متسجلة.
- [ ] كل عضو يقول الـ handover بتاعه من غير ورق.
- [ ] كل عضو يجاوب على 3 أسئلة من [expected-questions.md](../expected-questions.md) في جزئه.
- [ ] PowerPoint في presenter view، والـ notes ظاهرة للمتكلم بس.
- [ ] الوقوف بنفس ترتيب الكلام، عشان التسليم يبقى خطوة واحدة.
