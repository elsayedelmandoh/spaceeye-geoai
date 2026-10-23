"""docs/: data_dictionary (.xlsx + .md, EN + AR), answer_key.md (+ answer_key_rows.csv), validation_report.html."""
from __future__ import annotations

import numpy as np
import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Alignment, Font, PatternFill

from .common import Ctx
from .dictionary import DATASETS, PILLARS

SPEC_RATE = {"DQ1": "1–3%", "DQ2": "3–48 h blocks", "DQ3": "0.5%", "DQ4": "at DST dates", "DQ5": "0.1%", "DQ6": "1 block each",
             "DQ6b": "extra (Day 1)", "DQ7": "whole series", "DQ8": "10%", "DQ9": "5%", "DQ10": "1 sensor", "DQ11": "2%", "DQ12": "+1%/week"}
DQ_NAME = {"DQ1": "Random missing values", "DQ2": "Outage blocks", "DQ3": "Duplicate rows (retransmission)", "DQ4": "DST duplicates/gaps",
           "DQ5": "Spikes and impossible values", "DQ6": "Stuck sensor", "DQ6b": "Stuck traffic sensor (Day 1 dashboard)",
           "DQ7": "Unit mismatch", "DQ8": "Mixed timestamp formats / UTC vs local", "DQ9": "Inconsistent categories",
           "DQ10": "Orphan key", "DQ11": "Late-arriving records", "DQ12": "Slow drift"}


def _file_stats(ctx: Ctx) -> pd.DataFrame:
    rows = []
    for name, (pillar, *_r) in DATASETS.items():
        p = ctx.ref_dir / f"{name}.csv" if pillar == "reference" else ctx.data_dir / f"{name}.csv"
        if not p.exists():
            continue
        df = pd.read_csv(p, low_memory=False)
        rows.append((name, str(p.relative_to(ctx.root)), len(df), round(p.stat().st_size / 1e6, 2), round(df.isna().mean().mean() * 100, 2)))
    return pd.DataFrame(rows, columns=["dataset", "file", "rows", "size_mb", "empty_cells_pct"]).set_index("dataset")


def write_dictionary(ctx: Ctx) -> None:
    docs = ctx.root / "docs"; docs.mkdir(exist_ok=True)
    st = _file_stats(ctx)
    ds_rows, col_rows = [], []
    for name, (pillar, g_en, g_ar, d_en, d_ar, cols) in DATASETS.items():
        pe, pa = PILLARS[pillar]
        s = st.loc[name] if name in st.index else None
        ds_rows.append({"dataset": name, "file": s.file if s is not None else "", "pillar_en": pe, "pillar_ar": pa,
                        "grain_en": g_en, "grain_ar": g_ar, "description_en": d_en, "description_ar": d_ar,
                        "rows_lite": int(s.rows) if s is not None else "", "size_mb_lite": s.size_mb if s is not None else ""})
        for c, t, u, ce, ca in cols:
            col_rows.append({"dataset": name, "column": c, "type": t, "unit": u, "description_en": ce, "description_ar": ca})
    D = pd.DataFrame(ds_rows); C = pd.DataFrame(col_rows)
    about = pd.DataFrame({"item": ["Kit", "Label", "Edition", "Period", "Time zone", "Weekend", "Seed", "Build", "Personal data"],
                          "value_en": ["Oasis District synthetic city data kit (fictional)", ctx.cfg["label_en"], "lite (CSV)",
                                       f"{ctx.start.date()} to {ctx.end.date()}", "Africa/Cairo, local time, with daylight saving",
                                       "Friday and Saturday", str(ctx.seed), "python -m oasis_datakit build  ·  make all",
                                       "None real. requester_name / requester_phone are synthetic, for masking practice only."],
                          "value_ar": ["حقيبة بيانات حي الواحة الاصطناعية (حي افتراضي)", ctx.cfg["label_ar"], "النسخة المختصرة (CSV)",
                                       "من ١ مارس إلى ٣٠ يونيو ٢٠٢٥", "توقيت القاهرة المحلي مع التوقيت الصيفي", "الجمعة والسبت",
                                       str(ctx.seed), "python -m oasis_datakit build", "لا توجد بيانات حقيقية. حقلا الاسم والهاتف اصطناعيان لتمرين الإخفاء فقط."]})
    path = docs / "data_dictionary.xlsx"
    with pd.ExcelWriter(path, engine="openpyxl") as xw:
        about.to_excel(xw, sheet_name="About", index=False)
        D.to_excel(xw, sheet_name="Datasets", index=False)
        C.to_excel(xw, sheet_name="Columns", index=False)
    wb = load_workbook(path)
    head = PatternFill("solid", fgColor="773533")
    for ws in wb.worksheets:
        for cell in ws[1]:
            cell.font = Font(bold=True, color="FFFFFF", name="Arial"); cell.fill = head
        hdr = [c.value for c in ws[1]]
        for col_idx, h in enumerate(hdr, 1):
            letter = ws.cell(1, col_idx).column_letter
            width = {"description_en": 60, "description_ar": 60, "value_en": 60, "value_ar": 55}.get(h, 22)
            ws.column_dimensions[letter].width = width
            for row in ws.iter_rows(min_row=2, min_col=col_idx, max_col=col_idx):
                for cell in row:
                    cell.font = Font(name="Arial", size=10)
                    if h and h.endswith("_ar"):
                        cell.alignment = Alignment(horizontal="right", readingOrder=2, wrap_text=True, vertical="top")
                    else:
                        cell.alignment = Alignment(wrap_text=True, vertical="top")
        ws.freeze_panes = "A2"
    import datetime as _dt
    wb.properties.created = wb.properties.modified = _dt.datetime(2025, 7, 1)   # fixed metadata → identical file on every build
    wb.properties.creator = "oasis_datakit"
    wb.save(path)

    # Markdown
    L = ["# Oasis District data dictionary · قاموس بيانات حي الواحة", "",
         f"> **{ctx.cfg['label_en']}**", ">", f"> **{ctx.cfg['label_ar']}**", "",
         "Fictional district. Not real operational data. Lite edition: 1 March – 30 June 2025, CSV, local time Africa/Cairo (with daylight saving), weekend Friday–Saturday.", "",
         "حي افتراضي، وليست بيانات ACUD. النسخة المختصرة: من ١ مارس إلى ٣٠ يونيو ٢٠٢٥، بصيغة CSV، بالتوقيت المحلي للقاهرة، والعطلة الأسبوعية الجمعة والسبت.", "",
         "## Files · الملفات", "", "| Dataset | Pillar | Grain | Rows (lite) | MB |", "|---|---|---|---:|---:|"]
    for r in ds_rows:
        L.append(f"| `{r['dataset']}` | {r['pillar_en']} | {r['grain_en']} | {r['rows_lite']:,} | {r['size_mb_lite']} |" if r["rows_lite"] != "" else f"| `{r['dataset']}` | {r['pillar_en']} | {r['grain_en']} | — | — |")
    L += ["", "GeoJSON: `reference/zones.geojson` (zone polygons), `reference/roads.geojson` (road segments). Coordinates are fictional.", ""]
    for name, (pillar, g_en, g_ar, d_en, d_ar, cols) in DATASETS.items():
        pe, pa = PILLARS[pillar]
        L += [f"## `{name}`", "", f"**{pe}** · {g_en}. {d_en}", "", f'<p dir="rtl" align="right"><b>{pa}</b> · {g_ar}. {d_ar}</p>', "",
              "| Column | Type | Unit | Description | الوصف |", "|---|---|---|---|---|"]
        for c, t, u, ce, ca in cols:
            L.append(f"| `{c}` | {t} | {u} | {ce} | {ca} |")
        L.append("")
    (docs / "data_dictionary.md").write_text("\n".join(L), encoding="utf-8")


def _ranges(idx) -> str:
    idx = sorted(int(i) for i in idx)
    if not idx:
        return "—"
    out, s, p = [], idx[0], idx[0]
    for i in idx[1:]:
        if i == p + 1:
            p = i; continue
        out.append(f"{s}" if s == p else f"{s}–{p}"); s = p = i
    out.append(f"{s}" if s == p else f"{s}–{p}")
    txt = ", ".join(out)
    return txt if len(txt) < 400 else txt[:400] + " … (full list in answer_key_rows.csv)"


def write_answer_key(ctx: Ctx) -> None:
    docs = ctx.root / "docs"
    rl = ctx.rowlog_df
    rl.to_csv(docs / "answer_key_rows.csv", index=False, encoding="utf-8", lineterminator="\n")
    L = ["# Answer key — INSTRUCTORS ONLY · مفتاح الإجابات — للمدربين فقط", "",
         "> Do not share with learners. Lists every injected defect (DQ) and hidden story (H) in the **lite** edition.", "",
         f"Seed `{ctx.seed}` · edition `lite` · {ctx.start.date()} → {ctx.end.date()}.", "",
         "**Row numbers** are `row_index` = 0-based position after `pd.read_csv(file)` (header excluded; file line = row_index + 2). "
         "Every tagged row is in `docs/answer_key_rows.csv` (dataset, row_index, kind, tag). Rows that were *removed* (outages, DST gap) are described by time window.", "",
         "## 1 · Defects", "", "| ID | Defect | Dataset | Rows affected | Rate | Spec | Detail |", "|---|---|---|---:|---:|---|---|"]
    for e in ctx.log:
        if not e["id"].startswith("DQ"):
            continue
        L.append(f"| {e['id']} | {DQ_NAME[e['id']]} | `{e['dataset']}` | {e['rows']:,} | {e['rate']*100:.2f}% | {SPEC_RATE[e['id']]} | {e['detail']} |")
    L += ["", "DQ1 is applied to every sensor dataset (traffic, parking, electricity, streetlights, water meters, pressure, water quality, bins, cameras, BMS, air, noise). "
          "Event tables (incidents, requests, tickets, work orders, trips) and transit/gov_services counts are not sensor feeds.", ""]
    # DQ2 blocks
    L += ["### DQ2 · outage blocks (rows absent)", "", "| Dataset | Sensor | From | To | Hours | Rows removed |", "|---|---|---|---|---:|---:|"]
    for e in ctx.log:
        if e["id"] == "DQ2":
            for b in e["blocks"]:
                L.append(f"| `{e['dataset']}` | {b['sensor']} | {b['start']} | {b['end']} | {b['hours']} | {b['rows_removed']} |")
    L += ["", "### DQ4 · daylight saving", "",
          "Cairo moved clocks forward at **Fri 2025-04-25 00:00 → 01:00**. Fall-back (2025-10-31) is outside the lite window.", "",
          "- **Phantom rows** (gateway not DST-aware): `traffic_counts`, `network_pressure` (00:00, 00:15, 00:30, 00:45) and `bin_fill` (00:00) carry timestamps that do not exist in Africa/Cairo.",
          "- **Gap / 23-hour day** (DST-aware systems): `parking_occupancy`, `electricity_meters`, `water_meters`, `bms_readings`, `air_quality`, `noise` have no 00:00 row on 2025-04-25.", ""]
    for e in ctx.log:
        if e["id"] == "DQ7":
            L.append(f"**DQ7** `{e['dataset']}`: {', '.join(e['buildings'])} — {e['detail']}  ")
    L.append("")
    for e in ctx.log:
        if e["id"] == "DQ9":
            L += [f"**DQ9 variants in `{e['dataset']}`** (canonical → variants):", ""]
            for k, v in e["variants"].items():
                L.append(f"- {k} → " + " · ".join(f"«{x}»" for x in v))
            L.append("")
    L += ["### Row positions per defect", "", "| Tag | Dataset | Rows | Row index ranges |", "|---|---|---:|---|"]
    if len(rl):
        for (t, ds), g in rl[rl.kind == "defect"].groupby(["tag", "dataset"]):
            L.append(f"| {t} | `{ds}` | {len(g):,} | {_ranges(g.row_index) if len(g) < 3000 else 'see answer_key_rows.csv'} |")
    # stories
    s = ctx.cfg["stories"]
    F = getattr(ctx, "facts", {"h5_pm10_max": [float("nan")] * 2, "h5_speed_drop": float("nan")})
    L += ["", "## 2 · Hidden stories", ""]
    story_txt = {
        "H1": f"**H1 · Water main break, Zone 2 — Tue {s['H1']['date']} 06:40.** PRS-07 holds ≈4.2 bar to 06:30 and reads ≈2.0–2.2 bar from 06:45 (first 15-min reading after the break) until 09:15; recovery 2.7 → 3.4 → 3.95 bar at 09:30–10:00. Flow at PRS-07 ≈ ×2.6; PRS-05/06/08 drop ≈0.55 bar. "
              "Zone 2 traffic slows (speed ×0.58, 06:45–10:00); Zone 2 metered buildings lose supply 06:40–09:30 then rebound; 46 water requests («تسرب مياه» / «انقطاع المياه») from Zone 2 between 06:50 and ~11:00; "
              "incident (utility_failure, severity 1, sensor) at 06:44 and road hazard at 07:05; ops ticket severity 1 at 06:45, escalated to pillar_owner, resolved 09:35; work orders on VLV-07 and PMP-02; WQ-02 turbidity 2.8 NTU that day; Line B on-time % down.",
        "H3": f"**H3 · Sensor drift TRF-017 from {s['H3']['start']}.** All `traffic_counts` rows with `sensor_id == 'TRF-017'`: vehicle_count × (1 + 0.01 × weeks since 1 March). Same injection as DQ12.",
        "H5": f"**H5 · Dust storm — 2025-04-09 and 2025-04-10.** Daily max PM10 {F['h5_pm10_max'][0]:,.0f} µg/m³ on 9 April and {F['h5_pm10_max'][1]:,.0f} on 10 April; mean traffic speed −{F['h5_speed_drop']*100:.0f}% on 9 April; extra traffic_accident / road_hazard incidents; turbidity up; cleanliness requests up. Smaller dust days (not H5): 2025-03-20, 2025-05-04, 2025-05-05.",
        "H6": f"**H6 · Citizen app launch — {s['H6']['date']}.** Channel `app` appears; total requests rise to ≈×{s['H6']['uplift']} within {s['H6']['ramp_days']} days (17–30 June vs 17–30 May = +{F['h6']['pct']:.1f}%: {F['h6']['last14']:,} vs {F['h6']['same14_may']:,}); call-centre volume falls ≈30%; median resolution time and satisfaction stay flat. Rows: every `service_requests` row created on or after 2025-06-15. The 'more complaints' reading is misleading.",
        "H7": "**H7 · Ramadan — 2025-03-01 to 2025-03-29.** Morning traffic peak later and lower, dip at iftar (≈18:00), strong evening peak after iftar; residential electricity and water up in the evening (and water at suhoor). Seasonality, not anomaly. Rows: every hourly / 15-min row on those dates.",
        "H8": f"**H8 · Camera outage cluster, Zone 5 — {s['H8']['start']} to {s['H8']['end']}.** Z05 camera uptime ≈75%; ≈62% of CCTV-sourced incidents in Z05 are never recorded, so CCTV incidents fall (safety did not improve); 14 P1 CCTV work orders; ops ticket 2025-04-24 06:50.",
        "H2": "**H2 · Heatwave (mid-July)** — outside the lite window. Full edition, Phase 2.",
        "H4": "**H4 · New waste schedule in Z04 from 2025-09-01** — outside the lite window. Full edition, Phase 2.",
    }
    for h in ["H1", "H3", "H5", "H6", "H7", "H8", "H2", "H4"]:
        L += [story_txt[h], ""]
        if len(rl):
            g = rl[(rl.kind == "story") & (rl.tag == h)]
            if len(g):
                L += ["| Dataset | Rows | Row index ranges |", "|---|---:|---|"]
                for ds, gg in g.groupby("dataset"):
                    L.append(f"| `{ds}` | {len(gg):,} | {_ranges(gg.row_index)} |")
                L.append("")
    extra = getattr(ctx, "answer_extra", [])
    if extra:
        L += ["## 3 · Exact values used on Day 1", ""] + extra
    (docs / "answer_key.md").write_text("\n".join(L), encoding="utf-8")


def write_all(ctx: Ctx) -> None:
    write_dictionary(ctx)
    from . import validation
    validation.write_report(ctx)       # also fills ctx.answer_extra with checked numbers
    write_answer_key(ctx)
