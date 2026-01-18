"""
Integration tests for the full preprocessing pipeline.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add src to path for direct imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))


class TestFullPipeline:
    """Integration tests for the complete preprocessing pipeline."""

    def test_english_pipeline(self, sample_messages):
        """Test full pipeline with English messages."""
        from whatsapp_analyzer.preprocessors import preprocess_data

        authors = sample_messages['author'].unique().tolist()
        df, locations = preprocess_data(sample_messages, "English", authors)

        # Check all expected columns exist
        expected_columns = [
            'timestamp', 'author', 'message', 'date', 'year', 'week',
            'is_link', 'msg_length', 'is_image', 'is_deleted', 'is_edited',
            'is_emoji', 'is_conversation_starter'
        ]
        for col in expected_columns:
            assert col in df.columns, f"Missing column: {col}"

        # Check that processing worked
        assert df['is_deleted'].sum() >= 1  # At least one deleted message
        assert df['is_image'].sum() >= 1  # At least one image

    def test_turkish_pipeline(self, sample_turkish_messages):
        """Test full pipeline with Turkish messages."""
        from whatsapp_analyzer.preprocessors import preprocess_data

        authors = sample_turkish_messages['author'].unique().tolist()
        df, locations = preprocess_data(sample_turkish_messages, "Turkish", authors)

        # Check that Turkish-specific detection worked
        assert df['is_deleted'].sum() >= 1
        assert df['is_edited'].sum() >= 1
        assert df['is_image'].sum() >= 1

    def test_german_pipeline(self, sample_german_messages):
        """Test full pipeline with German messages."""
        from whatsapp_analyzer.preprocessors import preprocess_data

        authors = sample_german_messages['author'].unique().tolist()
        df, locations = preprocess_data(sample_german_messages, "German", authors)

        # Check that German-specific detection worked
        assert df['is_deleted'].sum() >= 1
        assert df['is_edited'].sum() >= 1
        assert df['is_image'].sum() >= 1

    def test_edited_messages_detected_all_languages(self):
        """Test that edited messages are detected in all languages."""
        from whatsapp_analyzer.preprocessors import preprocess_data

        test_cases = [
            ("English", "Hello This message was edited", "Alice"),
            ("Turkish", "Merhaba Bu mesaj düzenlendi", "Ahmet"),
            ("German", "Hallo Diese Nachricht wurde bearbeitet", "Hans"),
        ]

        for lang, message, author in test_cases:
            base_time = datetime(2024, 1, 1, 10, 0, 0)
            df = pd.DataFrame([
                {"timestamp": base_time, "author": author, "message": message}
            ])
            df["weekday"] = df["timestamp"].dt.strftime("%A")
            df["hour"] = df["timestamp"].dt.hour
            df["words"] = df["message"].apply(lambda s: len(s.split(" ")))
            df["letters"] = df["message"].apply(len)

            result, _ = preprocess_data(df, lang, [author])

            assert result['is_edited'].sum() == 1, f"Failed for {lang}"


class TestAnalyzerIntegration:
    """Integration tests for analyzer modules."""

    def test_trend_stats_integration(self, preprocessed_df):
        """Test trend_stats with preprocessed data."""
        from whatsapp_analyzer.analyzers import trend_stats

        result = trend_stats(preprocessed_df)

        assert "Author" in result.columns
        assert "Talkativeness" in result.columns
        assert len(result) == preprocessed_df['author'].nunique()

    def test_basic_stats_integration(self, preprocessed_df):
        """Test basic_stats with preprocessed data."""
        from whatsapp_analyzer.analyzers import basic_stats

        result = basic_stats(preprocessed_df)

        # Result should be a styled DataFrame
        assert hasattr(result, 'data')

    def test_activity_integration(self, preprocessed_df):
        """Test activity analyzer with preprocessed data."""
        from whatsapp_analyzer.analyzers import activity

        result = activity(preprocessed_df)

        assert "author" in result.columns
        assert "Activity %" in result.columns


class TestBackwardsCompatibility:
    """Tests for backwards compatibility with helpers.py."""

    def test_helpers_import_works(self):
        """Test that importing from helpers.py still works."""
        import warnings

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            # This should work but emit a deprecation warning
            import helpers

            # Check deprecation warning was emitted
            assert len(w) >= 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "deprecated" in str(w[0].message).lower()

    def test_helpers_functions_available(self):
        """Test that expected functions are available from helpers."""
        import warnings
        warnings.filterwarnings("ignore", category=DeprecationWarning)

        import helpers

        # Check key functions are available
        assert hasattr(helpers, 'read_file')
        assert hasattr(helpers, 'preprocess_data')
        assert hasattr(helpers, 'get_language_settings')
        assert hasattr(helpers, 'talkativeness')
        assert hasattr(helpers, 'trend_stats')
        assert hasattr(helpers, 'basic_stats')

    def test_talkativeness_from_helpers(self):
        """Test that talkativeness from helpers uses the fixed version."""
        import warnings
        warnings.filterwarnings("ignore", category=DeprecationWarning)

        import helpers

        # Should return 5-tier classification
        result = helpers.talkativeness(5, 4)
        assert result == "Very quiet"

        # Check all 5 tiers are available
        results = set()
        for pct in [5, 15, 25, 40, 60]:
            results.add(helpers.talkativeness(pct, 4))

        assert len(results) == 5
