"""
Conversation balance analysis for WhatsApp chat data.

Measures how balanced (or one-sided) conversations are between participants.
"""

import pandas as pd
import altair as alt


def calculate_conversation_balance(df: pd.DataFrame) -> dict:
    """
    Calculate conversation balance metrics for participants.
    
    Measures:
    - Share of messages
    - Share of words
    - Share of conversation starts
    - Balance/dominance score (Herfindahl index-style concentration)
    
    Args:
        df: Preprocessed DataFrame with columns: author, words, is_conversation_starter
    
    Returns:
        Dictionary with:
        - metrics_df: DataFrame with per-author shares
        - balance_score: Overall balance score (0-1, where 0=perfectly balanced, 1=monopoly)
        - chart: Altair chart
        - dominant_author: Author with highest combined share (for 2-person chats)
    """
    # Calculate per-author metrics
    message_counts = df.groupby('author').size()
    word_counts = df.groupby('author')['words'].sum()
    
    # Calculate conversation starters if the column exists
    if 'is_conversation_starter' in df.columns:
        starter_counts = df[df['is_conversation_starter'] == 1].groupby('author').size()
    else:
        starter_counts = pd.Series(dtype=int)
    
    # Create metrics dataframe
    metrics = pd.DataFrame({
        'author': message_counts.index,
        'messages': message_counts.values,
        'words': word_counts.values,
    })
    
    # Add starters if available
    if not starter_counts.empty:
        metrics = metrics.merge(
            starter_counts.rename('starters').reset_index(),
            on='author',
            how='left'
        )
        metrics['starters'] = metrics['starters'].fillna(0).astype(int)
    else:
        metrics['starters'] = 0
    
    # Calculate shares (percentages)
    total_messages = metrics['messages'].sum()
    total_words = metrics['words'].sum()
    total_starters = metrics['starters'].sum()
    
    metrics['message_share'] = 100 * metrics['messages'] / total_messages
    metrics['word_share'] = 100 * metrics['words'] / total_words
    
    if total_starters > 0:
        metrics['starter_share'] = 100 * metrics['starters'] / total_starters
    else:
        metrics['starter_share'] = 0
    
    # Calculate balance score using Herfindahl-style concentration
    # This measures how far from equal distribution we are
    # Score of 0 = perfectly balanced, score approaching 1 = monopoly
    n_authors = len(metrics)
    if n_authors > 1:
        equal_share = 100 / n_authors
        # Use message share as primary metric, but weight in word share
        combined_share = (metrics['message_share'] * 0.6 + metrics['word_share'] * 0.4)
        # Normalize to 0-1 scale where 0=perfect balance, 1=monopoly
        variance = ((combined_share - equal_share) ** 2).sum()
        max_variance = (n_authors - 1) * equal_share ** 2
        balance_score = variance / max_variance if max_variance > 0 else 0
    else:
        balance_score = 0  # Single author = no balance to measure
    
    # Determine dominant author (for 2-person chats primarily)
    dominant_idx = (metrics['message_share'] * 0.6 + metrics['word_share'] * 0.4).idxmax()
    dominant_author = metrics.loc[dominant_idx, 'author']
    
    # Create visualization
    chart = _create_balance_chart(metrics, n_authors)
    
    return {
        'metrics_df': metrics,
        'balance_score': balance_score,
        'chart': chart,
        'dominant_author': dominant_author,
        'n_authors': n_authors,
    }


def _create_balance_chart(metrics_df: pd.DataFrame, n_authors: int) -> alt.Chart:
    """
    Create a chart showing conversation balance.
    
    Args:
        metrics_df: DataFrame with author shares
        n_authors: Number of authors
    
    Returns:
        Altair chart
    """
    # Prepare data for charting
    chart_data = metrics_df[['author', 'message_share', 'word_share', 'starter_share']].copy()
    
    # Melt for grouped bar chart
    melted = chart_data.melt(
        id_vars='author',
        value_vars=['message_share', 'word_share', 'starter_share'],
        var_name='metric',
        value_name='percentage'
    )
    
    # Rename metrics for display
    metric_labels = {
        'message_share': 'Messages',
        'word_share': 'Words',
        'starter_share': 'Conversation Starts'
    }
    melted['metric'] = melted['metric'].map(metric_labels)
    
    # Add equal share line data if multiple authors
    if n_authors > 1:
        equal_share = 100 / n_authors
        melted['equal_share'] = equal_share
    
    # Create grouped bar chart (no faceting, just grouped by metric)
    bars = alt.Chart(melted).mark_bar().encode(
        x=alt.X('author:N', title='Author', axis=alt.Axis(labelAngle=-45)),
        xOffset='metric:N',
        y=alt.Y('percentage:Q', title='Share (%)'),
        color=alt.Color('metric:N', title='Metric'),
        tooltip=[
            alt.Tooltip('author:N', title='Author'),
            alt.Tooltip('metric:N', title='Metric'),
            alt.Tooltip('percentage:Q', title='Share', format='.1f')
        ]
    )
    
    # Add reference line for equal share if multiple authors
    if n_authors > 1:
        rule = alt.Chart(melted).mark_rule(
            color='red',
            strokeDash=[3, 3],
            size=2
        ).encode(
            y='equal_share:Q'
        )
        
        chart = (bars + rule).properties(
            width=600,
            height=400,
            title='Conversation Share by Author (red line = equal share)'
        )
    else:
        chart = bars.properties(
            width=600,
            height=400,
            title='Conversation Share by Author'
        )
    
    return chart


def get_balance_description(balance_score: float, n_authors: int) -> str:
    """
    Get a human-readable description of the balance score.
    
    Args:
        balance_score: Balance score from 0 (balanced) to 1 (monopoly)
        n_authors: Number of authors
    
    Returns:
        Description string
    """
    if n_authors <= 1:
        return "Single participant (no balance to measure)"
    
    if balance_score < 0.1:
        return "Very balanced - all participants contribute roughly equally"
    elif balance_score < 0.25:
        return "Fairly balanced - minor differences in participation"
    elif balance_score < 0.5:
        return "Moderately unbalanced - one participant clearly more active"
    elif balance_score < 0.75:
        return "Quite unbalanced - conversation dominated by one participant"
    else:
        return "Very unbalanced - strong dominance by one participant"
