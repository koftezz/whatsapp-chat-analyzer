"""
Response time and pattern analysis for WhatsApp chat data.
"""

import numpy as np
import pandas as pd
import altair as alt


def analyze_response_time(df: pd.DataFrame) -> dict:
    """
    Analyze response times for each author.

    Excludes self-responses within 3 minutes to focus on
    actual conversation responses.

    Args:
        df: Preprocessed DataFrame

    Returns:
        Dictionary with:
        - median_chart: Altair chart of median response times
        - slowest_responder: Author with highest median response time
    """
    df = df.sort_values(["timestamp", "author"]).copy()
    df['time_diff'] = df['timestamp'].diff().dt.total_seconds()
    df['same_author'] = df['author'] == df['author'].shift()

    # Filter out self-responses within 3 minutes
    response_data = df[~((df['time_diff'] < 180) & df['same_author'])].copy()

    # Calculate response time in minutes
    response_data['response_time'] = response_data['time_diff'] / 60

    # Calculate log response time for distribution plot
    response_data['log_response_time'] = np.log10(response_data['response_time'])

    # Calculate median response time for each author
    median_response_time = response_data.groupby('author')['response_time'].median().reset_index()

    # Create median response time chart
    median_chart = alt.Chart(median_response_time).mark_bar().encode(
        y=alt.Y('author:N', sort='-x'),
        x=alt.X('response_time:Q', title='Median Response Time (minutes)'),
        color='author:N'
    ).properties(
        title='Median Response Time by Author'
    )

    return {
        'median_chart': median_chart,
        'slowest_responder': median_response_time.loc[
            median_response_time['response_time'].idxmax(), 'author'
        ]
    }


def response_matrix(df: pd.DataFrame):
    """
    Create a response matrix showing who responds to whom.

    Args:
        df: Preprocessed DataFrame

    Returns:
        Altair heatmap chart
    """
    df = df.copy()
    df['time_diff'] = df['timestamp'].diff().dt.total_seconds()
    df['same_author'] = df['author'] == df['author'].shift()

    # Filter out self-responses within 3 minutes
    response_data = df[~((df['time_diff'] < 180) & df['same_author'])]

    # Create response matrix
    matrix = pd.crosstab(
        response_data['author'],
        response_data['author'].shift(),
        normalize='index'
    )

    # Prepare data for Altair
    matrix_melted = matrix.reset_index().melt(
        id_vars='author',
        var_name='responding_to',
        value_name='response_rate'
    )

    # Create Altair heatmap
    heatmap = alt.Chart(matrix_melted).mark_rect().encode(
        x=alt.X('responding_to:N', title='Responding to', axis=alt.Axis(labelAngle=-45)),
        y=alt.Y('author:N', title='Message author'),
        color=alt.Color('response_rate:Q', scale=alt.Scale(scheme='viridis')),
        tooltip=[
            alt.Tooltip('author:N', title='Message author'),
            alt.Tooltip('responding_to:N', title='Responding to'),
            alt.Tooltip('response_rate:Q', title='Response rate', format='.1%')
        ]
    ).properties(
        title='Response Matrix'
    )

    # Add text labels
    text = heatmap.mark_text(baseline='middle').encode(
        text=alt.Text('response_rate:Q', format='.0%'),
        color=alt.condition(
            alt.datum.response_rate > 0.5,
            alt.value('white'),
            alt.value('black')
        )
    )

    return (heatmap + text).configure_view(
        strokeWidth=0
    ).configure_axis(
        labelFontSize=12,
        titleFontSize=14
    )
