"""Observed imagery timelines: distinct Wayback captures and clear quarterly Sentinel context."""

import argparse
import hashlib
import html
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np
import pandas as pd
from shapely.geometry import shape
from shapely.ops import unary_union

from src.pipeline import imagery_sources as S
from src.pipeline.common import APP, CFG, REAL, qend, qindex
from src.pipeline.portable_io import install_files

OUT = APP / "imagery_comparison"
START = "2016-01-01"


def configured_through():
    return qend(qindex(CFG["asof"])).date().isoformat()


def inspection_pair(rows, asof):
    """Select distinct, published observations with at least a year between captures."""
    eligible = [r for r in rows if r["release_date"] <= asof and r["capture_dates"][-1] <= asof]
    if not eligible:
        return {}
    after = max(eligible, key=lambda r: (r["capture_dates"][-1], r["release_date"]))
    baseline = str((pd.Timestamp(after["capture_dates"][-1]) - pd.DateOffset(months=12)).date())
    older = [r for r in eligible if r["capture_dates"][-1] <= baseline]
    pair = {"after": after}
    if older:
        pair["before"] = max(older, key=lambda r: (r["capture_dates"][-1], r["release_date"]))
    return pair


def prepare_metadata():
    """Install checked-in source selections without copying or inventing pixels."""
    from src.pipeline.common import BASE_DIR
    source = BASE_DIR / "data/imagery"
    files = {OUT / name: (source / name).read_bytes() for name in (
        "wayback_selected.json", "catalogue_snapshot.json")}
    selections = json.loads((source / "sentinel_selection.json").read_text(encoding="utf-8"))
    for row in selections:
        if row["status"] != "available":
            continue
        info = {k: v for k, v in row.items() if k not in {"quarter", "status", "rendered_source_sha256"}}
        destination = OUT / "sentinel_scenes" / (row["quarter"] + ".json")
        # A producer cache can contain equivalent richer render bookkeeping;
        # preserve it rather than changing an existing scene selection.
        if not destination.exists():
            files[destination] = (json.dumps(info, indent=2) + "\n").encode()
    return install_files(files)


def restore_selected_sentinel(info, polygons):
    """Read the exact recorded public product, never select a replacement silently."""
    if info["method"].startswith("earth_engine"):
        from src.pipeline.imagery_earth_engine import revisualize_window
        return revisualize_window(info, polygons)
    from affine import Affine
    url = S.STAC + "/collections/" + info["collection"] + "/items/" + info["scene_id"]
    item = S.cached_request(url)
    rgb, transform_, bad, measurements = S.read_sentinel_window(item, list(polygons.values()))
    info["quality_by_code"] = dict(zip(polygons, measurements))
    if max(q["bad_fraction"] for q in measurements) > .10 or min(q["valid_fraction"] for q in measurements) < .95:
        raise ValueError("Recorded source no longer meets the saved quality contract")
    info["local_bad_fraction"] = bad
    return rgb, Affine(*transform_[:6]), info


def save_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def save_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(path, index=False, encoding="utf-8-sig")


def boundaries():
    source = REAL / "compound_boundaries.geojson"
    if not source.exists():
        raise FileNotFoundError("Run python -m src.pipeline.setup_review to install the coded boundaries")
    features = json.loads(source.read_text(encoding="utf-8"))["features"]
    result = {f["properties"]["code"]: shape(f["geometry"]) for f in features}
    if len(result) != 12 or any(not p.is_valid or p.is_empty for p in result.values()):
        raise ValueError("Expected exactly 12 valid coded R7 boundaries")
    return dict(sorted(result.items()))


def distinct_capture_states(rows):
    """A provider rename or publication-only refresh is not another observation."""
    unique = {}
    for row in sorted(rows, key=lambda r: r["release_date"]):
        unique.setdefault((row["code"], tuple(row["capture_dates"])), row)
    return sorted(unique.values(), key=lambda r: (r["code"], r["capture_dates"][-1], r["release_date"]))


def wayback_discovery(polygons, through):
    catalogue = S.cached_request(S.CONFIG_URL)
    save_json(OUT / "catalogue_snapshot.json", catalogue)
    point_jobs = {}
    for code, polygon in polygons.items():
        for point in S.sample_points(polygon):
            point_jobs.setdefault(S.tile_coordinates(point), {"point": point, "codes": set()})["codes"].add(code)
    discovered = {code: set() for code in polygons}
    errors = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        jobs = {pool.submit(S.local_releases, job["point"], catalogue, through): job for job in point_jobs.values()}
        for future in as_completed(jobs):
            job = jobs[future]
            try:
                releases = future.result()
                for code in job["codes"]:
                    discovered[code].update(releases)
            except Exception as error:  # noqa: BLE001 -- source failure is recorded explicitly
                errors.append({"codes": sorted(job["codes"]), "error": str(error)[:300]})
    # Also test the current release, so an earlier tile-change marker cannot
    # prevent source metadata changes from being inspected.
    latest = max((key for key, value in catalogue.items() if value["itemTitle"][-11:-1] <= through),
                 key=lambda key: catalogue[key]["itemTitle"])
    for releases in discovered.values():
        releases.add(latest)
    save_json(OUT / "discovery.json", {"releases": {c: sorted(v) for c, v in discovered.items()}, "errors": errors})
    rows, failed = [], []
    with ThreadPoolExecutor(max_workers=4) as pool:
        jobs = {pool.submit(S.wayback_metadata, polygons[code], catalogue[release]): (code, release)
                for code, releases in discovered.items() for release in releases}
        for index, future in enumerate(as_completed(jobs), 1):
            code, release = jobs[future]
            item = catalogue[release]
            try:
                meta = future.result()
                dates = meta["capture_dates"]
                if not dates or dates[-1] < START or dates[-1] > through or meta["dated_coverage_fraction"] < .99:
                    failed.append({"code": code, "release": release, "reason": "Missing dates, outside study period, or incomplete metadata", **meta})
                    continue
                rows.append({"code": code, "release_id": release, "release_date": item["itemTitle"][-11:-1], **meta})
            except Exception as error:  # noqa: BLE001 -- source failure is recorded explicitly
                failed.append({"code": code, "release": release, "reason": str(error)[:300]})
            if index % 20 == 0:
                print(f"Wayback metadata {index}/{len(jobs)}", flush=True)
    # Publication-only updates must not inflate the observed timeline.
    selected = distinct_capture_states(rows)
    save_json(OUT / "wayback_selected.json", selected)
    save_json(OUT / "wayback_rejected.json", failed)
    print(f"Wayback selected {len(selected)} distinct dated map states; rejected {len(failed)} metadata candidates", flush=True)
    return selected, catalogue


def wayback_render(polygons):
    selected = json.loads((OUT / "wayback_selected.json").read_text(encoding="utf-8"))
    catalogue = json.loads((OUT / "catalogue_snapshot.json").read_text(encoding="utf-8"))
    service_items = {}
    for release in sorted({row["release_id"] for row in selected}):
        item_id = catalogue[release]["itemID"]
        value = S.cached_request(f"https://www.arcgis.com/sharing/rest/content/items/{item_id}", {"f": "json"})
        service_items[release] = {"item_id": item_id, "access_information": value.get("accessInformation"),
                                  "license_info": value.get("licenseInfo"), "url": value.get("url")}
    save_json(OUT / "service_item_metadata.json", service_items)
    cutoff = qend(qindex(CFG["asof"])).date().isoformat()
    existing = {}
    if (OUT / "wayback_timeline.csv").exists():
        existing = {row["path"]: row for row in pd.read_csv(OUT / "wayback_timeline.csv").to_dict("records")}
    eligible = [row for row in selected if row["release_date"] <= cutoff and row["capture_dates"][-1] <= cutoff]
    sequences = {}
    roles = {}
    for code in polygons:
        rows = [row for row in eligible if row["code"] == code]
        pair = inspection_pair(rows, cutoff)
        roles.update({(code, row["release_id"]): role for role, row in pair.items()})
        for i, row in enumerate(rows):
            row["sequence"] = i + 1
            row["image_type"] = roles.get((code, row["release_id"]), f"stage_{i+1:02d}")
            sequences[(code, row["release_id"])] = row
    def render(row):
        code, release = row["code"], row["release_id"]
        current = sequences.get((code, release))
        image_type = current["image_type"] if current else "post_cutoff_" + release
        destination = APP / "images" / f"{code}_{image_type}.jpg"
        dates = row["capture_dates"]
        scene_credit = "Esri World Imagery Wayback; imagery: " + "; ".join(row.get("context_providers", row["providers"]))
        service_credit = re.sub(r"<[^>]+>", " ", service_items[release].get("access_information") or "Esri and imagery licensors")
        credit = scene_credit + ". Service credits: " + " ".join(service_credit.split())
        title = f"{code} | capture {dates[0]}" + (f" to {dates[-1]} (mixed)" if len(dates) > 1 else "")
        relative = destination.relative_to(APP).as_posix()
        previous = existing.get(relative, {})
        unchanged = (str(previous.get("release_id")) == str(release) and previous.get("attribution") == credit
                     and previous.get("capture_dates") == json.dumps(dates))
        if not destination.exists() or not unchanged:
            # Reuse the same licensed static render; update report attribution
            # locally without acquiring any offline map tiles.
            image, _ = S.static_wayback_map(polygons[code], catalogue[release], scene_credit)
            S.annotated_figure(image, polygons[code], S.frame_extent(polygons[code]), title, [
                "Wayback release " + row["release_date"] + " | " + credit,
                "Cyan: reviewed working boundary, not a legal survey. Source dates may vary within the map.",
                "Static educational report figure. Third-party imagery rights retained; not an open imagery dataset."], destination)
        return {"code": code, "image_type": image_type, "role": roles.get((code, release), "timeline"),
                "sequence": current["sequence"] if current else None,
                "path": destination.relative_to(APP).as_posix(), "capture_date": dates[0] if len(dates) == 1 else "",
                "capture_date_min": dates[0], "capture_date_max": dates[-1], "capture_dates": json.dumps(dates),
                "mixed_capture_dates": len(dates) > 1, "release_id": release, "release_date": row["release_date"],
                "publication_date": row["release_date"], "source": "Esri World Imagery Wayback",
                "resolution_m": json.dumps(row["resolution_m"]),
                "attribution": credit, "source_url": "https://www.arcgis.com/home/item.html?id=" + catalogue[release]["itemID"],
                "service_attribution": " ".join(service_credit.split()),
                "metadata_url": row["metadata_url"], "metadata_coverage_fraction": row["coverage_fraction"],
                "metadata_dated_coverage_fraction": row.get("dated_coverage_fraction"),
                "metadata_context_coverage_fraction": row.get("context_coverage_fraction"),
                "context_providers": json.dumps(row.get("context_providers", row["providers"])),
                "source_resolution_m": json.dumps(row["resolution_m"]), "source_accuracy_m": json.dumps(row["accuracy_m"]),
                "project_cutoff_eligible": bool(current), "method": "esri_static_print",
                "bbox_3857": json.dumps(S.frame_extent(polygons[code])),
                "usage": "Attributed static report figure; Esri and imagery-provider terms apply; not MIT",
                "pair_asof": cutoff,
                "pair_rule": "After: latest published capture by as-of; before: latest capture at least 12 months before after; mixed dates use their maximum",
                "sha256": hashlib.sha256(destination.read_bytes()).hexdigest()}
    completed, errors = [], []
    with ThreadPoolExecutor(max_workers=2) as pool:
        jobs = {pool.submit(render, row): row for row in selected}
        for i, future in enumerate(as_completed(jobs), 1):
            row = jobs[future]
            try:
                completed.append(future.result())
            except Exception as error:  # noqa: BLE001 -- source failure is recorded explicitly
                errors.append({"code": row["code"], "release_id": row["release_id"], "error": str(error)[:500]})
            print(f"Wayback static figures {i}/{len(jobs)}; available={len(completed)}", flush=True)
    completed.sort(key=lambda r: (r["code"], r["capture_date_max"], r["release_date"]))
    save_csv(OUT / "wayback_timeline.csv", completed)
    save_csv(APP / "images/images.csv", [row for row in completed if row["role"] in {"before", "after"}])
    save_json(OUT / "wayback_render_errors.json", errors)
    return completed


def select_sentinel(polygons, start, end):
    union = unary_union(list(polygons.values()))
    candidates = S.stac_candidates(union.bounds, start, end)
    if not candidates:
        candidates = S.stac_candidates(union.bounds, start, end, collection="sentinel-2-l2a")
    candidates = [item for item in candidates if shape(item["geometry"]).covers(union)]
    complete_quarter = str(pd.Timestamp(end).to_period("Q").end_time.date()) == end
    target = pd.Timestamp(end) - pd.Timedelta(days=15 if complete_quarter else 0)
    candidates.sort(key=lambda item: (abs((pd.Timestamp(item["properties"]["datetime"]).tz_localize(None) - target).days),
                                       item["properties"].get("eo:cloud_cover", 100)))
    choice, failures = None, []
    for item in candidates[:5]:
        try:
            rgb, transform_, bad, measurements = S.read_sentinel_window(item, list(polygons.values()))
            quality = dict(zip(polygons, measurements))
            score = max(q["bad_fraction"] for q in quality.values())
            if choice is None or score < choice[0]:
                choice = score, bad, item, rgb, transform_, quality
            if score <= .01:
                break
        except Exception as error:  # noqa: BLE001 -- record source-specific failures; try another actual scene
            failures.append(str(error)[:200])
    if choice is None or choice[0] > .10:
        from src.pipeline.imagery_earth_engine import thumbnail_window
        return thumbnail_window(polygons, start, end)
    _, bad, item, rgb, transform_, quality = choice
    info = {"scene_id": item["id"], "capture_date": item["properties"]["datetime"][:10],
            "product_created": item["properties"].get("created"), "collection": item.get("collection"),
            "local_bad_fraction": bad, "quality_by_code": quality,
            "tile_cloud_percent": item["properties"].get("eo:cloud_cover"),
            "visual_url": item["assets"]["visual"]["href"], "scl_url": item["assets"]["scl"]["href"],
            "candidates_in_first_page": len(candidates), "resolution_m": 10, "source_crs": "EPSG:32636",
            "method": "earth_search_public_cog", "product_level": "L2A surface reflectance",
            "quality_method": "SCL at 20 m, nearest-resampled to RGB 10 m grid",
            "selection_target_date": str(target.date()),
            "visualization_policy": "fixed_reflectance_0_0.6",
            "visualization": "Source red/green/blue calibration, reflectance 0-0.6, gamma 1.0; no per-scene stretch",
            "band_calibration": {b: {k: item["assets"][b]["raster:bands"][0][k] for k in ("scale", "offset")} for b in ("red", "green", "blue")},
            "rgb_band_urls": {b: item["assets"][b]["href"] for b in ("red", "green", "blue")},
            "note": "Retrospective visual context. Processing/availability may postdate capture; not model X or historical availability proof."}
    return rgb, transform_, info


def calibrate_cached_scenes(polygons):
    """Replace saturated preview display with a fixed source-reflectance rendering."""
    paths = sorted((OUT / "sentinel_scenes").glob("*.json"))
    def update(path):
        info = json.loads(path.read_text(encoding="utf-8"))
        if info.get("visualization_policy") == "fixed_reflectance_0_0.6":
            return
        old = np.load(path.with_suffix(".npz"))["rgb"]
        before = [float((channel == 255).mean()) for channel in old]
        if info["method"].startswith("earth_engine"):
            from src.pipeline.imagery_earth_engine import revisualize_window
            rgb, transform_, info = revisualize_window(info, polygons)
        else:
            url = S.STAC + "/collections/" + info["collection"] + "/items/" + info["scene_id"]
            item = S.cached_request(url)
            rgb, transform_, calibration, urls = S.read_reflectance_window(item, list(polygons.values()))
            info.update({"band_calibration": calibration, "rgb_band_urls": urls,
                         "preview_url": info.get("visual_url"), "source_item_url": url,
                         "visualization_policy": "fixed_reflectance_0_0.6",
                         "visualization": "Source red/green/blue calibration, reflectance 0-0.6, gamma 1.0; no per-scene stretch"})
        info["preview_saturation_fraction"] = before
        info["calibrated_saturation_fraction"] = [float((channel == 255).mean()) for channel in rgb]
        np.savez_compressed(path.with_suffix(".npz"), rgb=rgb, transform=np.array(tuple(transform_)))
        save_json(path, info)
        print(f"Calibrated {path.stem}: red clipped {before[0]:.3f} -> {info['calibrated_saturation_fraction'][0]:.3f}", flush=True)
    early, other = [], []
    for path in paths:
        info = json.loads(path.read_text(encoding="utf-8"))
        (early if info["method"].startswith("earth_engine") else other).append(path)
    for path in early:
        update(path)
    with ThreadPoolExecutor(max_workers=3) as pool:
        for future in as_completed([pool.submit(update, path) for path in other]):
            future.result()


def quarterly_sentinel(polygons, through):
    periods = pd.period_range(START, through, freq="Q")
    all_rows, logs = [], []
    for period in periods:
        start, end = str(period.start_time.date()), min(str(period.end_time.date()), through)
        cache = OUT / "sentinel_scenes" / f"{period}.npz"
        meta_path = cache.with_suffix(".json")
        try:
            if cache.exists() and meta_path.exists():
                saved = np.load(cache)
                rgb = saved["rgb"]
                from affine import Affine
                transform_ = Affine(*saved["transform"][:6])
                info = json.loads(meta_path.read_text(encoding="utf-8"))
                if "quality_by_code" not in info:
                    if info["local_bad_fraction"] == 0:
                        info["quality_by_code"] = {code: {"bad_fraction": 0., "valid_fraction": 1.} for code in polygons}
                    else:
                        item = {"assets": {"visual": {"href": info["visual_url"]}, "scl": {"href": info["scl_url"]}}}
                        _, _, _, quality = S.read_sentinel_window(item, list(polygons.values()))
                        info["quality_by_code"] = dict(zip(polygons, quality))
                info.setdefault("method", "earth_search_public_cog")
                info.setdefault("product_level", "L2A surface reflectance")
                info.setdefault("quality_method", "SCL at 20 m, nearest-resampled to RGB 10 m grid")
                if any(q["bad_fraction"] > .10 for q in info["quality_by_code"].values()):
                    rgb, transform_, info = select_sentinel(polygons, start, end)
                if end != str(period.end_time.date()) and info.get("selection_target_date") != end:
                    rgb, transform_, info = select_sentinel(polygons, start, end)
            elif meta_path.exists():
                info = json.loads(meta_path.read_text(encoding="utf-8"))
                rgb, transform_, info = restore_selected_sentinel(info, polygons)
            else:
                rgb, transform_, info = select_sentinel(polygons, start, end)
            cache.parent.mkdir(parents=True, exist_ok=True)
            if info.get("visualization_policy") != "fixed_reflectance_0_0.6":
                raise ValueError("Old saturated preview cache; run imagery_compare --phase calibrate before rendering")
            np.savez_compressed(cache, rgb=rgb, transform=np.array(tuple(transform_)))
            save_json(meta_path, info)
            date = info["capture_date"]
            source = "Google Earth Engine" if info["method"].startswith("earth_engine") else "Earth Search / Element 84 public COGs"
            render_signature = hashlib.sha256(
                rgb.tobytes() + json.dumps({
                    "transform": tuple(transform_), "info": {k: v for k, v in info.items() if k != "rendered_source_sha256"},
                    "boundaries": {code: polygon.wkb_hex for code, polygon in polygons.items()},
                    "through": through, "style": "fixed_rgb06_640_v1",
                }, sort_keys=True).encode()
            ).hexdigest()
            regenerate = info.get("rendered_source_sha256") != render_signature
            for code, polygon in polygons.items():
                quality = info["quality_by_code"][code]
                destination = OUT / "sentinel" / f"{code}_{period}_{date}_640_rgb06.jpg"
                if regenerate or not destination.exists():
                    image = S.sentinel_figure(rgb, transform_, S.frame_extent(polygon), info.get("source_crs", "EPSG:32636"))
                    label = str(period) + (" partial" if end != str(period.end_time.date()) else "")
                    S.annotated_figure(image, polygon, S.frame_extent(polygon), f"{code} | {label} | capture {date}", [
                        f"Contains modified Copernicus Sentinel data {date[:4]}. Source: {source}.",
                        f"Native RGB 10 m; {info['product_level']}. Bad fraction for this compound: {quality['bad_fraction']:.3f}.",
                        "Fixed RGB reflectance display 0-0.6, gamma 1.0; no per-scene contrast fitting.",
                        info["quality_method"] + ". One actual scene, not a quarterly composite or finishing measurement."], destination)
                public_info = {k: json.dumps(v) if isinstance(v, (dict, list)) else v for k, v in info.items()
                               if k not in {"quality_by_code", "rendered_source_sha256"}}
                public_info["display_source_sha256"] = render_signature
                public_info["source_url"] = info.get("source_item_url", info.get("visual_url"))
                if "rgb_band_urls" in info:
                    public_info["preview_url"] = info.get("preview_url", info.get("visual_url"))
                    public_info.pop("visual_url", None)
                all_rows.append({"code": code, "quarter": str(period), "capture_date": date,
                                 "path": destination.relative_to(APP).as_posix(), "status": "available", **public_info,
                                 "compound_bad_fraction": quality["bad_fraction"], "compound_valid_fraction": quality["valid_fraction"],
                                 "partial_quarter": end != str(period.end_time.date()),
                                 "observation_end": through,
                                 "retrospective_visual_context": True,
                                 "capture_within_project_window": date <= qend(qindex(CFG["asof"])).date().isoformat(),
                                 "attribution": f"Contains modified Copernicus Sentinel data {date[:4]}",
                                 "bbox_3857": json.dumps(S.frame_extent(polygon)),
                                 "sha256": hashlib.sha256(destination.read_bytes()).hexdigest()})
            info["rendered_source_sha256"] = render_signature
            save_json(meta_path, info)
            logs.append({"quarter": str(period), "status": "available", **info})
            print(f"Sentinel {period}: {date}, {info['method']}, local bad={info['local_bad_fraction']:.4f}", flush=True)
        except Exception as error:  # noqa: BLE001 -- preserve honest per-period availability and continue the remaining periods
            logs.append({"quarter": str(period), "status": "unavailable", "reason": str(error)[:600]})
            for code in polygons:
                all_rows.append({"code": code, "quarter": str(period), "status": "unavailable", "reason": str(error)[:600]})
            print(f"Sentinel {period}: unavailable; {str(error)[:120]}", flush=True)
        save_csv(OUT / "sentinel_quarterly.csv", all_rows)
        save_json(OUT / "sentinel_selection.json", logs)
    return all_rows


def report(polygons):
    wayback = pd.read_csv(OUT / "wayback_timeline.csv")
    wayback = wayback.astype(object).where(wayback.notna(), "")
    sentinel = pd.read_csv(OUT / "sentinel_quarterly.csv")
    sentinel = sentinel.astype(object).where(sentinel.notna(), "")
    cards, counts = [], []
    for code in polygons:
        w = wayback[wayback.code.eq(code)]
        s = sentinel[sentinel.code.eq(code) & sentinel.status.eq("available")]
        counts.append({"code": code, "wayback_frames": len(w), "wayback_first_capture": w.capture_date_min.min() if len(w) else None,
                       "wayback_last_capture": w.capture_date_max.max() if len(w) else None,
                       "sentinel_available_quarters": len(s), "sentinel_missing_quarters": len(sentinel[sentinel.code.eq(code)]) - len(s)})
        cards.append(f'<section id="{code}"><h2>{code}</h2><h3>Wayback: actual distinct capture states</h3><div class="grid">')
        for row in w.to_dict("records"):
            label = row["capture_date_min"] + (" to " + row["capture_date_max"] + " (mixed)" if row["mixed_capture_dates"] else "")
            cards.append(f'<figure><a href="../{row["path"]}"><img loading="lazy" src="../{row["path"]}"></a>'
                         f'<figcaption>{html.escape(str(label))}; published {row["release_date"]}<br>{html.escape(row["attribution"])} '
                         f'<a href="{html.escape(row["source_url"], quote=True)}">Source item</a></figcaption></figure>')
        cards.append('</div><details><summary>Quarterly Sentinel-2 timeline (10 m context)</summary><div class="grid">')
        for row in s.to_dict("records"):
            label = row["quarter"] + (" (partial)" if row.get("partial_quarter") else "")
            cards.append(f'<figure><a href="../{row["path"]}"><img loading="lazy" src="../{row["path"]}"></a>'
                         f'<figcaption>{label}: {row["capture_date"]}; {html.escape(row["attribution"])} '
                         f'<a href="{html.escape(row["source_url"], quote=True)}">Source</a></figcaption></figure>')
        cards.append('</div></details></section>')
    doc = '<!doctype html><html lang="en"><meta charset="utf-8"><title>R7 observed imagery timelines</title><style>'
    doc += 'body{font:16px system-ui;max-width:1500px;margin:24px auto;padding:0 18px;background:#f5f7fa;color:#172335}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(360px,1fr));gap:14px}figure{margin:0;background:white;padding:8px}img{width:100%}figcaption{font-size:13px}section{margin:32px 0}summary{cursor:pointer;padding:15px;background:#dce7f4}</style>'
    doc += '<h1>R7 observed imagery timelines</h1><p>Static educational map report. Actual capture dates and publication dates are separate. Mixed dates remain mixed. Boundary alignment is contextual, not a legal survey. Images are not model features or proof of finishing.</p>'
    doc += '<p>Wayback figures retain Esri and source-provider rights; the repository software licence does not cover that imagery. Sentinel figures contain modified Copernicus Sentinel data, served by Earth Search / Element 84.</p><nav>'
    doc += ' | '.join(f'<a href="#{code}">{code}</a>' for code in polygons) + '</nav>' + ''.join(cards) + '</html>'
    (OUT / "index.html").write_text(doc, encoding="utf-8")
    save_csv(OUT / "comparison.csv", counts)
    print(json.dumps(counts), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=["prepare", "discover", "render", "calibrate", "sentinel", "report", "all"], default="all")
    parser.add_argument("--through", default=configured_through(), help="ISO observation end; defaults to configs/data.yaml asof quarter-end")
    args = parser.parse_args()
    args.through = pd.Timestamp(args.through).date().isoformat()
    if args.through < START or args.through > pd.Timestamp.now(tz="UTC").date().isoformat():
        parser.error("Observation end must be within the study period and not in the future")
    polygons = boundaries()
    OUT.mkdir(parents=True, exist_ok=True)
    if args.phase == "prepare":
        print(f"Installed {prepare_metadata()} source-selection metadata files; no images installed")
    if args.phase in ("discover", "all"):
        wayback_discovery(polygons, args.through)
    if args.phase in ("render", "all"):
        wayback_render(polygons)
    if args.phase in ("calibrate", "all"):
        calibrate_cached_scenes(polygons)
    if args.phase in ("sentinel", "all"):
        quarterly_sentinel(polygons, args.through)
    if args.phase in ("report", "all"):
        report(polygons)


if __name__ == "__main__":
    main()
