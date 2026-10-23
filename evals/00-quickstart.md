# evals quickstart

**propose:** evaluation hub -- benchmarks, scorers, results, analysis, and figures.

**input:** model predictions from `artifacts/evaluation/predictions/`, test datasets, reference answers.

**output:** scored reports, analysis docs, and publication-ready figures.

**structure:**
- `01-evaluation.md` -- evaluation plan and metrics
- `02-testing.md` -- testing plan and validation notes
- `03-performance-comparison.md` -- benchmark comparisons
- `04-results-analysis.md` -- interpretation of results
- `benchmarks/` -- benchmark configs and evaluation code
- `results/` -- raw metrics, csv, json outputs (gitignored)
- `figures/` -- generated plots (committed, tracked)

> executable tests live in **`tests/`**.
