"""
Authors tab for WhatsApp Chat Analyzer.

Shows author statistics, rankings, and interaction patterns.
"""

import os
import sys

import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from whatsapp_analyzer.analyzers import (
    trend_stats,
    get_message_count_by_author,
    get_most_active_author,
    get_activity_stats,
    analyze_response_time,
    response_matrix,
    find_longest_consecutive_streak,
)
from whatsapp_analyzer.visualizations import create_message_count_chart

# Import responses if available
try:
    from responses import (
        get_random_chatter_response,
        get_random_activity_response,
        get_random_response_time_response,
        get_random_streak_response,
    )
    HAS_RESPONSES = True
except ImportError:
    HAS_RESPONSES = False


def render_authors_tab(df):
    """Render the author insights tab."""

    # Talkativeness & Trends
    _render_talkativeness(df)

    st.divider()

    # Message Counts
    _render_message_counts(df)

    st.divider()

    # Activity Stats
    _render_activity_stats(df)

    st.divider()

    # Response Analysis
    _render_response_analysis(df)

    st.divider()

    # Consecutive Streak
    _render_streak_analysis(df)


def _render_talkativeness(df):
    """Render talkativeness and trend analysis."""
    st.header("Talkativeness & Messaging Trends")

    with st.expander("About this table"):
        st.write(
            "Shows each author's messaging patterns and trends. "
            "Includes total messages, percentage of total, talkativeness rating, "
            "and trend analysis for the last 3, 6, and 12 months."
        )

    author_df = trend_stats(df)
    st.dataframe(author_df, use_container_width=True)


def _render_message_counts(df):
    """Render message count chart."""
    st.header("Messages Sent by Author")

    message_counts = get_message_count_by_author(df)
    most_active, total_msg = get_most_active_author(message_counts)

    if HAS_RESPONSES:
        response = get_random_chatter_response(most_active, total_msg)
        st.write(response)
    else:
        st.info(f"**{most_active}** leads with **{total_msg:,}** messages!")

    chart = create_message_count_chart(message_counts)
    st.altair_chart(chart)


def _render_activity_stats(df):
    """Render author participation stats."""
    st.header("Author Participation")

    with st.expander("About this chart"):
        st.write(
            "Shows the percentage of days each author participated. "
            "An 'active day' is when an author sends at least one message. "
            "Higher percentage = more consistent engagement."
        )

    activity_stats = get_activity_stats(df)

    if HAS_RESPONSES:
        response = get_random_activity_response(
            activity_stats['most_active'],
            activity_stats['most_active_perc']
        )
        st.write(response)
    else:
        st.info(
            f"**{activity_stats['most_active']}** is the most consistent with "
            f"**{activity_stats['most_active_perc']:.1f}%** active days!"
        )

    st.altair_chart(activity_stats['chart'])


def _render_response_analysis(df):
    """Render response time and matrix analysis."""

    # Response Matrix
    st.header("Response Matrix")

    with st.expander("About this chart"):
        st.write(
            "Shows how often each author responds to others. "
            "Percentages indicate the proportion of responses to each author. "
            "Self-responses within 3 minutes are excluded."
        )

    response_chart = response_matrix(df)
    st.altair_chart(response_chart, use_container_width=True)

    # Response Time
    st.header("Response Time Analysis")

    with st.expander("About this chart"):
        st.write(
            "Shows the median time each author takes to respond. "
            "Self-consecutive messages within 3 minutes are excluded."
        )

    response_analysis = analyze_response_time(df)
    st.altair_chart(response_analysis['median_chart'], use_container_width=True)

    slowest = response_analysis['slowest_responder']
    if HAS_RESPONSES:
        st.write(get_random_response_time_response(slowest))
    else:
        st.info(f"**{slowest}** takes the longest to respond!")


def _render_streak_analysis(df):
    """Render consecutive message streak analysis."""
    st.header("Consecutive Message Streak")

    streak_info = find_longest_consecutive_streak(df)

    if HAS_RESPONSES:
        response = get_random_streak_response(
            streak_info['author'],
            streak_info['streak_length']
        )
        st.write(response)
    else:
        st.info(
            f"**{streak_info['author']}** holds the record with "
            f"**{streak_info['streak_length']}** consecutive messages!"
        )

    with st.expander("View streak messages"):
        st.dataframe(streak_info['streak_messages'])
