# SpaceEye handover: start here

Task T-AH-21. Prepared data is available. The dashboard and the inspection agent are implemented and their review is pending; independent real-world predictive validation remains future work.

## Use the data

Download the current ZIP from [ready-data](../../releases/ready-data/README.md), extract it and follow [DATA_GUIDE](../../releases/ready-data/DATA_GUIDE.md). The bundle provides DuckDB, Parquet, CSV, inspection JSON contexts, dictionaries, examples and an integrity verifier. Use coded identifiers as join keys. Keep the original ZIP and verify it before editing copies.

| Need | Starting point |
| --- | --- |
| Public/derived indicators and geometry | Bundle real tables and coded boundaries; read their dictionaries |
| Generated finances, complaints and fines | Prepared operations tables; retain `Synthetic - for training only` |
| Train a model | Separate ML export, declared feature list, targets, censoring and time split |
| Build the inspection agent | Inspection contexts; images are explicitly absent |
| Train complaint classification | Choose one supplied corpus and keep its predefined splits; do not merge corpora |
| Prototype visits / what-if | Explicitly synthetic visits and hypothetical priority tables |

## Rules that must survive the handover

Scope is 12 R7 codes. Capacity is 4. Unknown values stay null. Join on the complete declared key, including quarter/month. Public statements require publication-date cutoffs. Keys, private truth, labels and post-cutoff observations never enter model X. Keep generated results distinct from real observations. Do not publish name mappings or private answer keys.

The extended ML data has 180 rows and 40 features. The approved classifier is binary distressed/not_distressed; use its normalized probabilities and current evaluation report. Use the current capacity-4 report; older experiment results do not validate the present schema. Annual heights after 2024 are not approved measurements; an older height carried into a feature is still an older value.

## Continue development

Work on a feature branch and PR; never commit directly to main. Use the configured human Git identity. See [technical operations](technical-track-a.md), [data handoff](../../data/HANDOFF.md), [sources and generation](../../data/DATA_SOURCES_AND_GENERATION.md) and [current task closure](../../data/PARTIAL_TASKS_CLOSURE.md). For source rebuilding, configure local paths and run `uv sync --locked`; the prepared bundle alone cannot reproduce private/source ingestion.

Current run: `make current` (or `uv run --locked --offline python -m src.pipeline.team_run`); add `--full` / `make run` to refit Track A. Tests: `uv run --locked --offline pytest -q`. On WSL, mount F: at `/mnt/f` first (`sudo mkdir -p /mnt/f && sudo mount -t drvfs F: /mnt/f`).

Route data/rule questions to Track A, generator/model questions to Track B, agent questions to the AI owner and interface questions to the dashboard owner. Named reviewer acceptance, final presentation and live deployment are not recorded by this handover.
