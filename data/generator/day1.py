"""Day 1 assets: hello_oasis.ipynb, warm-up (+ solution), dashboard_day1.html, day1_chart_values.md."""
from __future__ import annotations

import html
import json
from pathlib import Path

import nbformat
import numpy as np
import pandas as pd
from nbclient import NotebookClient
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook

from .common import Ctx
from .validation import parse_sr_time

LABS = "labs/D01"
LABEL_MD = "*Synthetic data — for training only*  \n<div dir=\"rtl\" align=\"right\"><i>بيانات اصطناعية لأغراض التدريب فقط</i></div>"

SETUP = '''# Setup — find the Oasis data kit folder (works on your laptop and on Google Colab)
import os, sys, pathlib, subprocess

KIT_REPO_URL = "https://github.com/ORG/oasis_datakit.git"  # [to be confirmed: the kit's Git address]

def find_kit():
    here = pathlib.Path.cwd()
    for folder in [here, *here.parents]:
        if (folder / "config.yaml").exists() and (folder / "reference").is_dir():
            return folder
    return None

kit = find_kit()
if kit is None and "google.colab" in sys.modules:
    subprocess.run(["git", "clone", "--depth", "1", KIT_REPO_URL, "/content/oasis_datakit"], check=True)
    kit = pathlib.Path("/content/oasis_datakit")
if kit is None:
    raise FileNotFoundError("Open this notebook from inside the oasis_datakit folder.")
os.chdir(kit)
print("Working in:", kit)'''

HELLO_CODE = '''import pandas as pd

zones = pd.read_csv("reference/zones.csv")

print(zones[["zone_id", "name_en",
             "name_ar", "population_start"]])

print("Total residents:",
      zones["population_start"].sum())'''


def _nb(cells, title):
    for i, c in enumerate(cells):          # stable cell ids → identical files on every build
        c["id"] = f"cell-{i:02d}"
    nb = new_notebook(cells=cells)
    nb.metadata["kernelspec"] = {"display_name": "Python 3", "language": "python", "name": "python3"}
    nb.metadata["language_info"] = {"name": "python"}
    nb.metadata["title"] = title
    return nb


def _execute(nb, cwd: Path):
    NotebookClient(nb, timeout=300, kernel_name="python3", record_timing=False, resources={"metadata": {"path": str(cwd)}}).execute()
    return nb


def hello_notebook():
    return _nb([
        new_markdown_cell("# Hello, Oasis · مرحبًا بحي الواحة\n\nDay 1 · Lab Part A. If this notebook runs to the end, your environment is ready.\n\n"
                          "<div dir=\"rtl\" align=\"right\">اليوم ١ · المعمل، الجزء أ. إذا عمل هذا الدفتر حتى النهاية فبيئة العمل جاهزة.</div>\n\n" + LABEL_MD),
        new_code_cell(SETUP),
        new_markdown_cell("## Load the zones · تحميل المناطق\n\nThe six lines from the slide. Expect about **60,000** residents.\n\n<div dir=\"rtl\" align=\"right\">الأسطر الستة من الشريحة. النتيجة المتوقعة نحو ٦٠ ألف نسمة.</div>"),
        new_code_cell(HELLO_CODE),
        new_markdown_cell("## Check: Arabic shows correctly · تحقّق: العربية تظهر سليمة\n\nIf the Arabic names below look like boxes or symbols, tell the instructor (file encoding).\n\n"
                          "<div dir=\"rtl\" align=\"right\">إذا ظهرت الأسماء العربية رموزًا غير مفهومة فأبلغ المدرب (مشكلة في الترميز).</div>"),
        new_code_cell('zones[["zone_id", "name_ar"]]'),
        new_code_cell('import sys, platform\nprint("Python", sys.version.split()[0], "·", platform.system())\nprint("pandas", pd.__version__)\nprint("Ready ✓  · جاهز")'),
    ], "Hello, Oasis")


TASKS = [
    ("Task 1 · Python · easy", "المهمة ١ · Python · سهلة",
     "Load `reference/zones.csv`. Which zone has the most residents? Print its `name_en` and `name_ar`.",
     "حمّل الملف `reference/zones.csv`. أي منطقة بها أكبر عدد من السكان؟ اطبع اسمها بالإنجليزية والعربية.",
     "Hint: `sort_values` or `idxmax`.",
     '''zones = pd.read_csv("reference/zones.csv")
top = zones.sort_values("population_start", ascending=False).iloc[0]
print(top["zone_id"], top["name_en"], top["name_ar"], top["population_start"])'''),
    ("Task 2 · Python · easy", "المهمة ٢ · Python · سهلة",
     "Load `reference/calendar.csv`. Between 2025-03-01 and 2025-06-30, how many days are Ramadan days and how many are weekend days?",
     "حمّل الملف `reference/calendar.csv`. في الفترة من ١ مارس إلى ٣٠ يونيو ٢٠٢٥، كم يومًا في رمضان؟ وكم يوم عطلة أسبوعية؟",
     "Hint: filter the dates first, then `sum()` the 0/1 columns.",
     '''cal = pd.read_csv("reference/calendar.csv", parse_dates=["date"])
lite = cal[(cal["date"] >= "2025-03-01") & (cal["date"] <= "2025-06-30")]
print("Ramadan days:", lite["is_ramadan"].sum())
print("Weekend days:", lite["is_weekend"].sum())'''),
    ("Task 3 · Python · easy–medium", "المهمة ٣ · Python · سهلة إلى متوسطة",
     "Load `data/lite/air_quality.csv`. Compute the mean PM10 per station. Which station has the highest mean?",
     "حمّل الملف `data/lite/air_quality.csv`. احسب متوسط PM10 لكل محطة. أي محطة متوسطها الأعلى؟",
     "Hint: `groupby(\"station_id\")[\"pm10\"].mean()`.",
     '''aq = pd.read_csv("data/lite/air_quality.csv")
pm10 = aq.groupby("station_id")["pm10"].mean().round(1).sort_values(ascending=False)
print(pm10)
print("Highest:", pm10.index[0])'''),
    ("Task 4 · Python · medium", "المهمة ٤ · Python · متوسطة",
     "Load `data/lite/incidents.csv`. Build a table with one row per zone and one column per severity (1–4), showing the number of incidents.",
     "حمّل الملف `data/lite/incidents.csv`. اصنع جدولًا فيه صف لكل منطقة وعمود لكل مستوى خطورة (١–٤) يعرض عدد الحوادث.",
     "Hint: `pd.crosstab`.",
     '''inc = pd.read_csv("data/lite/incidents.csv")
print(pd.crosstab(inc["zone_id"], inc["severity"]))'''),
    ("Task 5 · SQL · easy", "المهمة ٥ · SQL · سهلة",
     "With DuckDB, count the citizen service requests per `channel` in `data/lite/service_requests.csv`, largest first.",
     "باستخدام DuckDB، احسب عدد طلبات المواطنين لكل قناة (`channel`) في الملف `data/lite/service_requests.csv`، من الأكبر إلى الأصغر.",
     "Hint: `SELECT channel, COUNT(*) ... GROUP BY ... ORDER BY ...`",
     '''duckdb.sql("""
    SELECT channel, COUNT(*) AS requests
    FROM 'data/lite/service_requests.csv'
    GROUP BY channel
    ORDER BY requests DESC
""").df()'''),
    ("Task 6 · SQL · easy–medium", "المهمة ٦ · SQL · سهلة إلى متوسطة",
     "For traffic counter `TRF-001`, compute the average `avg_speed_kmh` for each hour of the day (0–23).",
     "لعداد المرور `TRF-001`، احسب متوسط السرعة `avg_speed_kmh` لكل ساعة من ساعات اليوم (٠–٢٣).",
     "Hint: `hour(timestamp)` gives the hour.",
     '''duckdb.sql("""
    SELECT hour(timestamp) AS hour, ROUND(AVG(avg_speed_kmh), 1) AS avg_speed
    FROM 'data/lite/traffic_counts.csv'
    WHERE sensor_id = 'TRF-001'
    GROUP BY hour
    ORDER BY hour
""").df()'''),
    ("Task 7 · SQL · medium", "المهمة ٧ · SQL · متوسطة",
     "Join `reference/sensors.csv` with `reference/zones.csv`. How many traffic counters (`sensor_type = 'traffic_counter'`) are there in each zone? Show the zone names in both languages.",
     "اربط الملف `reference/sensors.csv` بالملف `reference/zones.csv`. كم عداد مرور في كل منطقة؟ اعرض اسم المنطقة باللغتين.",
     "Hint: `JOIN ... ON s.zone_id = z.zone_id`.",
     '''duckdb.sql("""
    SELECT z.zone_id, z.name_en, z.name_ar, COUNT(*) AS traffic_counters
    FROM 'reference/sensors.csv' s
    JOIN 'reference/zones.csv' z ON s.zone_id = z.zone_id
    WHERE s.sensor_type = 'traffic_counter'
    GROUP BY z.zone_id, z.name_en, z.name_ar
    ORDER BY z.zone_id
""").df()'''),
    ("Task 8 · SQL · medium", "المهمة ٨ · SQL · متوسطة",
     "Which 5 buildings used the most water in May 2025? Show `building_id`, `use_type`, zone name (EN) and total m³. Which zone appears most often in your top 5?",
     "ما المباني الخمسة الأعلى استهلاكًا للمياه في مايو ٢٠٢٥؟ اعرض رمز المبنى ونوع استخدامه واسم المنطقة وإجمالي الاستهلاك بالمتر المكعب. أي منطقة تتكرر أكثر في النتيجة؟",
     "Hint: join three files: water_meters → buildings → zones; filter `month(timestamp) = 5`.",
     '''duckdb.sql("""
    SELECT w.building_id, b.use_type, z.name_en AS zone, ROUND(SUM(w.m3), 1) AS total_m3
    FROM 'data/lite/water_meters.csv' w
    JOIN 'reference/buildings.csv' b ON w.building_id = b.building_id
    JOIN 'reference/zones.csv' z ON b.zone_id = z.zone_id
    WHERE month(w.timestamp) = 5
    GROUP BY w.building_id, b.use_type, z.name_en
    ORDER BY total_m3 DESC
    LIMIT 5
""").df()'''),
]


def warmup_notebook(solution: bool):
    cells = [
        new_markdown_cell("# Day 1 warm-up check · الاختبار التمهيدي لليوم الأول" + (" — SOLUTION · الحل" if solution else "") +
                          "\n\n8 short tasks: 4 in Python (pandas), 4 in SQL (DuckDB). **Not graded.** Do what you can, skip what you can't, and submit the notebook as it is.\n\n"
                          "<div dir=\"rtl\" align=\"right\">٨ مهام قصيرة: ٤ في Python و٤ في SQL. الاختبار غير محسوب في الدرجات. أنجز ما تستطيع وتجاوز ما لا تستطيع، ثم سلّم الدفتر كما هو.</div>\n\n" + LABEL_MD),
        new_code_cell(SETUP),
        new_code_cell('''import pandas as pd
try:
    import duckdb
except ImportError:          # Colab or an older environment
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "duckdb"], check=True)
    import duckdb
print("pandas", pd.__version__, "· duckdb", duckdb.__version__)'''),
    ]
    for en_t, ar_t, en, ar, hint, code in TASKS:
        cells.append(new_markdown_cell(f"## {en_t}\n<div dir=\"rtl\" align=\"right\"><b>{ar_t}</b></div>\n\n{en}\n\n<div dir=\"rtl\" align=\"right\">{ar}</div>\n\n*{hint}*"))
        if solution:
            cells.append(new_code_cell(code))
        else:
            starter = "# your code here · اكتب الكود هنا\n"
            if "duckdb.sql" in code:
                starter += '# duckdb.sql("""\n#     SELECT ...\n#     FROM \'data/lite/....csv\'\n# """).df()\n'
            cells.append(new_code_cell(starter))
    if solution:
        cells.append(new_markdown_cell("## Notes for the instructor · ملاحظات للمدرب\n\n"
                                       "- Task 2: 29 Ramadan days (1–29 March) and 35 weekend days.\n"
                                       "- Task 3: AQ-03 and AQ-06 include a stuck block (DQ6); the dust storm of 9–10 April lifts every station.\n"
                                       "- Task 5: there are no `app` requests before 15 June (the app launch, H6).\n"
                                       "- Task 6: TRF-001 also has phantom rows at 00:00–00:45 on 25 April (DST, DQ4) — they do not change the averages much.\n"
                                       "- Task 8: large residential and commercial buildings top the list; zone names come from the second join.\n"
                                       "- Use the results to balance teams (who finished SQL tasks 7–8?), not to grade."))
    return _nb(cells, "Day 1 warm-up" + (" — solution" if solution else ""))


# ------------------------------------------------------------------ dashboard
C = {"red": "#ED1C24", "maroon": "#773533", "taupe": "#9A746C", "black": "#0C0C0C", "dgrey": "#4A4A4A", "mgrey": "#636263", "lgrey": "#BBBCBF", "pale": "#F1F1F1", "green": "#2E7D32"}


def _svg_line(series, w, h, ymin, ymax, labels, colors, ylab, xticks, highlight=None, flag=None, yticks=None):
    pad_l, pad_b, pad_t, pad_r = 56, 26, 14, 26
    iw, ih = w - pad_l - pad_r, h - pad_t - pad_b
    n = len(labels)
    X = lambda i: pad_l + iw * i / max(n - 1, 1)
    Y = lambda v: pad_t + ih * (1 - (v - ymin) / (ymax - ymin))
    o = [f'<svg viewBox="0 0 {w} {h}" width="100%" role="img" xmlns="http://www.w3.org/2000/svg" font-family="Arial" font-size="11">']
    for t in (yticks or np.linspace(ymin, ymax, 5)):
        o.append(f'<line x1="{pad_l}" x2="{w-pad_r}" y1="{Y(t):.1f}" y2="{Y(t):.1f}" stroke="#E3E3E3"/>')
        o.append(f'<text x="{pad_l-6}" y="{Y(t)+4:.1f}" text-anchor="end" fill="{C["dgrey"]}">{t:,.0f}</text>')
    for i in xticks:
        o.append(f'<text x="{X(i):.1f}" y="{h-8}" text-anchor="middle" fill="{C["dgrey"]}">{html.escape(labels[i])}</text>')
    o.append(f'<text x="12" y="{pad_t+ih/2}" transform="rotate(-90 12 {pad_t+ih/2})" text-anchor="middle" fill="{C["mgrey"]}" font-size="10">{html.escape(ylab)}</text>')
    if highlight is not None:
        a, b = highlight
        o.append(f'<rect x="{X(a)-6:.1f}" y="{pad_t}" width="{X(b)-X(a)+12:.1f}" height="{ih}" fill="{C["red"]}" fill-opacity="0.12"/>')
    for s, col in zip(series, colors):
        pts = " ".join(f"{X(i):.1f},{Y(v):.1f}" for i, v in enumerate(s) if v is not None and not (isinstance(v, float) and np.isnan(v)))
        o.append(f'<polyline points="{pts}" fill="none" stroke="{col}" stroke-width="2.4" stroke-linejoin="round"/>')
    if flag is not None:
        i, v, text = flag
        o.append(f'<circle cx="{X(i):.1f}" cy="{Y(v):.1f}" r="6" fill="{C["red"]}"/>')
        o.append(f'<rect x="{X(i)-58:.1f}" y="{Y(v)+10:.1f}" width="116" height="20" rx="3" fill="{C["red"]}"/>')
        o.append(f'<text x="{X(i):.1f}" y="{Y(v)+24:.1f}" text-anchor="middle" fill="#fff" font-weight="bold">{html.escape(text)}</text>')
    o.append("</svg>")
    return "".join(o)


def _svg_bars(values, labels, w, h, ymin, ymax, yticks, highlight=(), fmt="{:.1f}%"):
    pad_l, pad_b, pad_t, pad_r = 46, 26, 18, 10
    iw, ih = w - pad_l - pad_r, h - pad_t - pad_b
    n = len(values); bw = iw / n * 0.6
    Y = lambda v: pad_t + ih * (1 - (v - ymin) / (ymax - ymin))
    o = [f'<svg viewBox="0 0 {w} {h}" width="100%" role="img" xmlns="http://www.w3.org/2000/svg" font-family="Arial" font-size="11">']
    for t in yticks:
        o.append(f'<line x1="{pad_l}" x2="{w-pad_r}" y1="{Y(t):.1f}" y2="{Y(t):.1f}" stroke="#E3E3E3"/>')
        o.append(f'<text x="{pad_l-6}" y="{Y(t)+4:.1f}" text-anchor="end" fill="{C["dgrey"]}">{t:g}%</text>')
    for i, (v, lab) in enumerate(zip(values, labels)):
        x = pad_l + iw * (i + 0.5) / n - bw / 2
        col = C["red"] if i in highlight else C["maroon"]
        o.append(f'<rect x="{x:.1f}" y="{Y(v):.1f}" width="{bw:.1f}" height="{Y(ymin)-Y(v):.1f}" fill="{col}"/>')
        o.append(f'<text x="{x+bw/2:.1f}" y="{Y(v)-4:.1f}" text-anchor="middle" fill="{C["black"]}" font-weight="bold">{fmt.format(v)}</text>')
        o.append(f'<text x="{x+bw/2:.1f}" y="{h-8}" text-anchor="middle" fill="{C["dgrey"]}">{lab}</text>')
    o.append("</svg>")
    return "".join(o)


AR_DIG = str.maketrans("0123456789.,", "٠١٢٣٤٥٦٧٨٩٫٬")


def ar_num(x) -> str:
    return str(x).translate(AR_DIG)


def dashboard(ctx: Ctx) -> dict:
    D = ctx.data_dir
    sensors = pd.read_csv(ctx.ref_dir / "sensors.csv")
    vals = {}
    # Tile 1 (FLAW 1): complaints % without base
    sr = pd.read_csv(D / "service_requests.csv")
    sr["t"] = parse_sr_time(sr.created_at, sr.source_system)
    d = sr.groupby(sr.t.dt.normalize()).size()
    a, b = int(d["2025-06-17":"2025-06-30"].sum()), int(d["2025-05-17":"2025-05-30"].sum())
    pct = round((a / b - 1) * 100)
    vals["complaints"] = {"last14": a, "may14": b, "pct": pct}
    cl = sr.dropna(subset=["closed_at"]).copy()
    cl["c"] = parse_sr_time(cl.closed_at, cl.source_system)
    cl["days"] = (cl.c - cl.t).dt.total_seconds() / 86400
    m_now = cl[cl.t >= "2025-06-17"].days.median(); m_may = cl[(cl.t >= "2025-05-17") & (cl.t < "2025-05-31")].days.median()
    vals["resolution"] = (round(m_now, 1), round(m_may, 1))
    # Trend: daily metered electricity (cleaned: drop negative, impossible spikes and the Wh buildings) — rising
    el = pd.read_csv(D / "electricity_meters.csv", parse_dates=["timestamp"])
    wh = el.groupby("building_id").kwh.median().loc[lambda m: m > 500].index
    elc = el[~el.building_id.isin(wh) & (el.kwh >= 0) & (el.kwh < 2000)]
    daily = elc.groupby(elc.timestamp.dt.normalize()).kwh.sum() / 1000
    wk = daily.groupby((daily.index - daily.index[0]).days // 7).mean(); wk.index = daily.index[::7][: len(wk)]   # 7-day blocks labelled by their first day
    vals["elec_weekly"] = wk.round(1)
    e_mar, e_jun = daily["2025-03"].mean(), daily["2025-06"].mean()
    vals["elec"] = (round(e_mar, 1), round(e_jun, 1))
    # Cameras April by zone (FLAW 2: axis from 90)
    cam = pd.read_csv(D / "camera_status.csv", parse_dates=["date"]).merge(sensors[["sensor_id", "zone_id"]], left_on="camera_id", right_on="sensor_id")
    apr = cam[cam.date.dt.month == 4].groupby("zone_id").uptime_pct.mean().round(1)
    vals["camera_april"] = apr
    vals["camera_all"] = round(cam[cam.date.dt.month == 4].uptime_pct.mean(), 1)
    # Ramadan day (FLAW 3: iftar dip flagged as anomaly)
    tr = pd.read_csv(D / "traffic_counts.csv", parse_dates=["timestamp"]).drop_duplicates()
    tr = tr[tr.sensor_id.isin(sensors.sensor_id)]
    day = tr[tr.timestamp.dt.normalize() == "2025-03-12"]
    prof_day = day.groupby([day.sensor_id, day.timestamp.dt.hour]).vehicle_count.sum(min_count=4).groupby(level=1).mean()
    cal = pd.read_csv(ctx.ref_dir / "calendar.csv", parse_dates=["date"]).set_index("date")
    trd = tr.copy(); trd["date"] = trd.timestamp.dt.normalize()
    trd = trd.join(cal[["is_weekend", "is_holiday", "is_ramadan"]], on="date")
    base = trd[(trd.is_weekend == 0) & (trd.is_holiday == 0) & (trd.is_ramadan == 0) & (trd.date >= "2025-04-02") & (trd.date <= "2025-05-31")]
    prof_base = base.groupby([base.date, base.sensor_id, base.timestamp.dt.hour]).vehicle_count.sum(min_count=4).groupby(level=2).mean()
    vals["ramadan_day"] = prof_day.round(0); vals["typical"] = prof_base.round(0)
    dip = (prof_day.loc[18] / prof_base.loc[18] - 1) * 100
    vals["dip_pct"] = round(dip)
    # Stuck sensor TRF-023 vs three neighbours, 10 June
    show = ["TRF-021", "TRF-022", "TRF-023", "TRF-024"]
    t10 = tr[(tr.timestamp.dt.normalize() == "2025-06-10") & tr.sensor_id.isin(show)]
    piv = t10.pivot_table(index="timestamp", columns="sensor_id", values="vehicle_count")
    vals["stuck"] = piv

    hrs = [f"{h:02d}" for h in range(24)]
    top = float(np.ceil(wk.max() / 20) * 20)
    svg_trend = _svg_line([list(wk.values)], 520, 210, 0, top, [x.strftime("%d %b") for x in wk.index], [C["red"]], "MWh per day",
                          list(range(0, len(wk), 3)), yticks=list(np.arange(0, top + 1, 20)))
    zones = ["Z01", "Z02", "Z03", "Z04", "Z05", "Z06"]
    svg_cam = _svg_bars([apr[z] for z in zones], zones, 520, 210, 90, 100, [90, 92, 94, 96, 98, 100], highlight=(4,))
    ymax = float(np.ceil(max(prof_base.max(), prof_day.max()) / 500) * 500)
    svg_ram = _svg_line([list(prof_base.values), list(prof_day.values)], 520, 220, 0, ymax, hrs, [C["lgrey"], C["maroon"]], "vehicles per counter per hour", [0, 3, 6, 9, 12, 15, 18, 21, 23],
                        highlight=(17.6, 18.4), flag=(18, float(prof_day.loc[18]), f"ANOMALY {dip:+.0f}%"))
    small = []
    for sid in show:
        s = piv[sid]
        lbl = [t.strftime("%H:%M") for t in s.index]
        small.append(f'<div class="mini"><div class="mini-t">{sid}</div>' +
                     _svg_line([list(s.values)], 300, 150, 0, 800, lbl, [C["maroon"]], "veh / 15 min", [0, 24, 48, 72], yticks=[0, 400, 800]) + "</div>")
    page = DASH_TEMPLATE.format(
        pct=pct, res_now=f"{m_now:.1f}", res_may=f"{m_may:.1f}", e_jun=f"{e_jun:,.1f}", e_mar=f"{e_mar:,.1f}", e_pct=f"{(e_jun/e_mar-1)*100:+.0f}",
        cam_all=f"{vals['camera_all']:.1f}", res_may_ar=ar_num(f"{m_may:.1f}"), e_mar_ar=ar_num(f"{e_mar:,.1f}"), svg_trend=svg_trend, svg_cam=svg_cam, svg_ram=svg_ram, small="".join(small), **C)
    out = ctx.root / LABS / "dashboard_day1.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")
    return vals


DASH_TEMPLATE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Oasis District · Operations dashboard</title>
<style>
:root{{--red:{red};--maroon:{maroon};--taupe:{taupe};--black:{black};--dgrey:{dgrey};--mgrey:{mgrey};--lgrey:{lgrey};--pale:{pale}}}
*{{box-sizing:border-box}} body{{margin:0;font-family:Arial,Helvetica,sans-serif;color:var(--black);background:#fff}}
header{{background:var(--black);color:#fff;padding:14px 22px;display:flex;justify-content:space-between;align-items:flex-end;flex-wrap:wrap;gap:8px}}
header h1{{margin:0;font-size:20px}} header .ar{{font-size:17px}} header .meta{{font-size:12px;color:var(--lgrey);text-align:right}}
.band{{height:4px;background:var(--red)}}
main{{padding:16px 22px;max-width:1200px;margin:auto}}
.tiles{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:16px}}
.tile{{background:var(--pale);border-radius:8px;padding:12px 14px;min-height:128px}}
.tile .k{{font-size:13px;font-weight:bold;color:var(--dgrey)}} .tile .v{{font-size:34px;font-weight:bold;margin:6px 0 2px}}
.tile .s{{font-size:12px;color:var(--mgrey)}} .ar{{direction:rtl;text-align:right;unicode-bidi:isolate}}
.grid{{display:grid;grid-template-columns:1fr 1fr;gap:14px}}
.card{{border:1px solid var(--pale);border-radius:8px;padding:12px 14px}}
.card h2{{font-size:14px;margin:0}} .card .ar-h{{font-size:14px;color:var(--dgrey);margin:2px 0 6px}} .card .note{{font-size:11px;color:var(--mgrey);margin-top:4px}}
.legend span{{display:inline-block;margin-right:14px;font-size:11px;color:var(--dgrey)}} .sw{{display:inline-block;width:12px;height:3px;vertical-align:middle;margin-right:4px}}
.minis{{display:grid;grid-template-columns:1fr 1fr;gap:6px 14px}} .mini-t{{font-size:12px;font-weight:bold;color:var(--dgrey)}}
footer{{font-size:11px;color:var(--mgrey);padding:10px 22px 24px;max-width:1200px;margin:auto}}
@media (max-width:820px){{.tiles{{grid-template-columns:1fr 1fr}}.grid{{grid-template-columns:1fr}}.minis{{grid-template-columns:1fr}}}}
</style></head><body>
<header>
  <div><h1>Oasis District · Operations dashboard</h1><div class="ar">حي الواحة · لوحة العمليات</div></div>
  <div class="meta">Period: 1 Mar – 30 Jun 2025 · Data updated 30 Jun 2025, 23:45<br><span class="ar">الفترة: ١ مارس – ٣٠ يونيو ٢٠٢٥ · آخر تحديث ٣٠ يونيو ٢٠٢٥، ١١:٤٥ مساءً</span></div>
</header>
<div class="band"></div>
<main>
<section class="tiles">
  <div class="tile"><div class="k">Citizen complaints</div><div class="k ar">شكاوى المواطنين</div>
    <div class="v" style="color:var(--red)">+{pct}%</div><div class="s">Last 14 days vs same period in May</div><div class="s ar">آخر ١٤ يومًا مقارنةً بالفترة نفسها في مايو</div></div>
  <div class="tile"><div class="k">Median resolution time</div><div class="k ar">الوسيط لزمن حل الطلب</div>
    <div class="v">{res_now} days</div><div class="s">Last 14 days · same period in May: {res_may} days</div><div class="s ar">آخر ١٤ يومًا · الفترة نفسها في مايو: {res_may_ar} يوم</div></div>
  <div class="tile"><div class="k">Electricity, metered buildings</div><div class="k ar">الكهرباء في المباني ذات العدادات</div>
    <div class="v">{e_jun} MWh/day</div><div class="s">June average · March: {e_mar} MWh/day ({e_pct}%)</div><div class="s ar">متوسط يونيو · مارس: {e_mar_ar} ميجاوات ساعة يوميًا</div></div>
  <div class="tile"><div class="k">Camera availability, April</div><div class="k ar">إتاحة الكاميرات، أبريل</div>
    <div class="v">{cam_all}%</div><div class="s">All 60 cameras · target ≥ 97%</div><div class="s ar">كل الكاميرات (٦٠) · المستهدف ٩٧٪ أو أكثر</div></div>
</section>
<section class="grid">
  <div class="card"><h2>Electricity use, metered buildings (weekly average of daily MWh)</h2><div class="ar ar-h">استهلاك الكهرباء في المباني ذات العدادات (متوسط أسبوعي)</div>
    {svg_trend}<div class="note">80 metered buildings · cleaned readings · 7-day average, labelled by its first day</div></div>
  <div class="card"><h2>Camera availability by zone, April 2025</h2><div class="ar ar-h">إتاحة الكاميرات حسب المنطقة، أبريل ٢٠٢٥</div>
    {svg_cam}<div class="note">Average daily uptime of the cameras in each zone</div></div>
  <div class="card"><h2>Day drill-down: hourly traffic, Wed 12 Mar 2025</h2><div class="ar ar-h">تفصيل يوم: حركة المرور كل ساعة، الأربعاء ١٢ مارس ٢٠٢٥</div>
    <div class="legend"><span><i class="sw" style="background:{lgrey}"></i>Typical weekday (Apr–May)</span><span><i class="sw" style="background:{maroon}"></i>12 Mar 2025</span></div>
    {svg_ram}<div class="note">Alert rule: hour more than 50% below the typical weekday → ANOMALY</div></div>
  <div class="card"><h2>Traffic counters, Zone 4 · 10 Jun 2025 (vehicles per 15 min)</h2><div class="ar ar-h">عدادات المرور في المنطقة ٤ · ١٠ يونيو ٢٠٢٥ (مركبات كل ١٥ دقيقة)</div>
    <div class="minis">{small}</div><div class="note">Raw feed, 00:00–23:45</div></div>
</section>
</main>
<footer>Synthetic data — for training only · <span dir="rtl">بيانات اصطناعية لأغراض التدريب فقط</span> · Oasis District is fictional. Day 1 lab, Part C.</footer>
</body></html>
"""


# ------------------------------------------------------------------ chart values
def chart_values(ctx: Ctx, dash: dict) -> None:
    f = ctx.facts
    p7 = f["prs07"].loc["2025-05-13 06:00":"2025-05-13 07:30"]
    tn, trm = f["traffic_normal"], f["traffic_ramadan"]
    z5 = f["cctv_z5"].loc["2025-04-21":"2025-04-27"]
    cam = f["camera_april"]
    h6 = f["h6_month"]
    L = ["# Day 1 chart values (from the lite data kit)", "",
         "Real values to refresh the four Day 1 deck charts listed in spec §10a, plus the other Day 1 numbers that now come from the data.",
         f"Built from seed `{ctx.seed}`. Regenerate with `python -m oasis_datakit build`.", "",
         "## 1 · Slide 9 — Water network pressure · Zone 2 · sensor PRS-07 · Tue 13 May 2025", "",
         "The kit records pressure every **15 minutes**, so the deck's 10-minute labels should change to the 15-minute grid below. The break is at 06:40; 06:45 is the first reading after it.", "",
         "| Time | " + " | ".join(t.strftime("%H:%M") for t in p7.index) + " |", "|---|" + "---:|" * len(p7),
         "| Pressure (bar) | " + " | ".join(f"{v:.2f}" for v in p7.pressure_bar) + " |",
         "| Flow (L/s) | " + " | ".join(f"{v:.1f}" for v in p7.flow_lps) + " |", "",
         "pptxgenjs:", "```js",
         f"labels: {json.dumps([t.strftime('%H:%M') for t in p7.index])},",
         f"values: {json.dumps([round(float(v), 2) for v in p7.pressure_bar])}",
         "```", "",
         "Recovery for the debrief (slide 24): " + ", ".join(f"{t.strftime('%H:%M')} {v:.2f}" for t, v in f["prs07"].loc["2025-05-13 09:15":"2025-05-13 10:15"].pressure_bar.items()) + " bar.", "",
         "## 2 · Slide 35 — Hourly traffic profile, normal weekday vs Ramadan weekday", "",
         f"Mean vehicles **per counter per hour** (40 registered counters, duplicates removed). Normal weekday = {f['traffic_days'][0]} working days, 2 Apr – 12 Jun; Ramadan weekday = {f['traffic_days'][1]} working days, 1–29 Mar.",
         "The kit uses realistic road volumes, so the scale is about 35× the deck's illustrative values; the shape is the same (Ramadan: morning peak later and lower, dip at iftar 18:00, evening peak after iftar). Suggest the y-axis title “Vehicles per counter per hour”.", "",
         "| Hour | " + " | ".join(f"{h:02d}" for h in range(24)) + " |", "|---|" + "---:|" * 24,
         "| Normal weekday | " + " | ".join(str(v) for v in tn) + " |",
         "| Ramadan weekday | " + " | ".join(str(v) for v in trm) + " |", "",
         "```js", f"const normal = {json.dumps(tn)};", f"const ramadan = {json.dumps(trm)};", "```", "",
         "## 3 · Slide 37 (chart B) — Incidents seen by CCTV, Zone 5, 21–27 April 2025", "",
         "| Day | " + " | ".join(d.strftime("%d %b") for d in z5.index) + " |", "|---|" + "---:|" * len(z5),
         "| CCTV-sourced incidents | " + " | ".join(str(int(v)) for v in z5.values) + " |", "",
         "```js", f"labels: {json.dumps([d.strftime('%d %b') if i == 0 else d.strftime('%d') for i, d in enumerate(z5.index)])},", f"values: {json.dumps([int(v) for v in z5.values])}", "```", "",
         "The fall on 24–26 April is the camera outage (H8), not a safety improvement.", "",
         "## 4 · Slide 37 (chart A) — Camera availability, April 2025", "",
         "| Zone | Z01 | Z02 | Z03 | Z04 | Z05 | Z06 |", "|---|---:|---:|---:|---:|---:|---:|",
         "| Mean daily uptime % | " + " | ".join(f"{cam[z]:.1f}" for z in ["Z01", "Z02", "Z03", "Z04", "Z05", "Z06"]) + " |", "",
         f"Deck chart A uses Zone 1 and Zone 5 only: `values: [{cam['Z01']:.1f}, {cam['Z05']:.1f}]` (deck had 98 and 96).", "",
         "## Other Day 1 numbers now in the data", "",
         "**Slide 28 tiles (H6, June vs May).** The deck says “Requests +60%, June vs May” and “Median resolution 2.1 days, stable”. The data give:", "",
         f"- Requests: June {h6['june']:,} vs May {h6['may']:,} = **{h6['pct']:+.0f}%** (the app launched on 15 June, so only half of June is affected).",
         f"- Median resolution: May **{h6['median_res_may']:.1f}** days, June **{h6['median_res_jun']:.1f}** days. Satisfaction May {h6['sat_may']:.2f}, June {h6['sat_jun']:.2f} (stable).",
         f"- Suggest changing the tile to “+{h6['pct']:.0f}%” — or to the dashboard's comparison: last 14 days vs same period in May = **+{dash['complaints']['pct']}%** ({dash['complaints']['last14']:,} vs {dash['complaints']['may14']:,}).", "",
         "**Slide 47/48 and dashboard_day1.html (Part C answers).**", "",
         f"- Trend: electricity in the 80 metered buildings rises from {dash['elec'][0]:,.1f} MWh/day (March) to {dash['elec'][1]:,.1f} MWh/day (June): population growth + summer cooling.",
         f"- Anomaly: counter **TRF-023** repeats the same reading from 05:00 to 16:00 on 10 June (stuck sensor).",
         f"- Flaw 1: “Citizen complaints +{dash['complaints']['pct']}%” has no base — it is {dash['complaints']['last14']:,} vs {dash['complaints']['may14']:,} requests, and it follows the app launch (H6).",
         f"- Flaw 2: camera availability axis starts at 90% — Zone 5 ({cam['Z05']:.1f}%) looks far worse than Zone 1 ({cam['Z01']:.1f}%).",
         f"- Flaw 3: the 18:00 dip on Wed 12 March ({dash['dip_pct']:+d}% vs a typical weekday) is iftar in Ramadan (H7) — seasonality, flagged red as an anomaly.", ""]
    (ctx.root / LABS / "day1_chart_values.md").write_text("\n".join(L), encoding="utf-8")
    ctx.answer_extra = [
        f"- Dashboard flaw 1: complaints +{dash['complaints']['pct']}% = {dash['complaints']['last14']:,} requests (17–30 Jun) vs {dash['complaints']['may14']:,} (17–30 May).",
        f"- Dashboard flaw 2: camera availability axis 90–100%; April Z01 {cam['Z01']:.1f}%, Z05 {cam['Z05']:.1f}%.",
        f"- Dashboard flaw 3: 12 Mar 2025 18:00 traffic {dash['ramadan_day'].loc[18]:.0f} vs typical {dash['typical'].loc[18]:.0f} veh/counter/h ({dash['dip_pct']:+d}%) — iftar.",
        f"- Dashboard trend: metered electricity {dash['elec'][0]:,.1f} → {dash['elec'][1]:,.1f} MWh/day (Mar → Jun). Stuck sensor: TRF-023, 10 Jun 05:00–16:00.",
        "- Full chart values: `labs/D01/day1_chart_values.md`.",
    ]


def write_all(ctx: Ctx, execute: bool = True) -> None:
    labs = ctx.root / LABS
    labs.mkdir(parents=True, exist_ok=True)
    if not hasattr(ctx, "facts"):
        from .validation import write_report
        write_report(ctx)
    dash = dashboard(ctx)
    chart_values(ctx, dash)
    # learners get clean notebooks; the solution is kept executed (slide code is copied from executed cells);
    # every notebook is executed top to bottom here, and the executed copies are kept as proof in labs/D01/executed/
    ex = labs / "executed"; ex.mkdir(exist_ok=True)
    for name, make, keep_outputs in [("hello_oasis.ipynb", hello_notebook, False), ("warmup_day1.ipynb", lambda: warmup_notebook(False), False),
                                     ("warmup_day1_solution.ipynb", lambda: warmup_notebook(True), True)]:
        nb = make()
        if execute:
            done = _execute(make(), labs)
            nbformat.write(done, ex / name)
            if keep_outputs:
                nb = done
        nbformat.write(nb, labs / name)
