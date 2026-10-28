> Current partial-task extension (28 October 2026): Arabic exports, full-run reproducibility and current observed-class diagnostics are now implemented. Read [docs/data/PARTIAL_TASKS_CLOSURE.md](docs/data/PARTIAL_TASKS_CLOSURE.md). Older no-fitting statements refer to the base data-only delivery. Binary distress prediction is the approved scope; no completion class/probability remains.

# CLAUDE.md

Mandatory Git workflow: all work and commits use a feature branch,never main. No direct push to main;publish through a pull request. The approved current prepared bundle in releases/ready-data can be shared;raw inputs,name mappings,hidden answer keys and models remain excluded. Team instructions:releases/ready-data/README.md. Component inputs/protocol:docs/data/COMPONENT_DATA_PROTOCOL.md. Retired docs/plan drafts must not be restored.

## Current R1/R2 release

Read `docs/data/HANDOFF.md` and `docs/data/DELIVERY_PLAN.md` first. They supersede older implementation-status statements below. Use `uv run --locked --offline python -m src.pipeline.complete_data` for data-only rebuilding; `src.pipeline.delivery` checks two complete data-only runs and writes current reports/dictionaries. Do not rerun model fitting for documentation changes. Scope is12R7 compounds;capacity4;K5is a policy proxy with assumed EGP;K6enters priority;the current expanded data has180rows/40features. Prior N=8binary evaluation is historical. The full product specs are preserved; the implementation contracts are in `docs/data/`.

Commits use the repository's configured human author/committer identity. Do not add assistant attribution or co-author trailers. Preserve both current work and teammates' changes when integrating branches; no force push.

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

SpaceEye: R7 Digital Twin and Inspection Priority Observatory (New Administrative Capital, graduation project). It answers one question: **which R7 compounds should the inspection committee visit first this cycle, and why.** The system recommends; the committee decides.

**The plan lives in `docs/requirements/01-specs.md` and `docs/project-definition/03-dataset.md`.** These two files are the only live plan docs and win over everything else, including anything in `docs/.internal/archive/`. Task board (owners, `T-..` IDs, hand-off files): `docs/requirements/02-team-roles-and-tasks.md`. Repo layout, current and planned: `docs/project-definition/08-structure.md`.

## Commands

Use `uv`, not pip. Dev tools (pytest, ruff, nbstripout) are a `[dependency-groups]` group, so plain `uv sync` installs them.

```bash
make install                      # uv sync + nbstripout hook
make test                         # uv run pytest tests/ -v
uv run pytest tests/test_pipeline.py::test_level_is_the_worst_signal_and_may_be_complete_caps_at_3 -v   # one test
make lint / make format           # ruff check / ruff format on src/ tests/

python -m src.pipeline.run_all    # R1: real tables, activity score A, KPIs, backtest, gates, duckdb, manifest. exit 1 if a gate says STOP
python -m src.generator.simulate  # R2: generated ACUD data (stand-in) + realism checks; needs run_all output
python -m src.analysis.early_warning   # Track B early-warning experiment -> app_data/EW_REPORT.md
uv sync --extra pulls             # earthengine-api, only for src/pipeline/pulls/* (Earth Engine downloads into app_data/raw)
```

`app.py` is still a placeholder (prints settings). The Streamlit dashboard is the next step (specs section 9).

## Data lives outside the repo

`configs/data.yaml` `paths:` points at `real_data` (audited sources, read only, never modified), `app_data` (all built outputs) and `private` (code map with real names, `answer_key`). They are currently Windows paths (`F:/ACUD AI Data Lab/Project/...`); on another machine edit those paths. Nothing from `private/` or `app_data/` is committed. Tests that need built data are `skipif` when `app_data/sim/fin_monthly.parquet` is missing.

Ordering: `run_all` (writes `app_data/real`, `spaceeye.duckdb`) → `simulate` (reads `real`, writes `app_data/sim` + `private/answer_key`) → `early_warning` (reads both).

## Architecture (big picture)

Two tracks, one idea:

- **Track A: images (all real).** `src/pipeline/`. `codify` replaces every name with codes (`C..` compounds, `D..` developers; names stay only in `private/code_map.csv`) → `build_real` builds tables from audited sources → `activity` trains the activity score **A** (gradient boosting on Dynamic World + Sentinel-2 windows) plus a backtest variant without leaking plots → `kpis` computes K2 to K6 and the **priority level** → `backtest_check` runs the frozen-clock backtest → `gates` runs the 10 quality gates → duckdb + `manifest.csv`. `common.py` holds `CFG`, the paths and the quarter helpers (quarter index 0 = 2016Q1: `qindex`, `qlabel`, `qend`).
- **Track B: numbers (generated).** `src/generator/` simulates hidden ACUD finance (sales → cash → spending → progress → handover) per compound, with stories driven by each compound's real Track A signals, 6 planted defects and realism checks. `src/analysis/` (`ew_features`, `ew_eval`, `ew_report`, `early_warning`) builds features and compares the rule vs logistic vs gradient boosting with recall@N against a random top-N list. Track B reads Track A outputs and never redoes image work.
- `src/models`, `src/inference`, `src/evaluation`, `src/utils`: mostly template stubs.

**Priority level = the worst of K2, K3, K6 (no weights, no 0-100 score).** Thresholds are in `configs/data.yaml` `levels:` and are frozen: never change a threshold after seeing a result. Full table in specs section 2.

**Reproducibility:** `seed` and `computed_on` in `data.yaml` are fixed so two runs produce identical outputs. `run_id` hashes the config + raw inputs. Storage is delete-then-insert. Don't add `now()` or unseeded randomness. The generator uses `rng_for(*key)` per entity.

## Rules that never break (from specs section 14)

- **No compound or developer name in any output.** Codes only. The `no_names` gate stops the run and reports only paths and counts, never the matched name. Don't print names in logs either.
- **Never join a generated column into a real table** (the `separation` gate). Every column carries an origin: 🟢 real, 🔵 derived, 🟠 generated. Generated numbers appear only in Track B, labelled **"Synthetic - for training only"**, and never on a map.
- No leakage: statements are filtered by `published_date` ≤ as-of, and features never read `answer_key` (labels only, at training time).
- Never say "distressed", "completion %" or "finishing %" about a real compound, and say "priority level", never "risk level". Specs section 3 has the allowed/forbidden wording table.
- Scope is R7 only. R8 is filtered out of every built table. The "digital twin" means the light compound-level twin with what-if scenarios, never a 3D or real-time twin.
- No number that failed its pre-registered test goes into the product (for example height 2024-2026, or finishing from Sentinel-2). New ideas are tested against a condition written before the run.
- Committee-facing text (reason sentence, cycle list, inspection file) is in Arabic. Code and logs are in English.
- Complaint text is regex-masked before any model sees it (Law 151/2020). The masking pattern is tested in `tests/test_generator.py`.

## Code conventions

- Each module starts with a docstring of the form `propose: / input: / output:`. Lowercase comments and docstrings.
- Thresholds, paths and source file names come from `configs/data.yaml` via `CFG` / `src()`, never hardcoded. `.env` (from `.env.example`, gitignored) holds `MASK_SALT` (change it for production) and `GEMINI_API_KEY` / `GEMINI_MODEL`, loaded by `src/config/config.py` `settings`.
- Test names are full sentences describing the behaviour (`test_k2_counts_only_after_a_four_quarter_run_of_activity`).

## Working rules

- Ponytail mode, full: YAGNI → reuse this codebase → stdlib → native feature → installed dependency → one line → minimum working code. Mark deliberate simplifications with `# ponytail: ...`.
- Safety: never delete without confirmation; show impact before acting; secrets only in `.env`; keep the `src/` module structure.
- Planning: 3+ steps → `docs/.internal/agent-workflow/02-todo.md` with `- [ ]`; verify before starting; mark in progress / completed; add a review; capture lessons in `docs/.internal/agent-workflow/03-lessons.md`; stop and re-plan on failure.
- Delegation: codebase search and external docs can go to subagents; use a deeper architecture/debug pass only after 2+ failed fixes; never redo delegated work by hand.
- Verification: never call work done without evidence (relevant tests run, logs checked, before/after diffed). `make test` must exit 0.
- File discipline: no unnecessary files; don't modify outside the task's scope; prefer deleting over adding.
- Communication: terse, lowercase, no em dash, no filler. Code, commits and PRs are written normally.
