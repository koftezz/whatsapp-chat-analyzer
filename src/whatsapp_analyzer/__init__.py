"""
WhatsApp Chat Analyzer - A comprehensive toolkit for analyzing WhatsApp chat exports.

This package provides modules for parsing, preprocessing, analyzing, and visualizing
WhatsApp chat data with support for English, Turkish, and German languages.
"""

# Lazy imports to avoid requiring streamlit for testing
def __getattr__(name):
    """Lazy import handler for top-level package attributes."""
    if name == "read_file":
        from whatsapp_analyzer.parsers import read_file
        return read_file
    elif name in _PREPROCESSOR_EXPORTS:
        module = __import__("whatsapp_analyzer.preprocessors", fromlist=[name])
        return getattr(module, name)
    elif name in _ANALYZER_EXPORTS:
        module = __import__("whatsapp_analyzer.analyzers", fromlist=[name])
        return getattr(module, name)
    elif name in _VISUALIZATION_EXPORTS:
        module = __import__("whatsapp_analyzer.visualizations", fromlist=[name])
        return getattr(module, name)
    elif name == "calculate_chat_summary":
        from whatsapp_analyzer.ui import calculate_chat_summary
        return calculate_chat_summary
    elif name in ("gcd", "findnum", "percent_helper"):
        from whatsapp_analyzer.utils import gcd, findnum, percent_helper
        return {"gcd": gcd, "findnum": findnum, "percent_helper": percent_helper}[name]
    raise AttributeError(f"module 'whatsapp_analyzer' has no attribute '{name}'")

_PREPROCESSOR_EXPORTS = {
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
    "SUPPORTED_LANGUAGES",
}

_ANALYZER_EXPORTS = {
    "basic_stats",
    "stats_overall",
    "activity",
    "smoothed_daily_activity",
    "relative_activity_ts",
    "trend_stats",
    "calculate_talkativeness",
    "calculate_author_stats",
    "analyze_response_time",
    "response_matrix",
    "find_longest_consecutive_streak",
    "get_message_count_by_author",
    "activity_time_of_day_ts",
    "activity_day_of_week_ts",
    "heatmap",
    "word_stats",
    "get_most_used_emoji",
    "analyze_monthly_messages",
    "get_activity_stats",
}

_VISUALIZATION_EXPORTS = {
    "create_message_count_chart",
    "create_sunburst_charts",
    "create_word_cloud",
}

__version__ = "2.0.0"
__all__ = [
    # Parsers
    "read_file",
    # Preprocessors
    "get_language_settings",
    "SUPPORTED_LANGUAGES",
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
    "calculate_talkativeness",
    "calculate_author_stats",
    "analyze_response_time",
    "response_matrix",
    "find_longest_consecutive_streak",
    "get_message_count_by_author",
    "activity_time_of_day_ts",
    "activity_day_of_week_ts",
    "heatmap",
    "word_stats",
    "get_most_used_emoji",
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
