# spaceeye-geoai: AGENTS.md (compact, repo-specific)

SpaceEye: R7 digital twin and inspection priority observatory (New Administrative Capital graduation project). Ranks R7 compounds by priority level for the inspection committee. Real public data (satellites, statements) in Track A; generated stand-in ACUD data in Track B, always labelled `Synthetic - for training only`.

**Source of truth:** `docs/requirements/01-specs.md` + `docs/project-definition/03-dataset.md`. They win over every other doc (`docs/project-definition/08-structure.md` and `docs/.internal/archive/*` describe older designs). `CLAUDE.md` has the architecture summary.

## Would an agent miss this?

- `pyproject.toml`: package `spaceeye-geoai`, python>=3.12, hatch build of `src/`. Dev tools (pytest, ruff, nbstripout) are a `[dependency-groups]` group, so plain `uv sync` installs them. Earth Engine is the `pulls` extra (`uv sync --extra pulls`). Use `uv`, not pip.
- `Makefile`: `install` = `uv sync` + nbstripout hook; `lint` / `format` = ruff on `src/ tests/`; `test` = `uv run pytest tests/ -v`. One test: `uv run pytest tests/test_pipeline.py::<name> -v`.
- Entry points, in order: `python -m src.pipeline.run_all` (Track A, exit 1 on a STOP gate) → `python -m src.generator.simulate` (Track B data) → `python -m src.analysis.early_warning`. `app.py` is a placeholder; the Streamlit dashboard is not built yet.
- Data is outside the repo: `configs/data.yaml` `paths:` (`real_data` read only, `app_data`, `private`). Currently Windows `F:/...` paths. Nothing from `app_data/` or `private/` is committed. Tests needing built data are skipped when it is missing.
- All thresholds, seed, `computed_on` and source file names live in `configs/data.yaml`, read via `CFG` / `src()` in `src/pipeline/common.py`. Quarter index 0 = 2016Q1 (`qindex`, `qlabel`, `qend`). Thresholds are frozen: never change one after seeing a result.
- `.env` (from `.env.example`, gitignored): `MASK_SALT` (change for production), `GEMINI_API_KEY`, `GEMINI_MODEL`. Loaded by `src/config/config.py` `settings`.
- Tests: `tests/test_pipeline.py` (quarter helpers, worst-of-signals level, K2 start rule, first promise never resets, name gate), `tests/test_generator.py` (generator math, phone masking pattern), `tests/test_early_warning.py` (top-N ties, no data after cutoff).
- `src/models`, `src/inference`, `src/evaluation`, `src/utils` are mostly template stubs.

## Rules that never break (specs section 14)

- No compound or developer name in any output or log: codes only (`C..`, `D..`). The `no_names` gate stops the run. Names live only in `private/code_map.csv`.
- Never join a generated column into a real table (`separation` gate). Every number has an origin: real, derived or generated. Generated numbers only in Track B, never on a map.
- No leakage: statements filtered by `published_date`; features never read `answer_key`.
- Wording: "priority level", never "risk level"; no "distressed", "completion %" or "finishing %" about a real compound.
- Scope is R7 only. "Digital twin" = light compound-level twin with what-if, never 3D or real-time.
- Two runs must be identical: no `now()`, no unseeded randomness.

## Preserved behavioral rules

- Ponytail mode: active, full. Ladder: YAGNI → reuse this codebase → stdlib → native feature → installed dependency → one line → minimum working code. `# ponytail: ...` comments for deliberate simplifications.
- Safety: never delete without confirmation; show impact before acting; secrets only in `.env`; preserve the `src/` module structure.
- Planning: 3+ steps → `docs/.internal/agent-workflow/02-todo.md` with `- [ ]`; verify before start; mark in progress / completed; add a review; capture lessons in `docs/.internal/agent-workflow/03-lessons.md`; stop and re-plan on failure.
- Subagent delegation: `explore` for codebase, `librarian` for external docs, `oracle` for architecture/debug (only after 2+ failed fixes), `metis` for ambiguous scope, `momus` for plan review. Always `run_in_background=true`; never redo delegated work manually.
- Verification: never complete without evidence (relevant tests, logs checked, before/after diffed, staff-engineer check). Build/test exit 0 required.
- File discipline: no unnecessary files; don't modify outside scope; delete over add.
- Communication: terse, lowercase, no em dash, no filler; code/commits/PRs written normally.
- Code style: module docstring `propose: / input: / output:`; lowercase comments; test names are full sentences.
