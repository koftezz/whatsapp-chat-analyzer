"""
Activity tab for WhatsApp Chat Analyzer.

Shows temporal patterns: time of day, day of week, heatmaps.
"""

import os
import sys

import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from whatsapp_analyzer.analyzers import (
    smoothed_daily_activity,
    relative_activity_ts,
    activity_time_of_day_ts,
    activity_day_of_week_ts,
    heatmap,
)


def render_activity_tab(df):
    """Render the activity patterns tab."""

    # Message Volume Trends
    _render_volume_trends(df)

    st.divider()

    # Time of Day Analysis
    _render_time_of_day(df)

    st.divider()

    # Day of Week Analysis
    _render_day_of_week(df)

    st.divider()

    # Activity Heatmap
    _render_heatmap(df)


def _render_volume_trends(df):
    """Render message volume trend charts."""
    st.header("Message Volume Trends")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Absolute Activity")
        with st.expander("About this chart"):
            min_year = df.year.max() - 3
            st.write(
                f"Shows smoothed daily message volume for each author from {min_year} to {df.year.max()}. "
                "Data is smoothed using Gaussian distribution to highlight trends."
            )

        smoothed_df = smoothed_daily_activity(df, years=3)
        st.area_chart(smoothed_df)

    with col2:
        st.subheader("Relative Activity")
        with st.expander("About this chart"):
            st.write(
                "Shows each author's relative contribution to daily messages. "
                "Areas are stacked to 100%, showing how participation shifts over time."
            )

        relative_df = relative_activity_ts(df, years=3)
        st.area_chart(relative_df)


def _render_time_of_day(df):
    """Render time of day activity chart."""
    st.header("Activity by Time of Day")

    with st.expander("About this chart"):
        st.write(
            "Shows when each participant is most active throughout the day. "
            "Data is smoothed for better visualization of patterns."
        )

    chart = activity_time_of_day_ts(df)
    st.altair_chart(chart, use_container_width=True)


def _render_day_of_week(df):
    """Render day of week activity chart."""
    st.header("Activity by Day of Week")

    with st.expander("About this chart"):
        st.write(
            "Shows which days of the week each participant is most active. "
            "Percentages indicate the proportion of each author's messages sent on that day."
        )

    chart = activity_day_of_week_ts(df)
    st.altair_chart(chart, use_container_width=True)


def _render_heatmap(df):
    """Render the GitHub-style activity heatmap."""
    st.header("Activity Heatmap")

    with st.expander("About this chart"):
        st.write(
            "Shows message counts for each day, similar to GitHub's contribution graph. "
            "Hover over cells to see exact dates and counts. "
            "Displays the last two years of data."
        )

    chart = heatmap(df)
    st.altair_chart(chart, use_container_width=True)
