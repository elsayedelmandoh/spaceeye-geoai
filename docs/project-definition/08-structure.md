## Repository Structure

Current layout plus the files planned in [`02-team-roles-and-tasks.md`](../requirements/02-team-roles-and-tasks.md). `[planned T-..]` marks a file that does not exist yet and the task that creates it. Owners: ahmed (Track A), elsayed (Track B), verina (AI), nada (dashboard), salma (docs).

```text
spaceeye-geoai/
├── README.md                          # overview + how to run
├── CLAUDE.md, AGENTS.md               # agent instructions
├── pyproject.toml, uv.lock            # uv project (dev group: pytest, ruff, nbstripout; extra `pulls`: earthengine-api)
├── Makefile                           # install | lint | format | test | clean · [planned T-AH-13] run
├── .env.example                       # MASK_SALT, GEMINI_API_KEY, GEMINI_MODEL (never commit .env)
├── app.py                             # [nada] streamlit entry: track switch + 5 screens (placeholder today, T-NA-01)
├── configs/
│   ├── data.yaml                      # [ahmed] paths, seed, computed_on, thresholds, levels, cycle_capacity, generator block, fine rate (assumption)
│   ├── kpis.yaml                      # [salma] KPI cards
│   └── cost_assumptions.yaml          # [salma] value in EGP, 3 settings
├── src/
│   ├── config/                        # settings from .env
│   ├── pipeline/                      # [ahmed] Track A, one command: python -m src.pipeline.run_all
│   │   ├── common.py                  #   CFG, paths, quarter helpers (0 = 2016Q1)
│   │   ├── codify.py                  #   step 1: names -> codes (names stay in private/)
│   │   ├── build_real.py              #   step 2: real tables (R7 filter, T-AH-03)
│   │   ├── activity.py                #   step 3: activity score A (+ backtest variant)
│   │   ├── kpis.py                    #   step 4: K2-K6, level, reason (en + ar), cycle rank (K5/K6 T-AH-04/05)
│   │   ├── backtest_check.py          #   step 6: frozen-clock backtest
│   │   ├── gates.py                   #   step 5: 10 quality gates incl. no_names, separation
│   │   ├── run_all.py                 #   orchestration, duckdb, manifest
│   │   └── pulls/                     #   earth engine pulls (dw, s2 windows, vegetation) · [planned T-AH-15] wayback.py
│   ├── generator/                     # [elsayed] Track B data: python -m src.generator.simulate
│   │   ├── inputs.py, stories.py, economy.py, truth.py, observe.py, complaints.py
│   │   ├── answer.py                  #   hidden truth + label (3 classes, T-EL-06)
│   │   ├── defects.py, checks.py      #   6 planted defects, realism checks
│   │   ├── dictionaries.py, plots.py
│   │   └── scenarios.py               #   [planned T-EL-13] what-if S1-S5, base run never overwritten
│   ├── analysis/                      # [elsayed] Track B model: python -m src.analysis.early_warning
│   │   ├── ew_features.py             #   features <= cutoff
│   │   ├── ew_eval.py                 #   rule with B triggers, models, recall@N vs random
│   │   ├── ew_report.py, early_warning.py
│   │   └── ml_dataset.py              #   [planned T-EL-08] compound x quarter X, y + 3-class classifier
│   ├── inference/                     # [verina] AI component
│   │   ├── generate.py                #   gemini call helpers (stub today)
│   │   ├── tools.py                   #   [planned T-VE-02] get_facts, get_kpis, get_images, get_rules
│   │   ├── inspection_file.py         #   [planned T-VE-03/06] template + paragraph + Arabic HTML/PDF
│   │   ├── verify.py                  #   [planned T-VE-05] numbers vs source, ai_verification_log
│   │   └── complaints.py              #   [planned T-VE-07/08] masking + 5-class classifier vs keyword baseline
│   ├── dashboard/                     # [planned T-NA-01..07, nada] one module per screen: priority_map, compound_file, backtest, data_trust, what_if
│   ├── evaluation/, models/, utils/   # template stubs
├── prompts/                           # [verina] system/, templates/, few-shot/ for the inspection file
├── tests/
│   ├── test_pipeline.py               # quarter helpers, worst-of-signals level, K2 start rule, first promise, name gate (+ K5/K6, R7 filter)
│   ├── test_generator.py              # generator math, phone masking pattern (+ 3-class label, scenarios determinism)
│   ├── test_early_warning.py          # top-N ties, no data after cutoff (+ ml_dataset leakage)
│   └── test_inference.py              # [planned T-VE-05/07] verifier catches a wrong number, zero phones after masking
├── notebooks/                         # exploration only; repeatable logic lives in src/
├── evals/                             # benchmarks/, figures/, results/
└── docs/
    ├── requirements/                  # 01-specs.md (live plan), 02-team-roles-and-tasks.md (task board), 04-timeline.md, 05-project-compass.md
    ├── project-definition/            # 03-dataset.md (live data doc), 05-constraints.md, this file
    ├── deliverables/                  # [salma + owners] presentation, decision memo, kpi cards, method card, quality report,
    │                                  #   governance cards, responsible-ai, user guide, technical docs, knowledge transfer, data request
    └── .internal/                     # agent-workflow/ (todo, lessons), archive/ (old drafts, not live)
```

## Outside the repo (never committed)

Set in `configs/data.yaml` `paths:`.

```text
Project/
├── real_data/                         # audited sources, read only (R8 files stay here untouched)
├── app_data/                          # every built output
│   ├── raw/                           #   codified copies + cached earth engine pulls
│   ├── real/                          #   [ahmed] parquet tables, kpi_values, quality_checks_log, cycle_list_<asof>.csv, boundaries
│   ├── model/, backtest/              #   [ahmed] activity score, frozen-clock results
│   ├── images/                        #   [ahmed] 2 Wayback images per compound + images.csv
│   ├── sim/                           #   [elsayed] fin_monthly, complaints, realism checks, dictionaries
│   ├── ml/                            #   [elsayed] ml_dataset, predictions, metrics
│   ├── scenarios/                     #   [elsayed] S1..S5 outputs, same columns as the base
│   ├── files/                         #   [verina] inspection files (Arabic HTML/PDF)
│   ├── ai_verification_log.csv        #   [verina]
│   ├── ops_visits.csv                 #   [nada] visit results
│   ├── spaceeye.duckdb, manifest.csv
│   ├── EW_PROTOCOL.md, EW_REPORT.md   #   [elsayed]
└── private/                           # code_map (names), answer_key, defects_log, stories
```
