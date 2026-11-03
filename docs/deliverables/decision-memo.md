# Decision memo / مذكرة قرار

Task T-SA-05. Draft for review. All counts come from `data/BACKTEST_CURRENT.md`, `data/EW_REPORT_CURRENT.md`, `data/experiments/35_backtest_diagnosis/DIAGNOSIS.md` and `configs/cost_assumptions.yaml`. Codes only, no names.

## English

**Decision requested.** Use the inspection priority list to choose which R7 compounds the committee visits first next cycle. The system recommends; the committee decides.

**What the system does.** For 12 coded R7 compounds it assigns a priority level (1-4) from the worst of three signals: quarters with no building activity (K2), months since the first announced handover date (K3), and months since the first launch or promise with no confirmed start (K6). If a handover is announced or vegetation share is 0.10 or more, the level is capped at 3 (flag "may be complete"). The cycle list holds at most 4 compounds from levels 1-3, each with a one-sentence reason.

**What we found on real data.** Six public R7 cases were checked with the clock frozen. The rule gave an early alert in 1 of 6 cases (after-start reading) and 0 of 6 (point-in-time reading). The success criterion of 5 cases was not achieved and was not lowered. The diagnosis shows imaging was sufficient in every case (at least 10 images per quarter). In the five missed cases the sites were seen as active, so the rule had no stall to detect; it measures stalls and passed dates, not pace against plan. The one hit (C21) came from a start date set by publication timing and a lag in the activity score, not from a real stall. These counts do not prove why each delay happened.

**What generated data shows.** Track B uses synthetic data only ("Synthetic - for training only"). The capacity-4 test holds 4 distressed rows, so statistical power is very low. Recall at capacity 4 ranges from 1 of 4 to 4 of 4 across the models, against a random-list baseline of 0.335 (2,000 draws). Scores are diagnostic and show nothing about real-world accuracy.

**Value.** Under these assumptions, from 0.007 to 0.102 million EGP per year. Operating cost and missed cases are public proxies; the cost of late detection is a placeholder that needs ACUD. Even the conservative setting is positive, but small.

**Proposed next steps.** (1) Use the list as a prioritisation aid; the visit confirms. (2) Record every visit result to build real ground truth. (3) Request ACUD data: supervisor reports, contractual dates, field review records, escrow balances.

**Limits.** Satellites show whether building is happening, not interior finishing; no completion % is given. K3 relies on developer statements. No compound is called distressed.

## العربية

**القرار المطلوب.** استخدام قائمة أولوية التفتيش لاختيار كومباوندات R7 التي تزورها اللجنة أولاً في الدورة القادمة. النظام يوصي، واللجنة هي التي تقرر.

**ما يفعله النظام.** يحدد لكل من 12 كومباوند (بالأكواد) مستوى أولوية من 1 إلى 4 حسب أسوأ إشارة من ثلاث: عدد الأرباع دون نشاط بناء (K2)، وعدد الشهور منذ أول موعد تسليم معلن (K3)، وعدد الشهور منذ أول إطلاق أو وعد دون بداية مؤكدة (K6). وإذا أُعلن التسليم أو بلغ الغطاء النباتي 0.10 فأكثر فلا يتجاوز المستوى 3 (علامة "قد يكون مكتملاً"). تضم قائمة الدورة 4 كومباوندات على الأكثر من المستويات 1 إلى 3، ولكل منها جملة سبب واحدة.

**ما وجدناه في البيانات الحقيقية.** فُحصت ست حالات عامة في R7 بتجميد الساعة. أعطت القاعدة إنذاراً مبكراً في حالة واحدة من 6 (قراءة ما بعد البدء) وفي 0 من 6 (قراءة لحظية). لم يتحقق معيار النجاح (5 حالات) ولم يُخفَّض. أظهر التشخيص أن الصور كانت كافية في كل الحالات (10 صور على الأقل في الربع). وفي الحالات الخمس التي فاتت رُصدت المواقع كنشطة، فلم يكن أمام القاعدة توقف لتكتشفه؛ فهي تقيس التوقف والمواعيد الفائتة وليس السرعة مقارنة بالخطة. والحالة الوحيدة المكتشفة (C21) جاءت من تاريخ بداية حُدد بتوقيت النشر ومن تأخر مؤشر النشاط، وليس من توقف فعلي. هذه الأعداد لا تثبت سبب كل تأخير.

**ما تُظهره البيانات المولّدة.** المسار B يعتمد على بيانات مولّدة فقط ("مولّد - للتدريب والعرض فقط"). يحتوي اختبار السعة 4 على 4 صفوف متعثرة فقط، فالقوة الإحصائية منخفضة جداً. يتراوح الاسترجاع عند السعة 4 بين 1 من 4 و4 من 4 حسب النموذج، مقابل خط أساس عشوائي 0.335 (2,000 سحبة). الدرجات تشخيصية ولا تدل على دقة في الواقع.

**القيمة.** تحت هذه الافتراضات، من 0.007 إلى 0.102 مليون جنيه سنوياً. تكلفة التشغيل والحالات الفائتة مقاييس بديلة من مصادر عامة، وتكلفة الكشف المتأخر قيمة مؤقتة تحتاج إلى بيانات من شركة العاصمة الإدارية. حتى الإعداد المتحفظ موجب لكنه صغير.

**الخطوات المقترحة.** (1) استخدام القائمة كأداة ترتيب أولويات، والزيارة هي التي تؤكد. (2) تسجيل نتيجة كل زيارة لبناء حقيقة ميدانية. (3) طلب بيانات ACUD: تقارير المشرف، والمواعيد التعاقدية، وسجلات المراجعة الميدانية، وأرصدة الضمان.

**الحدود.** الأقمار الصناعية ترى هل البناء جارٍ ولا ترى التشطيب الداخلي، ولذلك لا نذكر نسبة إنجاز. يعتمد K3 على تصريحات المطورين. لا نصف أي كومباوند بأنه متعثر.
