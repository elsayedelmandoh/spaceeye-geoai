"""Replay Track A case counts from the published prepared inputs, without local data drives."""

import argparse
import hashlib
import json
from io import StringIO
from pathlib import Path

import pandas as pd

from src.pipeline import backtest_check
from src.pipeline.common import BASE_DIR, CFG

INPUTS = BASE_DIR / "releases/ready-data/backtest"


def replay(inputs: Path, output: Path) -> dict:
    inputs, output = inputs.resolve(), output.resolve()
    if output == inputs or inputs in output.parents or output in inputs.parents:
        raise ValueError("Choose an output directory separate from the published inputs")
    manifest = json.loads((inputs / "manifest.json").read_text(encoding="utf-8"))
    for name, expected in manifest["files"].items():
        if Path(name).name != name:
            raise ValueError("Manifest entries must be filenames")
        actual = hashlib.sha256((inputs / name).read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(f"Published file changed: {name}")
    for key, actual in (("backtest_config", CFG["backtest"]),
                        ("levels_config", CFG["levels"]), ("asof", CFG["asof"])):
        if manifest[key] != actual:
            raise ValueError(f"Configuration differs from the frozen published run: {key}")
    kpi = pd.read_csv(inputs / "kpi_inputs.csv")
    events = pd.read_csv(inputs / "events.csv")
    cases, summary = backtest_check.run(kpi, events)
    expected_cases = pd.read_csv(inputs / "cases.csv")
    # Compare CSV values after the same parsing (numeric-looking labels are strings in Parquet).
    pd.testing.assert_frame_equal(pd.read_csv(StringIO(cases.to_csv(index=False))), expected_cases)
    original = json.loads((inputs / "summary.json").read_text(encoding="utf-8"))
    if any(original.get(key) != value for key, value in summary.items()):
        raise ValueError("Recomputed summary differs from the published result")
    output.mkdir(parents=True, exist_ok=True)
    cases.to_csv(output / "cases.csv", index=False)
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    audit = {
        "case_table_matches": True,
        "case_summary_matches": True,
        "input_hashes_verified": True,
        "activity_model_refitted": False,
        "raw_source_frozen_clock_checks_rerun": False,
        "note": "summary.json contains recomputed case counts only. Activity metadata and clock checks in the published summary are saved full-run evidence, not rerun by this command.",
    }
    (output / "replay_audit.json").write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", type=Path, default=INPUTS)
    parser.add_argument("--output", type=Path, default=BASE_DIR / "artifacts/backtest")
    args = parser.parse_args()
    summary = replay(args.inputs, args.output)
    print(f"Matched all {summary['n_cases']} cases: after-start "
          f"{summary['after_start_reading']['n']}, point-in-time "
          f"{summary['point_in_time_reading']['n']}, literal "
          f"{summary['literal_reading']['n']}. Outputs: {args.output}")
    print("Prepared-input replay only; activity fitting and raw-source clock checks were not rerun.")


if __name__ == "__main__":
    main()
