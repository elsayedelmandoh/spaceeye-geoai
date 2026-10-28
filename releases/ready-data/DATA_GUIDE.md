# Which data should I use?

Scope: **12 coded R7 compounds**. `code` identifies a compound; `developer_code` identifies a developer. Join tables on their keys, not row order. A month is `YYYY-MM`; a quarter is `YYYYQn`.

| Your task | Start with | Contents |
| --- | --- | --- |
| Current inspection priorities | `tables/inspection/cycle_list.csv` | Latest selected compounds, priority and supporting indicators. Capacity is 4. |
| Quarterly indicator charts | `tables/real/kpi_values.parquet` | 372 rows; priority levels, K2, K3, K5 and K6. |
| Satellite monitoring | `tables/real/sat_quarterly.parquet` and `sat_yearly.parquet` | 516 quarterly / 132 annual rows; activity and approved observation products. |
| Map and register | `tables/real/compound_boundaries.geojson` and `compounds.parquet` | Coded polygons and register fields; origin columns distinguish observed and generated values. |
| Published evidence | `tables/real/statements.parquet` | 57 coded published statements. A real statement is not independent proof of physical completion. |
| Financial analysis | `tables/operations/fin_monthly.parquet` or `fin_quarterly.parquet` | 540 monthly / 180 quarterly prepared rows. Flows sum over a quarter; stocks use its last month. |
| Complaint analysis | `tables/operations/complaints.parquet` | 1,334 accepted synthetic complaints with phone masking. Original Arabic text remains as data. |
| Fine assumptions | `tables/operations/fine_assumptions.parquet` | 12 generated contract/allocation assumptions; exact rates and dates are not verified contracts. |
| Hypothetical financial comparisons | `tables/financial_paths/paths.parquet` and `summary.csv` | 648 forward rows: baseline, lower collections and higher imported cost. |
| Capacity comparisons | `tables/inspection/inspection_capacity.csv` | Selections under capacities 2, 4 and 6. Capacity changes selection only. |
| Machine-learning work | `training/ml_dataset_extended.parquet` and `metadata.json` | 180 rows, exact 40-feature list, binary/three-class targets and censoring flags. |
| Complaint classifier | `training/complaints_benchmark.parquet` and `complaints_benchmark_metadata.json` |296generated texts;train152/validation40/test104;all5classes in each split,body families isolated. Synthetic capability only. |
| Labels for existing complaint texts | `training/complaints_training.parquet` and `complaints_metadata.json` |100masked feed texts with correct synthetic category targets. Small grouped holdouts lack some classes;do not mix with the benchmark. |
| Inspection agent inputs | `inspection/index.csv` and its referenced JSON files |180cutoff-safe contexts with coded facts,safe source references,generated operations and follow-up questions;no hidden targets. |
| Visit exercises | `tables/review/synthetic_visits.parquet` |58explicitly generated visit records tied to selected cycles. Real-visit template stays empty;these are not real field evidence. |
| Financial priority comparison | `tables/review/hypothetical_priorities.parquet` |648rows applying frozen cutoff context plus projected B5gap>20;capacity4 and same-month baseline comparisons. Not predicted future satellite priority. |

Equivalent CSV copies of Parquet tables are under `csv/`. `TABLES.csv` lists all table names and row counts, including SQL names in `spaceeye_ready.duckdb`. Field definitions are in `dictionaries/` and `training/dictionary.md`.

## Read a table

From inside the extracted folder:

```python
import pandas as pd

finance = pd.read_parquet("tables/operations/fin_quarterly.parquet")
print(finance.head())
```

```python
import duckdb

with duckdb.connect("spaceeye_ready.duckdb", read_only=True) as con:
    priorities = con.execute(
        "SELECT * FROM inspection_cycle_list ORDER BY cycle_rank"
    ).df()
```

## Training: use the declared features only

```python
import json
import pandas as pd

with open("training/metadata.json", encoding="utf-8") as file:
    meta = json.load(file)
data = pd.read_parquet(meta["dataset"])
train = (
    data.quarter.le("2024Q4")
    & ~data.label_censored
    & ~data.already_completed_at_cutoff
)
X_train = data.loc[train, meta["features"]]
y_train = data.loc[train, "label_distress_next_6m"]
```

Do not include keys, targets, censoring flags or already-completed flags in X. Fit imputation/scaling on training only. Keep the time split: train through 2024Q4, embargo 2025Q1, test 2025Q2–2026Q1. The last two quarters have censored targets and are excluded from supervised fitting/target metrics.

## Definitions to remember

- **K5:** union of screening months under the declared research policy. EGP amounts and the 1% monthly rate are assumptions, not actual assessed fines. Relief is optional, not universal entitlement.
- **K6:** time without confirmed observed start since a known launch/promise reference. Missing evidence remains unknown; do not fill it with zero automatically. Retrospectively generated allocation dates are excluded from X/public K6.
- **Three-class target:** distress takes precedence; `completed` requires new full-project handover in the future six months. Partial handover does not count. There are zero completed training examples and one completed test example; no reliable three-class model is claimed.
- Monthly `units_sold` is a flow. The training complaint diagnostic uses cutoff-month sales, not cumulative buyer inventory.
- Financial paths are hypothetical, not handover forecasts. Historical N=8 model results do not validate the current capacity 4 or expanded feature schema.
- Read `docs/validation_summary.json` for retained limitations, including the 2019Q2 coverage flag.

Use the ready bundle for analysis, GIS, interface development and carefully defined modelling work. Rebuilding the original source pipeline requires additional external inputs and is a separate task.

For complaint work,use only `text_ar` as X and `label_category` as y,filtered by the supplied split. Desk categories,template/group IDs and evaluation flags are not features. Never report these generated-template results as real complaint accuracy. Inspection contexts separate published evidence from generated operations/visits;missing imagery is explicitly marked. Full component definitions:docs/COMPONENT_DATA_PROTOCOL.md inside the bundle.
