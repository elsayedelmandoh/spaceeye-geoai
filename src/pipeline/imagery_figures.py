"""Presentation set for the single-capture Wayback figures: audit, older frames, per-compound comparison panels.

Reuses the official render path of imagery_compare (Esri Print service, attributed static maps). The frozen
selection in data/imagery/wayback_selected.json is read, never rewritten; extra single-capture states are
recorded separately in data/imagery/wayback_extra.json.
"""

import argparse
import json
import math
import re
import textwrap
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageFont

from src.pipeline import imagery_sources as S
from src.pipeline.common import BASE_DIR
from src.pipeline.imagery_compare import (
    START,
    boundaries,
    configured_through,
    save_json,
)

IMAGERY = BASE_DIR / "data/imagery"
FIGURES = IMAGERY / "figures"
EXTRA = IMAGERY / "wayback_extra.json"
AUDIT = FIGURES / "figures_audit.csv"
COMPARE = FIGURES / "compare"
TILE_ZOOMS = (15, 16, 17, 18)  # older releases only carry tiles at coarser zooms
FULL_LAYER, COARSE_LAYER = 5, 6  # Esri metadata layer n describes zoom 23 - n; pre-2020 imagery is only listed at zoom 17
WORKERS = 8
MIN_DATED_COVERAGE = 0.99  # same bar as imagery_compare.wayback_discovery
MAP_TOP, MAP_SIZE = 48, (S.WIDTH, S.HEIGHT)  # annotated_figure puts a 48 px title strip above the map
DUPLICATE_MAD = 3  # raw grey difference; re-renders of unchanged tiles under another release date sit at 0-1.6, real changes above 9
BLUR = 8  # box size for the pixel-difference comparison
SIMILAR_CORRELATION = 0.5  # z-scored, blurred frames; unrelated captures of one site stay below ~0.45
LOW_CONTRAST_STD = 22  # blurred grey std; hazy frames sit at 18-20, normal ones above 25
PANEL_WIDTH = 640
LABEL_HEIGHT = 64
FOOTER_FONT = 15
PRESENTATION = {  # capture dates shown in each compare figure: earliest clean, construction stages, latest
    "C01": ["2016-12-17", "2021-04-09", "2022-06-13", "2025-07-23"],
    "C02": ["2016-11-08", "2021-04-09", "2023-02-10", "2025-07-23"],
    "C03": ["2016-11-08", "2022-06-13", "2023-02-10", "2025-07-23"],
    "C04": ["2016-11-08", "2021-04-09", "2023-07-29", "2025-07-23"],
    "C07": ["2016-11-08", "2022-06-13", "2024-05-15", "2025-07-23"],
    "C10": ["2016-12-17", "2021-04-09", "2023-02-10", "2025-07-23"],
    "C12": ["2016-11-08", "2020-06-28", "2023-02-10", "2025-07-23"],
    "C14": ["2016-11-08", "2021-04-09", "2023-02-10", "2025-07-23"],
    "C17": ["2016-11-08", "2022-06-13", "2024-05-15", "2025-07-23"],
    "C18": ["2016-12-17", "2020-06-28", "2022-06-13", "2025-07-23"],
    "C19": ["2016-11-08", "2022-06-13", "2023-02-10", "2025-07-23"],
    "C21": ["2016-11-08", "2021-04-09", "2023-02-10", "2025-07-23"],
}
# Found by looking at every frame: dust haze flattens the 2025-04-08 capture, so it adds nothing to the story.
HAZY = {("C01", "2025-04-08"), ("C04", "2025-04-08"), ("C10", "2025-04-08"), ("C12", "2025-04-08"), ("C18", "2025-04-08")}


def load_index():
    return pd.read_csv(FIGURES / "index.csv")


def map_pixels(path):
    """The map area of a figure, without the title strip and the caption block."""
    image = Image.open(IMAGERY / path).convert("RGB")
    return image.crop((0, MAP_TOP, MAP_SIZE[0], MAP_TOP + MAP_SIZE[1]))


def blurred_gray(image):
    gray = np.asarray(image.convert("L"), dtype=float)
    height, width = gray.shape
    return gray.reshape(height // BLUR, BLUR, width // BLUR, BLUR).mean((1, 3))


def zscore(values):
    return (values - values.mean()) / values.std()


def correlation(a, b):
    return float(np.corrcoef(zscore(a).ravel(), zscore(b).ravel())[0, 1])


def cyan_mask(image):
    pixels = np.asarray(image, dtype=int)
    return (pixels[..., 0] < 80) & (pixels[..., 1] > 200) & (pixels[..., 2] > 200)


def audit_frames(index, timeline):
    """One row per frame: identity, outline agreement, contrast, similarity to the other frames of the compound."""
    extra_files = {row["file"] for row in json.loads(EXTRA.read_text(encoding="utf-8"))} if EXTRA.exists() else set()
    timeline = timeline.assign(file=timeline["path"].str.replace("images/", "figures/", regex=False))
    meta = timeline.set_index("file")[["release_id", "mixed_capture_dates", "bbox_3857"]]
    boxes = timeline.groupby("code")["bbox_3857"].first()
    rows = []
    for code, group in index.sort_values(["code", "capture_date"]).groupby("code"):
        images = [map_pixels(f) for f in group["file"]]
        grays = [blurred_gray(im) for im in images]
        raw = [np.asarray(im.convert("L"), dtype=float) for im in images]
        outline = cyan_mask(images[0])
        for i, frame in enumerate(group.itertuples()):
            others = [(correlation(grays[i], grays[j]), group["capture_date"].iloc[j]) for j in range(len(grays)) if j != i]
            similarity, similar_date = max(others)
            min_raw_diff = min(np.abs(raw[i] - raw[j]).mean() for j in range(len(raw)) if j != i)
            info = meta.loc[frame.file] if frame.file in meta.index else None
            flags = []
            if similarity >= SIMILAR_CORRELATION:
                flags.append("similar_to_" + similar_date)
            if min_raw_diff < DUPLICATE_MAD:
                flags.append("pixel_duplicate")
            if (code, frame.capture_date) in HAZY:
                flags.append("hazy_dust")
            if grays[i].std() < LOW_CONTRAST_STD:
                flags.append("low_contrast")
            rows.append({
                "code": code, "file": frame.file, "capture_date": frame.capture_date, "role": frame.role,
                "origin": "added" if frame.file in extra_files else "pr33",
                "release_id": None if info is None else info["release_id"],
                "mixed_capture_dates": None if info is None else info["mixed_capture_dates"],
                "same_bbox_as_compound": None if info is None else info["bbox_3857"] == boxes[code],
                "outline_overlap_with_first": round(float((cyan_mask(images[i]) & outline).sum() / outline.sum()), 2),
                "contrast_std": round(float(grays[i].std()), 1),
                "min_raw_pixel_diff": round(float(min_raw_diff), 1),
                "most_similar_date": similar_date, "most_similar_corr": round(similarity, 2),
                "corr_with_previous": None if i == 0 else round(correlation(grays[i], grays[i - 1]), 2),
                "date_order_ok": i == 0 or frame.capture_date > group["capture_date"].iloc[i - 1],
                "flags": ";".join(flags)})
    return pd.DataFrame(rows)


def audit():
    timeline = pd.read_csv(IMAGERY / "wayback_timeline.csv")
    frame = audit_frames(load_index(), timeline)
    frame.to_csv(AUDIT, index=False)
    print(f"Audited {len(frame)} frames; {frame['flags'].ne('').sum()} flagged -> {AUDIT.relative_to(BASE_DIR)}")


def single_capture(layers):
    """The one capture date of the zoom-17 layer when zoom 18 has no footprint or the same date over the whole compound.

    A partial zoom-18 footprint means the figure stitches newer and older tiles, so it is not a single capture.
    """
    coarse, full = layers[COARSE_LAYER], layers[FULL_LAYER]
    if len(coarse["capture_dates"]) != 1 or coarse["dated_coverage_fraction"] < MIN_DATED_COVERAGE:
        return None
    if full["capture_dates"] == [] or (full["capture_dates"] == coarse["capture_dates"] and full["dated_coverage_fraction"] >= MIN_DATED_COVERAGE):
        return coarse["capture_dates"][0]
    return None


def discover():
    catalogue = json.loads((IMAGERY / "catalogue_snapshot.json").read_text(encoding="utf-8"))
    frozen = json.loads((IMAGERY / "wayback_selected.json").read_text(encoding="utf-8"))
    known = {(row["code"], row["capture_dates"][0]) for row in frozen if len(row["capture_dates"]) == 1}
    through = configured_through()
    polygons = boundaries()
    probes = [(code, point, zoom) for code, polygon in polygons.items() for point in S.sample_points(polygon)
              for zoom in TILE_ZOOMS]
    releases = {code: set() for code in polygons}
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        for (code, _, _), found in zip(probes, pool.map(lambda p: S.local_releases(p[1], catalogue, through, p[2]), probes), strict=True):
            releases[code].update(found)
    jobs = [(code, release, layer) for code, found in releases.items() for release in found for layer in (FULL_LAYER, COARSE_LAYER)]
    with ThreadPoolExecutor(max_workers=3 * WORKERS) as pool:
        metadata = list(pool.map(lambda j: S.wayback_metadata(polygons[j[0]], catalogue[j[1]], level=j[2]), jobs))
    layers = {}
    for (code, release, layer), value in zip(jobs, metadata, strict=True):
        layers.setdefault((code, release), {})[layer] = value
    chosen = {}
    for (code, release), pair in sorted(layers.items(), key=lambda kv: catalogue[kv[0][1]]["itemTitle"]):
        date = single_capture(pair)
        if date and START <= date <= through and (code, date) not in known:
            chosen.setdefault((code, date), (release, pair[COARSE_LAYER], pair[FULL_LAYER]))
    rows = [{"code": code, "capture_date": date, "release_id": release, "release_date": catalogue[release]["itemTitle"][-11:-1],
             "providers": coarse["providers"], "context_providers": coarse["context_providers"],
             "resolution_m": coarse["resolution_m"], "accuracy_m": coarse["accuracy_m"],
             "dated_coverage_zoom17": coarse["dated_coverage_fraction"], "dated_coverage_zoom18": full["dated_coverage_fraction"],
             "metadata_url": coarse["metadata_url"], "item_id": catalogue[release]["itemID"],
             "file": f"figures/{code}_{date}.jpg"}
            for (code, date), (release, coarse, full) in sorted(chosen.items())]
    save_json(EXTRA, rows)
    print(f"{len(rows)} extra single-capture states -> {EXTRA.relative_to(BASE_DIR)}")


def raw_difference(path_a, path_b):
    a, b = (np.asarray(map_pixels(path).convert("L"), dtype=float) for path in (path_a, path_b))
    return float(np.abs(a - b).mean())


def drop_duplicate_frames(rows, index):
    """The metadata can date a footprint later while the tiles stay unchanged; keep the earliest date, delete the repeats."""
    kept = []
    for row in sorted(rows, key=lambda r: (r["code"], r["capture_date"])):
        same = index[(index["code"] == row["code"]) & ~index["file"].isin([r["file"] for r in rows])]["file"].tolist()
        same += [r["file"] for r in kept if r["code"] == row["code"]]
        if any(raw_difference(row["file"], other) < DUPLICATE_MAD for other in same):
            (IMAGERY / row["file"]).unlink()
            print(f"Dropped {row['file']}: pixel-identical to an earlier frame")
        else:
            kept.append(row)
    return kept


def render():
    catalogue = json.loads((IMAGERY / "catalogue_snapshot.json").read_text(encoding="utf-8"))
    polygons = boundaries()
    rows = json.loads(EXTRA.read_text(encoding="utf-8"))
    all_files = {row["file"] for row in rows}

    def render_row(row):
        item = S.cached_request(f"https://www.arcgis.com/sharing/rest/content/items/{row['item_id']}", {"f": "json"})
        service = " ".join(re.sub(r"<[^>]+>", " ", item.get("accessInformation") or "Esri and imagery licensors").split())
        scene = "Esri World Imagery Wayback; imagery: " + "; ".join(row["context_providers"] or row["providers"])
        row["attribution"] = scene + ". Service credits: " + service
        polygon = polygons[row["code"]]
        image, _ = S.static_wayback_map(polygon, catalogue[row["release_id"]], scene)
        S.annotated_figure(image, polygon, S.frame_extent(polygon), f"{row['code']} | capture {row['capture_date']}", [
            "Wayback release " + row["release_date"] + " | " + row["attribution"],
            "Cyan: reviewed working boundary, not a legal survey. Source dates may vary within the map.",
            "Static educational report figure. Third-party imagery rights retained; not an open imagery dataset."],
            BASE_DIR / "data/imagery" / row["file"])

    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        list(pool.map(render_row, rows))
    index = load_index()
    rows = drop_duplicate_frames(rows, index)
    save_json(EXTRA, rows)
    added = pd.DataFrame([{"code": r["code"], "capture_date": r["capture_date"], "role": "timeline", "file": r["file"],
                           "source": "Esri World Imagery Wayback"} for r in rows])
    pd.concat([index[~index["file"].isin(all_files)], added]).sort_values(["code", "capture_date"]).to_csv(
        FIGURES / "index.csv", index=False)
    print(f"Rendered {len(rows)} frames; index now has {len(load_index())} rows")


def attributions():
    """Printed credit of every frame, from the PR timeline table and the added-frame record."""
    timeline = pd.read_csv(IMAGERY / "wayback_timeline.csv")
    credits = dict(zip(timeline["path"].str.replace("images/", "figures/", regex=False), timeline["attribution"], strict=True))
    if EXTRA.exists():
        credits |= {row["file"]: row["attribution"] for row in json.loads(EXTRA.read_text(encoding="utf-8"))}
    return credits


def font(size, bold=False):
    from matplotlib.font_manager import findfont
    return ImageFont.truetype(findfont("DejaVu Sans:bold" if bold else "DejaVu Sans"), size)


def shared_credit(credits):
    """One attribution line for a figure: every imagery provider shown plus the service credit."""
    providers, service = set(), ""
    for credit in credits:
        scene, _, service = credit.partition(". Service credits: ")
        providers.update(scene.split("imagery: ")[-1].split("; "))
    return "Esri World Imagery Wayback; imagery: " + "; ".join(sorted(providers)) + ". Service credits: " + service


def compare_figure(code, frames, credit):
    """Date-ordered panels with one shared extent; frames are (capture_date, file) pairs."""
    columns = len(frames) if len(frames) < 4 else 2
    rows = math.ceil(len(frames) / columns)
    panel_height = PANEL_WIDTH * MAP_SIZE[1] // MAP_SIZE[0]
    gap, title_height = 10, 56
    notice = ("Cyan: reviewed working boundary, not a legal survey. Same extent and zoom in every panel. "
              "Static educational report figure; third-party imagery rights retained; not an open imagery dataset.")
    footer = [part for line in (credit, notice) for part in textwrap.wrap(line, width=170)]
    width = columns * PANEL_WIDTH + (columns + 1) * gap
    footer_height = 22 * len(footer) + 16
    height = title_height + rows * (LABEL_HEIGHT + panel_height + gap) + footer_height
    sheet = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(sheet)
    draw.text((gap, 10), f"{code} | single-capture Wayback frames in date order", fill="black", font=font(30, bold=True))
    for i, (date, file) in enumerate(frames):
        x = gap + (i % columns) * (PANEL_WIDTH + gap)
        y = title_height + (i // columns) * (LABEL_HEIGHT + panel_height + gap)
        draw.rectangle((x, y, x + PANEL_WIDTH, y + LABEL_HEIGHT), fill="black")
        draw.text((x + 14, y + 8), date, fill="white", font=font(44, bold=True))
        sheet.paste(map_pixels(file).resize((PANEL_WIDTH, panel_height), Image.LANCZOS), (x, y + LABEL_HEIGHT))
    for i, line in enumerate(footer):
        draw.text((gap, height - footer_height + 8 + i * 22), line, fill="black", font=font(FOOTER_FONT))
    return sheet


def compare():
    index = load_index()
    credits = attributions()
    COMPARE.mkdir(exist_ok=True)
    for code, dates in PRESENTATION.items():
        shown = index[(index["code"] == code) & index["capture_date"].isin(dates)].sort_values("capture_date")
        if len(shown) != len(dates):
            raise ValueError(f"{code}: expected frames for {dates}, found {shown['capture_date'].tolist()}")
        frames = list(zip(shown["capture_date"], shown["file"], strict=True))
        sheet = compare_figure(code, frames, shared_credit(credits[f] for _, f in frames))
        sheet.save(COMPARE / f"{code}_compare.jpg", "JPEG", quality=90)
        print(f"{code}: {len(frames)} panels {sheet.size}")
    annotate_index(index)


def presentation_note(row, flags):
    dates = PRESENTATION[row.code]
    if row.capture_date == dates[0]:
        return "yes", "earliest clean capture"
    if row.capture_date == dates[-1]:
        return "yes", "latest capture"
    if row.capture_date in dates:
        return "yes", "construction stage"
    if "hazy_dust" in flags:
        return "no", "hazy, washed-out by dust"
    similar = [f for f in flags.split(";") if f.startswith("similar_to_")]
    if similar:
        return "no", f"visually close to the {similar[0].removeprefix('similar_to_')} frame"
    return "no", "extra timeline frame; the shown frames tell the story"


def annotate_index(index):
    audit_flags = pd.read_csv(AUDIT, keep_default_na=False).set_index("file")["flags"]
    notes = [presentation_note(row, audit_flags[row.file]) for row in index.itertuples()]
    index = index.assign(in_presentation=[n[0] for n in notes], note=[n[1] for n in notes])
    index.to_csv(FIGURES / "index.csv", index=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=["audit", "discover", "render", "compare"], required=True)
    args = parser.parse_args()
    {"audit": audit, "discover": discover, "render": render, "compare": compare}[args.phase]()


if __name__ == "__main__":
    main()
