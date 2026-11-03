"""Screen-1 search, filters and map click (T-NA-11, T-NA-12, T-NA-13) on fabricated frames."""
import re

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

import app
from src.dashboard import insights


@pytest.fixture
def frame() -> pd.DataFrame:
    return pd.DataFrame({
        "code": ["C01", "C10", "C12", "C20", "C03"],
        "developer_code": ["D05", "D14", "D05", "D01", None],
        "level": [1, 2, 4, None, 3],
        "cycle_rank": [1, 2, None, None, 3],
        "K2": [5, 2, None, 0, 1],
        "K3": [24, 0, 3, None, 12],
        "K6": [None, 6, 30, 1, 0],
    })


def codes(df: pd.DataFrame) -> list[str]:
    return list(df["code"])


def test_empty_or_blank_search_shows_everything(frame):
    assert codes(insights.filter_compounds(frame)) == codes(frame)
    assert codes(insights.filter_compounds(frame, "   ")) == codes(frame)


def test_search_is_a_case_insensitive_prefix_of_the_compound_code(frame):
    assert codes(insights.filter_compounds(frame, "c1")) == ["C10", "C12"]
    assert codes(insights.filter_compounds(frame, "C12")) == ["C12"]
    assert codes(insights.filter_compounds(frame, "c9")) == []


def test_search_matches_developer_codes_and_ignores_missing_ones(frame):
    assert codes(insights.filter_compounds(frame, "d05")) == ["C01", "C12"]
    assert codes(insights.filter_compounds(frame, "D")) == ["C01", "C10", "C12", "C20"]


def test_level_filter_keeps_only_the_chosen_levels(frame):
    assert codes(insights.filter_compounds(frame, levels=(1, 4))) == ["C01", "C12"]


def test_developer_filter(frame):
    assert codes(insights.filter_compounds(frame, developers=("D14", "D01"))) == ["C10", "C20"]


def test_developer_filter_without_the_column_is_a_no_op(frame):
    no_dev = frame.drop(columns="developer_code")
    assert codes(insights.filter_compounds(no_dev, developers=("D05",))) == codes(frame)


@pytest.mark.parametrize(("kwargs", "expected"), [
    ({"k2_min": 2}, ["C01", "C10"]),
    ({"k3_min": 12}, ["C01", "C03"]),
    ({"k6_min": 6}, ["C10", "C12"]),
])
def test_signal_thresholds_drop_unknown_values(frame, kwargs, expected):
    assert codes(insights.filter_compounds(frame, **kwargs)) == expected


def test_unknown_k_values_stay_when_every_threshold_is_zero(frame):
    assert codes(insights.filter_compounds(frame, k2_min=0, k3_min=0, k6_min=0)) == codes(frame)


def test_cycle_only_uses_the_stored_rank_or_levels_1_to_3(frame):
    assert codes(insights.filter_compounds(frame, cycle_only=True)) == ["C01", "C10", "C03"]
    no_rank = frame.drop(columns="cycle_rank")
    assert codes(insights.filter_compounds(no_rank, cycle_only=True)) == ["C01", "C10", "C03"]


def test_filters_combine(frame):
    out = insights.filter_compounds(frame, "c", levels=(1, 2, 3), developers=("D05", "D14"),
                                    k3_min=1, cycle_only=True)
    assert codes(out) == ["C01"]


def test_filtered_frame_keeps_codes_only(frame):
    out = insights.filter_compounds(frame, "d")
    assert all(re.fullmatch(r"C\d{2}", c) for c in out["code"])
    assert all(re.fullmatch(r"D\d{2}", d) for d in out["developer_code"])


def test_picked_code_reads_the_clicked_feature():
    selection = {"indices": {"compounds": [0]},
                 "objects": {"compounds": [{"type": "Feature", "properties": {"code": "C10"}}]}}
    assert insights.picked_code(selection, "compounds") == "C10"
    assert insights.picked_code({"indices": {}, "objects": {}}, "compounds") is None
    assert insights.picked_code(None, "compounds") is None


def test_listed_codes_puts_the_cycle_first_then_the_rest_by_level():
    df = pd.DataFrame({"code": ["C12", "C01", "C20", "C10"], "level": [4, 1, None, 2],
                       "cycle_rank": [None, 1, None, 2], "reason": [""] * 4})
    assert list(app.listed_codes(df, cycle_only=True)["code"]) == ["C01", "C10"]
    assert list(app.listed_codes(df, cycle_only=False)["code"]) == ["C01", "C10", "C12", "C20"]


def test_map_click_selects_the_compound_without_opening_the_file():
    def script():
        from types import SimpleNamespace

        import streamlit as st

        import app

        picked = {"objects": {app.MAP_LAYER_ID: [{"properties": {"code": "C10"}}]}}
        st.session_state[app.MAP_KEY] = SimpleNamespace(selection=picked)
        app.open_clicked_compound()
        st.write(st.session_state.get("selected_compound"), st.session_state.get("screen"))

    at = AppTest.from_function(script).run()
    assert not at.exception
    assert at.session_state["selected_compound"] == "C10"
    assert "screen" not in at.session_state


def test_visit_list_selection_updates_the_selected_compound():
    def script():
        import streamlit as st

        import app

        st.session_state["pm_visit_selection"] = "C12"
        app.select_visit_compound()

    at = AppTest.from_function(script).run()
    assert not at.exception
    assert at.session_state["selected_compound"] == "C12"


def test_clear_selection_removes_the_selected_compound():
    def script():
        import streamlit as st

        import app

        st.session_state["selected_compound"] = "C12"
        app.clear_selected_compound()

    at = AppTest.from_function(script).run()
    assert not at.exception
    assert at.session_state["selected_compound"] is None


def test_selected_compound_panel_renders_in_the_sidebar_with_drilldowns(monkeypatch):
    kpis = pd.DataFrame({
        "code": ["C01", "C01", "C02"],
        "quarter": ["2026Q2", "2026Q3", "2026Q3"],
        "level": [3, 1, 4],
        "K2": [2, 5, 0],
        "K3": [8, 24, 0],
        "K6": [12, None, 0],
        "K6_status": ["", "not_applicable_started", ""],
        "reason_ar": ["سبب تجريبي مخزن", "سبب تجريبي مخزن", ""],
        "K5_months": [None, None, None],
        "may_be_complete": [False, False, False],
    })
    monkeypatch.setattr(app, "load_table", lambda *args, **kwargs: kpis)
    monkeypatch.setattr(app, "space_frames",
                        lambda code: [{"date": "2025-07-23"}, {"date": "2026-01-10"}])
    monkeypatch.setattr(app, "stage_of_year",
                        lambda code: {2025: "under construction", 2026: "complete"})

    def script():
        import streamlit as st

        import app

        st.session_state["selected_compound"] = "C01"
        app.render_selected_compound_panel()

    at = AppTest.from_function(script).run()
    assert not at.exception
    sidebar_text = "\n".join(markdown.value for markdown in at.sidebar.markdown)
    assert "Selected compound" in sidebar_text
    assert 'dir="rtl"' in sidebar_text
    assert "سبب تجريبي مخزن" in sidebar_text
    assert "5 quarters" in sidebar_text
    assert "24 months" in sidebar_text
    assert "2026-01-10 · complete" in sidebar_text
    assert [button.label for button in at.sidebar.button] == ["Open compound file", "Clear selection"]
    assert [expander.label for expander in at.sidebar.expander] == ["Signal history", "Captures"]

    at.sidebar.button[0].click().run()
    assert not at.exception
    assert at.session_state["screen"] == app.SCREENS[1]
    assert at.session_state["compound_code"] == "C01"
