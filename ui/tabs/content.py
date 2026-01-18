"""
Content tab for WhatsApp Chat Analyzer.

Shows word clouds, emoji analysis, and content statistics.
"""

import streamlit as st
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from whatsapp_analyzer.analyzers import get_most_used_emoji
from whatsapp_analyzer.visualizations import create_word_cloud


def render_content_tab(df):
    """Render the content analysis tab."""

    # Word Cloud
    _render_word_cloud(df)

    st.divider()

    # Emoji Analysis
    _render_emoji_analysis(df)

    st.divider()

    # Raw Data
    _render_raw_data(df)


@st.fragment
def _render_word_cloud(df):
    """Render word cloud with interactive controls using fragment for fast updates."""
    st.header("Word Cloud")

    with st.expander("About this visualization"):
        st.write(
            "Shows the most frequently used words in the chat. "
            "Word size is proportional to frequency. "
            "Use the sliders to customize the visualization."
        )

    # Interactive controls - these won't cause full page reload thanks to @st.fragment
    col1, col2 = st.columns(2)

    with col1:
        min_length = st.slider(
            "Minimum word length",
            min_value=2,
            max_value=10,
            value=4,
            help="Filter out shorter words"
        )

    with col2:
        max_words = st.slider(
            "Maximum words to show",
            min_value=50,
            max_value=500,
            value=100,
            step=50,
            help="Limit the number of words displayed"
        )

    # Generate word cloud with current settings
    with st.spinner("Generating word cloud..."):
        word_cloud = create_word_cloud(df, min_word_length=min_length, max_words=max_words)
        st.image(word_cloud)


def _render_emoji_analysis(df):
    """Render emoji usage analysis."""
    st.header("Most Used Emojis")

    with st.expander("About this table"):
        st.write(
            "Shows the top 10 most frequently used emojis in the chat. "
            "Count indicates total occurrences across all messages."
        )

    emoji_counts = get_most_used_emoji(df)

    if emoji_counts.empty:
        st.info("No emojis found in the chat.")
    else:
        # Display as a nice formatted table
        st.dataframe(
            emoji_counts,
            column_config={
                "Emoji": st.column_config.TextColumn("Emoji", width="medium"),
                "Count": st.column_config.NumberColumn("Count", format="%d")
            },
            hide_index=True,
            use_container_width=True
        )


def _render_raw_data(df):
    """Render expandable raw data view."""
    st.header("Explore Raw Data")

    with st.expander("View processed chat data"):
        st.write(f"Total rows: {len(df):,}")
        st.dataframe(df, use_container_width=True)
