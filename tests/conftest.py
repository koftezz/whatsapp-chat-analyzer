"""
Pytest configuration and shared fixtures for WhatsApp Chat Analyzer tests.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


@pytest.fixture
def sample_messages():
    """Create sample message data for testing."""
    base_time = datetime(2024, 1, 1, 10, 0, 0)

    messages = [
        {"timestamp": base_time, "author": "Alice", "message": "Hello everyone!"},
        {"timestamp": base_time + timedelta(minutes=1), "author": "Bob", "message": "Hi Alice!"},
        {"timestamp": base_time + timedelta(minutes=2), "author": "Alice", "message": "How are you?"},
        {"timestamp": base_time + timedelta(minutes=5), "author": "Charlie", "message": "Hey folks!"},
        {"timestamp": base_time + timedelta(minutes=10), "author": "Bob", "message": "image omitted"},
        {"timestamp": base_time + timedelta(minutes=15), "author": "Alice", "message": "This message was deleted."},
        {"timestamp": base_time + timedelta(minutes=20), "author": "Charlie", "message": "Check this link https://example.com"},
        {"timestamp": base_time + timedelta(hours=8), "author": "Alice", "message": "Good morning!"},  # Conversation starter
        {"timestamp": base_time + timedelta(hours=8, minutes=5), "author": "Bob", "message": "Morning Alice!"},
        {"timestamp": base_time + timedelta(days=1), "author": "Alice", "message": "New day!"},
    ]

    df = pd.DataFrame(messages)
    df["weekday"] = df["timestamp"].dt.strftime("%A")
    df["hour"] = df["timestamp"].dt.hour
    df["words"] = df["message"].apply(lambda s: len(s.split(" ")))
    df["letters"] = df["message"].apply(len)

    return df


@pytest.fixture
def sample_df_with_edited_messages():
    """Create sample data including edited messages."""
    base_time = datetime(2024, 1, 1, 10, 0, 0)

    messages = [
        {"timestamp": base_time, "author": "Alice", "message": "Original message This message was edited"},
        {"timestamp": base_time + timedelta(minutes=1), "author": "Bob", "message": "Normal message"},
        {"timestamp": base_time + timedelta(minutes=2), "author": "Alice", "message": "This message was deleted."},
        {"timestamp": base_time + timedelta(minutes=3), "author": "Charlie", "message": "Another edit You edited this message"},
    ]

    df = pd.DataFrame(messages)
    df["weekday"] = df["timestamp"].dt.strftime("%A")
    df["hour"] = df["timestamp"].dt.hour
    df["words"] = df["message"].apply(lambda s: len(s.split(" ")))
    df["letters"] = df["message"].apply(len)

    return df


@pytest.fixture
def sample_turkish_messages():
    """Create sample Turkish message data for testing."""
    base_time = datetime(2024, 1, 1, 10, 0, 0)

    messages = [
        {"timestamp": base_time, "author": "Ahmet", "message": "Merhaba!"},
        {"timestamp": base_time + timedelta(minutes=1), "author": "Mehmet", "message": "Selam!"},
        {"timestamp": base_time + timedelta(minutes=2), "author": "Ahmet", "message": "Bu mesaj silindi."},
        {"timestamp": base_time + timedelta(minutes=3), "author": "Mehmet", "message": "Bu mesaj düzenlendi"},
        {"timestamp": base_time + timedelta(minutes=4), "author": "Ahmet", "message": "görüntü dahil edilmedi"},
    ]

    df = pd.DataFrame(messages)
    df["weekday"] = df["timestamp"].dt.strftime("%A")
    df["hour"] = df["timestamp"].dt.hour
    df["words"] = df["message"].apply(lambda s: len(s.split(" ")))
    df["letters"] = df["message"].apply(len)

    return df


@pytest.fixture
def sample_german_messages():
    """Create sample German message data for testing."""
    base_time = datetime(2024, 1, 1, 10, 0, 0)

    messages = [
        {"timestamp": base_time, "author": "Hans", "message": "Hallo!"},
        {"timestamp": base_time + timedelta(minutes=1), "author": "Greta", "message": "Guten Tag!"},
        {"timestamp": base_time + timedelta(minutes=2), "author": "Hans", "message": "Diese Nachricht wurde gelöscht."},
        {"timestamp": base_time + timedelta(minutes=3), "author": "Greta", "message": "Diese Nachricht wurde bearbeitet"},
        {"timestamp": base_time + timedelta(minutes=4), "author": "Hans", "message": "Bild weggelassen"},
    ]

    df = pd.DataFrame(messages)
    df["weekday"] = df["timestamp"].dt.strftime("%A")
    df["hour"] = df["timestamp"].dt.hour
    df["words"] = df["message"].apply(lambda s: len(s.split(" ")))
    df["letters"] = df["message"].apply(len)

    return df


@pytest.fixture
def preprocessed_df(sample_messages):
    """Create a preprocessed DataFrame with all standard columns."""
    df = sample_messages.copy()
    df["date"] = df["timestamp"].dt.strftime('%Y-%m-%d')
    df["year"] = df["timestamp"].dt.year
    df["week"] = df["timestamp"].dt.isocalendar().week
    df["is_link"] = df.message.str.contains('https?:', regex=True, na=False).astype(int)
    df["msg_length"] = df.message.str.len()
    df["is_image"] = (df.message == "image omitted").astype(int)
    df["is_video"] = 0
    df["is_gif"] = 0
    df["is_audio"] = 0
    df["is_sticker"] = 0
    df["is_media"] = 0
    df["is_deleted"] = df.message.isin(["This message was deleted.", "You deleted this message."]).astype(int)
    df["is_edited"] = 0
    df["is_emoji"] = 0
    df["is_location"] = 0
    df["is_conversation_starter"] = ((df.timestamp - df.timestamp.shift(1)) > pd.Timedelta('7 hours')).astype(int)
    df.loc[0, "is_conversation_starter"] = 0  # First message isn't a conversation starter

    # Clear message content for deleted/media
    df.loc[df.is_deleted == 1, 'message'] = np.nan
    df.loc[df.is_image == 1, 'message'] = np.nan

    return df


@pytest.fixture
def english_language_settings():
    """Return English language settings."""
    from whatsapp_analyzer.preprocessors.language_config import get_language_settings
    return get_language_settings("English")


@pytest.fixture
def turkish_language_settings():
    """Return Turkish language settings."""
    from whatsapp_analyzer.preprocessors.language_config import get_language_settings
    return get_language_settings("Turkish")


@pytest.fixture
def german_language_settings():
    """Return German language settings."""
    from whatsapp_analyzer.preprocessors.language_config import get_language_settings
    return get_language_settings("German")
