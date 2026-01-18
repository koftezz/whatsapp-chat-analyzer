"""
Message counting utilities for WhatsApp chat data.
"""

import pandas as pd


def get_message_count_by_author(df: pd.DataFrame) -> pd.DataFrame:
    """
    Get message counts per author, sorted descending.

    Args:
        df: Preprocessed DataFrame

    Returns:
        DataFrame with author and message columns
    """
    return df.groupby('author')["message"].count().sort_values(
        ascending=False
    ).reset_index()


def get_most_active_author(df_or_counts: pd.DataFrame) -> tuple:
    """
    Get the most active author and their message count.

    Args:
        df_or_counts: Either a preprocessed DataFrame or
                      message counts from get_message_count_by_author()

    Returns:
        Tuple of (author_name, message_count)
    """
    is_message_counts = 'message' in df_or_counts.columns and 'author' in df_or_counts.columns

    if is_message_counts:
        counts = df_or_counts.reset_index(drop=True) if df_or_counts.index.name == 'author' else df_or_counts
    else:
        counts = df_or_counts.groupby('author', as_index=False)["message"].count()

    most_active = counts.sort_values("message", ascending=False).iloc[0]
    return most_active['author'], most_active['message']
