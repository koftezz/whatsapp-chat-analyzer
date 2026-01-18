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
    has_plus_sign = df.author.str.contains(r'\+', regex=True, na=False)
    is_null = df.author.isnull()
    return df[~(has_plus_sign | is_null)]
