"""
Tests for conversation balance analyzer module.
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
    "conversation_balance_analyzer",
    os.path.join(_src_path, "whatsapp_analyzer", "analyzers", "conversation_balance_analyzer.py")
)
_balance_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_balance_module)

calculate_conversation_balance = _balance_module.calculate_conversation_balance
get_balance_description = _balance_module.get_balance_description


@pytest.fixture
def balanced_two_person_chat():
    """Create a perfectly balanced 2-person chat."""
    base_time = datetime(2024, 1, 1, 10, 0, 0)
    
    messages = []
    for i in range(10):
        messages.append({
            "author": "Alice",
            "words": 5,
            "is_conversation_starter": 1 if i % 2 == 0 else 0
        })
        messages.append({
            "author": "Bob",
            "words": 5,
            "is_conversation_starter": 0
        })
    
    return pd.DataFrame(messages)


@pytest.fixture
def unbalanced_two_person_chat():
    """Create an unbalanced 2-person chat (one dominates)."""
    base_time = datetime(2024, 1, 1, 10, 0, 0)
    
    messages = []
    # Alice sends 80% of messages
    for i in range(40):
        messages.append({
            "author": "Alice",
            "words": 5,
            "is_conversation_starter": 1 if i % 5 == 0 else 0
        })
    
    # Bob sends 20% of messages
    for i in range(10):
        messages.append({
            "author": "Bob",
            "words": 5,
            "is_conversation_starter": 0
        })
    
    return pd.DataFrame(messages)


@pytest.fixture
def balanced_group_chat():
    """Create a balanced 3-person group chat."""
    messages = []
    
    for author in ["Alice", "Bob", "Charlie"]:
        for i in range(10):
            messages.append({
                "author": author,
                "words": 5,
                "is_conversation_starter": 1 if i == 0 else 0
            })
    
    return pd.DataFrame(messages)


@pytest.fixture
def single_author_chat():
    """Create a chat with only one author."""
    messages = []
    
    for i in range(10):
        messages.append({
            "author": "Alice",
            "words": 5,
            "is_conversation_starter": 1 if i % 3 == 0 else 0
        })
    
    return pd.DataFrame(messages)


@pytest.fixture
def chat_no_starters():
    """Create a chat without conversation starter column."""
    messages = []
    
    for i in range(10):
        messages.append({
            "author": "Alice",
            "words": 5,
        })
        messages.append({
            "author": "Bob",
            "words": 5,
        })
    
    return pd.DataFrame(messages)


class TestCalculateConversationBalance:
    """Tests for calculate_conversation_balance function."""
    
    def test_balanced_two_person_chat(self, balanced_two_person_chat):
        """Test perfectly balanced 2-person chat."""
        result = calculate_conversation_balance(balanced_two_person_chat)
        
        assert 'metrics_df' in result
        assert 'balance_score' in result
        assert 'chart' in result
        assert 'dominant_author' in result
        
        # Balance score should be very low (close to 0)
        assert result['balance_score'] < 0.1
        
        # Both authors should have close to 50% share
        metrics = result['metrics_df']
        assert len(metrics) == 2
        assert all(metrics['message_share'].between(45, 55))
    
    def test_unbalanced_two_person_chat(self, unbalanced_two_person_chat):
        """Test unbalanced 2-person chat with one dominant author."""
        result = calculate_conversation_balance(unbalanced_two_person_chat)
        
        # Balance score should indicate imbalance (80/20 split ~ 0.36 with corrected formula)
        assert result['balance_score'] > 0.3  # Significantly unbalanced
        assert result['balance_score'] < 0.5  # But not a complete monopoly
        
        # Alice should be the dominant author
        assert result['dominant_author'] == "Alice"
        
        # Check shares
        metrics = result['metrics_df']
        alice_share = metrics[metrics['author'] == 'Alice']['message_share'].iloc[0]
        bob_share = metrics[metrics['author'] == 'Bob']['message_share'].iloc[0]
        
        assert alice_share > 70
        assert bob_share < 30
    
    def test_balanced_group_chat(self, balanced_group_chat):
        """Test balanced 3-person group chat."""
        result = calculate_conversation_balance(balanced_group_chat)
        
        assert result['n_authors'] == 3
        
        # Balance score should be low
        assert result['balance_score'] < 0.1
        
        # All authors should have close to 33.33% share
        metrics = result['metrics_df']
        assert len(metrics) == 3
        assert all(metrics['message_share'].between(30, 37))
    
    def test_single_author_chat(self, single_author_chat):
        """Test chat with single author."""
        result = calculate_conversation_balance(single_author_chat)
        
        assert result['n_authors'] == 1
        assert result['balance_score'] == 0  # No balance to measure
        
        metrics = result['metrics_df']
        assert len(metrics) == 1
        assert metrics['message_share'].iloc[0] == 100.0
    
    def test_chat_without_starters_column(self, chat_no_starters):
        """Test chat without is_conversation_starter column."""
        result = calculate_conversation_balance(chat_no_starters)
        
        # Should still work, with starters = 0
        assert 'metrics_df' in result
        metrics = result['metrics_df']
        assert 'starters' in metrics.columns
        assert all(metrics['starters'] == 0)
    
    def test_metrics_dataframe_structure(self, balanced_two_person_chat):
        """Test that metrics dataframe has expected columns."""
        result = calculate_conversation_balance(balanced_two_person_chat)
        metrics = result['metrics_df']
        
        expected_columns = [
            'author', 'messages', 'words', 'starters',
            'message_share', 'word_share', 'starter_share'
        ]
        
        for col in expected_columns:
            assert col in metrics.columns
    
    def test_shares_sum_to_100(self, balanced_group_chat):
        """Test that all shares sum to approximately 100%."""
        result = calculate_conversation_balance(balanced_group_chat)
        metrics = result['metrics_df']
        
        assert abs(metrics['message_share'].sum() - 100) < 0.01
        assert abs(metrics['word_share'].sum() - 100) < 0.01
        # starter_share might be 0 if no starters
        if metrics['starter_share'].sum() > 0:
            assert abs(metrics['starter_share'].sum() - 100) < 0.01
    
    def test_monopoly_balance_score(self):
        """Test that pure monopoly (100/0 split) scores exactly 1.0."""
        # Create extreme monopoly: Alice sends everything, Bob sends nothing
        # This is a theoretical edge case where Bob is in the chat but never messages
        messages = []
        for i in range(100):
            messages.append({
                "author": "Alice",
                "words": 10,
                "is_conversation_starter": 1 if i == 0 else 0
            })
        # Add one message from Bob to make it a 2-person chat
        # This creates nearly 100/0 split (100/1)
        messages.append({
            "author": "Bob",
            "words": 10,
            "is_conversation_starter": 0
        })
        
        df = pd.DataFrame(messages)
        result = calculate_conversation_balance(df)
        
        # In near-monopoly (100/1), balance score should be very close to 1.0
        assert result['balance_score'] > 0.95
        assert result['balance_score'] <= 1.0
        
    def test_balance_score_never_exceeds_one(self):
        """Test that balance score never exceeds 1.0 regardless of distribution."""
        import numpy as np
        
        # Test various extreme distributions
        test_cases = [
            # 2-person: 100/0, 90/10, 80/20
            ([100, 0], [100, 0]),
            ([90, 10], [90, 10]),
            ([80, 20], [75, 25]),
            # 3-person: various imbalances
            ([80, 15, 5], [75, 20, 5]),
            ([100, 0, 0], [100, 0, 0]),
            # 4-person
            ([70, 20, 8, 2], [65, 25, 8, 2]),
        ]
        
        for msg_dist, word_dist in test_cases:
            messages = []
            for i, (author_idx, msg_count) in enumerate(zip(range(len(msg_dist)), msg_dist)):
                author = f"Author{author_idx}"
                words_per_msg = word_dist[author_idx] / msg_count if msg_count > 0 else 0
                for j in range(msg_count):
                    messages.append({
                        "author": author,
                        "words": max(1, int(words_per_msg)),
                        "is_conversation_starter": 0
                    })
            
            if messages:  # Skip empty
                df = pd.DataFrame(messages)
                result = calculate_conversation_balance(df)
                
                # Balance score must never exceed 1.0 (with small epsilon for rounding)
                assert result['balance_score'] <= 1.0 + 1e-6, \
                    f"Balance score {result['balance_score']} exceeds 1.0 for distribution {msg_dist}"


class TestGetBalanceDescription:
    """Tests for get_balance_description function."""
    
    def test_single_author(self):
        """Test description for single author."""
        desc = get_balance_description(0, 1)
        assert "Single participant" in desc or "no balance" in desc
    
    def test_very_balanced(self):
        """Test description for very balanced conversation."""
        desc = get_balance_description(0.05, 3)
        assert "balanced" in desc.lower()
        assert "equal" in desc.lower() or "roughly" in desc.lower()
    
    def test_fairly_balanced(self):
        """Test description for fairly balanced conversation."""
        desc = get_balance_description(0.15, 3)
        assert "balanced" in desc.lower()
    
    def test_moderately_unbalanced(self):
        """Test description for moderately unbalanced conversation."""
        desc = get_balance_description(0.35, 2)
        assert "unbalanced" in desc.lower()
    
    def test_quite_unbalanced(self):
        """Test description for quite unbalanced conversation."""
        desc = get_balance_description(0.6, 2)
        assert "unbalanced" in desc.lower() or "dominat" in desc.lower()
    
    def test_very_unbalanced(self):
        """Test description for very unbalanced conversation."""
        desc = get_balance_description(0.9, 2)
        assert "unbalanced" in desc.lower() or "dominan" in desc.lower()
