"""
Chat summary calculation for WhatsApp chat analysis UI.
"""

import pandas as pd


def calculate_chat_summary(df: pd.DataFrame) -> dict:
    """
    Calculate summary statistics for a chat.

    Args:
        df: Preprocessed DataFrame

    Returns:
        Dictionary with:
        - total_messages: Total message count
        - unique_authors: Number of unique authors
        - start_date: First message date
        - end_date: Last message date
        - total_days: Number of days spanned
        - avg_messages_per_day: Average daily messages
        - most_active_author: Most active author name
        - most_active_author_messages: Their message count
        - most_active_author_percentage: Their percentage of total
    """
    df = df.copy()
    total_messages = len(df)
    unique_authors = len(df.author.unique())

    # Convert date strings to datetime objects if needed
    if df['date'].dtype == object:
        df['date'] = pd.to_datetime(df['date'])

    start_date = df.date.min()
    end_date = df.date.max()
    total_days = (end_date - start_date).days + 1  # Include both start and end dates
    avg_messages_per_day = total_messages / total_days

    author_counts = df['author'].value_counts()
    most_active_author = author_counts.index[0]
    most_active_author_messages = author_counts.iloc[0]
    most_active_author_percentage = (most_active_author_messages / total_messages) * 100

    return {
        "total_messages": total_messages,
        "unique_authors": unique_authors,
        "start_date": start_date,
        "end_date": end_date,
        "total_days": total_days,
        "avg_messages_per_day": avg_messages_per_day,
        "most_active_author": most_active_author,
        "most_active_author_messages": most_active_author_messages,
        "most_active_author_percentage": most_active_author_percentage
    }
