#!/usr/bin/env python3
"""Build the offline JavaScript manifest for the finishing-check image kit."""

from __future__ import annotations

import argparse
import json
import re
from collections.abc import Sequence
from pathlib import Path

KIT_DIR = Path(__file__).resolve().parent
DEFAULT_IMAGES_DIR = KIT_DIR / "images"
DEFAULT_OUTPUT_PATH = KIT_DIR / "manifest.js"
DATED_IMAGE_PATTERN = re.compile(r"^(?P<area>S\d+)_d(?P<date>\d+)\.jpg$", re.IGNORECASE)


def parse_dated_image(image_path: Path) -> tuple[str, int] | None:
    """Return the area and numeric date for a dated image filename."""
    match = DATED_IMAGE_PATTERN.fullmatch(image_path.name)
    if match is None:
        return None
    return match.group("area"), int(match.group("date"))


def collect_area_images(images_dir: Path) -> dict[str, list[tuple[int, str]]]:
    """Collect dated images by area, rejecting duplicate dates."""
    area_images: dict[str, list[tuple[int, str]]] = {}
    for image_path in images_dir.iterdir():
        parsed_image = parse_dated_image(image_path)
        if parsed_image is None:
            continue
        area_id, image_date = parsed_image
        area_images.setdefault(area_id, []).append((image_date, image_path.name))

    for area_id, dated_images in area_images.items():
        filenames = [filename for _, filename in dated_images]
        if len(filenames) != len(set(filenames)):
            raise ValueError(f"Duplicate dated image filename in {area_id}")
        dates = [image_date for image_date, _ in dated_images]
        if len(dates) != len(set(dates)):
            raise ValueError(f"Duplicate image date in {area_id}")
    return area_images


def build_manifest(images_dir: Path) -> dict[str, list[dict[str, object]]]:
    """Build the area/image structure consumed by label.html."""
    area_images = collect_area_images(images_dir)
    if not area_images:
        raise ValueError(f"No dated JPG images found in {images_dir}")

    areas: list[dict[str, object]] = []
    area_order = sorted(area_images, key=lambda area_id: (int(area_id[1:]), area_id))
    for area_id in area_order:
        dated_images = sorted(area_images[area_id], key=lambda image: image[0])
        areas.append(
            {
                "id": area_id,
                "images": [filename for _, filename in dated_images],
            }
        )
    return {"areas": areas}


def write_manifest(manifest: dict[str, list[dict[str, object]]], output_path: Path) -> None:
    """Write a deterministic JavaScript file containing JSON-compatible data."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_json = json.dumps(manifest, ensure_ascii=False, indent=2)
    output_path.write_text(f"window.KIT = {manifest_json};\n", encoding="utf-8")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse command-line options."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--images-dir",
        type=Path,
        default=DEFAULT_IMAGES_DIR,
        help="directory containing S01_d01.jpg-style files",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help="JavaScript manifest path to write",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """Generate the manifest and return a process exit code."""
    args = parse_args(argv)
    manifest = build_manifest(args.images_dir)
    write_manifest(manifest, args.output)
    print(f"Wrote {args.output} with {len(manifest['areas'])} areas")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
