# Laptop setup guide

<div dir="rtl" align="right"><h1>دليل تجهيز الجهاز</h1></div>

**AI & Data Readiness Program · Day 1 lab** — please do this **before Day 1**. It takes about 30 minutes.

<div dir="rtl" align="right"><b>برنامج جاهزية الذكاء الاصطناعي والبيانات · معمل اليوم الأول</b> — نرجو إتمام هذه الخطوات <b>قبل اليوم الأول</b>، وتستغرق نحو ٣٠ دقيقة.</div>

You need: 8 GB RAM (16 GB better), 20 GB free disk, admin rights, internet. Everything is free.

<div dir="rtl" align="right">المطلوب: ذاكرة ٨ جيجابايت (والأفضل ١٦)، ومساحة فارغة ٢٠ جيجابايت، وصلاحيات المسؤول على الجهاز، واتصال بالإنترنت. كل الأدوات مجانية.</div>

| # | Step | الخطوة |
|---|---|---|
| 1 | Install **Python 3.11 or newer** from python.org. On Windows, tick *Add python.exe to PATH*. | <div dir="rtl" align="right">ثبّت Python 3.11 أو أحدث من python.org. في Windows اختر <i>Add python.exe to PATH</i>.</div> |
| 2 | Install **VS Code** and its **Python** and **Jupyter** extensions. | <div dir="rtl" align="right">ثبّت VS Code ثم إضافتي Python وJupyter.</div> |
| 3 | Install **Git** from git-scm.com. | <div dir="rtl" align="right">ثبّت Git من git-scm.com.</div> |
| 4 | Get the data kit: `git clone [KIT_REPO_URL — to be confirmed]` into a folder **without spaces or Arabic letters** in its path, e.g. `C:\work\oasis_datakit`. | <div dir="rtl" align="right">انسخ حقيبة البيانات بالأمر git clone في مجلد مساره <b>بلا مسافات أو حروف عربية</b>، مثل C:\work\oasis_datakit.</div> |
| 5 | In a terminal inside the folder: `python -m venv .venv`, activate it (`.venv\Scripts\activate` on Windows, `source .venv/bin/activate` on macOS/Linux), then `pip install -r requirements.txt`. | <div dir="rtl" align="right">من الطرفية داخل المجلد: أنشئ بيئة افتراضية وفعّلها، ثم ثبّت المكتبات بالأمر pip install -r requirements.txt.</div> |
| 6 | Open the folder in VS Code, open `labs/D01/hello_oasis.ipynb`, choose the `.venv` kernel and **Run All**. You should see the six zones and *Total residents: 60000*. | <div dir="rtl" align="right">افتح المجلد في VS Code، ثم الدفتر labs/D01/hello_oasis.ipynb، واختر النواة .venv واضغط Run All. يجب أن تظهر المناطق الست و«إجمالي السكان ٦٠٠٠٠».</div> |
| 7 | Take a **screenshot** of the result — you will submit it on Day 1. | <div dir="rtl" align="right">التقط <b>صورة للشاشة</b> للنتيجة، فستسلّمها في اليوم الأول.</div> |

**Plan B — Google Colab.** If anything fails, go to colab.research.google.com, sign in, *File → Upload notebook* → `hello_oasis.ipynb`, and *Runtime → Run all*. The first cell downloads the kit for you.

<div dir="rtl" align="right"><b>الخطة البديلة: Google Colab.</b> إذا تعثّر أي شيء، افتح colab.research.google.com وسجّل الدخول، ثم ارفع الدفتر hello_oasis.ipynb وشغّل كل الخلايا. الخلية الأولى تُنزّل الحقيبة تلقائيًا.</div>

**Common problems**

<div dir="rtl" align="right"><b>مشكلات شائعة</b></div>

| Problem | Fix | الحل |
|---|---|---|
| `python` not found | Reinstall with *Add to PATH*; open a new terminal. | <div dir="rtl" align="right">أعد تثبيت Python مع خيار PATH، ثم افتح طرفية جديدة.</div> |
| Arabic shows as boxes | Open the file in VS Code or Jupyter, not Excel. CSV files are UTF-8. | <div dir="rtl" align="right">افتح الملف في VS Code أو Jupyter وليس Excel، فالملفات بترميز UTF-8.</div> |
| `git clone` blocked | Download the ZIP from the same page. | <div dir="rtl" align="right">نزّل الملف المضغوط ZIP من الصفحة نفسها.</div> |

*All data in the kit is synthetic, for training only.*

<div dir="rtl" align="right"><i>كل البيانات في الحقيبة اصطناعية لأغراض التدريب فقط.</i></div>
