"""Back up current local outputs, then compare two complete Track A runs.

This intentionally includes activity fitting. Historical binary evaluation and
raw simulation are not rebuilt. The backup is outside app_data and public Git.
"""

import hashlib
import json
import shutil
import subprocess

import pandas as pd

from src.pipeline import run_all
from src.pipeline.common import APP, BASE_DIR, CFG, PRIVATE


def build_result(
    manifests: list[pd.DataFrame],
    protected_equal: bool,
    run_id: str,
    git_revision: str,
) -> dict[str, object]:
    same = manifests[0].equals(manifests[1])
    manifest_csv = manifests[0].to_csv(index=False).encode()
    return {
        "mode": "two full src.pipeline.run_all runs, including activity fitting",
        "equal_manifests": same,
        "artifacts": len(manifests[0]),
        "protected_simulation_and_historical_binary_evaluation_unchanged": protected_equal,
        "status": "PASS" if same and protected_equal else "FAIL",
        "manifest_sha256": hashlib.sha256(manifest_csv).hexdigest(),
        "run_id": run_id,
        "git_revision": git_revision,
        "computed_on": CFG["computed_on"],
    }


def main():
    root = APP.parent / "before_corrections" / f"{CFG['computed_on']}_full_repro"
    target, suffix = root, 2
    while target.exists():
        target = root.with_name(root.name + f"_{suffix}")
        suffix += 1
    shutil.copytree(APP, target / "app_data")
    shutil.copytree(PRIVATE, target / "private")
    print("Previous local outputs backed up outside app_data", flush=True)
    protected = [p for folder in ("sim", "ew") for p in (APP / folder).rglob("*") if p.is_file()]
    protected += [PRIVATE / n for n in ("answer_key.parquet", "answer_key_complaints.parquet", "ml_dataset.parquet", "ml_dataset_metadata.json")]
    before = {str(p): run_all.sha(p) for p in protected}
    manifests = []
    for number in (1, 2):
        if run_all.main() != 0:
            raise RuntimeError(f"Full Track A run {number} STOP; previous outputs are backed up")
        manifest = pd.read_csv(APP / "manifest.csv").sort_values("file").reset_index(drop=True)
        manifests.append(manifest)
        print(f"Full Track A run {number}/2 finished", flush=True)
    protected_equal = all(run_all.sha(p) == before[str(p)] for p in protected)
    git_revision = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    result = build_result(
        manifests,
        protected_equal,
        run_all.make_run_id(),
        git_revision,
    )
    (BASE_DIR / "data/FULL_TRACK_A_REPRODUCIBILITY.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    if not result["equal_manifests"] or not protected_equal:
        raise RuntimeError("Full-run reproducibility or protected-history check failed")
    print("Full Track A reproducibility PASS", flush=True)


if __name__ == "__main__":
    main()
