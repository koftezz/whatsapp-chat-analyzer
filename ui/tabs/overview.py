"""
Overview tab for WhatsApp Chat Analyzer.

Shows chat summary metrics and message volume trends.
"""

import streamlit as st
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from whatsapp_analyzer.ui import calculate_chat_summary
from whatsapp_analyzer.analyzers import (
    basic_stats,
    stats_overall,
    analyze_monthly_messages,
)


def render_overview_tab(df):
    """Render the overview tab with summary metrics and charts."""

    # Chat Snapshot
    _render_chat_snapshot(df)

    st.divider()

    # Monthly Message Volume
    _render_monthly_volume(df)

    st.divider()

    # Basic Statistics Tables
    _render_statistics_tables(df)


def _render_chat_snapshot(df):
    """Render the chat snapshot section with key metrics."""
    st.header("Chat Snapshot")

    summary = calculate_chat_summary(df)

    # Metrics row 1
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Messages", f"{summary['total_messages']:,}")

    with col2:
        st.metric("Unique Participants", summary['unique_authors'])

    with col3:
        st.metric("Chat Duration", f"{summary['total_days']} days")

    # Metrics row 2
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Avg Messages/Day", f"{summary['avg_messages_per_day']:.1f}")

    with col2:
        st.metric("Most Active", summary['most_active_author'])

    with col3:
        st.metric("Their Messages", f"{summary['most_active_author_messages']:,}")

    # Summary text
    st.info(
        f"From {summary['start_date'].strftime('%B %d, %Y')} to {summary['end_date'].strftime('%B %d, %Y')} - "
        f"**{summary['most_active_author']}** leads with **{summary['most_active_author_percentage']:.1f}%** of all messages!"
    )


def _render_monthly_volume(df):
    """Render the monthly message volume chart."""
    st.header("Monthly Message Volume")

    with st.expander("About this chart"):
        st.write(
            "Shows the total number of messages sent each month. "
            "The red line represents the average monthly message count. "
            "Bars are colored by year for easy comparison."
        )

    monthly_analysis = analyze_monthly_messages(df)

    st.success(
        f"Peak month: **{monthly_analysis['peak_month']}** with "
        f"**{monthly_analysis['total_messages']:,}** messages!"
    )

    st.altair_chart(monthly_analysis['chart'], use_container_width=True)


def _render_statistics_tables(df):
    """Render the statistics tables."""

    # Average Message Characteristics
    st.header("Average Message Characteristics")

    with st.expander("What do these metrics mean?"):
        st.markdown("""
        - **Words**: Average words per message
        - **Message Length**: Average characters per message
        - **Link**: % of messages with links
        - **Conversation Starter**: % of messages starting new conversations (7+ hours gap)
        - **Image/Video/GIF/Audio/Sticker**: % containing each media type
        - **Deleted**: % of deleted messages
        - **Edited**: % of edited messages
        - **Emoji**: % containing emojis
        - **Location**: % sharing locations
        """)

    st.dataframe(basic_stats(df), use_container_width=True)

    # Overall Chat Statistics
    st.header("Overall Statistics (Aggregated)")

    with st.expander("About this table"):
        st.write(
            "Shows overall totals aggregated across all authors. "
            "Gives a bird's-eye view of general chat activity."
        )

    st.dataframe(stats_overall(df))
