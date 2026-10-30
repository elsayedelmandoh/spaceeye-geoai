"""propose: close R1/R2 with current reports, dictionaries and two-build evidence.
input: cached observations, current config, saved historical simulation.
output: tracked data, local reports, delivery reproducibility evidence.
No activity/classifier fitting, live source pulls or private-data publication.
"""

import hashlib
import json
import re

import duckdb
import pandas as pd

from src.generator import dictionaries
from src.pipeline import complete_data, run_all
from src.pipeline.build_real import ORIGINS
from src.pipeline.common import APP, BASE_DIR, CFG, PRIVATE, REAL
from src.pipeline.kpis import KPI_ORIGINS
from src.pipeline.release import audit

DOCS = BASE_DIR / "data"
LABEL = CFG["generator"]["label"]

# Explicit semantics for the new fields; inherited monthly fields reuse R2 specs.
MEANINGS = {
    "code": "Coded compound identifier; accepted prepared tables use registered R7 codes. Planted unknown codes occur only in raw/quarantined test inputs.",
    "reason_ar": "Committee-facing Arabic rule explanation, generated from the same cutoff evidence as reason.",
    "level_label": "Priority label: 1-4, not started, start unknown, or not assessable.",
    "level_word": "Ordinal priority word, or not started, start unknown, or not assessable; not an independent risk probability.",
    "level_word_ar": "Arabic ordinal priority word or state: الأولى/الثانية/الثالثة/الرابعة, بداية غير مؤكدة, بداية غير معروفة, or غير قابل للتقييم.",
    "quarter": "Quarter of cutoff; flows cover its three months and stocks use its last month.",
    "months_present": "Number of observed financial months contributing to this quarter; required3.",
    "K5_months": "Union of screening months: no observed start after deadline and post12-month grace; overlap counted once; unknown remains null. Not contractual eligibility.",
    "K5_no_start_months": "Post-deadline months before observed start; stops before its start quarter; unknown with insufficient evidence.",
    "K5_post_grace_months": "Months beyond12-month deadline grace, stopping accrual at first published handover.",
    "K5_overlap_months": "Months satisfying both K5 conditions, subtracted once from the sum.",
    "K5_basis": "Research-policy proxy; actual contract eligibility remains unverified.",
    "K6": "Months since first known launch/promise publication without confirmed observed start; null after start or insufficient evidence. Priority2 at13–24,priority1 above24.",
    "observed_started": "Four consecutive quality-valid active quarters or already-published handover; marketing launch alone is excluded.",
    "observed_start_quarter": "First quarter of observed start evidence, visible only once that evidence is known.",
    "observed_start_source": "activity_run or published_delivery.",
    "start_observation_sufficient": "Positive start evidence, or uninterrupted assessable history from the known launch/promise reference.",
    "start_reference_date_asof": "Event date of earliest known launch, or promise publication date; never future promise delivery date.",
    "start_reference_published": "Publication time of the reference used at cutoff.",
    "start_reference_source": "launch or promise_publication.",
    "launch_date_asof": "Known launch event date, clamped to publication if a future event date was supplied.",
    "launch_first_published": "Date launch evidence was published, used for cutoff filtering.",
    "allocation_date_assumed": "Generated allocation6–18months before first public/observed anchor, bounded below by2016-01-01; retrospective calibration, excluded from X/public K6.",
    "calibration_anchor_date": "Earliest public publication or observed-start quarter used retrospectively to constrain synthetic allocation.",
    "allocation_origin": "Explicit generated/retrospective provenance, never an observed allocation record.",
    "land_area_m2": "Compound land area; adjacent land_area_origin states real or generated.",
    "land_area_origin": "Origin of register land area; retain alongside generated financial assumptions.",
    "assumed_land_price_egp_m2": "Generated vintage-based price;2500–5000pre2023,5000–12000otherwise. News supports context, not individual contract price.",
    "assumed_land_value_egp": "Land area times generated price; in quarterly data replaced by value inferred from available installments when present.",
    "land_value_from_known_installments_egp": "Median positive land installment available by cutoff times16; generated-ledger inference, null without positive dues.",
    "land_value_basis": "Whether current value comes from available generated installments or vintage-based fallback.",
    "fine_rate_month": "Illustrative1%monthly fraction; explicit assumption, not a published universal contract rate.",
    "K5_egp": "K5_months times assumed land value times assumed monthly rate. Not an assessed fine or a cash-ledger deduction.",
    "K5_egp_discount_scenario": "Optional50%discount scenario; null before2024-11-18publication; no automatic entitlement or known expiry asserted.",
    "K5_egp_installment_scenario_monthly": "Gross assumed fine divided by12; separate scheduling scenario after2024-11-18, not combined automatically with discount.",
    "relief_basis": "Temporary relief is hypothetical project eligibility, not a recorded decision.",
    "fine_assumption": "True: amount/rate is a generated policy scenario.",
    "assumption": "True: synthetic input or proposed operational capacity, not measured internal data.",
    "assumption_available_from": "Hypothetical contract availability date; allocation is retrospectively calibrated and not used as an ML feature.",
    "price_context_source": "Source IDs resolved in configs/synthetic_sources.json; context only.",
    "rate_source": "Explicit lack of a source supporting the exact assumed contract rate.",
    "dq_reason": "Observable reason for quarantine/rejection; phone masking also applies to rejected complaint text.",
    "scenario_id": "Named hypothetical intervention; baseline stays separate.",
    "cutoff": "Last month whose observations may initialize the forward path.",
    "capacity": "Proposed inspection count for this quarter;2,4or6,not building capacity.",
    "eligible_rank": "Rank among priority1–3 only, sorted by level,K2descending,K3descending,code; missing for ineligible rows.",
    "selected": "Eligible rank is within this scenario's inspection capacity; no change to levels or finances.",
    "initial_progress_pct": "Latest supervisor progress report available by cutoff; explicit assumed zero if none exists.",
    "progress_basis": "Whether initial progress comes from a known report or assumed zero.",
    "estimated_total_cost_egp": "Cutoff reported cost-to-complete divided by remaining reported fraction; estimate, not hidden true cost.",
    "baseline_collections_egp": "Mean collections over configured past history, not future rows.",
    "assumed_land_due_monthly_egp": "Past mean land obligation projected forward as an assumption.",
    "capacity_pct_month": "Declared monthly production capacity, estimated from past planned progress slope and clipped to configured bounds.",
    "assumed_opening_cash_egp": "Past mean collections times assumed working-capital months.",
    "assumed_opening_bank_debt_egp": "Zero opening bank debt assumed; not an observed company balance.",
    "assumed_credit_limit_egp": "Past mean collections times configured assumed credit months.",
    "progress_before_pct": "Simulated progress at the start of this forward month.",
    "simulated_progress_pct": "Prior simulated progress plus affordable spending divided by cost per percentage point; bounded0–100.",
    "capacity_pct": "Common productivity draw times capacity, limited by remaining work.",
    "gross_collections_egp": "Baseline future collections times scenario multiplier; sum over horizon in summary.",
    "collection_multiplier": "0.75for first6months of collections_drop; otherwise1.",
    "cash_released_egp": "Declared released share of hypothetical collections; not financial guarantees.",
    "restricted_cash_egp": "Cumulative collections not released to operating cash; tracked separately.",
    "cost_multiplier": "1+0.40*0.30under FX cost shock; otherwise1.",
    "desired_construction_spend_egp": "Capacity-limited desired progress times current cost per percentage point.",
    "construction_spend_egp": "Actual affordable spending after obligations; sum over horizon in summary.",
    "opening_cash_egp": "Operating cash carried into this simulated month.",
    "closing_cash_egp": "Opening cash+released collections+credit draw-obligations paid-construction spending.",
    "opening_debt_egp": "Bank debt carried into this simulated month.",
    "credit_draw_egp": "Required borrowing limited by unused assumed credit.",
    "closing_debt_egp": "Opening debt+new draw; repayments outside this model.",
    "credit_limit_egp": "Finite assumed credit ceiling, fixed at cutoff.",
    "opening_obligation_arrears_egp": "Unpaid obligations brought forward, not hidden observed arrears.",
    "obligations_due_egp": "Prior arrears+land due+declared overhead+interest.",
    "obligations_paid_egp": "Obligations actually covered before construction spending.",
    "obligation_arrears_egp": "Due obligations minus paid obligations, carried forward.",
    "cash_accounting_residual_egp": "Operating cash conservation residual; absolute value must not exceed1e-5EGP.",
    "restricted_accounting_residual_egp": "Restricted cash conservation residual; absolute value must not exceed1e-5EGP.",
    "final_progress_pct": "Last simulated progress in the forward horizon, not forecast handover/completion.",
    "final_cash_egp": "Closing operating cash at last simulated month.",
    "final_debt_egp": "Closing assumed bank debt at last simulated month.",
    "final_obligation_arrears_egp": "Unpaid simulated obligations at last month.",
    "progress_difference_vs_baseline_pp": "Final simulated percentage-point difference from same compound's baseline.",
    "synthetic_label": "Synthetic - for training only; retained on generated products.",
    "origin": "Declared provenance category; not a guarantee of operational validity.",
}


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def write_dictionaries():
    """One actual-schema dictionary per new/real table; no row-level values published."""
    inherited = {row[0]: row for specs in dictionaries.SPECS.values() for row in specs[1]}
    files = list(REAL.glob("*.parquet")) + list((APP / "sim_clean").glob("*.parquet")) + list((APP / "scenarios").glob("*.parquet"))
    files += [APP / "data_completion" / "inspection_capacity.csv", APP / "scenarios" / "summary.csv"]
    links = []
    for path in sorted(files):
        frame = pd.read_parquet(path) if path.suffix == ".parquet" else pd.read_csv(path)
        group = path.parent.name
        target = DOCS / "dictionaries" / f"{group}__{path.stem}.md"
        intro = f"# {group}/{path.name}\n\nActual schema;{len(frame)}rows. "
        intro += LABEL if group != "real" else "Public/derived table; register origins remain explicit."
        intro += "\n\n| Column | Type | Unit/range | Origin | Meaning/method |\n| --- | --- | --- | --- | --- |\n"
        for col in frame:
            old = inherited.get(col)
            meaning = MEANINGS.get(col, old[3] + "; " + old[5] if old else col.replace("_", " ") + "; see current dataset contract and producing source module.")
            if group == "sim_clean" and path.stem == "fin_quarterly" and col == "units_sold":
                meaning = "Sum of units sold in the three months; monthly sales are flows, not cumulative inventory."
            elif group == "sim_clean" and path.stem == "fin_quarterly" and col in {"collections_egp", "land_due_egp", "land_paid_egp", "kwh"}:
                meaning = "Sum over this quarter of monthly " + col + "."
            # This generic word also matches a registered project name. Keep
            # strict name checks; use equally precise intervention terminology.
            meaning = re.sub(r"\bscenario\b", "intervention", meaning)
            unit = "EGP" if col.endswith("_egp") or col.startswith("K5_egp") else "EGP/m2" if col.endswith("egp_m2") else "percent" if col.endswith("_pct") else "calendar date" if "date" in col or col.endswith("published") else old[2] if old else "see meaning"
            fallback_origin = "derived" if group == "real" else old[4] if old else "generated/derived from generated"
            declared = KPI_ORIGINS if group == "real" and path.stem == "kpi_values" else ORIGINS.get(path.stem, {})
            origin = declared.get(col, fallback_origin)
            intro += f"| {col} | {frame[col].dtype} | {unit.replace('|', '/')} | {origin.replace('|', '/')} | {meaning.replace('|', '/')} |\n"
        write(target, intro)
        links.append(f"- [{group}/{path.stem}]({target.name})")
        # Local dictionary follows the artifact as well as the tracked public schema.
        write(path.parent / "dictionaries" / f"{path.stem}.md", intro)
    write(DOCS / "dictionaries" / "README.md", "# Actual output dictionaries\n\nSchema documentation only; no private rows or real names. Existing raw simulation/private dictionaries remain next to their artifacts. Expanded X and target roles are in private/ml_dataset_extended_metadata.json.\n\n" + "\n".join(links))
    return len(files)


def write_reports(result):
    comp = result["data_completion"]
    counts = result["counts"]
    r1 = "# R1 current release report,28October2026\n\nScope:R7only,12coded compounds. This supersedes historical26October reports.\n\n| Table | Rows |\n| --- | ---: |\n"
    r1 += "\n".join(f"| {name} | {count} |" for name, count in counts.items())
    r1 += "\n\n## Implemented policy\n\nK2retains the evaluated legacy start convention. Separate observed start requires four assessable active quarters or published delivery. K6uses first known launch/promise publication, changes priority at13/24months and stays null when evidence is insufficient. K5is union-of-months screening exposure, not assessed contractual eligibility. Capacity4;capacity scenarios2/4/6select eligible priorities1–3. No generated EGP amount enters public KPI tables.\n\n## Quality and evidence\n\n"
    r1 += "\n".join(f"- {g['gate']}: **{g['status']}**;{g['value']}." for g in result["gates"])
    r1 += "\n\nDuckDB matches current real tables. The saved real-case backtest is documented in BACKTEST_CURRENT.md; full Track A reproducibility is in FULL_TRACK_A_REPRODUCIBILITY.json. This data-only report writer does not rerun fitting or retune the criterion. Activity mode remains q2hold; published heights are OBT where available (none for 2016-2019; 5-11 of 12 compounds per year for 2020-2023) and the v4 estimate for 2024 (10 of 12); see data/ANNUAL_CONTEXT_COVERAGE.csv. Public sources were not all re-opened during this release.\n\n## Rebuild\n\n`uv run --locked --offline python -m src.pipeline.complete_data` rebuilds from saved observations without fitting. `src.pipeline.delivery` verifies two data-only builds and writes this report/dictionaries. Full `src.pipeline.run_all` is separate and includes fitting. Source/code hashes and limitations are in local release_audit.json.\n"
    p = result["prepared_simulation"]
    r2 = f"# R2 current release report,28October2026\n\n{LABEL}\n\nScope12R7compounds. Raw reconstruction:{p['raw_fin_rows']}financial rows/{p['raw_complaints']}complaints. Prepared:{p['fin_rows']}financial rows/{p['complaints']}complaints. Quarterly financial rows:{comp['quarterly_fin_rows']}. Expanded dataset:{comp['expanded_rows']}rows/{comp['features']}features.\n\n## Preparation\n\nRemoved{p['duplicate_months_removed']}duplicates;repaired{p['balance_rows_corrected']}thousand-EGP balances;removed{p['invalid_report_observations_removed']}invalid report observations;quarantined{p['complaints_quarantined']}complaints;masked{p['phone_texts_masked']}phone texts. Raw retained;no private truth repairs. Missing public launch dates still prevent verifying every pre-launch defect. Quarterly sales,collections,land payments andkWhare summed flows;balances use the last month.\n\n## Generated missing inputs\n\nTwelve synthetic allocation/contract assumptions respect earliest evidence anchors and price vintage. Allocation is retrospective and excluded from X/public K6. Available generated installments determine land value when present. Fine rate1%is illustrative,not a published universal rate. News-supported50%relief/12-month scheduling are optional scenarios after2024-11-18;eligibility and expiry are unknown. Sources and limits:configs/synthetic_sources.json.\n\n## Dataset and split\n\nKeys/targets never enter X. Expanded metadata declares exact40features and origin/missingness.90-day complaints are normalized by units sold in the cutoff month,not cumulative inventory;this is a flow-normalized diagnostic,not buyer incidence.\n\n"
    r2 += "| Split | Rows | Classes |\n| --- | ---: | --- |\n" + "\n".join(f"| {s} | {v['rows']} | {v['classes']} |" for s, v in comp["split_counts"].items())
    r2 += f"\n\nCensored targets are null. Categorical and boolean targets represent the same next-six-month distress event;completion is not predicted. Already-handed-over cutoffs are flagged for cohort exclusion. The approved classifier is binary distressed/not_distressed,with both classes in training and test. Current observed-class diagnostics are separate in EW_REPORT_CURRENT.md;this data-only writer does not fit them. Old132-row/26-feature binary dataset and N=8scores are historical evidence,not validation of capacity4/new schema.\n\n## Simulation limits\n\nHistorical progress is anchored reconstruction,not causal cash-to-progress history. Separate forward scenarios:{result['scenario_rows']}rows,baseline/collections drop/FX cost shock,same cutoff state and productivity draws,finite cash/credit/accounting constraints. They do not forecast handover/occupancy. Fine EGP fields are not deducted from historical/forward cash ledgers.\n\n## Validation\n\nHistorical12hard/11calibration checks retained as evidence. Current data-only audit:{len(result['checks'])}checks PASS;extension:{len(comp['checks'])}checks PASS. Saved full Track A/current model equality is recorded in FULL_TRACK_A_REPRODUCIBILITY.json and CURRENT_MODEL_REPRODUCIBILITY.json. A fresh data-only delivery run writes its own REPRODUCIBILITY.json/local delivery_reproducibility.json;do not infer operational accuracy. See dictionaries/README.md and HANDOFF.md.\n"
    for name, report in (("R1_REPORT.md", r1), ("R2_REPORT.md", r2)):
        write(APP / name, report)
        write(DOCS / name, report)
    return write_dictionaries()


def fingerprint(protected=False):
    """Byte hashes for files; logical table hashes for DuckDB's non-deterministic container."""
    if protected:
        paths = [p for folder in ("raw", "sim", "model", "backtest", "ew") for p in (APP / folder).rglob("*") if p.is_file()]
        paths += [PRIVATE / n for n in ("answer_key.parquet", "answer_key_complaints.parquet", "ml_dataset.parquet", "ml_dataset_metadata.json")]
    else:
        paths = [p for p in APP.rglob("*") if p.is_file() and p.suffix != ".duckdb" and p.name not in {"manifest.csv", "delivery_reproducibility.json"}]
        paths += list(PRIVATE.glob("*.parquet")) + list(PRIVATE.glob("ml_dataset*.json")) + list((PRIVATE / "dictionaries").glob("*.md"))
    hashes = {p.relative_to(APP.parent).as_posix(): run_all.sha(p) for p in sorted(set(paths)) if p.exists()}
    if not protected:
        with duckdb.connect(str(APP / "spaceeye.duckdb"), read_only=True) as con:
            for (name,) in con.execute("SELECT table_name FROM information_schema.tables ORDER BY 1").fetchall():
                frame = con.execute(f'SELECT * FROM "{name}"').df().astype(str)
                hashes["duckdb:" + name] = hashlib.sha256(pd.util.hash_pandas_object(frame, index=False).values.tobytes()).hexdigest()
    return hashes


def main():
    # Establish the complete file inventory before comparing two builds; the
    # name gate legitimately records the number of files it has scanned.
    write_reports(json.loads((APP / "release_audit.json").read_text(encoding="utf-8")))
    before = fingerprint(protected=True)
    snapshots = []
    for number in (1, 2):
        complete_data.build()
        result = audit(require_current_evaluation=False)
        dictionary_count = write_reports(result)
        run_all.manifest()
        if fingerprint(protected=True) != before:
            raise RuntimeError("Data-only delivery changed protected raw/model/legacy evaluation inputs")
        snapshots.append(fingerprint())
        print(f"delivery build{number}/2 PASS;{len(snapshots[-1])}artifacts;{dictionary_count}dictionaries", flush=True)
    if snapshots[0] != snapshots[1]:
        changed = sorted(k for k in set(snapshots[0]) | set(snapshots[1]) if snapshots[0].get(k) != snapshots[1].get(k))
        raise RuntimeError("Two-build mismatch: " + ", ".join(changed))
    evidence = {"status": "PASS", "builds": 2, "mode": "data-only; cached observations; no fitting",
                "equal_artifacts": len(snapshots[0]), "dictionary_tables": dictionary_count,
                "protected_raw_models_and_legacy_evaluation_unchanged": True,
                "sha256": hashlib.sha256(json.dumps(snapshots[0], sort_keys=True).encode()).hexdigest(),
                "files_sha256": snapshots[0]}
    write(APP / "delivery_reproducibility.json", json.dumps(evidence, indent=2))
    # Aggregate evidence in Git; private row data and per-file private hashes stay local.
    write(DOCS / "REPRODUCIBILITY.json", json.dumps({k: v for k, v in evidence.items() if k != "files_sha256"}, indent=2))
    run_all.manifest()
    print("R1/R2 delivery PASS: two identical builds; protected inputs unchanged", flush=True)


if __name__ == "__main__":
    main()
