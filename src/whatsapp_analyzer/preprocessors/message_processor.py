"""
Message processing for multimedia, deleted, and edited message detection.
"""

import re
import numpy as np
import pandas as pd
from typing import Dict, Any


def process_multimedia(df: pd.DataFrame, lang: Dict[str, Any]) -> pd.DataFrame:
    """
    Process multimedia messages, deleted messages, and edited messages.

    Detects and flags:
    - Images, videos, GIFs, stickers, audio, generic media
    - Deleted messages
    - Edited messages (NEW)

    For deleted and edited messages, the message content is cleared (set to NaN)
    to exclude from text analysis while preserving the metadata.

    Args:
        df: DataFrame with 'message' column
        lang: Language settings dictionary from get_language_settings()

    Returns:
        DataFrame with added flag columns:
        - is_image, is_video, is_gif, is_sticker, is_audio, is_media
        - is_deleted
        - is_edited (NEW)
    """
    df = df.copy()

    # Process multimedia types
    multimedia_types = ['image', 'video', 'gif', 'sticker', 'audio', 'media']
    for media_type in multimedia_types:
        column_name = f'is_{media_type}'
        df[column_name] = (df.message == lang[media_type]).astype(int)
        df.loc[df[column_name] == 1, 'message'] = np.nan

    # Process deleted messages
    df['is_deleted'] = df.message.isin(lang["deleted"]).astype(int)
    df.loc[df.is_deleted == 1, 'message'] = np.nan

    # Process edited messages (NEW)
    # Check if message ends with any of the edited patterns
    edited_patterns = lang.get("edited", [])
    if edited_patterns:
        # Create a regex pattern that matches any of the edited message indicators
        # These typically appear at the end of the message
        df['is_edited'] = df.message.apply(
            lambda x: _check_edited(x, edited_patterns) if pd.notna(x) else False
        ).astype(int)
        # Note: We do NOT clear edited message content - just flag it
        # This differs from deleted messages where content is unavailable
    else:
        df['is_edited'] = 0

    return df


def _check_edited(message: str, edited_patterns: list) -> bool:
    """
    Check if a message contains an edited indicator.

    WhatsApp shows edited status in different ways depending on the version:
    - Appended to the end of the message
    - As a separate indicator

    Args:
        message: The message text to check
        edited_patterns: List of patterns indicating edited messages

    Returns:
        True if the message appears to be edited
    """
    if not message:
        return False

    message_lower = message.lower().strip()
    for pattern in edited_patterns:
        pattern_lower = pattern.lower()
        # Check if pattern is at the end of message or is the entire message
        if message_lower.endswith(pattern_lower) or message_lower == pattern_lower:
            return True
    return False


def process_emojis(df: pd.DataFrame) -> pd.DataFrame:
    """
    Detect messages containing emojis.

    Args:
        df: DataFrame with 'message' column

    Returns:
        DataFrame with 'is_emoji' flag column
    """
    df = df.copy()

    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        "]+", flags=re.UNICODE)

    def search_emoji(x):
        if isinstance(x, str):
            return bool(emoji_pattern.search(x))
        return False

    df['is_emoji'] = df['message'].apply(search_emoji).astype(int)
    return df
