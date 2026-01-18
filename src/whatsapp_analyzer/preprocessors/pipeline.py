"""
Main preprocessing pipeline for WhatsApp chat data.
"""

import pandas as pd
from typing import List, Tuple

from whatsapp_analyzer.preprocessors.language_config import get_language_settings
from whatsapp_analyzer.preprocessors.timestamp_processor import preprocess_timestamps, add_year_week
from whatsapp_analyzer.preprocessors.feature_extractor import (
    process_links,
    process_message_length,
    process_locations,
    add_conversation_starter_flag,
)
from whatsapp_analyzer.preprocessors.message_processor import process_multimedia, process_emojis
from whatsapp_analyzer.preprocessors.data_filter import filter_authors


def preprocess_data(
    df: pd.DataFrame,
    selected_lang: str,
    selected_authors: List[str]
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Run the complete preprocessing pipeline on WhatsApp chat data.

    Pipeline steps:
    1. Get language settings
    2. Process timestamps and filter authors
    3. Process links
    4. Process message length
    5. Process multimedia (including edited messages)
    6. Process emojis
    7. Filter invalid authors
    8. Add conversation starter flags
    9. Process locations
    10. Add year/week columns

    Args:
        df: Raw DataFrame from read_file()
        selected_lang: Language ("English", "Turkish", or "German")
        selected_authors: List of authors to include in analysis

    Returns:
        Tuple of (processed DataFrame, locations DataFrame)
    """
    lang = get_language_settings(selected_lang)
    df = preprocess_timestamps(df, selected_authors)
    df = process_links(df)
    df = process_message_length(df)
    df = process_multimedia(df, lang)
    df = process_emojis(df)
    df = filter_authors(df)
    df = add_conversation_starter_flag(df)
    df, locations = process_locations(df)
    df = add_year_week(df)
    return df, locations
