# SpaceEye handover: start here

Task T-AH-21. Prepared data is available. The dashboard and inspection agent remain unfinished; independent real-world predictive validation remains future work.

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

The extended ML data has 180 rows and 40 features. For generated Track B data, the approved classifier is binary distressed/not_distressed; use its normalized probabilities and current evaluation report. Use the current capacity-4 report; older experiment results do not validate the present schema. Annual heights after 2024 are not approved measurements; an older height carried into a feature is still an older value.

## Continue development

Work on a feature branch and PR; never commit directly to main. Use the configured human Git identity. See [technical operations](technical-track-a.md), [data handoff](../../data/HANDOFF.md), [sources and generation](../../data/DATA_SOURCES_AND_GENERATION.md) and [current task closure](../../data/PARTIAL_TASKS_CLOSURE.md). For source rebuilding, configure local paths and run `uv sync --locked`; the prepared bundle alone cannot reproduce private/source ingestion.

Current run: `make current` (or `uv run --locked --offline python -m src.pipeline.team_run`); add `--full` / `make run` to refit Track A. Tests: `uv run --locked --offline pytest -q`. On WSL, mount F: at `/mnt/f` first (`sudo mkdir -p /mnt/f && sudo mount -t drvfs F: /mnt/f`).

Route data/rule questions to Track A, generator/model questions to Track B, agent questions to the AI owner and interface questions to the dashboard owner. Named reviewer acceptance, final presentation and live deployment are not recorded by this handover.

## Use it in another district

Only R7 has been run. No transfer is proven; this is the path, not a result.

What a new district needs, in order:

1. **Coded boundaries.** One reviewed working polygon per compound in the boundaries file (`configs/data.yaml` `sources.boundaries`), with the code-to-name map kept by the custodian outside `data/`.
2. **Published statements with dates.** Launch, promised dates, progress claims and handover events, each with its publication date, so the clock can be frozen at any past quarter.
3. **Quarterly satellite windows for the new plots.** The same source workflow as R7 (Dynamic World and Sentinel-2 windows); refreshing the cache is a separate operation (`docs/REVIEW_SETUP.md`, section 5).
4. **Configuration.** Add the district to `scope_districts` and set `cycle_capacity` (R7 uses 12 compounds / 3 = 4). Thresholds and the level order stay as they are unless a reviewed decision changes them.
5. **Checks before use.** The activity score A must pass its acceptance tests on the new plots (`configs/data.yaml` `activity`); if not, use `source: k1`. The quality gates must pass. Collect the district's public late cases and run the frozen-clock backtest before trusting the list there.

Nothing in the code is tied to R7 except the scope setting and the data; the effort is in steps 1 to 3. A dry run on another district was not done: the source caches for other districts are not in this checkout.
