# Current configuration

Paths in `data.yaml` are resolved relative to the repository root. Default data is under sibling `../Project/`; set `SPACEEYE_DATA_ROOT` before a command to relocate `real_data/`, `app_data/` and `private/` together. See [device/review setup](../docs/REVIEW_SETUP.md). Live satellite refreshes use your own `SPACEEYE_EE_PROJECT`.

configs/data.yaml defines source/output paths, R7 scope, fixed seeds, indicator thresholds, capacity and generator assumptions. configs/synthetic_sources.json records source-supported context and unsupported exact assumptions. The current binary evaluation protocol records its fixed parameters in data/EW_PROTOCOL_CURRENT.md.

Unrelated energy/water KPI examples and unused default configuration were retired. Construction KPI cards/configuration and EGP-value assumptions remain T-SA-02/T-SA-03; create their project-specific outputs when those tasks are implemented. Do not restore utility-demo values as current SpaceEye settings.
