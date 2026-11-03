"""Contract tests for the offline finishing-check labelling kit."""

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
KIT_DIR = REPO_ROOT / "data/experiments/40_finishing_human_check/kit"
MANIFEST_SCRIPT = KIT_DIR / "make_manifest.py"
LABEL_PAGE = KIT_DIR / "label.html"


def test_make_manifest_lists_areas_and_images_in_numeric_date_order(tmp_path):
    images_dir = tmp_path / "images"
    images_dir.mkdir()
    for filename in (
        "S01_d10.jpg",
        "S01_d02.jpg",
        "S01_d01.jpg",
        "S01_overview_a.jpg",
        "S02_d01.jpg",
        "S02_d02.jpg",
    ):
        (images_dir / filename).write_bytes(b"tiny fabricated jpeg")

    output_path = tmp_path / "manifest.js"
    assert MANIFEST_SCRIPT.is_file(), "make_manifest.py must exist"
    result = subprocess.run(
        [
            sys.executable,
            str(MANIFEST_SCRIPT),
            "--images-dir",
            str(images_dir),
            "--output",
            str(output_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    manifest_text = output_path.read_text(encoding="utf-8")
    payload = json.loads(manifest_text.removeprefix("window.KIT = ").removesuffix(";\n"))
    assert payload == {
        "areas": [
            {"id": "S01", "images": ["S01_d01.jpg", "S01_d02.jpg", "S01_d10.jpg"]},
            {"id": "S02", "images": ["S02_d01.jpg", "S02_d02.jpg"]},
        ]
    }
    assert result.returncode == 0


def test_kit_images_and_generated_manifest_are_git_ignored():
    ignored_paths = (
        "data/experiments/40_finishing_human_check/kit/images/example.jpg",
        "data/experiments/40_finishing_human_check/kit/manifest.js",
    )
    for path in ignored_paths:
        result = subprocess.run(
            ["git", "check-ignore", "--no-index", "-q", path],
            cwd=REPO_ROOT,
            check=False,
        )
        assert result.returncode == 0, f"{path} must stay git-ignored"


def test_label_page_has_no_model_output_references():
    assert LABEL_PAGE.is_file(), "label.html must exist"
    page_text = LABEL_PAGE.read_text(encoding="utf-8").lower()
    for forbidden_reference in ("labels_ai_rater", "predictions"):
        assert forbidden_reference not in page_text


def test_label_page_loads_images_from_the_images_folder():
    """The manifest holds bare file names; the page must prefix the kit's images/ folder."""
    html = (KIT_DIR / "label.html").read_text(encoding="utf-8")
    assert '"images/" + a.images[i]' in html
