"""
File reading and parsing for WhatsApp chat exports.
"""

import tempfile
import streamlit as st
import pandas as pd
from chatminer.chatparsers import WhatsAppParser


class ParseError(Exception):
    """Custom exception for file parsing errors with user-friendly messages."""
    pass


def _parse_whatsapp_file(file_bytes: bytes) -> pd.DataFrame:
    """
    Internal function to parse WhatsApp file bytes.
    
    This function is not cached and is used for testing.
    
    Args:
        file_bytes: Raw bytes of the WhatsApp export file
        
    Returns:
        DataFrame with parsed messages
        
    Raises:
        ParseError: If the file cannot be parsed or contains no valid messages
    """
    if len(file_bytes) == 0:
        raise ParseError(
            "The uploaded file is empty. "
            "Please export your chat from WhatsApp and try again."
        )
    
    with tempfile.NamedTemporaryFile(mode="wb", delete=False) as temp:
        try:
            temp.write(file_bytes)
            temp.flush()
            
            try:
                parser = WhatsAppParser(temp.name)
                parser.parse_file()
                df = parser.parsed_messages.get_df(as_pandas=True)
            except ValueError as e:
                # Specific handling for split/unpack errors during parsing
                if "not enough values to unpack" in str(e) or "unpack" in str(e).lower():
                    raise ParseError(
                        "Could not parse the WhatsApp export format. "
                        "This usually happens when:\n"
                        "- The file is from a different WhatsApp version or platform\n"
                        "- The export format doesn't match the expected pattern\n"
                        "- Some message lines are corrupted or improperly formatted\n\n"
                        "Expected format: `MM/DD/YY, HH:MM AM/PM - Author: Message`\n\n"
                        "Please try:\n"
                        "1. Export the chat again from WhatsApp\n"
                        "2. Ensure you're using 'Export Chat' (not a copy/paste)\n"
                        "3. Check that the file isn't edited or modified"
                    )
                # Re-raise other ValueErrors with context
                raise ParseError(f"Error parsing message format: {str(e)}")
            except IndexError:
                raise ParseError(
                    "Could not parse any messages from the file. "
                    "This can happen if:\n"
                    "- The file contains only system messages or notifications\n"
                    "- The file format doesn't match WhatsApp's export format\n"
                    "- The file is corrupted or incomplete\n\n"
                    "Please ensure you're uploading a valid WhatsApp chat export "
                    "(not a screenshot or edited file)."
                )
            except Exception as e:
                if "date" in str(e).lower() or "format" in str(e).lower():
                    raise ParseError(
                        f"Could not parse date format in the file. "
                        f"Please ensure the file is a valid WhatsApp export.\n\n"
                        f"Technical details: {str(e)}"
                    )
                raise ParseError(
                    f"An error occurred while parsing the file: {str(e)}\n\n"
                    f"Please ensure you're uploading a valid WhatsApp chat export."
                )
            
            if len(df) == 0:
                raise ParseError(
                    "No messages found in the file. "
                    "The file may contain only system messages or notifications, "
                    "which are automatically filtered out."
                )
            
            df["weekday"] = df["timestamp"].dt.strftime("%A")
            df["hour"] = df["timestamp"].dt.hour
            df["words"] = df["message"].apply(lambda s: len(s.split(" ")))
            df["letters"] = df["message"].apply(len)
            
            return df
        finally:
            import os
            if os.path.exists(temp.name):
                os.unlink(temp.name)


@st.cache_data(show_spinner=False)
def read_file(file) -> pd.DataFrame:
    """
    Read and parse a WhatsApp chat export file.

    Uses ChatMiner library to parse the WhatsApp format and extracts
    basic features like weekday, hour, word count, and letter count.

    Args:
        file: Streamlit UploadedFile object

    Returns:
        DataFrame with columns:
        - timestamp: datetime of message
        - author: message sender
        - message: message content
        - weekday: day of week name
        - hour: hour of day (0-23)
        - words: word count
        - letters: character count
        
    Raises:
        ParseError: If the file cannot be parsed or contains no valid messages
    """
    with st.spinner('This may take a while. Wait for it...'):
        bytes_data = file.getvalue()
        return _parse_whatsapp_file(bytes_data)
