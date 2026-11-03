# Decision memo / مذكرة قرار

Task T-SA-05. Draft for review. All counts come from `data/BACKTEST_CURRENT.md`, `data/EW_REPORT_CURRENT.md`, `data/experiments/35_backtest_diagnosis/DIAGNOSIS.md`, `configs/cost_assumptions.yaml` and, for the problem chain, the release tables `real/eval_outcomes`, `real/compounds` and `real/kpi_values` (as of 2026Q3). Codes only, no names.

## English

**Decision requested.** Use the inspection priority list to choose which R7 compounds the committee visits first next cycle. The system recommends; the committee decides.

**The problem in one chain (R7, our count).** *Number:* 5 of the 6 public late cases in R7 ran 18 to 33 months past their original promise (median 25). *Problem:* the delay is seen late; a review that asks "is the site working?" passes a site that keeps working while its promise slips (`docs/deliverables/as-is.md`). *Impact:* those five compounds hold 6,474 homes; if every buyer waited the full delay, that is 153,816 home-months of waiting (an estimate that assumes every home shared the first promised date; buyers in later phases waited longer). In 3 of them (C10, C12, C21; 3,624 homes) the delay passed 24 months, beyond which Decree 2184/2022 art. 5 lets a buyer choose a refund; in all 5 it passed 12 months, beyond which installments are deferred. Delays are counted from the published promise, not the contract date, so the legal effect depends on each contract. *Assumed money:* at an assumed rent of 5,000 EGP per home per month while waiting (assumption, no source), the waiting costs buyers about 0.77 billion EGP. This is the stability link in the compass: late handovers weaken buyer trust in the market.

**Why now.** (1) Decree 2184/2022 art. 5 applies to projects already under way: 12 months past the contract date, installments are deferred, and past 24 months a buyer may choose a refund. (2) Two R7 clocks are running today: C18 is 57 months past its first announced handover date with 45 months eligible for contract review (K5, a screening count, not a fine), and C14 has moved its date twice (end of 2024, then 2026, then 2027). (3) Free public satellite data, quarterly since 2019, lets the committee check every compound every quarter without a visit; the pipeline already runs on it.

**What the system does.** For 12 coded R7 compounds it assigns a priority level (1-4) from the worst of three signals: quarters with no building activity (K2), months since the first announced handover date (K3), and months since the first launch or promise with no confirmed start (K6). If a handover is announced or vegetation share is 0.10 or more, the level is capped at 3 (flag "may be complete"). The cycle list holds at most 4 compounds from levels 1-3, each with a one-sentence reason.

**What we found on real data.** Six public R7 cases were checked with the clock frozen. The rule gave an early alert in 1 of 6 cases (after-start reading) and 0 of 6 (point-in-time reading). The success criterion of 5 cases was not achieved and was not lowered. The diagnosis shows imaging was sufficient in every case (at least 10 images per quarter). In the five missed cases the sites were seen as active, so the rule had no stall to detect; it measures stalls and passed dates, not pace against plan. The one hit (C21) came from a start date set by publication timing and a lag in the activity score, not from a real stall. These counts do not prove why each delay happened.

**What generated data shows.** Track B uses synthetic data only ("Synthetic - for training only"). The capacity-4 test holds 4 distressed rows, so statistical power is very low. Recall at capacity 4 ranges from 1 of 4 to 4 of 4 across the models, against a random-list baseline of 0.335 (2,000 draws). Scores are diagnostic and show nothing about real-world accuracy.

**Value.** Under these assumptions, from 0.007 to 0.102 million EGP per year. Operating cost and missed cases are public proxies; the cost of late detection is a placeholder that needs ACUD. Even the conservative setting is positive, but small.

**Proposed next steps.** (1) Use the list as a prioritisation aid; the visit confirms. (2) Record every visit result to build real ground truth. (3) Request ACUD data: supervisor reports, contractual dates, field review records, escrow balances.

**Limits.** Satellites show whether building is happening, not interior finishing; no completion % is given. K3 relies on developer statements. No compound is called distressed.

## العربية

**القرار المطلوب.** استخدام قائمة أولوية التفتيش لاختيار كومباوندات R7 التي تزورها اللجنة أولاً في الدورة القادمة. النظام يوصي، واللجنة هي التي تقرر.

**المشكلة في سلسلة واحدة (R7، من حسابنا).** *الرقم:* 5 من 6 حالات تأخير عامة في R7 تأخرت من 18 إلى 33 شهرًا عن الوعد الأصلي (الوسيط 25). *المشكلة:* التأخير يُكتشف متأخرًا؛ المراجعة التي تسأل "هل الموقع يعمل؟" تمرّر موقعًا يعمل بينما يتأخر وعده (`docs/deliverables/as-is.md`). *الأثر:* في هذه الكومباوندات الخمسة 6,474 وحدة؛ لو انتظر كل مشترٍ مدة التأخير كاملة فهذا 153,816 شهر انتظار للوحدات (تقدير يفترض أن كل الوحدات لها أول موعد موعود نفسه؛ مشترو المراحل اللاحقة انتظروا أكثر). في 3 منها (C10 وC12 وC21؛ 3,624 وحدة) تجاوز التأخير 24 شهرًا، وبعدها يتيح قرار 2184 لسنة 2022 مادة 5 للمشتري اختيار الاسترداد؛ وفي الخمسة تجاوز 12 شهرًا، وبعدها تُرحّل الأقساط. التأخير محسوب من الوعد المنشور لا من تاريخ العقد، فالأثر القانوني يتوقف على كل عقد. *مال مفترض:* بإيجار مفترض 5,000 جنيه للوحدة شهريًا أثناء الانتظار (افتراض بلا مصدر) يكلّف الانتظار المشترين نحو 0.77 مليار جنيه. هذه صلة الاستقرار في البوصلة: التسليم المتأخر يُضعف ثقة المشترين في السوق.

**لماذا الآن.** (1) مادة 5 من قرار 2184 لسنة 2022 تسري على المشروعات الجارية، فبعد 12 شهرًا من موعد العقد تُرحّل الأقساط، وبعد 24 شهرًا يحق للمشتري اختيار الاسترداد. (2) ساعتان تعملان الآن في R7: C18 تجاوز أول موعد تسليم معلن بـ57 شهرًا ومعه 45 شهرًا مؤهلة للمراجعة، وC14 أجّل موعده مرتين (نهاية 2024 ثم 2026 ثم 2027). (3) بيانات الأقمار الصناعية العامة المجانية، ربع سنوية منذ 2019، تتيح للجنة فحص كل كومباوند كل ربع سنة دون زيارة؛ والنظام يعمل عليها بالفعل.

**ما يفعله النظام.** يحدد لكل من 12 كومباوند (بالأكواد) مستوى أولوية من 1 إلى 4 حسب أسوأ إشارة من ثلاث: عدد الأرباع دون نشاط بناء (K2)، وعدد الشهور منذ أول موعد تسليم معلن (K3)، وعدد الشهور منذ أول إطلاق أو وعد دون بداية مؤكدة (K6). وإذا أُعلن التسليم أو بلغ الغطاء النباتي 0.10 فأكثر فلا يتجاوز المستوى 3 (علامة "قد يكون مكتملاً"). تضم قائمة الدورة 4 كومباوندات على الأكثر من المستويات 1 إلى 3، ولكل منها جملة سبب واحدة.

**ما وجدناه في البيانات الحقيقية.** فُحصت ست حالات عامة في R7 بتجميد الساعة. أعطت القاعدة إنذاراً مبكراً في حالة واحدة من 6 (قراءة ما بعد البدء) وفي 0 من 6 (قراءة لحظية). لم يتحقق معيار النجاح (5 حالات) ولم يُخفَّض. أظهر التشخيص أن الصور كانت كافية في كل الحالات (10 صور على الأقل في الربع). وفي الحالات الخمس التي فاتت رُصدت المواقع كنشطة، فلم يكن أمام القاعدة توقف لتكتشفه؛ فهي تقيس التوقف والمواعيد الفائتة وليس السرعة مقارنة بالخطة. والحالة الوحيدة المكتشفة (C21) جاءت من تاريخ بداية حُدد بتوقيت النشر ومن تأخر مؤشر النشاط، وليس من توقف فعلي. هذه الأعداد لا تثبت سبب كل تأخير.

**ما تُظهره البيانات المولّدة.** المسار B يعتمد على بيانات مولّدة فقط ("مولّد - للتدريب والعرض فقط"). يحتوي اختبار السعة 4 على 4 صفوف متعثرة فقط، فالقوة الإحصائية منخفضة جداً. يتراوح الاسترجاع عند السعة 4 بين 1 من 4 و4 من 4 حسب النموذج، مقابل خط أساس عشوائي 0.335 (2,000 سحبة). الدرجات تشخيصية ولا تدل على دقة في الواقع.

**القيمة.** تحت هذه الافتراضات، من 0.007 إلى 0.102 مليون جنيه سنوياً. تكلفة التشغيل والحالات الفائتة مقاييس بديلة من مصادر عامة، وتكلفة الكشف المتأخر قيمة مؤقتة تحتاج إلى بيانات من شركة العاصمة الإدارية. حتى الإعداد المتحفظ موجب لكنه صغير.

**الخطوات المقترحة.** (1) استخدام القائمة كأداة ترتيب أولويات، والزيارة هي التي تؤكد. (2) تسجيل نتيجة كل زيارة لبناء حقيقة ميدانية. (3) طلب بيانات ACUD: تقارير المشرف، والمواعيد التعاقدية، وسجلات المراجعة الميدانية، وأرصدة الضمان.

**الحدود.** الأقمار الصناعية ترى هل البناء جارٍ ولا ترى التشطيب الداخلي، ولذلك لا نذكر نسبة إنجاز. يعتمد K3 على تصريحات المطورين. لا نصف أي كومباوند بأنه متعثر.
