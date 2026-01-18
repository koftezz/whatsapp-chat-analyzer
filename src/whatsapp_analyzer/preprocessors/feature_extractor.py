"""
Feature extraction utilities for WhatsApp chat data.
"""

import numpy as np
import pandas as pd
from typing import Tuple


def add_conversation_starter_flag(df: pd.DataFrame) -> pd.DataFrame:
    """
    Flag messages that start a new conversation.

    A message is considered a conversation starter if it's sent more than
    7 hours after the previous message.

    Args:
        df: DataFrame with 'timestamp' column, sorted chronologically

    Returns:
        DataFrame with 'is_conversation_starter' flag column
    """
    df = df.copy()
    df['is_conversation_starter'] = (
        (df.timestamp - df.timestamp.shift(1)) > pd.Timedelta('7 hours')
    ).astype(int)
    return df


def process_locations(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Extract and process location sharing messages.

    Args:
        df: DataFrame with 'message' column

    Returns:
        Tuple of (processed DataFrame, locations DataFrame with lat/lon)
    """
    df = df.copy()
    df["is_location"] = df.message.str.contains('maps.google', na=False).astype(int)
    locations = df.loc[df["is_location"] == 1].copy()
    df.loc[df.is_location == 1, 'message'] = np.nan

    if locations.shape[0] > 0:
        locs = locations["message"].str.split(" ", expand=True)
        locs[1] = locs[1].str[27:]
        locs = locs[1].str.split(",", expand=True)
        locs = locs.rename(columns={0: "lat", 1: "lon"})
        locs = locs.loc[
            (locs["lat"] != "") &
            (locs["lon"] != "") &
            (~locs["lat"].isna()) &
            (~locs["lon"].isna())
        ]
        locations = locs[["lat", "lon"]].astype(float).drop_duplicates()
    else:
        locations = pd.DataFrame(columns=["lat", "lon"])

    return df, locations


def process_links(df: pd.DataFrame) -> pd.DataFrame:
    """
    Detect messages containing links.

    Args:
        df: DataFrame with 'message' column

    Returns:
        DataFrame with 'is_link' flag column
    """
    df = df.copy()
    df['is_link'] = df.message.str.contains(r'https?:\S+', regex=True, na=False).astype(int)
    return df


def process_message_length(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate message length, excluding links.

    Args:
        df: DataFrame with 'message' and 'is_link' columns

    Returns:
        DataFrame with 'msg_length' column
    """
    df = df.copy()
    df['msg_length'] = df.message.str.len()
    df.loc[df.is_link == 1, 'msg_length'] = np.nan
    return df
