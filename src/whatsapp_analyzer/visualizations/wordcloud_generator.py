"""
Word cloud generation for WhatsApp chat data.
"""

import pandas as pd
from wordcloud import WordCloud


def create_word_cloud(df: pd.DataFrame, min_word_length: int = 4, max_words: int = 100):
    """
    Create a word cloud image from chat messages.

    Args:
        df: Preprocessed DataFrame with 'message' column
        min_word_length: Minimum word length to include (default 4)
        max_words: Maximum number of words to display (default 100)

    Returns:
        PIL Image object of the word cloud
    """
    # Combine all messages and split into words
    all_words = ' '.join(df['message'].astype(str)).split()

    # Filter by minimum word length
    all_words = [w for w in all_words if len(w) >= min_word_length]

    # Count word frequencies
    word_freq = pd.Series(all_words).value_counts().reset_index()
    word_freq.columns = ['word', 'frequency']

    # Take top N words for better performance
    word_freq = word_freq.head(max_words)

    # Create a word cloud object
    wordcloud = WordCloud(
        width=800,
        height=400,
        background_color='white'
    ).generate_from_frequencies(
        dict(zip(word_freq['word'], word_freq['frequency']))
    )

    # Convert the word cloud to an image
    img = wordcloud.to_image()

    return img
