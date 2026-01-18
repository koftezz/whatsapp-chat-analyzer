"""
Tests for language configuration module.
"""

import pytest
import sys
import os

# Add src to path for direct imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from whatsapp_analyzer.preprocessors.language_config import (
    get_language_settings,
    SUPPORTED_LANGUAGES,
    LANGUAGE_SETTINGS,
)


class TestLanguageConfig:
    """Tests for language configuration."""

    def test_supported_languages(self):
        """Test that expected languages are supported."""
        assert "English" in SUPPORTED_LANGUAGES
        assert "Turkish" in SUPPORTED_LANGUAGES
        assert "German" in SUPPORTED_LANGUAGES
        assert len(SUPPORTED_LANGUAGES) == 3

    def test_get_english_settings(self):
        """Test English language settings."""
        settings = get_language_settings("English")

        assert settings["image"] == "image omitted"
        assert settings["video"] == "video omitted"
        assert settings["media"] == "<Media omitted>"
        assert "This message was deleted." in settings["deleted"]
        assert "This message was edited" in settings["edited"]

    def test_get_turkish_settings(self):
        """Test Turkish language settings."""
        settings = get_language_settings("Turkish")

        assert settings["image"] == "görüntü dahil edilmedi"
        assert "Bu mesaj silindi." in settings["deleted"]
        assert "Bu mesaj düzenlendi" in settings["edited"]

    def test_get_german_settings(self):
        """Test German language settings."""
        settings = get_language_settings("German")

        assert settings["image"] == "Bild weggelassen"
        assert "Diese Nachricht wurde gelöscht." in settings["deleted"]
        assert "Diese Nachricht wurde bearbeitet" in settings["edited"]

    def test_invalid_language_raises_error(self):
        """Test that invalid language raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            get_language_settings("French")

        assert "Unsupported language" in str(exc_info.value)
        assert "French" in str(exc_info.value)

    def test_all_languages_have_edited_patterns(self):
        """Test that all languages have edited message patterns."""
        for lang in SUPPORTED_LANGUAGES:
            settings = get_language_settings(lang)
            assert "edited" in settings, f"{lang} missing 'edited' key"
            assert len(settings["edited"]) > 0, f"{lang} has empty 'edited' list"

    def test_all_languages_have_required_keys(self):
        """Test that all languages have all required keys."""
        required_keys = ["image", "video", "gif", "audio", "sticker", "deleted", "edited", "location", "media"]

        for lang in SUPPORTED_LANGUAGES:
            settings = get_language_settings(lang)
            for key in required_keys:
                assert key in settings, f"{lang} missing required key: {key}"


class TestEditedMessagePatterns:
    """Tests specifically for edited message patterns."""

    def test_english_edited_patterns(self):
        """Test English edited message patterns."""
        settings = get_language_settings("English")
        edited = settings["edited"]

        assert "This message was edited" in edited
        assert "You edited this message" in edited

    def test_turkish_edited_patterns(self):
        """Test Turkish edited message patterns."""
        settings = get_language_settings("Turkish")
        edited = settings["edited"]

        assert "Bu mesaj düzenlendi" in edited
        assert "Bu mesajı düzenlediniz" in edited

    def test_german_edited_patterns(self):
        """Test German edited message patterns."""
        settings = get_language_settings("German")
        edited = settings["edited"]

        assert "Diese Nachricht wurde bearbeitet" in edited
        assert "Du hast diese Nachricht bearbeitet" in edited
