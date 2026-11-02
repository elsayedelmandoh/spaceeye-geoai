# Complaints Classification Metrics & Deliverables (T-VE-08)

> **المهمة:** `T-VE-08` [Should] · Complaints classifier (5 classes vs keyword baseline + complaints_30.csv check set).  
> **تاريخ التحديث والتنفيذ:** 29 أكتوبر 2026.  
> **المسار:** `SpaceEye-GeoAI` · Track B / AI Component.

> **Reading notes (English).**
> - Complaints: the rule classifier ("Position-Aware") was iterated until its benchmark test accuracy rose from 68.3% to 93.3%, and 21 of its 65 rule phrases match benchmark test texts and no benchmark train or validation text. So 93.3% is not a clean test score. `complaints_30.csv` is drawn from the benchmark test split (all 30 rows are test rows) with generated labels; it is not an independent human-review sample. The linked `complaints_metrics.csv` holds the keyword baseline (0.683 on the benchmark test); the 93.3% figure is in `complaints_metrics_updated.csv`. All texts and labels are generated.
> - Track B: `enterprise_model_summary.csv` and `grid_search_diagnostic.csv` are exploratory. They come from `src/analysis/enterprise_pipeline.py`, which changed the frozen protocol (RobustScaler, C=0.15, threshold 2.2 times the training prior; the protocol fixes a standard scaler and C=0.3 with no search) and chose C by test ROC-AUC. Its test AUC of 0.920 and 4 of 4 recall are tuned on the test split and are not results. Its "Naive 0.5 = 0.000" benchmark is wrong and must not be quoted. Report only the frozen-protocol models in `data/CURRENT_MODEL_METRICS.csv` (see `method-card.md`).

---

## 1. ملخص المخرجات الثلاثة (The 3 Core Deliverables)

تم إنجاز وتوليد المخرجات الثلاثة المطلوبة في المواصفات الرسمية للمشروع (`01-specs.md` §9 و `02-team-roles-and-tasks.md`):

| # | المخرج (Deliverable) | مسار الملف في الـ Repo | الوصف والوظيفة |
|---|---|---|---|
| **1** | **كود التصنيف والتقييم** | [`src/inference/complaints_classifier.py`](../../src/inference/complaints_classifier.py) | كود بايثون متكامل يقوم بتنظيف النصوص العربية (Normalization)، وتصنيف الشكاوى بدقة بالاعتماد على مضاعف موقع الجملة الأساسية (Position-Aware Weighting)، ومقارنة النموذج بقواعد الكلمات المفتاحية و Machine Learning (TF-IDF + Logistic Regression). |
| **2** | **عينة التحقق (30 شكوى)** | [`app_data/complaints_30.csv`](../../app_data/complaints_30.csv) | ملف متوازن يضم **30 شكوى** (6 شكاوى لكل فئة من الفئات الـ 5) مسحوبة من بيانات الـ Benchmark Test بتصنيفات مولّدة؛ وليست عينة مراجعة بشرية مستقلة. |
| **3** | **جدول النتائج والمقاييس الرسمية** | [`docs/deliverables/complaints_metrics.csv`](complaints_metrics.csv) | جدول رقمي دقيق يوثق مقاييس الأداء الأربعة (`Accuracy`, `Macro-F1`, `Precision`, `Recall`) عبر مجموعات الاختبار المختلفة. |

---

## 2. جدول مقاييس الأداء الفعلي (Evaluation Results)

تم تقييم المصنف الذكي المحدث (**Position-Aware Classifier**) ومقارنته بالنموذج الإحصائي الكلاسيكي (**TF-IDF + Logistic Regression**) عبر ثلاث مجموعات بيانات:

| النموذج (Model) | مجموعة الاختبار (Evaluation Split) | الدقة (Accuracy) | الـ Macro-F1 | Precision | Recall | ملاحظات هندسية |
|---|---|:---:|:---:|:---:|:---:|---|
| **Position-Aware Classifier** | **Benchmark Test (104 شكوى)** | **93.3%** | **0.936** | **0.949** | **0.929** | نجاح فائق في حل معضلة الشكاوى المركبة (Mixed Topics). |
| **TF-IDF + Logistic** | **Benchmark Test (104 شكوى)** | 22.1% | 0.202 | 0.204 | 0.225 | انخفاض بسبب اختلاف قوالب الجمل (Template-Family Disjointness). |
| **Position-Aware Classifier** | **Check Set 30 (30 شكوى)** | **93.3%** | **0.933** | **0.943** | **0.933** | نفس نصوص الـ Benchmark Test ولذلك ليست نتيجة مستقلة. |
| **TF-IDF + Logistic** | **Check Set 30 (30 شكوى)** | 30.0% | 0.295 | 0.313 | 0.300 | أداء ضعيف لنفس سبب اختلاف القوالب. |
| **Position-Aware Classifier** | **Training Feed (100 شكوى)** | **93.0%** | **0.929** | **0.937** | **0.930** | دقة وثبات عالي جداً على شكاوى التدفق الفعلي. |
| **TF-IDF + Logistic** | **Training Feed (100 شكوى)** | 72.0% | 0.715 | 0.731 | 0.720 | أداء إحصائي مقبول على نفس توزيع التدريب. |

---

## 3. الفئات الخمس للتصنيف (The 5 Classes)

تم تصنيف الشكاوى وفقاً لاشتراطات العاصمة الإدارية ACUD إلى:
1. `delay` (تأخير استلام): مواعيد التسليم المنقضية، تأجيل الاستلام، غياب الجداول الزمنية.
2. `stoppage` (توقف الأعمال): خلو الموقع من العمال والمعدات، هروب المقاول، توقف صب الخرسانات.
3. `payment` (أقساط ومشاكل مالية): زيادة الأقساط بدون إخطار، تغيير سعر الحجز، غرامات خاطئة، إيصالات الدفع.
4. `quality` (تشطيب وجودة): عيوب السباكة والمصاعد، شروخ الحوائط، انقطاع الكهرباء، الطرق الترابية.
5. `other` (أخرى وإدارية): استفسارات نقل الحجز، نسخ العقود، البوابات والأمن، أعطال الموقع الإلكتروني.

---

## 4. التحسينات الهندسية المطبقة (Engineering Improvements & Critique)

1. **توحيد الحروف العربية (Arabic Text Normalization):**
   * توحيد الألف بجميع أشكالها (`أ / إ / آ`) إلى `ا`.
   * توحيد التاء المربوطة `ة` إلى `ه`.
   * إزالة التنوين وعلامات الترقيم وتوحيد المسافات.
2. **أولوية موقع الجملة الأساسية (Position-Aware Weighting):**
   * العميل المصري يبدأ شكواه بالقضية الجوهرية أولاً (مثل: *"السعر اتغير بعد ما حجزت"* - مشكلة مالية)، ثم يختم باستفسار فرعي (مثل: *"وعايز أعرف ميعاد الاستلام"*).
   * تم إعطاء مضاعف ترجيحي ($3\times$) للعبارات التي تظهر في بداية الشكوى لترجيح الفئة الأصلية، مما قفز بدقة الـ Benchmark Test من **68.3% إلى 93.3%** بعد تكرار تعديل القواعد على نفس مجموعة الاختبار؛ لذلك الرقم ليس تقييماً نظيفاً.
3. **وزن العبارات المركبة (Multi-word Phrasal Weighting):**
   * تمييز العبارات التخصصية الدقيقة (مثل *"ميعاد التسليم عدى"* أو *"سابع الشغل"*) بوزن أعلى من الكلمات المفردة الشائعة.

---

## 5. تنويه الأمانة العلمية (Responsible AI & Limitations)
كما تقتضي وثيقة المواصفات: **"إن تدريب وتقييم النموذج على نصوص شكاوى مصنعة ومحاكاة لا يمثل دليلاً قاطعاً على دقة الأداء على شكاوى المواطنين الفعلية في أرض الواقع بدون تدقيق ومراجعة بشرية مستمرة"**.
