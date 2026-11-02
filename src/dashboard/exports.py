# Constants mirror app.py (FORBIDDEN_COLUMNS app.py:38, CODE_COLUMNS app.py:42, CODE_PATTERN app.py:43)
import re

import pandas

FORBIDDEN_COLUMNS = {
    "name", "compound_name", "developer_name", "developer", "project_name",
    "name_ar", "name_en",
}
CODE_COLUMNS = {"code", "compound_code", "compound", "developer_code"}
CODE_PATTERN = re.compile(r"^[CD]\d{2,3}$")

def check_export(frame: pandas.DataFrame, source: str) -> pandas.DataFrame:
    df = frame.copy()
    for col in list(df.columns):
        if col.lower() in {c.lower() for c in FORBIDDEN_COLUMNS}:
            df = df.drop(columns=[col])
    for col in df.columns:
        if col.lower() in {c.lower() for c in CODE_COLUMNS}:
            bad = df[col].dropna()
            bad = bad[bad.astype(str).str.match(CODE_PATTERN.pattern, na=False) == False]
            if len(bad) > 0:
                raise ValueError(f"{source}: column {col} has {len(bad)} bad values")
    return df

def export_csv(frame, source: str) -> bytes:
    return check_export(frame, source).to_csv(index=False).encode("utf-8-sig")
