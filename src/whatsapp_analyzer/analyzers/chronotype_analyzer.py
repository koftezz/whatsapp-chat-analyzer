"""
Chronotype analysis for WhatsApp chat data.

Classifies authors as night owls vs early birds based on messaging patterns.
"""

import pandas as pd
import numpy as np
import altair as alt


def calculate_chronotype_scores(df: pd.DataFrame) -> dict:
    """
    Calculate chronotype scores for each author based on message timing.
    
    Classifies authors on a night-owl ↔ early-bird spectrum using hourly
    message distribution. Score ranges from -1 (extreme night owl) to +1
    (extreme early bird).
    
    Args:
        df: Preprocessed DataFrame with columns: author, timestamp (or hour)
    
    Returns:
        Dictionary with:
        - scores_df: DataFrame with author, score, classification, peak_hour
        - chart: Altair visualization showing hourly distributions
    """
    # Extract hour if not already present
    if 'hour' not in df.columns:
        df = df.copy()
        df['hour'] = df['timestamp'].dt.hour
    
    # Calculate hourly message distribution per author
    hourly_dist = df.groupby(['author', 'hour']).size().reset_index(name='count')
    
    # Normalize by total messages per author
    total_per_author = hourly_dist.groupby('author')['count'].transform('sum')
    hourly_dist['proportion'] = hourly_dist['count'] / total_per_author
    
    # Calculate chronotype score for each author
    scores = []
    for author in df['author'].unique():
        author_data = hourly_dist[hourly_dist['author'] == author]
        
        # Create full 24-hour series (fill missing hours with 0)
        hour_series = pd.Series(0.0, index=range(24))
        for _, row in author_data.iterrows():
            hour_series[row['hour']] = row['proportion']
        
        # Calculate score based on weighted hourly distribution
        # Early morning (5-11): +1.0
        # Late morning/afternoon (12-17): +0.5
        # Evening (18-21): 0
        # Night (22-23, 0-4): -1.0
        weights = np.array([
            -1.0, -1.0, -1.0, -1.0, -1.0,  # 0-4: deep night (night owl)
            +1.0, +1.0, +1.0, +1.0, +1.0, +1.0, +1.0,  # 5-11: early morning (early bird)
            +0.5, +0.5, +0.5, +0.5, +0.5, +0.5,  # 12-17: afternoon (mild early bird)
            0.0, 0.0, 0.0, 0.0,  # 18-21: evening (neutral)
            -1.0, -1.0  # 22-23: night (night owl)
        ])
        
        score = np.dot(hour_series.values, weights)
        
        # Find peak activity hour
        peak_hour = hour_series.idxmax()
        
        # Classify based on score
        classification = _classify_chronotype(score)
        
        scores.append({
            'author': author,
            'score': score,
            'classification': classification,
            'peak_hour': peak_hour
        })
    
    scores_df = pd.DataFrame(scores)
    
    # Create visualization
    chart = _create_chronotype_chart(hourly_dist, scores_df)
    
    return {
        'scores_df': scores_df,
        'chart': chart
    }


def _classify_chronotype(score: float) -> str:
    """
    Classify chronotype based on score.
    
    Args:
        score: Chronotype score (-1 to +1)
    
    Returns:
        Classification string
    """
    if score > 0.3:
        return "Early Bird 🌅"
    elif score > 0.1:
        return "Morning Person ☀️"
    elif score > -0.1:
        return "Neutral 🕐"
    elif score > -0.3:
        return "Evening Person 🌆"
    else:
        return "Night Owl 🦉"


def _create_chronotype_chart(hourly_dist: pd.DataFrame, scores_df: pd.DataFrame) -> alt.Chart:
    """
    Create a visualization showing hourly message distribution per author.
    
    Args:
        hourly_dist: DataFrame with hourly message counts
        scores_df: DataFrame with chronotype scores
    
    Returns:
        Altair chart
    """
    # Merge classification into hourly data
    hourly_with_class = hourly_dist.merge(
        scores_df[['author', 'classification']],
        on='author',
        how='left'
    )
    
    # Create line chart showing hourly patterns
    line_chart = alt.Chart(hourly_with_class).mark_line(point=True).encode(
        x=alt.X('hour:O', title='Hour of Day', axis=alt.Axis(labelAngle=0)),
        y=alt.Y('proportion:Q', title='Proportion of Messages'),
        color=alt.Color('author:N', title='Author'),
        tooltip=[
            alt.Tooltip('author:N', title='Author'),
            alt.Tooltip('classification:N', title='Type'),
            alt.Tooltip('hour:O', title='Hour'),
            alt.Tooltip('proportion:Q', title='Proportion', format='.2%')
        ]
    ).properties(
        width=800,
        height=400,
        title='Message Activity by Hour (Chronotype Profiles)'
    )
    
    return line_chart


def get_chronotype_summary(scores_df: pd.DataFrame) -> str:
    """
    Get a human-readable summary of chronotype distribution.
    
    Args:
        scores_df: DataFrame with chronotype scores
    
    Returns:
        Summary string
    """
    if len(scores_df) == 0:
        return "No data to analyze"
    
    # Find extremes
    most_early = scores_df.loc[scores_df['score'].idxmax()]
    most_late = scores_df.loc[scores_df['score'].idxmin()]
    
    summary_parts = []
    
    if len(scores_df) == 1:
        author = scores_df.iloc[0]
        summary_parts.append(
            f"**{author['author']}** is a {author['classification']} "
            f"with peak activity at {author['peak_hour']:02d}:00"
        )
    else:
        summary_parts.append(
            f"**{most_early['author']}** is the earliest bird "
            f"(peak at {most_early['peak_hour']:02d}:00)"
        )
        summary_parts.append(
            f"**{most_late['author']}** is the latest night owl "
            f"(peak at {most_late['peak_hour']:02d}:00)"
        )
    
    return " • ".join(summary_parts)


def get_peak_hour_label(hour: int) -> str:
    """
    Convert hour to readable time label.
    
    Args:
        hour: Hour (0-23)
    
    Returns:
        Formatted time string
    """
    if hour == 0:
        return "12 AM"
    elif hour < 12:
        return f"{hour} AM"
    elif hour == 12:
        return "12 PM"
    else:
        return f"{hour - 12} PM"
