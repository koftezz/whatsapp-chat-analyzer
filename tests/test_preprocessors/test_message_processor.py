"""
Tests for message processor module.
"""

import pytest
import pandas as pd
import numpy as np
import sys
import os

# Add src to path for direct imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from whatsapp_analyzer.preprocessors.message_processor import (
    process_multimedia,
    process_emojis,
    _check_edited,
)
from whatsapp_analyzer.preprocessors.language_config import get_language_settings


class TestProcessMultimedia:
    """Tests for process_multimedia function."""

    def test_detects_image_messages(self, sample_messages, english_language_settings):
        """Test that image messages are detected."""
        result = process_multimedia(sample_messages, english_language_settings)

        assert "is_image" in result.columns
        assert result[result["is_image"] == 1].shape[0] == 1

    def test_detects_deleted_messages(self, sample_messages, english_language_settings):
        """Test that deleted messages are detected."""
        result = process_multimedia(sample_messages, english_language_settings)

        assert "is_deleted" in result.columns
        assert result[result["is_deleted"] == 1].shape[0] == 1

    def test_clears_deleted_message_content(self, sample_messages, english_language_settings):
        """Test that deleted message content is cleared."""
        result = process_multimedia(sample_messages, english_language_settings)

        deleted_rows = result[result["is_deleted"] == 1]
        assert deleted_rows["message"].isna().all()

    def test_detects_edited_messages_english(self, sample_df_with_edited_messages, english_language_settings):
        """Test that edited messages are detected in English."""
        result = process_multimedia(sample_df_with_edited_messages, english_language_settings)

        assert "is_edited" in result.columns
        # Should detect 2 edited messages
        assert result[result["is_edited"] == 1].shape[0] == 2

    def test_detects_edited_messages_turkish(self, sample_turkish_messages, turkish_language_settings):
        """Test that edited messages are detected in Turkish."""
        result = process_multimedia(sample_turkish_messages, turkish_language_settings)

        assert "is_edited" in result.columns
        edited_count = result[result["is_edited"] == 1].shape[0]
        assert edited_count == 1

    def test_detects_edited_messages_german(self, sample_german_messages, german_language_settings):
        """Test that edited messages are detected in German."""
        result = process_multimedia(sample_german_messages, german_language_settings)

        assert "is_edited" in result.columns
        edited_count = result[result["is_edited"] == 1].shape[0]
        assert edited_count == 1

    def test_does_not_clear_edited_message_content(self, sample_df_with_edited_messages, english_language_settings):
        """Test that edited message content is NOT cleared (unlike deleted)."""
        result = process_multimedia(sample_df_with_edited_messages, english_language_settings)

        edited_rows = result[result["is_edited"] == 1]
        # Edited messages should retain their content
        assert not edited_rows["message"].isna().all()


class TestCheckEdited:
    """Tests for _check_edited helper function."""

    def test_detects_edited_at_end(self):
        """Test detection of edited indicator at end of message."""
        patterns = ["This message was edited"]

        assert _check_edited("Hello world This message was edited", patterns)
        assert _check_edited("Test This message was edited", patterns)

    def test_case_insensitive(self):
        """Test that detection is case-insensitive."""
        patterns = ["This message was edited"]

        assert _check_edited("Hello THIS MESSAGE WAS EDITED", patterns)
        assert _check_edited("Hello this message was edited", patterns)

    def test_exact_match(self):
        """Test detection of exact match (entire message is the pattern)."""
        patterns = ["This message was edited"]

        assert _check_edited("This message was edited", patterns)

    def test_no_false_positives(self):
        """Test that normal messages aren't flagged."""
        patterns = ["This message was edited"]

        assert not _check_edited("Hello world", patterns)
        assert not _check_edited("This message was great", patterns)

    def test_handles_empty_input(self):
        """Test handling of empty/None input."""
        patterns = ["This message was edited"]

        assert not _check_edited("", patterns)
        assert not _check_edited(None, patterns)


class TestProcessEmojis:
    """Tests for process_emojis function."""

    def test_detects_emoji_messages(self):
        """Test that emoji-containing messages are detected."""
        df = pd.DataFrame({
            "message": ["Hello!", "Hi there 😀", "Good morning 🌞🌻"]
        })

        result = process_emojis(df)

        assert "is_emoji" in result.columns
        assert result.loc[0, "is_emoji"] == 0
        assert result.loc[1, "is_emoji"] == 1
        assert result.loc[2, "is_emoji"] == 1

    def test_handles_non_string_messages(self):
        """Test handling of non-string messages."""
        df = pd.DataFrame({
            "message": ["Hello", np.nan, None, 123]
        })

        result = process_emojis(df)

        assert result.loc[0, "is_emoji"] == 0
        assert result.loc[1, "is_emoji"] == 0
