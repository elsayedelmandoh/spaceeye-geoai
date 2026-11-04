"""Visible dashboard wording checks for T-SA-07."""
import json

from streamlit.testing.v1 import AppTest


def _visible_text(at: AppTest) -> str:
    parts = [metric.label for metric in at.metric]
    parts.extend(metric.value for metric in at.metric)
    parts.extend(caption.value for caption in at.caption)
    parts.extend(info.value for info in at.info)
    parts.extend(markdown.value for markdown in at.markdown)
    parts.extend(json.dumps(chart.spec, sort_keys=True) for chart in at.get("vega_lite_chart"))
    return "\n".join(parts)


def test_k5_dashboard_copy_refers_to_contract_review_not_assessed_fine():
    def script():
        import pandas as pd
        import streamlit as st

        import app
        from src.dashboard import insights

        latest = pd.DataFrame({
            "code": ["C01"],
            "level": [1],
            "cycle_rank": [1],
            "reason": ["stored reason"],
            "K2": [1],
            "K3": [2],
            "K6": [3],
            "K6_status": [""],
            "K5_months": [12],
            "K5_status": ["published"],
        })
        compounds = pd.DataFrame({
            "code": ["C01"],
            "units_origin": ["real"],
            "units": [100],
        })

        app.render_summary_tiles(latest, "2026Q3", [])
        app.render_kpi_tiles(latest.iloc[0], "2026Q3")
        app.render_homes_waiting(compounds, latest, "2026Q3")
        app.render_fine_months(latest, "2026Q3")
        st.write(insights.suggested_action(latest.iloc[0])[1])

        empty_latest = latest.iloc[0:0].copy()
        empty_compounds = compounds.iloc[0:0].copy()
        app.render_homes_waiting(empty_compounds, empty_latest, "2026Q3")
        app.render_fine_months(empty_latest, "2026Q3")

    at = AppTest.from_function(script).run(timeout=30)

    assert not at.exception
    visible = _visible_text(at)
    assert "fine-eligible" not in visible.lower()
    assert "contract decides the fine" not in visible.lower()
    assert "Months eligible for review under contract terms" in visible
    assert "months eligible for review under contract terms" in visible
    assert "Homes in compounds eligible for review under contract terms" in visible
    assert "No compound with a published unit count is eligible for review under contract terms." in visible
    assert "Label = months eligible for review under contract terms." in visible
    assert "No compound has months eligible for review under contract terms." in visible
    assert "12 months eligible for review under contract terms (proposal: 12)." in visible
    assert "the committee decides any action" in visible
    assert "The committee decides any action." in visible


def test_what_if_s3_caption_shows_quarter_origin_not_assessed_fine():
    """Page B (S3 capacity): caption must say the quarter is from the stored scenario, not a contract rate."""
    def script():
        import pandas as pd
        import app
        raw = pd.DataFrame({
            "quarter": ["2026Q3"],
            "code": ["C21"],
            "scenario_id": ["S3"],
            "selected": [True],
            "selection_changed": [False],
        })
        app.render_capacity_variant(raw, "capacity_minus_2")
    at = AppTest.from_function(script).run(timeout=30)
    assert not at.exception
    visible = _visible_text(at)
    # Must say it is generated and reference the stored scenario quarter.
    assert "Generated" in visible
    assert "quarter from stored capacity scenario" in visible
    # Must NOT conflate it with the contract fine language.
    assert "contract decides" not in visible.lower()


def test_early_warning_c21_shows_alert_quarter_and_uses_real_k2():
    """Page A (District → early signal): C21 must reference its alert quarter explicitly; the text must say
    the value comes from the real quarter data, not the generated twin scenario (fixes bug-02 contradiction)."""
    def script():
        import pandas as pd
        import app
        app.render_early_warning({
            "code": "C21", "alert": "2020Q3", "months": 39,
            "deadline": "Dec 2023", "freeze": "2020-12-31",
            "level_at_freeze": 3, "saw": "no new building activity for 6 quarters; handover announced",
            "outcome": "delayed", "reported": None,
        })
    at = AppTest.from_function(script).run(timeout=30)
    assert not at.exception
    visible = _visible_text(at)
    # Must reference the alert quarter (real) explicitly.
    assert "2020Q3" in visible
    assert "as of that quarter, real" in visible
    # Must reference the real 6 quarters value, not the generated 2.
    assert "no new building activity for 6 quarters" in visible
    # Must NOT say it is the generated scenario value.
    assert "generated twin scenario" not in visible.lower()
