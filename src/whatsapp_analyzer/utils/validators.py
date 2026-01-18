"""
Input validation utilities for WhatsApp chat analysis.
"""

import pandas as pd
from typing import List, Optional

from whatsapp_analyzer.preprocessors.language_config import SUPPORTED_LANGUAGES


class ValidationError(Exception):
    """Exception raised for validation errors."""
    pass


def validate_dataframe(
    df: pd.DataFrame,
    required_columns: Optional[List[str]] = None
) -> None:
    """
    Validate that a DataFrame has the expected structure.

    Args:
        df: DataFrame to validate
        required_columns: List of required column names (default: basic columns)

    Raises:
        ValidationError: If validation fails
    """
    if df is None:
        raise ValidationError("DataFrame is None")

    if not isinstance(df, pd.DataFrame):
        raise ValidationError(f"Expected DataFrame, got {type(df).__name__}")

    if df.empty:
        raise ValidationError("DataFrame is empty")

    if required_columns is None:
        required_columns = ['timestamp', 'author', 'message']

    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        raise ValidationError(
            f"Missing required columns: {', '.join(missing)}. "
            f"Available columns: {', '.join(df.columns)}"
        )


def validate_language(language: str) -> None:
    """
    Validate that a language is supported.

    Args:
        language: Language name to validate

    Raises:
        ValidationError: If language is not supported
    """
    if language not in SUPPORTED_LANGUAGES:
        raise ValidationError(
            f"Unsupported language: {language}. "
            f"Supported languages: {', '.join(SUPPORTED_LANGUAGES)}"
        )


def validate_authors(
    authors: List[str],
    available_authors: List[str]
) -> None:
    """
    Validate that selected authors exist in the data.

    Args:
        authors: List of selected author names
        available_authors: List of authors available in the data

    Raises:
        ValidationError: If any author is not found
    """
    if not authors:
        raise ValidationError("No authors selected")

    missing = [a for a in authors if a not in available_authors]
    if missing:
        raise ValidationError(
            f"Authors not found in data: {', '.join(missing)}. "
            f"Available authors: {', '.join(available_authors)}"
        )
