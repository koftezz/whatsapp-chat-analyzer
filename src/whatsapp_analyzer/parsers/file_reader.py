"""
File reading and parsing for WhatsApp chat exports.
"""

import tempfile
import streamlit as st
import pandas as pd
from chatminer.chatparsers import WhatsAppParser


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
    """
    with tempfile.NamedTemporaryFile(mode="wb") as temp:
        with st.spinner('This may take a while. Wait for it...'):
            bytes_data = file.getvalue()
            temp.write(bytes_data)
            parser = WhatsAppParser(temp.name)
            parser.parse_file()
            df = parser.parsed_messages.get_df(as_pandas=True)
            df["weekday"] = df["timestamp"].dt.strftime("%A")
            df["hour"] = df["timestamp"].dt.hour
            df["words"] = df["message"].apply(lambda s: len(s.split(" ")))
            df["letters"] = df["message"].apply(len)
    return df
