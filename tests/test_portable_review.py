"""A fresh reviewer can relocate inputs, verify archives and preserve existing work."""

from pathlib import Path

import pandas as pd
import pytest

from src.pipeline import common, setup_review, source_cache
from src.pipeline.portable_io import relative_file, sha256


def test_paths_are_checkout_relative_not_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("SPACEEYE_DATA_ROOT", raising=False)
    assert common.resolve_path("../Project/app_data") == (common.BASE_DIR.parent / "Project/app_data").resolve()
    monkeypatch.setenv("SPACEEYE_DATA_ROOT", ".spaceeye")
    paths = common.data_paths(common.CFG)
    assert paths["app_data"] == common.BASE_DIR / ".spaceeye/app_data"
    assert paths["private"].parent == paths["real_data"].parent == paths["app_data"].parent


def test_prepared_setup_works_without_external_sources(tmp_path, monkeypatch):
    monkeypatch.setattr(setup_review, "APP", tmp_path / "app_data")
    monkeypatch.setattr(setup_review, "PRIVATE", tmp_path / "private")
    assert setup_review.setup() > 0
    assert (tmp_path / "app_data/real/quality_checks_log.parquet").exists()
    assert (tmp_path / "private/ml_dataset_extended.parquet").exists()
    assert (tmp_path / "ready-data/MANIFEST.csv").exists()
    assert not (tmp_path / "private/answer_key.parquet").exists()
    assert not (tmp_path / "real_data").exists()
    assert setup_review.setup() == 0


def test_setup_preserves_changed_existing_data_before_installing(tmp_path, monkeypatch):
    app = tmp_path / "app_data"
    monkeypatch.setattr(setup_review, "APP", app)
    monkeypatch.setattr(setup_review, "PRIVATE", tmp_path / "private")
    old = app / "real/compounds.parquet"
    old.parent.mkdir(parents=True)
    old.write_bytes(b"existing team work")
    with pytest.raises(ValueError, match="Existing file differs"):
        setup_review.setup()
    assert old.read_bytes() == b"existing team work"
    assert not (tmp_path / "ready-data").exists()


def test_source_export_import_and_hash_failure(tmp_path, monkeypatch):
    source = tmp_path / "source"
    source.mkdir()
    content = b"code,value\nC01,1\n"
    (source / "sample.csv").write_bytes(content)
    row = {"root": "real_data", "file": "sample.csv", "sha256": sha256(content), "bytes": str(len(content))}
    monkeypatch.setattr(source_cache, "records", lambda: [row])
    monkeypatch.setattr(source_cache, "SRC", source)
    archive = tmp_path / "sources.zip"
    assert source_cache.export_archive(archive) == 1
    target = tmp_path / "new_device"
    monkeypatch.setattr(source_cache, "SRC", target)
    assert source_cache.install_archive(archive) == 1
    assert source_cache.check_inputs() == [row]
    (target / "sample.csv").write_bytes(b"changed")
    with pytest.raises(ValueError, match="Hash differs"):
        source_cache.check_inputs()
    with pytest.raises(ValueError, match="Existing file differs"):
        source_cache.install_archive(archive)


@pytest.mark.parametrize("name", ["../private/key", "/absolute", "C:/drive", "nested\\escape"])
def test_archive_paths_cannot_escape_data_root(name):
    with pytest.raises(ValueError, match="relative file"):
        relative_file(name)
    assert relative_file("raw/cache.csv") == Path("raw/cache.csv")


def test_data_only_training_contract_checks_all_targets_and_censoring():
    from src.pipeline.release import training_contract_checks
    frame = pd.DataFrame({"code": ["C01", "C01"], "x": [1, 2], "target": [True, None],
                          "class": ["distressed", None], "censored": [False, True], "excluded": [False, False]})
    meta = {"keys": ["code"], "features": ["x"], "targets": ["target", "class"],
            "censor_column": "censored", "excluded_from_X": ["excluded"]}
    assert all(training_contract_checks(frame, meta).values())
    frame.loc[1, "class"] = "not_distressed"
    assert not training_contract_checks(frame, meta)["ml_unknown_future_is_null"]
