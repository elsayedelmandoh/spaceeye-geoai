"""Forward-only, cash-constrained scenario data; not a reconstruction or forecast.

Input: monthly observations available at the configured cutoff and a coded scope.
Output: separate app_data/scenarios history, assumed initial state and scenario paths.
No private truth, future observations, future announcements or future handovers are read.
Opening working cash, zero opening bank debt, credit line and cash release share are
explicit assumptions: financial cover/guarantees are never treated as liquid cash.
"""

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.analysis.ew_features import clean_fin
from src.pipeline.common import APP, BASE_DIR, CFG, REAL

LABEL = "Synthetic - for training only"
SCENARIOS = ("baseline", "collections_drop", "usd_cost_shock", "material_cost_jump")


def available_history(fin: pd.DataFrame, cutoff: str, codes: list[str]) -> pd.DataFrame:
    """Preserve the original observations through cutoff, including logged raw defects."""
    months = pd.PeriodIndex(fin["month"], freq="M")
    return fin.loc[(months <= pd.Period(cutoff, "M")) & fin["code"].isin(codes)].copy().reset_index(drop=True)


def initial_states(history: pd.DataFrame, codes: list[str], settings: dict) -> pd.DataFrame:
    """Use only known monthly rows and supervisor reports actually available at cutoff."""
    cutoff = pd.Period(settings["cutoff"], "M")
    monthly, reports, _ = clean_fin(history)
    states = []
    for code in sorted(codes):
        g = monthly[monthly["code"] == code].sort_values("month")
        if g.empty or g["month"].iloc[-1] != cutoff:
            raise ValueError(f"{code}: missing cutoff observation")
        recent = g[g["month"] > cutoff - int(settings["history_months"])]
        latest = g.iloc[-1]
        rep = reports[(reports["code"] == code) & (reports["report_date"] <= cutoff.end_time)].sort_values("report_date")
        if len(rep):
            progress = float(rep["reported_pct"].iloc[-1])
            progress_basis = "last supervisor report available at cutoff; not physical truth"
        else:
            progress = 0.0
            progress_basis = "assumed zero: no supervisor report available at cutoff"
        progress = float(np.clip(progress, 0, 100))
        collections = float(recent["collections_egp"].clip(lower=0).mean())
        land_due = float(recent["land_due_egp"].clip(lower=0).mean())
        delta = recent["planned_pct"].diff().dropna().clip(lower=0)
        capacity = float(delta.median()) if len(delta) else 0.0
        capacity = float(np.clip(capacity, settings["min_capacity_pct"], settings["max_capacity_pct"]))
        remaining_cost = float(latest["cost_to_complete_egp"])
        if progress < 100 and (not np.isfinite(remaining_cost) or remaining_cost <= 0):
            raise ValueError(f"{code}: no positive known remaining cost for unfinished work")
        total_cost = remaining_cost / (1 - progress / 100) if progress < 100 else 0.0
        values = [progress, collections, land_due, capacity, total_cost]
        if not np.isfinite(values).all():
            raise ValueError(f"{code}: non-finite scenario initial state")
        states.append({
            "code": code, "cutoff": str(cutoff), "initial_progress_pct": progress,
            "progress_basis": progress_basis, "estimated_total_cost_egp": total_cost,
            "baseline_collections_egp": collections, "assumed_land_due_monthly_egp": land_due,
            "capacity_pct_month": capacity,
            "assumed_opening_cash_egp": collections * float(settings["working_cash_months"]),
            "assumed_opening_bank_debt_egp": 0.0,
            "assumed_credit_limit_egp": collections * float(settings["credit_months"]),
            "synthetic_label": LABEL,
        })
    return pd.DataFrame(states)


def _validate_settings(settings: dict) -> None:
    if int(settings["horizon_months"]) <= 0 or int(settings["history_months"]) <= 0:
        raise ValueError("Scenario horizons must be positive")
    for key in ("release_share", "collections_drop", "imported_share"):
        if not 0 <= settings[key] <= 1:
            raise ValueError(f"{key} must lie in [0, 1]")
    for key in ("working_cash_months", "credit_months", "overhead_cost_share_month",
                "annual_credit_rate_pct", "productivity_sd", "usd_cost_rise", "material_cost_rise"):
        if settings[key] < 0 or not np.isfinite(settings[key]):
            raise ValueError(f"{key} must be finite and non-negative")
    if not 0 < settings["min_capacity_pct"] <= settings["max_capacity_pct"] <= 100:
        raise ValueError("Invalid monthly capacity range")
    if int(settings["shock_months"]) <= 0:
        raise ValueError("Shock duration must be positive")


def cost_multiplier_for(scenario_id: str, step: int, settings: dict) -> float:
    """Construction cost multiplier: S1 applies from month 0, S4 from the shock month onward."""
    if scenario_id == "usd_cost_shock":
        return 1 + settings["imported_share"] * settings["usd_cost_rise"]
    if scenario_id == "material_cost_jump" and step >= settings["shock_months"]:
        return 1 + settings["material_cost_rise"]
    return 1.0


def simulate(fin: pd.DataFrame, codes: list[str], settings: dict, seed: int) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Same cutoff state/common productivity draws for every intervention.

    Collections are held at their known trailing mean, not copied from the future.
    A declared share is released as operating cash; the rest stays restricted.
    Due operating costs/land precede construction. Finite credit can cover a cash
    deficit; unpaid obligations carry forward. No future anchor or rescue funding
    forces progress to reach a known date. Debt repayment is outside this model.
    """
    _validate_settings(settings)
    history = available_history(fin, settings["cutoff"], codes)
    states = initial_states(history, codes, settings)
    months = pd.period_range(pd.Period(settings["cutoff"], "M") + 1,
                             periods=int(settings["horizon_months"]), freq="M")
    rows = []
    for state in states.itertuples():
        code_seed = int.from_bytes(hashlib.sha256(state.code.encode()).digest()[:4], "little")
        rng = np.random.default_rng(np.random.SeedSequence([seed, code_seed]))
        sd = float(settings["productivity_sd"])
        productivity = rng.lognormal(-0.5 * sd * sd, sd, len(months))
        for scenario_id in SCENARIOS:
            progress = state.initial_progress_pct
            cash = state.assumed_opening_cash_egp
            debt = state.assumed_opening_bank_debt_egp
            arrears = restricted = 0.0  # unknown historical arrears/escrow are not invented as observations
            limit = state.assumed_credit_limit_egp
            for step, month in enumerate(months):
                cash_open, debt_open, restricted_open, arrears_open = cash, debt, restricted, arrears
                before = progress
                collection_multiplier = (1 - settings["collections_drop"]
                                         if scenario_id == "collections_drop" and step < settings["shock_months"] else 1.0)
                cost_multiplier = cost_multiplier_for(scenario_id, step, settings)
                collections = state.baseline_collections_egp * collection_multiplier
                release = collections * settings["release_share"]
                restricted += collections - release
                capacity = min(100 - progress, state.capacity_pct_month * productivity[step])
                cost_per_point = state.estimated_total_cost_egp / 100 * cost_multiplier
                desired_spend = capacity * cost_per_point
                overhead = (state.estimated_total_cost_egp * settings["overhead_cost_share_month"]
                            if progress < 100 else 0.0)
                interest = debt * settings["annual_credit_rate_pct"] / 1200
                obligations = arrears + overhead + state.assumed_land_due_monthly_egp + interest
                available = cash + release
                draw = min(max(obligations + desired_spend - available, 0.0), max(limit - debt, 0.0))
                debt += draw
                available += draw
                obligations_paid = min(obligations, available)
                available -= obligations_paid
                arrears = obligations - obligations_paid
                spend = min(desired_spend, available)
                cash = available - spend
                gain = spend / cost_per_point if cost_per_point > 0 else 0.0
                progress = min(100.0, progress + gain)
                residual = cash_open + release + draw - obligations_paid - spend - cash
                restricted_residual = restricted_open + collections - release - restricted
                if (abs(residual) > 1e-5 or abs(restricted_residual) > 1e-5 or cash < -1e-6
                        or debt > limit + 1e-6 or spend > desired_spend + 1e-6
                        or progress < before - 1e-9 or progress > 100 + 1e-9):
                    raise AssertionError(f"Scenario accounting failed: {scenario_id}/{state.code}/{month}")
                rows.append({
                    "scenario_id": scenario_id, "code": state.code, "cutoff": settings["cutoff"], "month": str(month),
                    "initial_progress_pct": state.initial_progress_pct, "progress_before_pct": before,
                    "simulated_progress_pct": progress, "capacity_pct": capacity,
                    "gross_collections_egp": collections, "collection_multiplier": collection_multiplier,
                    "cash_released_egp": release, "restricted_cash_egp": restricted,
                    "cost_multiplier": cost_multiplier, "desired_construction_spend_egp": desired_spend,
                    "construction_spend_egp": spend, "opening_cash_egp": cash_open, "closing_cash_egp": cash,
                    "opening_debt_egp": debt_open, "credit_draw_egp": draw, "closing_debt_egp": debt,
                    "credit_limit_egp": limit, "opening_obligation_arrears_egp": arrears_open,
                    "obligations_due_egp": obligations, "obligations_paid_egp": obligations_paid,
                    "obligation_arrears_egp": arrears, "cash_accounting_residual_egp": residual,
                    "restricted_accounting_residual_egp": restricted_residual, "synthetic_label": LABEL,
                })
    return history, states, pd.DataFrame(rows)


def summary(paths: pd.DataFrame) -> pd.DataFrame:
    grouped = paths.sort_values("month").groupby(["scenario_id", "code"], sort=True)
    out = grouped.agg(initial_progress_pct=("initial_progress_pct", "first"),
                      final_progress_pct=("simulated_progress_pct", "last"),
                      gross_collections_egp=("gross_collections_egp", "sum"),
                      construction_spend_egp=("construction_spend_egp", "sum"),
                      final_cash_egp=("closing_cash_egp", "last"),
                      final_debt_egp=("closing_debt_egp", "last"),
                      final_obligation_arrears_egp=("obligation_arrears_egp", "last")).reset_index()
    base = out[out.scenario_id == "baseline"].set_index("code").final_progress_pct
    out["progress_difference_vs_baseline_pp"] = out.final_progress_pct - out.code.map(base)
    out["synthetic_label"] = LABEL
    return out


def _frame_hash(df: pd.DataFrame) -> str:
    return hashlib.sha256(df.to_csv(index=False).encode()).hexdigest()


def main() -> None:
    settings = CFG["generator"]["scenarios"]
    fin = pd.read_parquet(APP / "sim" / "fin_monthly.parquet")
    codes = sorted(pd.read_parquet(REAL / "compounds.parquet").code)
    history, states, paths = simulate(fin, codes, settings, int(CFG["seed"]))
    again = simulate(fin, codes, settings, int(CFG["seed"]))
    if any(_frame_hash(a) != _frame_hash(b) for a, b in zip((history, states, paths), again)):
        raise AssertionError("Scenario reproducibility failed")
    out = APP / "scenarios"
    out.mkdir(parents=True, exist_ok=True)
    from src.generator.simulate import write_parquet
    for name, frame in (("history", history), ("initial_state", states), ("paths", paths)):
        write_parquet(frame, out / f"{name}.parquet")
    summary(paths).to_csv(out / "summary.csv", index=False)
    assumptions = {
        "synthetic_label": LABEL, "settings": settings, "seed": int(CFG["seed"]),
        "purpose": "hypothetical forward cash-constrained scenarios, not observed truth or a calibrated forecast",
        "initial_progress": "last reported_pct with report_date <= cutoff; zero assumed if no report",
        "total_cost": "known cutoff cost_to_complete / remaining reported fraction; estimated, not true cost",
        "liquidity": "opening working cash and credit are assumptions based on past mean collections; zero opening bank debt and obligation arrears assumed",
        "cash_release": "assumed fraction of future collections, remainder restricted; cover_balance/financial guarantees are never liquid cash",
        "future_inputs": "past mean collections/land dues and planned_pct slope; no future rows, announcements, handovers or private truth",
        "scope_limits": "no forecast of handover/occupancy; no historical prior debt/arrears/escrow reconstruction; no credit repayment",
    }
    (out / "assumptions.json").write_text(json.dumps(assumptions, ensure_ascii=False, indent=2), encoding="utf-8")
    provenance = {
        "known_history_sha256": _frame_hash(history),
        "initial_state_sha256": _frame_hash(states), "paths_sha256": _frame_hash(paths),
        "source_code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "feature_cleaning_code_sha256": hashlib.sha256((BASE_DIR / "src" / "analysis" / "ew_features.py").read_bytes()).hexdigest(),
        "config_sha256": hashlib.sha256((BASE_DIR / "configs" / "data.yaml").read_bytes()).hexdigest(),
        "scope_codes": codes, "cutoff": settings["cutoff"], "synthetic_label": LABEL,
    }
    (out / "provenance.json").write_text(json.dumps(provenance, indent=2), encoding="utf-8")
    files = sorted(p for p in out.iterdir() if p.is_file() and p.name != "manifest.csv")
    pd.DataFrame({"file": [p.name for p in files],
                  "sha256": [hashlib.sha256(p.read_bytes()).hexdigest() for p in files]}).to_csv(out / "manifest.csv", index=False)
    print(f"scenarios: {len(codes)} codes, {len(paths)} forward rows, reproducibility/accounting PASS; {out}")


if __name__ == "__main__":
    main()
