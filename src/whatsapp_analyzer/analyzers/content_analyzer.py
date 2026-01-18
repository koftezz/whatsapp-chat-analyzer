"""
Content analysis for WhatsApp chat data (words, emojis, monthly stats).
"""

import re
import pandas as pd
import altair as alt
from collections import Counter

from whatsapp_analyzer.utils.math_helpers import percent_helper


def word_stats(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate word frequency statistics.

    Args:
        df: Preprocessed DataFrame

    Returns:
        DataFrame with word, count, and frequency description
    """
    words_lst = ''.join(df["message"].values.astype(str)).split(' ')
    words_lst = [i for i in words_lst if len(i) > 3]

    result = pd.DataFrame.from_dict(
        Counter(words_lst),
        orient='index',
        columns=["count"]
    ).reset_index().rename(columns={'index': 'word'})

    result.sort_values('count', ascending=False, inplace=True, ignore_index=True)
    result[""] = result["count"].apply(
        lambda x: percent_helper(x / result.shape[0])
    )

    return result


def extract_emojis(s: str) -> str:
    """
    Extract all emojis from a string.

    Args:
        s: Input string

    Returns:
        String containing only emoji characters
    """
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        "]+", flags=re.UNICODE)
    return ''.join(emoji_pattern.findall(s))


def get_most_used_emoji(df: pd.DataFrame) -> pd.DataFrame:
    """
    Get the most frequently used emojis in the chat.

    Args:
        df: Preprocessed DataFrame

    Returns:
        DataFrame with top 10 emojis and their counts
    """
    try:
        # Combine all messages and extract emojis
        all_emojis = ' '.join(df['message'].astype(str).apply(extract_emojis))
        emoji_counts = Counter(all_emojis)

        # Convert to DataFrame for sorting
        emoji_df = pd.DataFrame(emoji_counts.items(), columns=['Emoji', 'Count'])

        # Clean emoji column: remove whitespace and filter invalid entries
        emoji_df['Emoji'] = emoji_df['Emoji'].str.replace(r'\s+', '', regex=True)
        emoji_df = emoji_df[emoji_df['Emoji'].notna() & (emoji_df['Emoji'] != '')]

        # Sort by count in descending order
        emoji_df = emoji_df.sort_values('Count', ascending=False)
        emoji_df['Count'] = emoji_df['Count'].astype(int)

        return emoji_df.head(10)
    except Exception:
        return pd.DataFrame(columns=['Emoji', 'Count'])


def analyze_monthly_messages(df: pd.DataFrame) -> dict:
    """
    Analyze monthly message volume over time.

    Args:
        df: Preprocessed DataFrame

    Returns:
        Dictionary with:
        - chart: Altair chart of monthly messages
        - peak_month: Month with most messages
        - total_messages: Message count in peak month
    """
    df = df.copy()
    df['YearMonth'] = df['timestamp'].dt.to_period('M')
    df['year'] = df['timestamp'].dt.year

    # Group by YearMonth and count messages
    year_content = df.groupby('YearMonth').agg({
        'message': 'count',
        'year': 'first'
    }).reset_index()

    # Find the month with the most messages
    peak_month = year_content.loc[year_content['message'].idxmax()]
    total_messages = peak_month['message']
    year = peak_month['YearMonth'].year
    month = peak_month['YearMonth'].month

    # Convert YearMonth to string for proper sorting
    year_content['YearMonth'] = year_content['YearMonth'].astype(str)

    # Create Altair chart
    base = alt.Chart(year_content).encode(
        x=alt.X("YearMonth:O", axis=alt.Axis(title="Year-Month", labelAngle=-45)),
        y=alt.Y('message:Q', axis=alt.Axis(title="Number of Messages"))
    )

    bar_chart = base.mark_bar().encode(
        color='year:O'
    )

    rule = base.mark_rule(color='red').encode(
        y='mean(message):Q'
    )

    chart = (bar_chart + rule).properties(
        width=1000,
        height=600,
        title='Monthly Message Volume Over Time'
    )

    return {
        'chart': chart,
        'peak_month': f"{year}-{str(month).zfill(2)}",
        'total_messages': total_messages
    }
