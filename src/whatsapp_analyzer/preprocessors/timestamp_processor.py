"""
Timestamp processing utilities for WhatsApp chat data.
"""

import pandas as pd
from typing import List


def preprocess_timestamps(df: pd.DataFrame, selected_authors: List[str]) -> pd.DataFrame:
    """
    Process timestamps and filter by selected authors.

    Args:
        df: DataFrame with 'timestamp' and 'author' columns
        selected_authors: List of authors to include

    Returns:
        DataFrame with processed timestamps, sorted chronologically
    """
    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors='coerce')
    df["date"] = df["timestamp"].dt.strftime('%Y-%m-%d')
    df = df.loc[df["author"].isin(selected_authors)]
    return df.sort_values(["timestamp"])


def add_year_week(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add year and week columns to DataFrame.

    Args:
        df: DataFrame with 'timestamp' column

    Returns:
        DataFrame with 'year' and 'week' columns added
    """
    df = df.copy()
    df['year'] = df['timestamp'].dt.year
    df['week'] = df['timestamp'].dt.isocalendar().week
    return df
