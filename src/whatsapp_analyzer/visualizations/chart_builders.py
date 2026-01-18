"""
Chart building utilities for WhatsApp chat analysis.
"""

import numpy as np
import pandas as pd
import altair as alt


def create_message_count_chart(message_counts: pd.DataFrame):
    """
    Create a bar chart of message counts per author with mean line.

    Args:
        message_counts: DataFrame with author and message columns

    Returns:
        Altair chart
    """
    base = alt.Chart(message_counts).encode(
        x=alt.X("author", sort="-y"),
        y=alt.Y('message:Q'),
        color='author'
    )

    bars = base.mark_bar()

    # Calculate the mean
    mean_value = message_counts['message'].mean()

    # Create a rule for the mean line
    mean_line = alt.Chart(
        pd.DataFrame({'mean': [mean_value]})
    ).mark_rule(color='red').encode(
        y='mean:Q'
    )

    # Add text annotation for the mean
    mean_text = alt.Chart(
        pd.DataFrame({'mean': [mean_value]})
    ).mark_text(
        align='left',
        baseline='bottom',
        dx=5,
        dy=-5,
        color='red'
    ).encode(
        y='mean:Q',
        text=alt.Text('mean:Q', format='.2f')
    )

    chart = (bars + mean_line + mean_text).properties(
        width=600,
        height=600,
        title='Number of messages sent'
    )

    return chart


def create_sunburst_charts(df: pd.DataFrame) -> tuple:
    """
    Create radial charts showing message distribution by hour.

    Args:
        df: Preprocessed DataFrame

    Returns:
        Tuple of (all_hours_chart, highlight_max_chart)
    """
    df = df.copy()
    df['hour_of_day'] = df['timestamp'].dt.hour

    # Count messages per hour of day
    hour_counts = df.groupby('hour_of_day').size().reset_index(name='count')

    # Create hour labels and radians
    hour_counts['hour_label'] = hour_counts['hour_of_day'].apply(lambda x: f"{x:02d}:00")
    hour_counts['rad'] = hour_counts['hour_of_day'] * 2 * np.pi / 24 + np.pi / 24

    # Create base chart
    base = alt.Chart(hour_counts).encode(
        theta=alt.Theta('rad:Q', scale=alt.Scale(domain=[0, 2*np.pi])),
        radius=alt.Radius(
            'count:Q',
            scale=alt.Scale(type='sqrt', zero=True, rangeMin=20, rangeMax=180)
        ),
        color=alt.Color('count:Q', scale=alt.Scale(scheme='viridis')),
        tooltip=['hour_label:O', 'count:Q']
    )

    # Create arc chart
    arc = base.mark_arc(innerRadius=20, stroke="black", strokeWidth=0.5)

    # Create hour labels
    hour_labels = alt.Chart(hour_counts).mark_text(
        radiusOffset=10,
        align='center'
    ).encode(
        theta=alt.Theta('rad:Q'),
        text='hour_label:N',
        angle=alt.Angle('rad:Q', offset=-90)
    )

    # Create background for full circle
    background = alt.Chart(hour_counts).mark_arc(
        innerRadius=20,
        stroke="black",
        strokeWidth=0.5,
        opacity=0.1
    ).encode(
        theta=alt.Theta('rad:Q'),
        radius=alt.value(180)
    )

    # Create the first sunburst chart (all data)
    chart1 = (background + arc + hour_labels).properties(
        width=400,
        height=400,
        title='Message Distribution by Hour (All Times)'
    )

    # Create the second sunburst chart (highlight max)
    max_hour = hour_counts.loc[hour_counts['count'].idxmax()]
    highlight = alt.Chart(pd.DataFrame([max_hour])).mark_arc(
        innerRadius=20,
        stroke="black",
        strokeWidth=0.5
    ).encode(
        theta=alt.Theta('rad:Q', scale=alt.Scale(domain=[0, 2*np.pi])),
        radius=alt.Radius(
            'count:Q',
            scale=alt.Scale(type='sqrt', zero=True, rangeMin=20, rangeMax=180)
        ),
        color=alt.Color('count:Q', scale=alt.Scale(scheme='viridis')),
        opacity=alt.value(1)
    )

    chart2 = (background + arc.encode(opacity=alt.value(0.6)) + highlight + hour_labels).properties(
        width=400,
        height=400,
        title='Message Distribution by Hour (Highlight Max)'
    )

    return chart1, chart2
