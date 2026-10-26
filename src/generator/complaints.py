"""
propose: step 5. the complaint desk: counts per compound-month, true cause, desk category (10-15 % wrong), channel, time, and ~100 Arabic texts from templates.
input: the simulated units (sales, events, warnings), the drivers, one random generator per compound.
output: `complaints` (public table) and `truth` (private: true cause, duplicate links, true category). no LLM, no real names, no phone numbers (defects.py plants those).

count   NegBin, mean = units sold so far x 1.5 per 1000 per month x event multiplier (2-5 x for 3 months after a postponement, handover news, the post-float price
        rise, a stall or a grace-period warning). a quiet distressed compound: buyers give up, complaints halve 8 months after a stall starts.
surprise one healthy compound gets a one-month spike (a social media post, 3-6 x).
"""

import numpy as np
import pandas as pd

from src.generator.inputs import DAYS, GEN, M_START, N, O0, mi

C = GEN["complaints"]
CATS = ["delay", "stoppage", "payment", "quality", "other"]
BASE_MIX = [0.30, 0.05, 0.25, 0.20, 0.20]
KIND_CAT = {"postponement": "delay", "grace_expiry": "delay", "handover": "quality", "price": "payment", "stall": "stoppage", "stall_review": "stoppage", "viral": "other"}
DECAY = [1.0, 0.7, 0.4]
HOURS = np.array([0, 0, 0, 0, 0, 0, 1, 2, 6, 9, 9, 9, 8, 7, 7, 6, 5, 4, 3, 3, 2, 1, 1, 0], dtype=float)

OPEN = ["السلام عليكم", "لو سمحتم", "تحية طيبة", "يا جماعة", "مساء الخير", "صباح الخير", "من فضلكم", "أنا حاجز عندكم", "أنا مشتري في المشروع", "بخصوص وحدتي"]
CLOSE = ["ياريت حد يرد عليا", "محتاج رد رسمي", "هستنى ردكم", "ومحدش بيرد", "ده تالت مرة أكلمكم", "عايز أعرف الموقف بالظبط", "شكرا", "مستنى مكالمة", "ياريت توضحوا", "الوضع مش مريح"]
BODY = {
    "delay": ["ميعاد التسليم عدى ومفيش أي خبر", "اتأجل التسليم مرتين من غير سبب واضح", "الوحدة اتأخرت عن الميعاد المكتوب في العقد", "عايز أعرف ميعاد الاستلام الجديد",
              "قالوا هنستلم السنة دي ولسه الموقع زي ما هو", "مفيش جدول زمني معلن للتسليم", "التأخير بقى أكتر من سنة", "كل مرة بيقولوا بعد شهرين"],
    "stoppage": ["الشغل واقف في الموقع من شهور", "مفيش عمال ولا معدات خلاص", "العماير زي ما هي من فترة طويلة", "الموقع فاضي والبوابة مقفولة", "المقاول سابع الشغل",
                 "الشغل بطل فجأة وسمعنا إن فيه مشاكل تمويل", "مفيش أي حركة في المشروع"],
    "payment": ["القسط زاد من غير ما حد يبلغني", "عايز كشف حساب بالأقساط المدفوعة", "السعر اتغير بعد ما حجزت", "طلبوا مني دفعة إضافية مش في العقد", "الإيصال مش بيوصلني بعد الدفع",
                "عايز أستعيد مقدم الحجز", "الغرامة اتحسبت غلط", "عايز أجدول القسط الجاي"],
    "quality": ["التشطيب مش زي المواصفات المتفق عليها", "فيه شروخ في الحيطة من أول يوم", "المصعد لسه مش شغال", "المياه ضعيفة في الدور الأخير", "الكهربا بتقطع كتير",
                "الطرق جوه الكمبوند لسه ترابي", "الخدمات اللي وعدوا بيها مش موجودة", "فيه تسريب في السقف"],
    "other": ["عايز أنقل الحجز على اسم تاني", "مفيش رد على الإيميلات", "الموقع الإلكتروني مش بيفتح", "محتاج نسخة من العقد", "الأمن عند البوابة مش منظم", "عايز أعرف رقم الوحدة النهائي"],
}
TYPO = [("ة", "ه"), ("أ", "ا"), ("إ", "ا"), ("ى", "ي"), ("ؤ", "و"), ("ئ", "ي")]


def counts_and_causes(u, rng, viral: bool) -> tuple[np.ndarray, list]:
    """per-month complaint count and, per month, the extra mass of each cause (kind -> mass)."""
    sold_cum = np.concatenate([[0], np.cumsum(u.eco.sold)[:-1]]).astype(float)
    ev = [(m, k) for m, k in u.eco.events] + [(m, k) for m, k in u.warn_events]
    mult, share = np.ones(N), [dict() for _ in range(N)]
    for m, kind in ev:
        f = float(rng.uniform(*C["event_multiplier"]))
        for j, d in enumerate(DECAY[: C["event_months"]]):
            if 0 <= m + j < N:
                extra = (f - 1) * d
                mult[m + j] += extra
                share[m + j][kind] = share[m + j].get(kind, 0.0) + extra
    if viral:
        m = mi("2025-05-01")
        extra = float(rng.uniform(*C["viral_multiplier"])) - 1
        mult[m] += extra
        share[m]["viral"] = extra
    if u.sig.onset is not None and u.sig.story == "gradual_stall":
        mult[u.sig.onset + 8:] *= 0.5
    mu = sold_cum * C["base_per_1000_units_month"] / 1000 * mult
    n = np.where(mu > 0, rng.negative_binomial(C["dispersion"], C["dispersion"] / (C["dispersion"] + np.maximum(mu, 1e-9))), 0)
    return n, [dict(s, base=float(mult[i] - sum(s.values()))) for i, s in enumerate(share)]


def one_text(rng: np.random.Generator, cat: str) -> str:
    parts = [str(rng.choice(OPEN)), str(rng.choice(BODY[cat]))]
    if rng.random() < 0.25:                                    # mixed topic
        parts.append(str(rng.choice(BODY[str(rng.choice([c for c in CATS if c != cat]))])))
    parts.append(str(rng.choice(CLOSE)))
    t = "، ".join(parts)
    if rng.random() < 0.25:                                    # spelling slips
        for a, b in [TYPO[i] for i in rng.choice(len(TYPO), 2, replace=False)]:
            t = t.replace(a, b)
    return t


def generate(units: list, viral_code: str, rng_for) -> pd.DataFrame:
    """all complaints 2023-01 .. 2026-09 with private helper columns (_true_cat, _cause, _dup_of, _wrong); ids are assigned after sorting by time."""
    rows = []
    for u in units:
        rng = rng_for(40, int(u.sig.code[1:]))
        n, shares = counts_and_causes(u, rng, u.sig.code == viral_code)
        for m in range(O0, N):
            for _ in range(int(n[m])):
                kinds, w = list(shares[m]), np.array(list(shares[m].values()), dtype=float)
                pick = str(rng.choice(kinds, p=np.clip(w, 0, None) / np.clip(w, 0, None).sum())) if len(kinds) and np.clip(w, 0, None).sum() > 0 else "base"
                cause = pick
                cat = str(rng.choice(CATS, p=BASE_MIX)) if pick == "base" else KIND_CAT[pick]
                rows.append(_row(rng, u.sig.code, m, cat, cause, len(rows), None))
                if rng.random() < C["duplicate_share"]:            # same buyer, second channel, within 7 days
                    rows.append(_row(rng, u.sig.code, m, cat, cause, len(rows), len(rows) - 1, shift_days=int(rng.integers(0, 8))))
    df = pd.DataFrame(rows).sort_values(["created_at", "code"], kind="stable").reset_index(drop=True)
    df.insert(0, "complaint_id", [f"CMP-{i + 1:06d}" for i in range(len(df))])
    ids = dict(zip(df._uid, df.complaint_id))
    df["_dup_of"] = df._dup_of.map(lambda v: ids.get(v) if pd.notna(v) else None)
    return df.drop(columns="_uid")


def _row(rng, code, m, cat, cause, uid, dup_of, shift_days=0) -> dict:
    day = int(rng.integers(0, DAYS[m]))
    hour = int(rng.choice(24, p=HOURS / HOURS.sum()))
    ts = M_START[m] + pd.Timedelta(days=day + shift_days, hours=hour, minutes=int(rng.integers(0, 60)), seconds=int(rng.integers(0, 60)))
    wrong = rng.random() < C["wrong_category"]
    filed = str(rng.choice([c for c in CATS if c != cat])) if wrong else cat
    ch = str(rng.choice(list(C["channels"]), p=list(C["channels"].values())))
    return {"code": code, "created_at": ts, "channel": ch, "category": filed, "text_ar": None, "_uid": uid, "_true_cat": cat, "_cause": cause, "_dup_of": dup_of, "_wrong": wrong}


def add_texts(df: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    """~100 texts on a stratified sample of the non-duplicate rows (every true category appears), written from the TRUE cause so the desk label can be wrong."""
    pool = df[df._dup_of.isna()]
    k = C["n_texts"]
    idx = []
    for cat in CATS:
        sub = pool[pool._true_cat == cat].index.to_numpy()
        idx += list(rng.choice(sub, min(len(sub), k // len(CATS)), replace=False))
    rest = [i for i in pool.index if i not in set(idx)]
    idx += list(rng.choice(rest, k - len(idx), replace=False))
    seen = set()
    for i in sorted(idx):
        t = one_text(rng, df.at[i, "_true_cat"])
        while t in seen:
            t = one_text(rng, df.at[i, "_true_cat"])
        seen.add(t)
        df.at[i, "text_ar"] = t
    return df

