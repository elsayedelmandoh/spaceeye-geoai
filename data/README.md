# Oasis District synthetic data kit · حقيبة بيانات حي الواحة

**Synthetic data — for training only · بيانات اصطناعية لأغراض التدريب فقط.**
Oasis District (حي الواحة) is fictional. Nothing here is ACUD data, and there is no real personal data.

## Use the data (learners)

Everything you need is already built in `data/lite/` and `reference/`. Start with `labs/D01/hello_oasis.ipynb`.
Setup: `docs/setup_guide.md`. Column meanings: `docs/data_dictionary.md` (or `.xlsx`).

## Rebuild (instructors)

```bash
pip install -r requirements.txt
make all                    # or: python -m generator build      (from this folder)
                            # or: python -m oasis_datakit build  (from the parent folder)
make check                  # rebuild the data and compare SHA-256 checksums
```

One seed (`config.yaml → seed`) drives everything; each dataset has its own random stream, so the same seed always gives byte-identical files (`data/lite_checksums.sha256`). A build takes about 30 seconds.

| Folder | What |
|---|---|
| `config.yaml` | Seed, dates, zones, story and defect settings |
| `generator/` | Python modules, one per pillar, plus calendar, reference, defects, docs, validation, Day 1 |
| `reference/` | zones.csv/.geojson, roads.geojson, sensors.csv, assets.csv, buildings.csv, calendar.csv |
| `data/lite/` | 19 datasets, 1 Mar – 30 Jun 2025, CSV, local time Africa/Cairo |
| `docs/` | data dictionary (EN + AR), validation report, setup guide, **answer key (instructors only)** |
| `labs/D01/` | hello_oasis, warm-up + solution, dashboard_day1.html, day1_chart_values.md |

**Instructors only:** `docs/answer_key.md` and `docs/answer_key_rows.csv` list every injected defect and hidden story. They, `docs/validation_report.html` (it shows every defect and story), the solution notebooks and `labs/D01/day1_chart_values.md` are listed in `.gitignore`, so they never reach the repository learners clone; share them with instructors separately.

Phase 2 (not built yet): full edition (12 months, Parquet, H2 heatwave, H4 waste schedule), KPI reference, Days 2–8 labs, shift-replay app.


--- 

# Oasis District data kit · حقيبة بيانات حي الواحة

**Synthetic data — for training only · بيانات اصطناعية لأغراض التدريب فقط.**
Oasis District (حي الواحة) is a fictional district. Nothing here is ACUD data and there is no real personal data.

## Start here · ابدأ من هنا

1. Upload this file, unchanged, to Google Drive: `MyDrive/ACUD_Oasis/oasis_datakit.zip` (once).
2. In Google Colab: File → New notebook. Type Cell 1 from the slide and run it. It unzips the kit into the session.
3. Every new Colab session: run Cell 1 first.

<p dir="rtl" align="right">١. ارفع هذا الملف كما هو إلى Google Drive في المجلد MyDrive/ACUD_Oasis (مرة واحدة).<br>٢. في Google Colab: File ← New notebook، ثم اكتب الخلية ١ من الشريحة وشغّلها.<br>٣. في كل جلسة جديدة: شغّل الخلية ١ أولًا.</p>

## What is inside · المحتويات

| Folder | What |
|---|---|
| `data/lite/` | 4 months (1 Mar – 30 Jun 2025), CSV |
| `reference/` | zones, roads, sensors, assets, buildings, calendar |
| `docs/` | data dictionary (EN + AR) and KPI reference |
| `labs/` | the Day 1 dashboard, and the Day 3 complaints file with its answer key |
| `snippets/` | small helpers you import, e.g. `from snippets.helpers import ar` |
| `templates/`, `handouts/` | report templates and printed handouts |

The full edition (12 months of 2025, Parquet) comes later as `oasis_full.zip` (Day 7).
Local time is Africa/Cairo with daylight saving; the weekend is Friday and Saturday.
