"""
Feature extraction utilities for WhatsApp chat data.
"""

import numpy as np
import pandas as pd
from typing import Tuple
from urllib.parse import parse_qs, urlparse


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
    location_messages = df.loc[df["is_location"] == 1, "message"].copy()
    df.loc[df.is_location == 1, 'message'] = np.nan

    coordinates = []
    for message in location_messages:
        coordinate = _extract_google_maps_coordinates(message)
        if coordinate is not None:
            coordinates.append(coordinate)

    locations = pd.DataFrame(coordinates, columns=["lat", "lon"]).drop_duplicates()

    return df, locations


def _extract_google_maps_coordinates(message: str):
    """Extract validated coordinates from a Google Maps URL, if present."""
    for raw_url in str(message).split():
        url = raw_url.rstrip(".,;!?)")
        parsed = urlparse(url)
        hostname = parsed.hostname or ""
        if hostname != "maps.google.com" and not hostname.startswith("maps.google."):
            continue

        query = parse_qs(parsed.query)
        value = next(iter(query.get("q", query.get("query", []))), None)
        if value is None:
            continue

        try:
            latitude, longitude = (float(part.strip()) for part in value.split(",", 1))
        except (TypeError, ValueError):
            continue
        if -90 <= latitude <= 90 and -180 <= longitude <= 180:
            return latitude, longitude

    return None


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
