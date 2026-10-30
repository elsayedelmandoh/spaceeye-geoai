# Decision memo / مذكرة قرار

Task T-SA-05. Draft for review. All counts come from `data/BACKTEST_CURRENT.md`, `data/EW_REPORT_CURRENT.md`, `data/experiments/35_backtest_diagnosis/DIAGNOSIS.md` and `configs/cost_assumptions.yaml`. Codes only, no names.

## English

**Decision requested.** Use the inspection priority list to choose which R7 compounds the committee visits first next cycle. The system recommends; the committee decides.

**What the system does.** For 12 coded R7 compounds it assigns a priority level (1-4) from the worst of three signals: quarters with no building activity (K2), months since the first announced handover date (K3), and months since the first launch or promise with no confirmed start (K6). The cycle list holds at most 4 compounds from levels 1-3, each with a one-sentence reason.

**What we found on real data.** Six public R7 cases were checked with the clock frozen. The rule gave an early alert in 1 of 6 cases (after-start reading) and 0 of 6 (point-in-time reading). The success criterion of 5 cases was not achieved and was not lowered. The diagnosis shows imaging was sufficient in every case (at least 10 images per quarter). In the five missed cases the sites were seen as active, so the rule had no stall to detect; it measures stalls and passed dates, not pace against plan. These counts do not prove why each delay happened.

**What generated data shows.** Track B uses synthetic data only ("Synthetic - for training only"). The capacity-4 test holds 4 distressed rows, so statistical power is very low. Scores are diagnostic and show nothing about real-world accuracy.

**Value.** Under these assumptions, from -0.006 to 0.098 million EGP per year. Every cost input is an assumption, and the conservative setting is negative.

**Proposed next steps.** (1) Use the list as a prioritisation aid; the visit confirms. (2) Record every visit result to build real ground truth. (3) Request ACUD data: supervisor reports, contractual dates, field review records, escrow balances.

**Limits.** Satellites show whether building is happening, not interior finishing; no completion % is given. K3 relies on developer statements. No compound is called distressed.

## العربية

**القرار المطلوب.** استخدام قائمة أولوية التفتيش لاختيار كومباوندات R7 التي تزورها اللجنة أولاً في الدورة القادمة. النظام يوصي، واللجنة هي التي تقرر.

**ما يفعله النظام.** يحدد لكل من 12 كومباوند (بالأكواد) مستوى أولوية من 1 إلى 4 حسب أسوأ إشارة من ثلاث: عدد الأرباع دون نشاط بناء (K2)، وعدد الشهور منذ أول موعد تسليم معلن (K3)، وعدد الشهور منذ أول إطلاق أو وعد دون بداية مؤكدة (K6). تضم قائمة الدورة 4 كومباوندات على الأكثر من المستويات 1 إلى 3، ولكل منها جملة سبب واحدة.

**ما وجدناه في البيانات الحقيقية.** فُحصت ست حالات عامة في R7 بتجميد الساعة. أعطت القاعدة إنذاراً مبكراً في حالة واحدة من 6 (قراءة ما بعد البدء) وفي 0 من 6 (قراءة لحظية). لم يتحقق معيار النجاح (5 حالات) ولم يُخفَّض. أظهر التشخيص أن الصور كانت كافية في كل الحالات (10 صور على الأقل في الربع). وفي الحالات الخمس التي فاتت رُصدت المواقع كنشطة، فلم يكن أمام القاعدة توقف لتكتشفه؛ فهي تقيس التوقف والمواعيد الفائتة وليس السرعة مقارنة بالخطة. هذه الأعداد لا تثبت سبب كل تأخير.

**ما تُظهره البيانات المولّدة.** المسار B يعتمد على بيانات مولّدة فقط ("مولّد - للتدريب والعرض فقط"). يحتوي اختبار السعة 4 على 4 صفوف متعثرة فقط، فالقوة الإحصائية منخفضة جداً. الدرجات تشخيصية ولا تدل على دقة في الواقع.

**القيمة.** تحت هذه الافتراضات، من -0.006 إلى 0.098 مليون جنيه سنوياً. كل مدخلات التكلفة افتراضات، والإعداد المتحفظ سالب.

**الخطوات المقترحة.** (1) استخدام القائمة كأداة ترتيب أولويات، والزيارة هي التي تؤكد. (2) تسجيل نتيجة كل زيارة لبناء حقيقة ميدانية. (3) طلب بيانات ACUD: تقارير المشرف، والمواعيد التعاقدية، وسجلات المراجعة الميدانية، وأرصدة الضمان.

**الحدود.** الأقمار الصناعية ترى هل البناء جارٍ ولا ترى التشطيب الداخلي، ولذلك لا نذكر نسبة إنجاز. يعتمد K3 على تصريحات المطورين. لا نصف أي كومباوند بأنه متعثر.
