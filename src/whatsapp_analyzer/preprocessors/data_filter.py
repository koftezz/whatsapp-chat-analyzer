"""
Data filtering utilities for WhatsApp chat data.
"""

import pandas as pd


def filter_authors(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter out system messages and invalid authors.

    Removes rows where:
    - Author contains a '+' (typically phone numbers without contact names)
    - Author is null

    Args:
        df: DataFrame with 'author' column

    Returns:
        Filtered DataFrame
    """
    return df[~(~df.author.str.extract('(\+)', expand=False).isnull() | df.author.isnull())]
