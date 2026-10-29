"""Regression tests for full-reproduction evidence and manifest hashing."""

import hashlib

import duckdb
import pandas as pd

from src.pipeline import full_repro, run_all


def test_build_result_includes_reproducibility_metadata(monkeypatch):
    monkeypatch.setitem(full_repro.CFG, "computed_on", "2026-10-29")
    manifests = [
        pd.DataFrame({"file": ["artifact.txt"], "sha256": ["abc123"]}),
        pd.DataFrame({"file": ["artifact.txt"], "sha256": ["abc123"]}),
    ]

    result = full_repro.build_result(
        manifests,
        protected_equal=True,
        run_id="R1-test-run",
        git_revision="deadbeef",
    )

    assert result["manifest_sha256"] == hashlib.sha256(
        manifests[0].to_csv(index=False).encode()
    ).hexdigest()
    assert result["run_id"] == "R1-test-run"
    assert result["git_revision"] == "deadbeef"
    assert result["computed_on"] == "2026-10-29"
    assert result["mode"] == "two full src.pipeline.run_all runs, including activity fitting"
    assert result["equal_manifests"] is True
    assert result["artifacts"] == 1
    assert result["protected_simulation_and_historical_binary_evaluation_unchanged"] is True
    assert result["status"] == "PASS"


def test_manifest_excludes_its_own_csv(monkeypatch, tmp_path):
    app = tmp_path / "app_data"
    app.mkdir()
    (app / "artifact.txt").write_text("stable", encoding="utf-8")
    (app / "manifest.csv").write_text("stale,row\n", encoding="utf-8")
    with duckdb.connect(str(app / "spaceeye.duckdb")):
        pass
    monkeypatch.setattr(run_all, "APP", app)

    manifest = run_all.manifest()

    assert "manifest.csv" not in manifest["file"].tolist()
    assert "artifact.txt" in manifest["file"].tolist()
