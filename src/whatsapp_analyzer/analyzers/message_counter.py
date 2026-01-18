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


def get_most_active_author(df_or_counts) -> tuple:
    """
    Get the most active author and their message count.

    Args:
        df_or_counts: Either a preprocessed DataFrame or
                      message counts from get_message_count_by_author()

    Returns:
        Tuple of (author_name, message_count)
    """
    if 'message' in df_or_counts.columns and 'author' in df_or_counts.columns:
        # It's a message counts DataFrame
        if df_or_counts.index.name == 'author':
            df_or_counts = df_or_counts.reset_index()
        most_active = df_or_counts.sort_values("message", ascending=False).iloc[0]
        return most_active['author'], most_active['message']
    else:
        # It's a raw DataFrame - compute counts first
        author_message_counts = df_or_counts.groupby(
            'author', as_index=False
        )["message"].count().reset_index()
        most_active_author = author_message_counts.sort_values(
            "message", ascending=False
        ).iloc[0]
        return most_active_author['author'], most_active_author['message']
