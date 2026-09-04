"""
Tests for chronotype analyzer module.
"""

import pytest
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

# Add src to path for direct imports
_src_path = os.path.join(os.path.dirname(__file__), '..', '..', 'src')
sys.path.insert(0, _src_path)

import importlib.util
_spec = importlib.util.spec_from_file_location(
    "chronotype_analyzer",
    os.path.join(_src_path, "whatsapp_analyzer", "analyzers", "chronotype_analyzer.py")
)
_chrono_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_chrono_module)

calculate_chronotype_scores = _chrono_module.calculate_chronotype_scores
get_chronotype_summary = _chrono_module.get_chronotype_summary
get_peak_hour_label = _chrono_module.get_peak_hour_label


@pytest.fixture
def early_bird_messages():
    """Create messages from an early bird (active in morning)."""
    base_date = datetime(2024, 1, 1)
    messages = []
    
    # Messages concentrated in morning hours (6-11am)
    for day in range(10):
        for hour in [6, 7, 8, 9, 10, 11]:
            for _ in range(3):  # 3 messages per hour
                timestamp = base_date + timedelta(days=day, hours=hour)
                messages.append({
                    "author": "Alice",
                    "timestamp": timestamp,
                    "hour": hour
                })
    
    return pd.DataFrame(messages)


@pytest.fixture
def night_owl_messages():
    """Create messages from a night owl (active late night)."""
    base_date = datetime(2024, 1, 1)
    messages = []
    
    # Messages concentrated in late night hours (22-2am)
    for day in range(10):
        for hour in [22, 23, 0, 1, 2]:
            for _ in range(3):  # 3 messages per hour
                timestamp = base_date + timedelta(days=day, hours=hour)
                messages.append({
                    "author": "Bob",
                    "timestamp": timestamp,
                    "hour": hour
                })
    
    return pd.DataFrame(messages)


@pytest.fixture
def neutral_chronotype_messages():
    """Create messages from someone with neutral timing (evening)."""
    base_date = datetime(2024, 1, 1)
    messages = []
    
    # Messages concentrated in evening hours (18-21)
    for day in range(10):
        for hour in [18, 19, 20, 21]:
            for _ in range(3):  # 3 messages per hour
                timestamp = base_date + timedelta(days=day, hours=hour)
                messages.append({
                    "author": "Charlie",
                    "timestamp": timestamp,
                    "hour": hour
                })
    
    return pd.DataFrame(messages)


@pytest.fixture
def mixed_chronotype_chat(early_bird_messages, night_owl_messages, neutral_chronotype_messages):
    """Combine early bird and night owl for a mixed chat."""
    return pd.concat([early_bird_messages, night_owl_messages, neutral_chronotype_messages], ignore_index=True)


@pytest.fixture
def single_author_early(early_bird_messages):
    """Single author early bird chat."""
    return early_bird_messages


@pytest.fixture
def uniform_distribution():
    """Create messages uniformly distributed across all hours."""
    base_date = datetime(2024, 1, 1)
    messages = []
    
    for day in range(5):
        for hour in range(24):
            timestamp = base_date + timedelta(days=day, hours=hour)
            messages.append({
                "author": "Dave",
                "timestamp": timestamp,
                "hour": hour
            })
    
    return pd.DataFrame(messages)


class TestCalculateChronotypeScores:
    """Tests for calculate_chronotype_scores function."""
    
    def test_early_bird_detection(self, early_bird_messages):
        """Test detection of early bird chronotype."""
        result = calculate_chronotype_scores(early_bird_messages)
        
        assert 'scores_df' in result
        assert 'chart' in result
        
        scores = result['scores_df']
        assert len(scores) == 1
        
        alice_score = scores[scores['author'] == 'Alice'].iloc[0]
        assert alice_score['score'] > 0.3  # Should be positive (early bird)
        assert "Early Bird" in alice_score['classification'] or "Morning" in alice_score['classification']
        assert alice_score['peak_hour'] in [6, 7, 8, 9, 10, 11]
    
    def test_night_owl_detection(self, night_owl_messages):
        """Test detection of night owl chronotype."""
        result = calculate_chronotype_scores(night_owl_messages)
        
        scores = result['scores_df']
        assert len(scores) == 1
        
        bob_score = scores[scores['author'] == 'Bob'].iloc[0]
        assert bob_score['score'] < -0.3  # Should be negative (night owl)
        assert "Night Owl" in bob_score['classification'] or "Evening" in bob_score['classification']
    
    def test_neutral_chronotype(self, neutral_chronotype_messages):
        """Test detection of neutral chronotype."""
        result = calculate_chronotype_scores(neutral_chronotype_messages)
        
        scores = result['scores_df']
        assert len(scores) == 1
        
        charlie_score = scores[scores['author'] == 'Charlie'].iloc[0]
        # Neutral score should be close to 0
        assert -0.2 < charlie_score['score'] < 0.2
    
    def test_mixed_chronotype_chat(self, mixed_chronotype_chat):
        """Test analysis of chat with multiple chronotypes."""
        result = calculate_chronotype_scores(mixed_chronotype_chat)
        
        scores = result['scores_df']
        assert len(scores) == 3
        
        # Check that we have different chronotypes
        alice_score = scores[scores['author'] == 'Alice']['score'].iloc[0]
        bob_score = scores[scores['author'] == 'Bob']['score'].iloc[0]
        charlie_score = scores[scores['author'] == 'Charlie']['score'].iloc[0]
        
        # Alice should be positive, Bob negative, Charlie neutral
        assert alice_score > 0
        assert bob_score < 0
        assert abs(charlie_score) < abs(alice_score)
    
    def test_uniform_distribution(self, uniform_distribution):
        """Test uniform distribution results in neutral score."""
        result = calculate_chronotype_scores(uniform_distribution)
        
        scores = result['scores_df']
        dave_score = scores[scores['author'] == 'Dave'].iloc[0]
        
        # Should be close to neutral (0)
        assert -0.15 < dave_score['score'] < 0.15
    
    def test_scores_dataframe_structure(self, mixed_chronotype_chat):
        """Test that scores dataframe has expected columns."""
        result = calculate_chronotype_scores(mixed_chronotype_chat)
        scores = result['scores_df']
        
        expected_columns = ['author', 'score', 'classification', 'peak_hour']
        
        for col in expected_columns:
            assert col in scores.columns
    
    def test_score_bounds(self, mixed_chronotype_chat):
        """Test that scores are within reasonable bounds."""
        result = calculate_chronotype_scores(mixed_chronotype_chat)
        scores = result['scores_df']
        
        # Scores should be between -1 and 1 (approximately)
        assert all(scores['score'].between(-1.5, 1.5))
    
    def test_peak_hour_validity(self, mixed_chronotype_chat):
        """Test that peak hours are valid (0-23)."""
        result = calculate_chronotype_scores(mixed_chronotype_chat)
        scores = result['scores_df']
        
        assert all(scores['peak_hour'].between(0, 23))


class TestGetChronotypeSummary:
    """Tests for get_chronotype_summary function."""
    
    def test_single_author_summary(self, early_bird_messages):
        """Test summary for single author."""
        result = calculate_chronotype_scores(early_bird_messages)
        summary = get_chronotype_summary(result['scores_df'])
        
        assert "Alice" in summary
        assert "peak" in summary.lower()
    
    def test_multiple_authors_summary(self, mixed_chronotype_chat):
        """Test summary for multiple authors."""
        result = calculate_chronotype_scores(mixed_chronotype_chat)
        summary = get_chronotype_summary(result['scores_df'])
        
        # Should mention extremes
        assert "earliest" in summary.lower() or "early bird" in summary.lower()
        assert "night owl" in summary.lower() or "latest" in summary.lower()
    
    def test_empty_dataframe(self):
        """Test summary with empty dataframe."""
        empty_df = pd.DataFrame(columns=['author', 'score', 'classification', 'peak_hour'])
        summary = get_chronotype_summary(empty_df)
        
        assert "No data" in summary or "no data" in summary


class TestGetPeakHourLabel:
    """Tests for get_peak_hour_label function."""
    
    def test_midnight(self):
        """Test midnight formatting."""
        assert "12 AM" in get_peak_hour_label(0)
    
    def test_morning_hours(self):
        """Test morning hours formatting."""
        assert "6 AM" in get_peak_hour_label(6)
        assert "11 AM" in get_peak_hour_label(11)
    
    def test_noon(self):
        """Test noon formatting."""
        assert "12 PM" in get_peak_hour_label(12)
    
    def test_afternoon_hours(self):
        """Test afternoon/evening hours formatting."""
        assert "3 PM" in get_peak_hour_label(15)
        assert "11 PM" in get_peak_hour_label(23)
    
    def test_all_hours(self):
        """Test that all hours return a valid label."""
        for hour in range(24):
            label = get_peak_hour_label(hour)
            assert "AM" in label or "PM" in label
            assert len(label) > 0
