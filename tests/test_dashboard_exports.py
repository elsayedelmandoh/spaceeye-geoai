import pandas as pd

from src.dashboard import exports


def test_forbidden_removed():
    df = pd.DataFrame({"name": ["x"], "code": ["C12"]})
    res = exports.check_export(df, "s")
    assert "name" not in res.columns

def test_valid_code_passes():
    df = pd.DataFrame({"code": ["C12", "D123"]})
    assert list(exports.check_export(df, "s")["code"]) == ["C12", "D123"]

def test_bad_code_raises():
    df = pd.DataFrame({"code": ["bad"]})
    try:
        exports.check_export(df, "src")
        assert False
    except ValueError as e:
        msg = str(e)
        assert "src" in msg and "code" in msg
        assert msg.replace("bad values", "").count("bad") == 0

def test_case_insensitive_code_column_bad():
    df = pd.DataFrame({"Code": ["bad"]})
    try:
        exports.check_export(df, "t")
        assert False
    except ValueError as e:
        assert "t" in str(e) and "Code" in str(e)

def test_not_mutated():
    df = pd.DataFrame({"name": ["a"]})
    exports.check_export(df, "s")
    assert "name" in df.columns

def test_export_bytes():
    b = exports.export_csv(pd.DataFrame({"code": ["C12"]}), "s")
    assert isinstance(b, bytes)
    assert b.startswith(b"\xef\xbb\xbf")
    assert b"code" in b


def test_export_csv_removes_forbidden_name_column():
    frame = pd.DataFrame({"code": ["C12"], "name": ["C12"]})
    exported = exports.export_csv(frame, "C01").decode("utf-8-sig")
    assert exported.splitlines()[0] == "code"
    assert "C12" in exported


def test_constants_match_app():
    with open("app.py") as f:
        txt = f.read()
    assert exports.CODE_PATTERN.pattern in txt
    for n in exports.CODE_COLUMNS:
        assert n in txt
