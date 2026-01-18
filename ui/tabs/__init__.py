"""Tab components for WhatsApp Chat Analyzer."""

from ui.tabs.overview import render_overview_tab
from ui.tabs.activity import render_activity_tab
from ui.tabs.authors import render_authors_tab
from ui.tabs.content import render_content_tab


def render_tabs(df, locations):
    """
    Render all analysis tabs.

    Args:
        df: Preprocessed DataFrame
        locations: Locations DataFrame
    """
    import streamlit as st

    tab1, tab2, tab3, tab4 = st.tabs([
        "Overview",
        "Activity Patterns",
        "Author Insights",
        "Content Analysis"
    ])

    with tab1:
        render_overview_tab(df)

    with tab2:
        render_activity_tab(df)

    with tab3:
        render_authors_tab(df)

    with tab4:
        render_content_tab(df)


__all__ = [
    "render_tabs",
    "render_overview_tab",
    "render_activity_tab",
    "render_authors_tab",
    "render_content_tab",
]
