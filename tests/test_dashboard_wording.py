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
