# spaceeye-geoai — AGENTS.md (compact, repo-specific)

Repo: smart-city graduation project (`spaceeye-geoai`, synthetic `ACUD_Oasis` dataset). Not operational ACUD data. All outputs must say `Synthetic data — for training only`.

## Would an agent miss this?

- `pyproject.toml`: python>=3.12, `pytest>=8.0.0`, `streamlit`/`fastapi`/`uvicorn`, `duckdb`/`pandera`, `scikit-learn`/`lightgbm`, `plotly`, `google-genai`, `sqlglot`. Package: `src/` (hatch build). `PROJECT_NAME` stale (`base-product`) — source of truth: `src/config/config.py` (`PROJECT_NAME = "spaceeye-geoai"`).
- `.env.example`: `ENV=development`, `MASK_SALT` (never default in prod — `spaceeye-geoai-default-salt-` is dev-only), `GEMINI_API_KEY`, `GEMINI_MODEL=gemini-2.5-flash`. `.env` is gitignored (`.gitignore` includes `.env`) — never commit secrets. Set `.env` before work.
- `Makefile`: `make install` = `uv sync`; `lint` = `ruff check src/ tests/`; `format` = `ruff format src/ tests/`; `test` = `uv run pytest tests/ -v`; `clean` = remove `__pycache__` + `.pytest_cache`. Use `uv`, not `pip`.
- Notebooks: primary workspace. Sequential: `00-quickstart.ipynb` → `01-data-acquisition/` → `02-eda/` → `03-data-preprocessing/` → `04-feature-engineering/` → `05-model-training/` → `06-model-evaluation/` → `07-model-testing/`. Don't skip `01-` before `03-`.
- Source conventions: import globals via `from src.config.settings import *`, helpers via `from src.utils.helper import *`. Never hardcode paths/thresholds — use `settings.py` / `helper.py` (`AGENTS.md` §11 verified in repo).
- `src/config/config.py`: `Settings` loads `.env` via `pydantic-settings`; `BASE_DIR` resolved from `__file__`. `create_required_directories()` bootstraps `data/`, `artifacts/`, `logs/`, `evals/figures/`.
- Dataset: synthetic `ACUD_Oasis` (fictional district, `data/nac-dataset-*`, `data/processed/oasis.duckdb`). Real ACUD data must never appear in outputs. Disclaimer required per `docs/project-definition/05-constraints.md`.
- PII masking (`src/pii_masking.py`): regex-based (not LLM) authority; `MaskConfig()` defaults; `assert_zero_phones()` must return `True` (verified by `tests/test_masking.py`). `MASK_SALT` must change for production.
- Tests (`tests/`): `test_masking.py` enforces exactly 6 `CANONICAL_CATEGORIES`, `SPECIAL_BUILDINGS` = `{"B-0112","B-0240","B-0269"}`, zero unmasked phones, deterministic salted sha-256. `test_app.py`, `test_cleaning.py`, `test_settings.py` exist. `pytest.ini_options` in `pyproject.toml`: `pythonpath=["."]`, `testpaths=["tests"]`.
- `docs/project-definition/07-architecture.md`: does NOT exist (`grep` confirmed absent). Architecture info is in `08-structure.md` and `06-architecture.md`. Planning protocol (`AGENTS.md` §2) uses `docs/.internal/plan/todo.md` and `.internal/plan/lessons.md`.
- `README.md`: renamed to `spaceeye-geoai — Graduation Project`. All synthetic disclaimers updated (`Synthetic data only — for spaceeye-geoai training`).
- `docs/requirements/ACUD-company.md`: merged into `docs/requirements/01-quickinfo.md` (company context + `spaceeye-geoai` company description appended at line 114+); original removed.
- `docs/.internal/agent-workflow/06-system-prompt.md`: agent prompt references ACUD program context; preserved (not rewritten blindly). References dataset names (`ACUD_Oasis`) which are dataset identifiers, not project name — kept.

## Preserved behavioral rules (verified relevant)

- Ponytail mode (`AGENTS.md` §0.5): active, full, no exceptions. Ladder applies: YAGNI → reuse this codebase → stdlib → native feature → installed dependency (`pydantic`, `duckdb`, `pandera`) → one line → minimum working code. `# ponytail: ...` comments for deliberate simplifications.
- Safety (`AGENTS.md` §1): never delete without confirmation; show impact before acting; `.env` secrets only; preserve `src/` module structure (`docs/project-definition/07-architecture.md` missing — don't invent it).
- Planning (`AGENTS.md` §2): 3+ steps → `docs/.internal/plan/todo.md` with `- [ ]`; verify before start; mark `in_progress`/`completed`; add review; capture `lessons.md`; stop and re-plan on failure.
- Subagent delegation (`AGENTS.md` §3): `explore` for codebase, `librarian` for external docs, `oracle` for architecture/debug (only after 2+ failed fixes), `metis` for ambiguous scope, `momus` for plan review. Always `run_in_background=true`; never redo delegated work manually.
- Verification (`AGENTS.md` §4): never complete without evidence — [ ] relevant tests, [ ] logs checked, [ ] before/after diffed, [ ] staff-engineer check. `lsp_diagnostics` after file edits; build/test exit 0 required.
- File discipline (`AGENTS.md` §7): no unnecessary files; don't modify outside scope; delete over add.
- Communication (`AGENTS.md` §9): terse, lowercase, no em dash (`—`), no filler; code/commits/PRs written normally.
- Environment (`AGENTS.md` §10): `.env` from `.env.example`; `conda` env `python=3.12`; `uv sync`; activate before work; `.env` never committed.
