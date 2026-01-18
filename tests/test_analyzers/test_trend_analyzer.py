"""
Tests for trend analyzer module.

This module tests the FIXED talkativeness function - verifying that the
duplicate function bug has been resolved.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add src to path for direct imports - import the module file directly to avoid altair dependency
_src_path = os.path.join(os.path.dirname(__file__), '..', '..', 'src')
sys.path.insert(0, _src_path)

# Import directly from the module file to avoid __init__.py which imports altair
import importlib.util
_spec = importlib.util.spec_from_file_location(
    "trend_analyzer",
    os.path.join(_src_path, "whatsapp_analyzer", "analyzers", "trend_analyzer.py")
)
_trend_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_trend_module)

calculate_talkativeness = _trend_module.calculate_talkativeness
talkativeness = _trend_module.talkativeness
trend_stats = _trend_module.trend_stats
calculate_author_stats = _trend_module.calculate_author_stats
prepare_time_data = _trend_module.prepare_time_data
analyze_trend = _trend_module.analyze_trend
trendline = _trend_module.trendline


class TestCalculateTalkativeness:
    """Tests for the fixed talkativeness function."""

    def test_very_talkative(self):
        """Test classification of very talkative users (>2x average)."""
        # In a 2-person chat, average is 50%.
        # Someone with >100% (impossible) or >2x ratio
        # Let's use 4 people, avg = 25%, very talkative > 50%
        result = calculate_talkativeness(60, 4)
        assert result == "Very talkative"

    def test_talkative(self):
        """Test classification of talkative users (1.5x-2x average)."""
        # 4 people, avg = 25%, talkative = 37.5-50%
        result = calculate_talkativeness(40, 4)
        assert result == "Talkative"

    def test_average(self):
        """Test classification of average users (0.75x-1.5x average)."""
        # 4 people, avg = 25%, average = 18.75-37.5%
        result = calculate_talkativeness(25, 4)
        assert result == "Average"

    def test_quiet(self):
        """Test classification of quiet users (0.5x-0.75x average)."""
        # 4 people, avg = 25%, quiet = 12.5-18.75%
        result = calculate_talkativeness(15, 4)
        assert result == "Quiet"

    def test_very_quiet(self):
        """Test classification of very quiet users (<0.5x average)."""
        # 4 people, avg = 25%, very quiet < 12.5%
        result = calculate_talkativeness(5, 4)
        assert result == "Very quiet"

    def test_backwards_compatible_alias(self):
        """Test that talkativeness is an alias for calculate_talkativeness."""
        assert talkativeness(50, 2) == calculate_talkativeness(50, 2)

    def test_five_tier_classification(self):
        """Test that we have exactly 5 tiers (not 3 like the old duplicate)."""
        # Test all 5 classifications are achievable
        results = set()
        for pct in [5, 15, 25, 40, 60]:
            results.add(calculate_talkativeness(pct, 4))

        assert len(results) == 5
        assert "Very talkative" in results
        assert "Talkative" in results
        assert "Average" in results
        assert "Quiet" in results
        assert "Very quiet" in results


class TestCalculateAuthorStats:
    """Tests for calculate_author_stats function."""

    def test_returns_expected_columns(self, preprocessed_df):
        """Test that the function returns expected columns."""
        result = calculate_author_stats(preprocessed_df)

        expected_columns = [
            "Author",
            "Number of messages",
            "Total %",
            "Talkativeness",
            "Avg Messages/Day"
        ]

        for col in expected_columns:
            assert col in result.columns

    def test_message_counts_correct(self, preprocessed_df):
        """Test that message counts are calculated correctly."""
        result = calculate_author_stats(preprocessed_df)

        # Total should equal original DataFrame size
        assert result["Number of messages"].sum() == len(preprocessed_df)

    def test_percentages_sum_to_100(self, preprocessed_df):
        """Test that percentages sum to 100."""
        result = calculate_author_stats(preprocessed_df)

        assert abs(result["Total %"].sum() - 100) < 0.01


class TestPrepareTimeData:
    """Tests for prepare_time_data function."""

    def test_returns_pivoted_dataframe(self, preprocessed_df):
        """Test that function returns a pivoted DataFrame."""
        result = prepare_time_data(preprocessed_df)

        # Columns should be authors
        assert all(author in result.columns for author in preprocessed_df['author'].unique())

    def test_index_is_sorted(self, preprocessed_df):
        """Test that the index is sorted chronologically."""
        result = prepare_time_data(preprocessed_df)

        assert result.index.is_monotonic_increasing


class TestAnalyzeTrend:
    """Tests for analyze_trend function."""

    def test_insufficient_data(self):
        """Test handling of insufficient data."""
        series = pd.Series([10])
        result = analyze_trend(series)

        assert result == "Insufficient data"

    def test_increasing_trend(self):
        """Test detection of increasing trend."""
        series = pd.Series([10, 20, 30, 40, 50, 60])
        result = analyze_trend(series)

        assert "Increase" in result

    def test_decreasing_trend(self):
        """Test detection of decreasing trend."""
        series = pd.Series([60, 50, 40, 30, 20, 10])
        result = analyze_trend(series)

        assert "Decrease" in result


class TestTrendline:
    """Tests for trendline function."""

    def test_increasing_trendline(self):
        """Test increasing trendline detection."""
        df = pd.Series([1, 2, 3, 4, 5])
        result = trendline(df)

        assert "Increasing" in result

    def test_decreasing_trendline(self):
        """Test decreasing trendline detection."""
        df = pd.Series([5, 4, 3, 2, 1])
        result = trendline(df)

        assert "Decreasing" in result
