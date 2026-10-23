"""Citizen services (service_requests, gov_services) and Operations (ops_tickets)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .common import Ctx, fmt_ts, real_local, tag, write_dataset
from .safety_buildings_env import dq9_variants

# canonical category (AR) -> (EN label, zone weights Z01..Z06, resolution factor, variants for DQ9)
CATS = {
    "تسرب مياه": ("Water leak", [1.3, 1.3, .5, .8, 1.0, .6], 0.9, ["تسرب المياه", "Water leak", "تسريب مياه", "مياه"]),
    "انقطاع المياه": ("Water outage", [1.2, 1.2, .4, .7, 1.0, .4], 0.6, ["انقطاع مياه", "Water", "المياه", "قطع المياه"]),
    "إنارة الشوارع": ("Streetlight out", [1.0, 1.0, .8, .8, 1.0, 1.4], 1.2, ["انارة الشوارع", "Streetlight", "الإنارة", "إنارة"]),
    "تراكم المخلفات": ("Waste overflow", [1.0, 1.1, .5, 1.2, 1.4, 1.2], 0.7, ["تراكم مخلفات", "Waste", "القمامة", "مخلفات"]),
    "ضوضاء": ("Noise", [.7, .7, .3, 1.0, 1.5, 1.6], 1.1, ["الضوضاء", "Noise", "ازعاج", "ضوضاء "]),
    "مخالفات الانتظار": ("Parking", [.6, .6, 1.2, 1.6, 1.4, .8], 0.8, ["مخالفات انتظار", "Parking", "الانتظار", "ركن السيارات"]),
    "تكييف مبنى عام": ("AC failure in a public building", [.3, .3, 2.5, .8, .5, .2], 0.9, ["تكييف مبني عام", "AC failure", "التكييف", "تكييف"]),
    "مشكلة في التطبيق": ("App problem", [1, 1, 1, 1, 1, 1], 0.5, ["مشكلة بالتطبيق", "App problem", "التطبيق", "مشكله في التطبيق"]),
    "الطرق والأرصفة": ("Roads and pavements", [1.0, 1.0, .7, 1.0, 1.1, .7], 1.6, ["طرق وأرصفة", "Roads", "الطرق", "الارصفة"]),
    "إشارات المرور": ("Traffic signals", [.7, .7, 1.0, 1.4, 1.2, .5], 0.8, ["اشارات المرور", "Traffic signals", "إشارة مرور", "المرور"]),
    "النظافة العامة": ("Street cleanliness", [1.0, 1.0, .6, 1.0, 1.2, 1.3], 0.9, ["نظافة عامة", "Cleanliness", "النظافه العامة", "نظافة"]),
    "الحدائق والمساحات الخضراء": ("Parks and green spaces", [.5, .5, .3, .3, .5, 3.0], 1.4, ["الحدائق", "Parks", "حدائق ومساحات خضراء", "المساحات الخضراء"]),
    "الصرف الصحي": ("Sewage", [1.0, 1.0, .4, .7, 1.1, .4], 1.1, ["صرف صحي", "Sewage", "الصرف", "المجاري"]),
    "انقطاع الكهرباء": ("Power outage", [1.0, 1.0, .5, .9, 1.0, .5], 0.6, ["انقطاع كهرباء", "Electricity", "الكهرباء", "قطع الكهرباء"]),
    "الأمن والسلامة": ("Safety and security", [.8, .8, .5, .9, 1.3, 1.0], 1.0, ["الامن والسلامة", "Safety", "السلامة", "أمن"]),
}
CAT_BASE = {"تسرب مياه": 9, "انقطاع المياه": 6, "إنارة الشوارع": 10, "تراكم المخلفات": 11, "ضوضاء": 7, "مخالفات الانتظار": 8,
            "تكييف مبنى عام": 3, "مشكلة في التطبيق": 0, "الطرق والأرصفة": 8, "إشارات المرور": 4, "النظافة العامة": 9,
            "الحدائق والمساحات الخضراء": 4, "الصرف الصحي": 5, "انقطاع الكهرباء": 5, "الأمن والسلامة": 5}

TEXTS = {
    "تسرب مياه": ["في تسريب مياه قدام العمارة في {street} من الصبح", "ماسورة مكسورة في {street} والمية مغرقة الرصيف",
                  "تسرب مياه كبير جنب المدرسة، محتاجين حد ييجي بسرعة", "water leak قدام المدخل الرئيسي في {street}",
                  "fe tasreeb maya fel share3 ganb el bawaba", "المية بتطلع من الأرض في {street} ومحدش جه لحد دلوقتي"],
    "انقطاع المياه": ["المية مقطوعة عندنا من الساعة {hour} الصبح", "مفيش مية خالص في العمارة ومحدش بلغنا بأي صيانة",
                      "ضغط المية ضعيف جدًا في الدور الأخير", "el maya ma2tou3a men badri w mafeesh ay e3lan",
                      "انقطاع المياه في {street} للمرة التانية الأسبوع ده"],
    "إنارة الشوارع": ["عمود النور في {street} مطفي من كام يوم", "الشارع ضلمة خالص بالليل في {street}",
                      "لمبة الإنارة بتولع وتطفي طول الليل", "streetlight عطلان قدام البوابة", "el nour mafeesh fel share3 bel leil"],
    "تراكم المخلفات": ["الصندوق مليان والزبالة على الأرض في {street}", "محدش جه يلم الزبالة من امبارح",
                       "الحاوية بتطفح والريحة وحشة جدًا", "waste overflow جنب السوق", "el zebala kteer gamb el mosque"],
    "ضوضاء": ["صوت عالي جدًا من الحديقة لحد بعد نص الليل", "ورشة شغالة بدري جدًا ومزعجة في {street}",
              "دوشة عربيات ومكبرات صوت طول الليل", "noise عالي من الكافيه اللي تحت البيت"],
    "مخالفات الانتظار": ["عربية راكنة صف تاني وقافلة الشارع في {street}", "حد راكن قدام الجراج ومش عارف أطلع",
                          "الركن العشوائي قدام المبنى الحكومي", "parking مقفول ومفيش أماكن خالص"],
    "تكييف مبنى عام": ["التكييف في المبنى عطلان والموظفين والجمهور تعبانين من الحر", "AC مش شغال في صالة الانتظار",
                       "التكييف بيطلع هوا سخن في الدور التاني", "الحر شديد جوه المبنى والتكييف واقف"],
    "مشكلة في التطبيق": ["التطبيق بيقفل لوحده لما أرفع صورة", "مش عارف أسجل دخول على الـ app",
                          "الطلب اتبعت مرتين من التطبيق بالغلط", "el app msh bey7ammel el khareeta", "رسالة error لما أختار المنطقة"],
    "الطرق والأرصفة": ["حفرة كبيرة في نص {street}", "الرصيف مكسور وخطر على الأطفال", "بلاط الرصيف واقع قدام المدرسة",
                       "مطب جديد من غير علامات في {street}"],
    "إشارات المرور": ["الإشارة عطلانة في التقاطع والزحمة جامدة", "الإشارة حمرا على طول في {street}",
                      "traffic signal واقفة من الصبح", "توقيت الإشارة قصير جدًا للمشاة"],
    "النظافة العامة": ["تراب ورمل كتير في الشارع بعد العاصفة", "الشارع محتاج كنس في {street}", "مخلفات بناء مرمية على الرصيف",
                       "el share3 msh nedeef khales"],
    "الحدائق والمساحات الخضراء": ["الرشاشات بايظة والزرع ناشف في الحديقة", "ألعاب الأطفال في المتنزه مكسورة",
                                   "محتاجين صيانة للنجيل في المتنزه", "شجرة واقعة على الممشى"],
    "الصرف الصحي": ["بلاعة طافحة في {street}", "ريحة صرف صحي قوية جنب العمارة", "غطا البلاعة مفتوح وخطر"],
    "انقطاع الكهرباء": ["الكهرباء قاطعة في العمارة من ساعة", "النور بيقطع ويرجع كتير النهارده",
                        "el kahraba ati3a men el sob7", "انقطاع كهرباء في {street} كله"],
    "الأمن والسلامة": ["في ناس متجمعة بشكل مريب بالليل في {street}", "باب المدخل الخلفي مفتوح على طول",
                       "كاميرا المدخل شكلها عطلانة", "عربية بتسوق بسرعة جنونية في الشارع"],
}
FIRST = ["أحمد", "محمد", "محمود", "مصطفى", "عمر", "يوسف", "كريم", "حسن", "علي", "خالد", "طارق", "إبراهيم", "سارة", "مريم", "نور",
         "فاطمة", "هدى", "منى", "ياسمين", "دينا", "رنا", "سلمى", "آية", "هبة"]
SECOND = ["عبد الله", "عبد الرحمن", "السيد", "حسين", "سامي", "فؤاد", "عادل", "شريف", "ماهر", "نبيل", "رمضان", "صلاح", "جمال", "سعيد"]
SAT_P = [.06, .09, .18, .35, .32]


def service_requests(ctx: Ctx) -> pd.DataFrame:
    rng = ctx.rng("service_requests")
    cfg = ctx.cfg
    h6 = cfg["stories"]["H6"]; launch = pd.Timestamp(str(h6["date"]))
    zones = ["Z01", "Z02", "Z03", "Z04", "Z05", "Z06"]
    zpop = np.array([18000, 16000, 2000, 6000, 14000, 4000], float)
    streets = ctx.ref["roads"].set_index("zone_id").name_ar
    cats = list(CATS)
    rows = []
    zrng = ctx.rng("service_requests.counts")      # one fixed normal draw per day: counts move smoothly with the config
    days_all = ctx.cal.loc[ctx.start:ctx.end].index
    zday = dict(zip(days_all, zrng.normal(0, 1, len(days_all))))
    call_h = np.array([.2, .1, .05, .05, .05, .1, .3, .8, 1.2, 1.4, 1.4, 1.3, 1.2, 1.2, 1.1, 1.1, 1.1, 1.0, 1.0, 1.0, .9, .8, .6, .4])
    app_h = np.array([.5, .3, .2, .1, .1, .2, .4, .7, .9, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.1, 1.2, 1.3, 1.4, 1.4, 1.3, 1.1, .8])
    for d, c in ctx.cal.loc[ctx.start:ctx.end].iterrows():
        lam = 0.00125 * c.population * (1.08 if c.is_workday else 0.82) * (0.9 if c.is_ramadan else 1) * (0.6 if c.is_eid else 1) * (1 + 0.5 * c.dust)
        uplift = 1.0
        if d >= launch:
            k = min(1.0, ((d - launch).days + 1) / h6["ramp_days"])
            uplift = 1 + (h6["uplift"] - 1) * k
        mu = lam * uplift
        n = max(0, int(round(mu + np.sqrt(mu) * zday[d])))
        # category mix for the day
        w = np.array([CAT_BASE[k] for k in cats], float)
        w[cats.index("تراكم المخلفات")] *= 1.8 if c.day_after_eid else 1
        w[cats.index("ضوضاء")] *= 2.0 if c.is_eid else (1.3 if c.is_ramadan else 1)
        w[cats.index("النظافة العامة")] *= 1 + 4 * c.dust
        w[cats.index("تكييف مبنى عام")] *= 1 + 0.12 * max(0, c.temp_mean - 22)
        if d >= launch:
            w[cats.index("مشكلة في التطبيق")] = 9 if (d - launch).days < 5 else 3
        w /= w.sum()
        sc_open = bool(c.is_workday)
        for _ in range(n):
            cat = cats[rng.choice(len(cats), p=w)]
            zw = zpop * np.array(CATS[cat][1]); zw /= zw.sum()
            z = zones[rng.choice(6, p=zw)]
            if d < launch:
                p = [0.0, .68, .32] if sc_open else [0.0, 1.0, 0.0]
            else:
                callv, scv = .68 * .70, (.32 * .80 if sc_open else 0)
                if not sc_open:
                    callv = .70
                app = max(0, uplift - callv - scv)
                p = np.array([app, callv, scv]); p = p / p.sum()
            ch = ["app", "call_centre", "service_centre"][rng.choice(3, p=p)]
            if ch == "service_centre":
                hr = int(rng.integers(10, 14)) if c.is_ramadan else int(rng.integers(9, 15))
            else:
                hp = app_h if ch == "app" else call_h
                hr = int(rng.choice(24, p=hp / hp.sum()))
            ts = d + pd.Timedelta(hours=hr, minutes=int(rng.integers(0, 60)))
            rows.append((ts, ch, cat, z, ""))
    # H1 surge: water requests from Zone 2 after 06:40
    d1 = pd.Timestamp(str(cfg["stories"]["H1"]["date"]))
    for i in range(46):
        mins = 10 + rng.gamma(2.2, 38)
        ts = d1 + pd.Timedelta("06:40:00") + pd.Timedelta(minutes=float(min(mins, 260)))
        cat = "تسرب مياه" if rng.random() < 0.55 else "انقطاع المياه"
        ch = "service_centre" if ts.hour >= 9 and rng.random() < 0.15 else "call_centre"
        rows.append((ts.floor("min"), ch, cat, "Z02", "H1"))
    df = pd.DataFrame(rows, columns=["created_at", "channel", "category", "zone_id", "_story"])
    df["created_at"] = real_local(df.created_at)
    df = df.sort_values("created_at", kind="stable").reset_index(drop=True)
    df.insert(0, "request_id", [f"SR-{i:06d}" for i in range(1, len(df) + 1)])
    # text
    desc = []
    for _, r in df.iterrows():
        tpl = TEXTS[r.category][rng.integers(len(TEXTS[r.category]))]
        st = streets.loc[r.zone_id]
        st = st if isinstance(st, str) else st.iloc[rng.integers(len(st))]
        desc.append(tpl.format(street=st, hour=["٦", "٧", "٨", "٩"][rng.integers(4)]))
    df["description_ar"] = desc
    # resolution, status, satisfaction
    fac = df.category.map({k: v[2] for k, v in CATS.items()}).to_numpy()
    res_days = 2.1 * fac / 0.95 * rng.lognormal(0, 0.55, len(df))
    res_days = np.where(df._story == "H1", rng.uniform(0.08, 0.2, len(df)), res_days)
    closed = real_local((df.created_at + pd.to_timedelta(res_days, unit="D")).dt.floor("min"))
    horizon = ctx.end + pd.Timedelta(days=1)
    is_closed = closed < horizon
    df["status"] = np.where(is_closed, "closed", np.where(rng.random(len(df)) < 0.55, "in_progress", "open"))
    df["closed_at"] = closed.where(is_closed)
    sat = rng.choice([1, 2, 3, 4, 5], p=SAT_P, size=len(df)).astype(float)
    sat[(~is_closed) | (rng.random(len(df)) < 0.42)] = np.nan
    df["satisfaction_1_5"] = sat
    df["requester_name"] = [f"{FIRST[rng.integers(len(FIRST))]} {SECOND[rng.integers(len(SECOND))]}" for _ in range(len(df))]
    df["requester_phone"] = [f"+20 100 000 {rng.integers(0, 10000):04d}" for _ in range(len(df))]
    df["_dq"] = ""
    # DQ8 — 10 % come from the legacy call-centre system: UTC and different formats
    legacy_ok = np.flatnonzero((df.channel == "call_centre").to_numpy() & (df._story == "").to_numpy())
    leg = np.sort(rng.choice(legacy_ok, size=int(round(cfg["defects"]["DQ8_rate"] * len(df))), replace=False))
    df["source_system"] = "CRM"
    df.loc[df.index[leg], "source_system"] = "LEGACY_CC"
    created_s = fmt_ts(df.created_at)
    closed_s = df.closed_at.dt.strftime("%Y-%m-%d %H:%M")
    utc_c = df.created_at.iloc[leg].dt.tz_localize("Africa/Cairo").dt.tz_convert("UTC")
    utc_x = df.closed_at.iloc[leg].dt.tz_localize("Africa/Cairo", nonexistent="shift_forward", ambiguous=True).dt.tz_convert("UTC")
    iso = rng.random(len(leg)) < 0.6
    created_s.iloc[leg] = np.where(iso, utc_c.dt.strftime("%Y-%m-%dT%H:%M:%SZ"), utc_c.dt.strftime("%d/%m/%Y %H:%M"))
    closed_s.iloc[leg] = np.where(iso, utc_x.dt.strftime("%Y-%m-%dT%H:%M:%SZ"), utc_x.dt.strftime("%d/%m/%Y %H:%M"))
    closed_s = closed_s.where(df.closed_at.notna(), np.nan)
    m = np.zeros(len(df), bool); m[leg] = True
    tag(df, m, "DQ8")
    ctx.note(id="DQ8", dataset="service_requests", rows=len(leg), rate=len(leg) / len(df),
             detail=f"source_system LEGACY_CC rows: created_at/closed_at are in UTC (Cairo is UTC+2, UTC+3 from 25 Apr); {iso.sum()} use ISO 'YYYY-MM-DDTHH:MM:SSZ', {(~iso).sum()} use 'DD/MM/YYYY HH:MM'")
    df["_created_local"] = df.created_at
    df["created_at"] = created_s; df["closed_at"] = closed_s
    df["_cat"] = df.category
    variants = {k: v[3] for k, v in CATS.items()}
    df = dq9_variants(ctx, "service_requests", df, "category", variants)
    cols = ["request_id", "created_at", "channel", "category", "zone_id", "description_ar", "status", "closed_at",
            "satisfaction_1_5", "requester_name", "requester_phone", "source_system", "_dq", "_story"]
    write_dataset(ctx, "service_requests", df[cols])
    df["_res_days"] = res_days
    return df


SERVICES = {"building_permit": (14, 12.0), "utility_connection": (22, 5.0), "residency_registration": (35, 2.0),
            "business_licence": (12, 8.0), "parking_permit": (18, 1.0), "certificate_request": (40, 1.0)}


def gov_services(ctx: Ctx) -> pd.DataFrame:
    rng = ctx.rng("gov_services")
    rows = []
    for d, c in ctx.cal.loc[ctx.start:ctx.end].iterrows():
        for svc, (base, days) in SERVICES.items():
            for ch in ["online", "service_centre"]:
                if ch == "service_centre":
                    lam = 0 if not c.is_workday else base * 0.6 * (0.8 if c.is_ramadan else 1)
                else:
                    lam = base * 0.4 * (1 if c.is_workday else 0.4) * (1.6 if d >= pd.Timestamp("2025-06-15") else 1)
                tx = rng.poisson(lam * c.growth ** 1.1)
                post_eid = 1.2 if c.day_after_eid else 1.0
                pdays = round(days * post_eid * rng.lognormal(0, 0.12), 1) if tx else np.nan
                rows.append((d.strftime("%Y-%m-%d"), svc, ch, tx, pdays))
    df = pd.DataFrame(rows, columns=["date", "service_type", "channel", "transactions", "avg_processing_days"])
    write_dataset(ctx, "gov_services", df)
    return df


NOTES = ["تم التصعيد لمسؤول الركيزة والفريق الميداني في الموقع", "في انتظار قطعة غيار، المتابعة في الوردية التالية",
         "تم التحقق من الحساس، القراءة سليمة", "بلاغ مكرر، تم الربط بالتذكرة الأصلية", "تم إبلاغ المواطنين عبر التطبيق",
         "يحتاج متابعة صباح الغد", "تم الحل والتأكد من عودة الخدمة"]
PILLAR_OF_INC = {"traffic_accident": "mobility", "illegal_parking": "mobility", "road_hazard": "mobility", "vandalism": "public_safety",
                 "suspicious_activity": "public_safety", "crowd_gathering": "public_safety", "medical_emergency": "public_safety",
                 "fire_alarm": "buildings", "utility_failure": "water"}
PILLAR_OF_CAT = {"تسرب مياه": "water", "انقطاع المياه": "water", "إنارة الشوارع": "energy", "تراكم المخلفات": "waste", "ضوضاء": "environment",
                 "مخالفات الانتظار": "mobility", "تكييف مبنى عام": "buildings", "مشكلة في التطبيق": "citizen_services",
                 "الطرق والأرصفة": "mobility", "إشارات المرور": "mobility", "النظافة العامة": "waste", "الحدائق والمساحات الخضراء": "environment",
                 "الصرف الصحي": "water", "انقطاع الكهرباء": "energy", "الأمن والسلامة": "public_safety"}


def ops_tickets(ctx: Ctx, inc: pd.DataFrame, sr: pd.DataFrame, outage_blocks) -> pd.DataFrame:
    rng = ctx.rng("ops_tickets")
    rows = []
    incd = inc.copy()
    incd["ts"] = pd.to_datetime(incd.timestamp)
    for _, r in incd[(incd.severity <= 2) & (incd._story != "H1")].iterrows():
        if rng.random() < 0.8:
            src = "alert" if r.source in ("sensor", "CCTV") else "manual"
            rows.append((r.ts + pd.Timedelta(minutes=float(rng.uniform(2, 12))), PILLAR_OF_INC[r.type], src, int(r.severity), r._story))
    for blk in outage_blocks:
        sid = blk["sensor"]
        pil = "mobility" if sid.startswith("TRF") else "water"
        rows.append((pd.Timestamp(blk["start"]) + pd.Timedelta(minutes=30), pil, "alert", 3, ""))
    srd = sr[sr._story != "H1"]
    pick = srd.sample(frac=0.06, random_state=int(rng.integers(10**9)))
    for _, r in pick.iterrows():
        pil = PILLAR_OF_CAT[r._cat]
        rows.append((r._created_local + pd.Timedelta(minutes=float(rng.uniform(5, 90))), pil, "citizen", int(rng.choice([2, 3, 4], p=[.15, .55, .30])), ""))
    df = pd.DataFrame(rows, columns=["created_at", "pillar", "source", "severity", "_story"])
    d1 = pd.Timestamp(str(ctx.cfg["stories"]["H1"]["date"]))
    h1 = pd.DataFrame([
        {"created_at": d1 + pd.Timedelta("06:45:00"), "pillar": "water", "source": "alert", "severity": 1, "_story": "H1"},
        {"created_at": d1 + pd.Timedelta("07:08:00"), "pillar": "mobility", "source": "alert", "severity": 2, "_story": "H1"},
        {"created_at": d1 + pd.Timedelta("07:15:00"), "pillar": "citizen_services", "source": "citizen", "severity": 2, "_story": "H1"},
    ])
    h8 = ctx.cfg["stories"]["H8"]
    h8r = pd.DataFrame([{"created_at": pd.Timestamp(str(h8["start"])) + pd.Timedelta("06:50:00"), "pillar": "public_safety", "source": "alert", "severity": 2, "_story": "H8"}])
    df = pd.concat([df, h1, h8r], ignore_index=True)
    df["created_at"] = real_local(df.created_at.dt.floor("min"))
    df = df.sort_values("created_at", kind="stable").reset_index(drop=True)
    df.insert(0, "ticket_id", [f"OPS-{i:06d}" for i in range(1, len(df) + 1)])
    sev = df.severity.to_numpy()
    esc = (sev == 1) | ((sev == 2) & (rng.random(len(df)) < 0.45)) | ((sev == 3) & (rng.random(len(df)) < 0.07))
    df["escalated"] = esc
    df["escalated_to_role"] = np.where(esc, np.where(sev == 1, "pillar_owner", rng.choice(["shift_supervisor", "field_dispatcher"], len(df))), "")
    dur_h = {1: 2.5, 2: 5, 3: 14, 4: 40}
    res = df.created_at + pd.to_timedelta([dur_h[s] * rng.lognormal(0, 0.5) for s in sev], unit="h")
    res = real_local(res.dt.floor("min")).where(res < ctx.end + pd.Timedelta(days=1))
    df["resolved_at"] = res
    df["status"] = np.where(res.notna(), "resolved", np.where(rng.random(len(df)) < 0.5, "in_progress", "open"))
    mclosed = (df.status == "resolved").to_numpy() & (rng.random(len(df)) < 0.7)
    df.loc[mclosed, "status"] = "closed"
    note = np.where(rng.random(len(df)) < 0.3, [NOTES[i] for i in rng.integers(0, len(NOTES), len(df))], "")
    df["handover_note"] = note
    # H1 ticket details
    m = (df._story == "H1") & (df.pillar == "water")
    df.loc[m, ["escalated", "escalated_to_role", "status"]] = [True, "pillar_owner", "closed"]
    df.loc[m, "resolved_at"] = d1 + pd.Timedelta("09:35:00")
    df.loc[m, "handover_note"] = "كسر في خط مياه رئيسي بالمنطقة ٢، تم الإصلاح ٩:٣٠، متابعة جودة المياه (العكارة) غدًا"
    df["created_at"] = fmt_ts(df.created_at)
    df["resolved_at"] = df.resolved_at.dt.strftime("%Y-%m-%d %H:%M")
    df["_dq"] = ""
    cols = ["ticket_id", "created_at", "pillar", "source", "severity", "status", "escalated", "escalated_to_role", "resolved_at", "handover_note", "_dq", "_story"]
    write_dataset(ctx, "ops_tickets", df[cols])
    return df
