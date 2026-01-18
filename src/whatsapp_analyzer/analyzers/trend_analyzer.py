"""
Trend analysis for WhatsApp chat messaging patterns.

This module contains the FIXED talkativeness function - the duplicate
at line 769 in the original helpers.py has been removed. This version
uses the more nuanced 5-tier classification system.
"""

import numpy as np
import pandas as pd
from scipy import stats


def calculate_talkativeness(percentage: float, num_authors: int) -> str:
    """
    Calculate talkativeness classification based on message percentage.

    Uses a ratio-based 5-tier classification system:
    - Very talkative: > 2x average
    - Talkative: > 1.5x average
    - Average: 0.75x - 1.5x average
    - Quiet: 0.5x - 0.75x average
    - Very quiet: < 0.5x average

    Args:
        percentage: Author's percentage of total messages
        num_authors: Total number of authors in chat

    Returns:
        Talkativeness classification string
    """
    average = 100 / num_authors
    ratio = percentage / average

    if ratio > 2:
        return "Very talkative"
    elif ratio > 1.5:
        return "Talkative"
    elif ratio > 0.75:
        return "Average"
    elif ratio > 0.5:
        return "Quiet"
    else:
        return "Very quiet"


# Backwards compatibility alias
talkativeness = calculate_talkativeness


def trend_stats(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate comprehensive trend statistics for all authors.

    Args:
        df: Preprocessed DataFrame with timestamp and author columns

    Returns:
        DataFrame with author statistics and trends
    """
    author_stats = calculate_author_stats(df)
    time_data = prepare_time_data(df)
    author_stats = calculate_messaging_trends(author_stats, time_data)
    return author_stats


def calculate_author_stats(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate basic statistics per author.

    Args:
        df: Preprocessed DataFrame

    Returns:
        DataFrame with columns:
        - Author
        - Number of messages
        - Total %
        - Talkativeness
        - Avg Messages/Day
    """
    author_stats = df["author"].value_counts().reset_index()
    author_stats.columns = ["Author", "Number of messages"]
    total_messages = df.shape[0]
    author_stats["Total %"] = round(author_stats["Number of messages"] * 100 / total_messages, 2)
    author_stats["Talkativeness"] = author_stats["Total %"].apply(
        lambda x: calculate_talkativeness(x, df["author"].nunique())
    )

    # Add average messages per day
    date_range = (df['timestamp'].max() - df['timestamp'].min()).days + 1
    author_stats["Avg Messages/Day"] = round(author_stats["Number of messages"] / date_range, 2)

    return author_stats


def prepare_time_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare time-series data for trend analysis.

    Args:
        df: Preprocessed DataFrame with timestamp column

    Returns:
        Pivoted DataFrame with months as rows and authors as columns
    """
    df = df.copy()
    df["yearmonth"] = df["timestamp"].dt.to_period('M')
    time_data = df.groupby(["yearmonth", "author"]).size().unstack(fill_value=0)
    return time_data.sort_index()


def calculate_messaging_trends(
    author_stats: pd.DataFrame,
    time_data: pd.DataFrame
) -> pd.DataFrame:
    """
    Calculate messaging trends for multiple time periods.

    Args:
        author_stats: DataFrame with Author column
        time_data: Time-series data from prepare_time_data()

    Returns:
        author_stats with trend columns added
    """
    for period in [12, 6, 3]:
        column_name = f"Trend Last {period} Months"
        author_stats[column_name] = author_stats["Author"].apply(
            lambda x: analyze_trend(time_data.tail(period)[x])
        )
    return author_stats


def analyze_trend(series: pd.Series) -> str:
    """
    Analyze trend direction and strength for a time series.

    Args:
        series: Pandas Series of message counts over time

    Returns:
        Trend description (e.g., "Strong Increase", "Moderate Decrease")
    """
    if len(series) < 2:
        return "Insufficient data"

    x = np.arange(len(series))
    y = series.values

    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)

    # Calculate percentage change
    start_value = series.iloc[0]
    end_value = series.iloc[-1]
    pct_change = ((end_value - start_value) / start_value) * 100 if start_value != 0 else np.inf

    # Interpret trend
    if p_value < 0.1:  # Statistical significance threshold
        if slope > 0:
            trend = "Increase"
        else:
            trend = "Decrease"
    else:
        trend = "No trend"

    # Determine trend strength
    if abs(pct_change) > 50:
        strength = "Strong"
    elif abs(pct_change) > 25:
        strength = "Moderate"
    else:
        strength = "Slight"

    return f"{strength} {trend}"


def trendline(df: pd.DataFrame, order: int = 1) -> str:
    """
    Calculate simple linear trendline.

    Args:
        df: DataFrame or Series with numeric values
        order: Polynomial order (default 1 for linear)

    Returns:
        Trend direction with slope value
    """
    index = range(0, len(df))
    coeffs = np.polyfit(index, list(df), order)
    slope = coeffs[-2]

    if slope > 0:
        return f"Increasing ({round(slope, 2)})"
    else:
        return f"Decreasing ({round(slope, 2)})"
