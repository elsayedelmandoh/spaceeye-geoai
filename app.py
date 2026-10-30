import streamlit as st
from src.dashboard.ops_visits import render_ops_visits_form

def main() -> None:
    # Temporary Streamlit page configuration for this branch
    st.set_page_config(
        page_title="SpaceEye GeoAI - Ops Visits",
        layout="wide"
    )
    
    st.title("🌍 SpaceEye GeoAI Dashboard")
    
    st.markdown("---")
    
    # Render the operations visits form
    render_ops_visits_form()

if __name__ == "__main__":
    main()