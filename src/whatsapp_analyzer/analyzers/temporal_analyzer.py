"""
Temporal analysis for WhatsApp chat data (time of day, day of week, heatmaps).
"""

import numpy as np
import pandas as pd
import altair as alt
from scipy.ndimage import gaussian_filter


def activity_day_of_week_ts(df: pd.DataFrame):
    """
    Create a heatmap of activity by day of week per author.

    Args:
        df: Preprocessed DataFrame

    Returns:
        Altair chart
    """
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    o = df.groupby([df.timestamp.dt.dayofweek, df.author])['msg_length'].sum().unstack(fill_value=0)
    o.index = pd.CategoricalIndex(o.index.map(lambda x: days[x]), categories=days, ordered=True)
    o = o.sort_index()

    # Normalize the data for each author
    o_normalized = o.div(o.sum(axis=0), axis=1)

    # Explicitly name the index
    o_normalized.index.name = 'day_of_week'

    # Convert the DataFrame to a format suitable for Altair
    o_melted = o_normalized.reset_index().melt(
        id_vars='day_of_week',
        var_name='author',
        value_name='activity'
    )

    # Create Altair chart
    chart = alt.Chart(o_melted).mark_rect().encode(
        x=alt.X('day_of_week:N', sort=days, title='Day of Week'),
        y=alt.Y('author:N', title='Author'),
        color=alt.Color('activity:Q', scale=alt.Scale(scheme='viridis'), title='Activity'),
        tooltip=[
            alt.Tooltip('day_of_week:N', title='Day'),
            alt.Tooltip('author:N', title='Author'),
            alt.Tooltip('activity:Q', title='Activity', format='.1%')
        ]
    ).properties(
        width=600,
        height=400,
        title='Activity Distribution by Day of Week'
    )

    # Add text labels
    text = chart.mark_text(baseline='middle').encode(
        text=alt.Text('activity:Q', format='.1%'),
        color=alt.condition(
            alt.datum.activity > 0.15,
            alt.value('white'),
            alt.value('black')
        )
    )

    return chart + text


def activity_time_of_day_ts(df: pd.DataFrame):
    """
    Create a smoothed line chart of activity by time of day per author.

    Args:
        df: Preprocessed DataFrame

    Returns:
        Altair chart
    """
    # Group by hour and minute, sum message lengths
    a = df.groupby(
        [df.timestamp.dt.hour, df.timestamp.dt.minute, 'author']
    )['msg_length'].sum().unstack(fill_value=0)

    # Reindex to fill missing times with 0
    a = a.reindex(
        pd.MultiIndex.from_product([range(24), range(60)], names=['hour', 'minute']),
        fill_value=0
    )

    # Temporarily add the tail at the start and head at the end for continuous smoothing
    a = pd.concat([a.tail(120), a, a.head(120)])

    # Apply gaussian convolution
    smoothed = pd.DataFrame(
        gaussian_filter(a.values, (60, 0)),
        index=a.index,
        columns=a.columns
    )

    # Remove the temporarily added points
    smoothed = smoothed.iloc[120:-120]

    # Reset index and prepare for plotting
    smoothed = smoothed.reset_index()
    smoothed['time'] = pd.to_datetime(
        smoothed['hour'].astype(str) + ':' + smoothed['minute'].astype(str).str.zfill(2)
    )

    # Melt the dataframe for Altair
    melted = smoothed.melt(
        id_vars=['hour', 'minute', 'time'],
        var_name='author',
        value_name='activity'
    )

    # Create Altair chart
    chart = alt.Chart(melted).mark_line().encode(
        x=alt.X('time:T', title='Time of Day', axis=alt.Axis(format='%H:%M')),
        y=alt.Y('activity:Q', title='Activity'),
        color=alt.Color('author:N', title='Author')
    ).properties(
        width=800,
        height=400,
        title='Activity by Time of Day'
    )

    return chart


def heatmap(df: pd.DataFrame):
    """
    Create a GitHub-style activity heatmap for the last two years.

    Args:
        df: Preprocessed DataFrame

    Returns:
        Altair faceted chart
    """
    df = df.copy()
    df['date'] = df['timestamp'].dt.date
    df['weekday'] = df['timestamp'].dt.weekday
    df['week'] = df['timestamp'].dt.isocalendar().week
    df['year'] = df['timestamp'].dt.year

    # Filter for last two years
    last_two_years = df['year'].max() - 1
    df_filtered = df[df['year'] >= last_two_years]

    # Count messages per day
    heatmap_data = df_filtered.groupby(
        ['date', 'weekday', 'week', 'year']
    )['message'].count().reset_index()

    # Calculate the maximum message count
    max_message_count = heatmap_data['message'].max()

    # Create weekday labels
    weekday_labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    heatmap_data['weekday_label'] = heatmap_data['weekday'].map(
        dict(enumerate(weekday_labels))
    )

    # Create Altair chart
    chart = alt.Chart(heatmap_data).mark_rect().encode(
        x=alt.X('week:O', title='Week', axis=alt.Axis(labelAngle=0, tickCount=53)),
        y=alt.Y(
            'weekday_label:O',
            title='Day',
            sort=weekday_labels,
            axis=alt.Axis(labelAngle=0)
        ),
        color=alt.Color(
            'message:Q',
            scale=alt.Scale(scheme='viridis', domain=[0, max_message_count]),
            legend=alt.Legend(title='Message Count')
        ),
        tooltip=[
            alt.Tooltip('year:O', title='Year'),
            alt.Tooltip('date:T', title='Date', format='%Y-%m-%d'),
            alt.Tooltip('message:Q', title='Message Count')
        ]
    ).properties(
        width=1000,
        height=300
    ).facet(
        row=alt.Row('year:O', title='Year', header=alt.Header(labelAngle=0))
    ).properties(
        title='Message Count Heatmap (Last Two Years)'
    )

    return chart


def year_month(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate messages by year and month.

    Args:
        df: Preprocessed DataFrame

    Returns:
        DataFrame with year, YearMonth, and message count
    """
    df = df.copy()
    df['YearMonth'] = df.timestamp.dt.year * 100 + df.timestamp.dt.month
    year_content = df.groupby(
        ["year", 'YearMonth'], as_index=False
    ).count()[["year", 'YearMonth', 'message']]
    year_content = year_content.sort_values('YearMonth')
    return year_content
