"""Check the plain-Python inspection tools without external services."""

import json
import subprocess
import sys
import textwrap
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.inference.tools import get_facts, get_images, get_kpis, get_rules

REPO_ROOT = Path(__file__).resolve().parents[1]
RELEASE_ZIP = REPO_ROOT / "releases" / "ready-data" / "SpaceEye_R7_READY_DATA_2026-10-30_v6.zip"
_REQUIRED_RELEASE_TABLES = (
    "tables/real/statements.parquet",
    "tables/real/kpi_values.parquet",
    "tables/real/compounds.parquet",
    "tables/real/rules.parquet",
)


def _release_has_required_tables():
    probe = textwrap.dedent(
        """
        import sys
        from zipfile import ZipFile
        required = (
            "tables/real/statements.parquet",
            "tables/real/kpi_values.parquet",
            "tables/real/compounds.parquet",
            "tables/real/rules.parquet",
        )
        with ZipFile(sys.argv[1]) as archive:
            names = archive.namelist()
        print("available" if all(any(name.endswith(item) for name in names) for item in required) else "missing")
        """
    )
    result = subprocess.run(
        [sys.executable, "-I", "-c", probe, str(RELEASE_ZIP)],
        check=False,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0 and result.stdout.strip() == "available"


def _all_keys(value):
    if isinstance(value, dict):
        for key, child in value.items():
            yield key
            yield from _all_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from _all_keys(child)


def test_get_facts_uses_an_inclusive_quarter_cutoff_and_source_links():
    statements = pd.DataFrame(
        [
            {
                "statement_id": "S1",
                "code": "C01",
                "kind": "promise",
                "subtype": "handover",
                "detail": "First published handover promise",
                "published_date": "2025-01-15",
                "period_start": None,
                "period_end": "2025-06-30",
                "record_id": "R-001",
                "link": "https://example.org/R-001",
            },
            {
                "statement_id": "S2",
                "code": "C01",
                "kind": "event",
                "subtype": "progress",
                "detail": "Quarter-end publication",
                "published_date": "2025-03-31 18:00",
                "period_start": "2025-01-01",
                "period_end": "2025-03-31",
                "record_id": "R-002",
            },
            {
                "statement_id": "S3",
                "code": "C01",
                "kind": "event",
                "subtype": "progress",
                "detail": "Future publication",
                "published_date": "2025-04-01",
                "period_start": "2025-04-01",
                "period_end": "2025-04-01",
                "record_id": "R-003",
            },
        ]
    )

    facts = get_facts("C01", "2025Q1", tables={"statements": statements})

    assert [fact["record_id"] for fact in facts] == ["R-001", "R-002"]
    assert facts[0]["link"] == "https://example.org/R-001"
    assert facts[1]["link"] is None
    assert facts[0]["detail"] == "First published handover promise"
    assert facts[0]["period_start"] is None


def test_get_kpis_preserves_unknowns_orders_history_and_marks_false_k4():
    kpis = pd.DataFrame(
        [
            {
                "code": "C01",
                "quarter": "2024Q3",
                "activity_prob": 0.8,
                "K2": 0,
                "K3": 0,
                "K4": True,
                "K5_months": 0,
                "K6": None,
                "level": 4,
                "level_label": "4",
                "level_word": "routine",
                "reason": "Routine",
                "reason_ar": "روتيني",
                "may_be_complete": False,
                "origin": "derived",
                "run_id": "R-1",
                "computed_at": "2026-10-26",
            },
            {
                "code": "C01",
                "quarter": "2025Q1",
                "activity_prob": 0.4,
                "K2": 1,
                "K3": 2,
                "K4": True,
                "K5_months": 0,
                "K6": 3,
                "level": 3,
                "level_label": "3",
                "level_word": "third",
                "reason": "Review",
                "reason_ar": "مراجعة",
                "may_be_complete": False,
                "origin": "derived",
                "run_id": "R-2",
                "computed_at": "2026-10-26",
            },
            {
                "code": "C01",
                "quarter": "2025Q2",
                "activity_prob": 0.2,
                "K2": 2,
                "K3": 3,
                "K4": True,
                "K5_months": 1,
                "K6": 4,
                "level": 2,
                "level_label": "2",
                "level_word": "second",
                "reason": "Inspect",
                "reason_ar": "افحص",
                "may_be_complete": False,
                "origin": "derived",
                "run_id": "R-3",
                "computed_at": "2026-10-26",
            },
            {
                "code": "C01",
                "quarter": "2025Q3",
                "activity_prob": np.nan,
                "K2": pd.NA,
                "K3": pd.NA,
                "K4": False,
                "K5_months": pd.NA,
                "K6": pd.NA,
                "level": 4,
                "level_label": "4",
                "level_word": "routine",
                "reason": "Observation incomplete",
                "reason_ar": "الملاحظة غير مكتملة",
                "may_be_complete": pd.NA,
                "origin": "derived",
                "run_id": "R-4",
                "computed_at": "2026-10-26",
            },
        ]
    )

    result = get_kpis("C01", "2025Q3", tables={"kpi_values": kpis}, history=2)

    assert result["A"] is None
    assert result["K2"] is None
    assert result["K3"] is None
    assert result["K5_months"] is None
    assert result["K6"] is None
    assert result["may_be_complete"] is None
    assert result["level_label"] == "not assessable"
    assert result["level_word"] == "not assessable"
    assert [item["quarter"] for item in result["series"]] == ["2025Q1", "2025Q2"]
    assert result["origin"] == "derived"
    assert result["run_id"] == "R-4"
    assert result["computed_at"] == "2026-10-26"
    json.dumps(result, allow_nan=False)


def test_get_facts_accepts_a_real_table_directory(tmp_path):
    base = tmp_path / "real"
    base.mkdir()
    statements = pd.DataFrame(
        [
            {
                "statement_id": "S1",
                "code": "C01",
                "kind": "event",
                "subtype": "launch",
                "detail": "Launch",
                "published_date": "2025-01-01",
                "period_start": None,
                "period_end": None,
                "record_id": "R-001",
            }
        ]
    )
    statements.to_parquet(base / "statements.parquet", index=False)
    pd.DataFrame({"code": ["C01"]}).to_parquet(base / "kpi_values.parquet", index=False)
    pd.DataFrame({"code": ["C01"]}).to_parquet(base / "compounds.parquet", index=False)

    facts = get_facts("C01", "2025Q1", tables=base)

    assert facts[0]["record_id"] == "R-001"


def test_get_images_returns_two_source_images_when_available(tmp_path):
    images_path = tmp_path / "images.csv"
    pd.DataFrame(
        [
            {
                "code": "C01",
                "image_type": "before",
                "capture_date": "2022-04-01",
                "attribution": "Example archive",
                "path": "images/C01_before.jpg",
            },
            {
                "code": "C01",
                "image_type": "after",
                "capture_date": "2026-08-01",
                "attribution": "Example archive",
                "path": "images/C01_after.jpg",
            },
        ]
    ).to_csv(images_path, index=False)

    result = get_images("C01", images_path=images_path)

    assert result["status"] == "available"
    assert [image["image_type"] for image in result["images"]] == ["before", "after"]
    assert result["images"][0]["capture_date"] == "2022-04-01"
    assert result["images"][0]["attribution"] == "Example archive"
    assert result["images"][0]["path"] == "images/C01_before.jpg"


def test_get_images_reports_an_explicit_missing_status(tmp_path):
    result = get_images("C01", images_path=tmp_path / "missing.csv")

    assert result == {
        "status": "missing",
        "images": [],
        "reason": "Wayback images not prepared (T-AH-15)",
    }


def test_get_rules_filters_articles_and_returns_all_csv_fields(tmp_path):
    rules_path = tmp_path / "decree.csv"
    pd.DataFrame(
        [
            {
                "article_id": "D-3-3",
                "article": "art 3(3)",
                "text": "Financial cover on phase construction cost",
                "value": 20,
            },
            {
                "article_id": "D-5",
                "article": "art 5",
                "text": "Delivery grace after the promised date",
                "value": 12,
            },
        ]
    ).to_csv(rules_path, index=False)

    by_article = get_rules(articles="art 3(3)", path=rules_path)
    by_text = get_rules(query="delivery grace", path=rules_path)

    assert len(by_article) == 1
    assert by_article[0]["article_id"] == "D-3-3"
    assert by_article[0]["text"] == "Financial cover on phase construction cost"
    assert len(by_text) == 1
    assert by_text[0]["article"] == "art 5"


def test_get_rules_names_the_missing_configuration_key(tmp_path):
    with pytest.raises(FileNotFoundError, match="sources.decree"):
        get_rules(path=tmp_path / "missing.csv")


def test_tool_outputs_have_no_name_like_keys(tmp_path):
    statements = pd.DataFrame(
        [
            {
                "statement_id": "S1",
                "code": "C01",
                "kind": "event",
                "subtype": "launch",
                "detail": "Launch",
                "published_date": "2025-01-01",
                "period_start": None,
                "period_end": None,
                "record_id": "R-001",
            }
        ]
    )
    kpis = pd.DataFrame(
        [
            {
                "code": "C01",
                "quarter": "2025Q1",
                "activity_prob": 0.2,
                "K2": 0,
                "K3": 0,
                "K4": True,
                "K5_months": 0,
                "K6": None,
                "level": 4,
                "level_label": "4",
                "level_word": "routine",
                "reason": "Routine",
                "reason_ar": "روتيني",
                "may_be_complete": False,
                "origin": "derived",
                "run_id": "R-1",
                "computed_at": "2026-10-26",
            }
        ]
    )
    images_path = tmp_path / "images.csv"
    pd.DataFrame(
        [
            {
                "code": "C01",
                "image_type": "before",
                "capture_date": "2022-04-01",
                "attribution": "Example archive",
                "path": "images/C01_before.jpg",
            }
        ]
    ).to_csv(images_path, index=False)
    rules_path = tmp_path / "decree.csv"
    pd.DataFrame([{"article_id": "D-5", "article": "art 5", "text": "Grace"}]).to_csv(rules_path, index=False)

    outputs = [
        get_facts("C01", "2025Q1", tables={"statements": statements}),
        get_kpis("C01", "2025Q1", tables={"kpi_values": kpis}),
        get_images("C01", images_path=images_path),
        get_rules(path=rules_path),
    ]

    assert not any("name" in key.lower() for output in outputs for key in _all_keys(output))
    for output in outputs:
        json.dumps(output, allow_nan=False)


@pytest.mark.skipif(
    not _release_has_required_tables(),
    reason="prepared release archive or required real tables are missing",
)
def test_prepared_release_tables_drive_the_inspection_tools(tmp_path):
    script = textwrap.dedent(
        """
        import json
        import shutil
        import stat
        import sys
        from pathlib import Path, PurePosixPath
        from zipfile import ZipFile

        archive = Path(sys.argv[1])
        destination = Path(sys.argv[2])
        repository = Path(sys.argv[3])
        if destination.exists() and any(destination.iterdir()):
            raise RuntimeError("release extraction directory is not empty")
        destination.mkdir(parents=True, exist_ok=True)
        root = destination.resolve()
        total_size = 0
        with ZipFile(archive) as source:
            for member in source.infolist():
                relative = PurePosixPath(member.filename)
                if relative.is_absolute() or ".." in relative.parts or "\\\\" in member.filename:
                    raise RuntimeError(f"unsafe release member: {member.filename}")
                mode = (member.external_attr >> 16) & 0xFFFF
                if stat.S_ISLNK(mode):
                    raise RuntimeError(f"release symlink is not allowed: {member.filename}")
                target = (root / Path(*relative.parts)).resolve()
                if target != root and root not in target.parents:
                    raise RuntimeError(f"release member escapes destination: {member.filename}")
                if member.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                    continue
                if member.file_size > 100_000_000:
                    raise RuntimeError(f"release member is too large: {member.filename}")
                total_size += member.file_size
                if total_size > 500_000_000:
                    raise RuntimeError("release extraction exceeds the size limit")
                target.parent.mkdir(parents=True, exist_ok=True)
                with source.open(member) as input_file, target.open("wb") as output_file:
                    shutil.copyfileobj(input_file, output_file)

        candidates = [
            path.parent
            for path in destination.rglob("statements.parquet")
            if path.parent.name == "real" and path.parent.parent.name == "tables"
        ]
        if len(candidates) != 1:
            raise RuntimeError("prepared release does not contain one real table directory")
        base = candidates[0]
        required = ("statements", "kpi_values", "compounds", "rules")
        if not all((base / f"{name}.parquet").is_file() for name in required):
            raise RuntimeError("prepared release is missing a required real table")

        sys.path.insert(0, str(repository))
        import pandas as pd
        from src.inference.tools import get_facts, get_kpis

        compounds = pd.read_parquet(base / "compounds.parquet")
        kpi_values = pd.read_parquet(base / "kpi_values.parquet")
        code = sorted(compounds["code"].dropna().astype(str).unique())[0]
        quarters = kpi_values.loc[kpi_values["code"].eq(code), "quarter"].dropna().astype(str)
        quarter = sorted(quarters.unique())[-1]
        facts = get_facts(code, quarter, tables=base)
        kpis = get_kpis(code, quarter, tables=base)
        payload = {
            "archive_root": base.parent.parent.name,
            "table_files": sorted(path.name for path in base.glob("*.parquet")),
            "code": code,
            "quarter": quarter,
            "facts": facts,
            "kpis": kpis,
        }
        print(json.dumps(payload, allow_nan=False))
        """
    )
    destination = tmp_path / "release"
    result = subprocess.run(
        [
            sys.executable,
            "-I",
            "-c",
            script,
            str(RELEASE_ZIP),
            str(destination),
            str(REPO_ROOT),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    facts = payload["facts"]
    kpis = payload["kpis"]
    required_fact_fields = {
        "record_id",
        "kind",
        "subtype",
        "published_date",
        "period_start",
        "period_end",
        "detail",
        "link",
    }
    required_kpi_fields = {
        "A",
        "K2",
        "K3",
        "K4",
        "K5_months",
        "K6",
        "level",
        "level_label",
        "level_word",
        "reason",
        "reason_ar",
        "may_be_complete",
        "series",
        "origin",
        "run_id",
        "computed_at",
    }

    assert payload["archive_root"] == "SpaceEye_R7_READY_DATA_2026-10-30_v6"
    assert payload["table_files"] == [
        "compounds.parquet",
        "drivers_monthly.parquet",
        "eval_outcomes.parquet",
        "kpi_values.parquet",
        "rules.parquet",
        "sat_quarterly.parquet",
        "sat_yearly.parquet",
        "statements.parquet",
    ]
    assert facts
    assert all(required_fact_fields.issubset(fact) for fact in facts)
    assert all(fact["record_id"] for fact in facts)
    cutoff = pd.Period(payload["quarter"], freq="Q").end_time.date()
    published_dates = pd.to_datetime(
        [fact["published_date"] for fact in facts],
        format="mixed",
        errors="coerce",
    ).date
    assert all(published_date <= cutoff for published_date in published_dates)
    assert required_kpi_fields.issubset(kpis)
    assert isinstance(kpis["series"], list)
    assert not any("name" in key.lower() for key in _all_keys(payload))


def test_get_kpis_returns_the_compound_code_for_the_inspection_file():
    frame = pd.DataFrame({"code": ["C01"], "quarter": ["2026Q3"], "qi": [43], "K4": [True], "level": [2], "origin": ["derived"], "run_id": ["R1"]})
    assert get_kpis("C01", "2026Q3", tables={"kpi_values": frame})["code"] == "C01"
