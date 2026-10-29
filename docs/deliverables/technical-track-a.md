# Track A technical guide and monitoring plan

Task T-AH-20. Current prepared-data scope: 12 coded R7 compounds, through 2026Q3. This guide documents existing behavior; it does not certify future refreshes or product completion.

## Flow and rules

Configured public-source caches feed compound boundaries/register, published statements, quarterly satellite observations and annual vegetation/height. `src/pipeline/kpis.py` derives activity, K2–K6, priorities, English reasons and the capacity-limited cycle list. Quality gates determine whether delivery may proceed. Publication dates limit what is known at each historical cutoff.

Separate observed start requires four assessable active quarters or published delivery. Legacy start remains for K2 comparability. K6 uses the first known launch/promise publication, with thresholds 13–24 and above 24 months; insufficient evidence stays null. K5 is a union of screening months, not a legal finding. Priorities use the worst applicable signal, the completion cap and data assessability. Capacity 4 selects eligible levels 1–3 by level, descending K2, descending K3, then code. Height is context only: OBT 2016–2023 and approved v4 estimate for 2024; later annual heights remain unknown.

Generated finance, complaints, fine assumptions and forward scenarios stay separate from public observations. The financial-priority scenarios are hypothetical. Read the [implemented specification](../../data/IMPLEMENTED_DATA_SPEC.md) and [dataset contract](../../data/DATASET_CONTRACT.md) for field definitions and limits.

## Run with existing configured inputs

```powershell
uv sync --locked
uv run --locked --offline python -m src.pipeline.complete_data
uv run --locked --offline python -m src.pipeline.component_data
uv run --locked --offline python -m src.pipeline.source_catalog
uv run --locked --offline python -m src.pipeline.quality_report
```

If Make is installed, `make data` executes those four preparation steps without fitting. `make current` runs `python -m src.pipeline.team_run`, including the current small model diagnostics. `make run` runs `python -m src.pipeline.team_run --full`, first rebuilding/fitting Track A. All need external caches/private inputs configured in `configs/data.yaml`; none downloads new satellite imagery. Teammates using the ready-data ZIP do not need these source inputs or commands.

`uv run --locked --offline python -m src.pipeline.delivery` separately compares two base data-only builds and protects raw/model/historical-evaluation files. Its saved evidence covers that scoped build, not every later component artifact. `src.pipeline.full_repro` backs up current local outputs then compares two full Track A runs; [saved evidence](../../data/FULL_TRACK_A_REPRODUCIBILITY.json) records equal manifests for 276 artifacts. `src.pipeline.release` remains the historical experiment workflow; use `team_run` for the current schema.

## Quarterly monitoring procedure

Proposed accountable operator: Track A owner; reviewer: another team member. These are operating responsibilities, not signed assignments.

1. Open a feature branch; preserve the last accepted bundle and input hashes. Update source observations and publication evidence before advancing cutoff/computation dates in configuration. Cache refresh requires the original source workflow.
2. Keep thresholds and capacity fixed unless a reviewed decision changes them. Recheck R7 scope and boundary provenance, source dates, missing observations and approved height products. New quarters must be supported by actual inputs.
3. Run the preparation steps, inspect the current audit and render the quality report. Resolve STOP/FIX. Document an explicit review decision for every FLAG, including the existing 2019Q2 flag. Never fill missing physical measurements with invented observations.
4. Run relevant tests. If behavior changed, run the two-build delivery check. Separately verify new component outputs and bundle integrity; a prior manifest does not certify new files.
5. Review changes in priorities/reasons against source evidence. Inspect a sample of publication cutoffs and confirm that generated data has not entered public maps or the real backtest.
6. Publish a reviewed versioned bundle through a feature branch/PR. Record cutoff, code revision, source hashes, limits and reviewer. Keep prior releases available for comparison.

If source coverage fails, mark affected observations not assessable and review. A production-ready automatic K1 fallback switch has not been established. No monitoring schedule, dashboard, field collection service or deployment is implied by this document.
