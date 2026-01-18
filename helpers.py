"""
WhatsApp Chat Analyzer - Backwards Compatibility Shim

DEPRECATED: This module is maintained for backwards compatibility only.
New code should import directly from the whatsapp_analyzer package:

    from whatsapp_analyzer import read_file, preprocess_data, ...

Or for specific modules:

    from whatsapp_analyzer.preprocessors import get_language_settings
    from whatsapp_analyzer.analyzers import trend_stats
"""

import warnings
import sys
import os

# Add src to path so imports work
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Emit deprecation warning on import
warnings.warn(
    "helpers.py is deprecated. Please use: from whatsapp_analyzer import *",
    DeprecationWarning,
    stacklevel=2
)

# Re-export everything from the new package structure for backwards compatibility

# Parsers
from whatsapp_analyzer.parsers import read_file

# Preprocessors
from whatsapp_analyzer.preprocessors import (
    get_language_settings,
    preprocess_data,
    preprocess_timestamps,
    process_multimedia,
    process_emojis,
    process_links,
    process_message_length,
    process_locations,
    filter_authors,
    add_conversation_starter_flag,
    add_year_week,
)

# Analyzers
from whatsapp_analyzer.analyzers import (
    basic_stats,
    stats_overall,
    activity,
    smoothed_daily_activity,
    relative_activity_ts,
    trend_stats,
    calculate_author_stats,
    prepare_time_data,
    calculate_messaging_trends,
    analyze_trend,
    trendline,
    analyze_response_time,
    response_matrix,
    find_longest_consecutive_streak,
    get_message_count_by_author,
    get_most_active_author,
    activity_time_of_day_ts,
    activity_day_of_week_ts,
    heatmap,
    year_month,
    word_stats,
    get_most_used_emoji,
    extract_emojis,
    analyze_monthly_messages,
    get_activity_stats,
)

# Import talkativeness with backwards compatible name
from whatsapp_analyzer.analyzers.trend_analyzer import calculate_talkativeness as talkativeness

# Visualizations
from whatsapp_analyzer.visualizations import (
    create_message_count_chart,
    create_sunburst_charts,
    create_word_cloud,
)

# UI utilities
from whatsapp_analyzer.ui import calculate_chat_summary

# Math utilities
from whatsapp_analyzer.utils import gcd, findnum, percent_helper

# Define __all__ for explicit exports
__all__ = [
    # Parsers
    "read_file",
    # Preprocessors
    "get_language_settings",
    "preprocess_data",
    "preprocess_timestamps",
    "process_multimedia",
    "process_emojis",
    "process_links",
    "process_message_length",
    "process_locations",
    "filter_authors",
    "add_conversation_starter_flag",
    "add_year_week",
    # Analyzers
    "basic_stats",
    "stats_overall",
    "activity",
    "smoothed_daily_activity",
    "relative_activity_ts",
    "trend_stats",
    "calculate_author_stats",
    "prepare_time_data",
    "calculate_messaging_trends",
    "analyze_trend",
    "trendline",
    "talkativeness",
    "analyze_response_time",
    "response_matrix",
    "find_longest_consecutive_streak",
    "get_message_count_by_author",
    "get_most_active_author",
    "activity_time_of_day_ts",
    "activity_day_of_week_ts",
    "heatmap",
    "year_month",
    "word_stats",
    "get_most_used_emoji",
    "extract_emojis",
    "analyze_monthly_messages",
    "get_activity_stats",
    # Visualizations
    "create_message_count_chart",
    "create_sunburst_charts",
    "create_word_cloud",
    # UI
    "calculate_chat_summary",
    # Utils
    "gcd",
    "findnum",
    "percent_helper",
]
