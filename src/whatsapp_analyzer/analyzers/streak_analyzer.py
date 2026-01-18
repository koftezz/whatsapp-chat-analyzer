"""
Messaging streak analysis for WhatsApp chat data.
"""

import pandas as pd


def find_longest_consecutive_streak(df: pd.DataFrame) -> dict:
    """
    Find the longest consecutive messaging streak by a single author.

    A streak is defined as consecutive messages from the same author
    without interruption from other authors.

    Args:
        df: Preprocessed DataFrame

    Returns:
        Dictionary with:
        - author: Author with longest streak
        - streak_length: Number of consecutive messages
        - start_time: Streak start timestamp
        - end_time: Streak end timestamp
        - streak_messages: DataFrame of messages in the streak
    """
    df = df.sort_values('timestamp').copy()

    # Create a new column to identify changes in author
    df['author_change'] = (df['author'] != df['author'].shift()).cumsum()

    # Group by the author and the change indicator
    grouped = df.groupby(['author', 'author_change'])

    # Find the group with the maximum count
    streak_info = grouped.size().reset_index(name='streak_length')
    longest_streak = streak_info.loc[streak_info['streak_length'].idxmax()]

    max_spammer = longest_streak['author']
    max_spam = longest_streak['streak_length']

    # Get the start and end times of the longest streak
    streak_data = grouped.get_group((max_spammer, longest_streak['author_change']))
    start_time = streak_data['timestamp'].min()
    end_time = streak_data['timestamp'].max()

    # Select relevant columns for display
    streak_messages = streak_data[['timestamp', 'author', 'message']]

    return {
        'author': max_spammer,
        'streak_length': max_spam,
        'start_time': start_time,
        'end_time': end_time,
        'streak_messages': streak_messages
    }
