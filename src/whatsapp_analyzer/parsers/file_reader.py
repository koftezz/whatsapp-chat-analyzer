"""File reading and parsing for supported chat export formats."""

from email.utils import parsedate_to_datetime
import re
import tempfile

import streamlit as st
import pandas as pd
from chatminer.chatparsers import SignalParser, WhatsAppParser


_SIGTOP_FROM_RE = re.compile(r"^From:\s*(.+)$")
_SIGTOP_SENT_RE = re.compile(r"^Sent:\s*(.+)$")


def _is_sigtop_message_start(lines: list[str], index: int) -> bool:
    """Identify a message header without mistaking body text for ``From:``."""
    if _SIGTOP_FROM_RE.match(lines[index]) is None:
        return False
    header = []
    for line in lines[index + 1:index + 8]:
        if line == "":
            break
        header.append(line)
    return any(line.startswith("Type:") for line in header) and any(
        _SIGTOP_SENT_RE.match(line) for line in header
    )


def _looks_like_sigtop(text: str) -> bool:
    """Return whether text has the structure of sigtop's default text format."""
    lines = text.splitlines()
    first_content_line = next((line for line in lines if line.strip()), "")
    return (
        first_content_line.startswith("Conversation:")
        and any(_is_sigtop_message_start(lines, index) for index in range(len(lines)))
    )


def _normalise_sigtop_author(author: str) -> str:
    """Remove sigtop's parenthesised recipient identifier from display names."""
    return re.sub(r"\s+\([^()]+\)\s*$", "", author).strip()


def _parse_sigtop_timestamp(value: str):
    """Parse sigtop's RFC-822-like timestamp while retaining local wall time."""
    try:
        return parsedate_to_datetime(value).replace(tzinfo=None)
    except (TypeError, ValueError, OverflowError):
        return None


def _sigtop_message_body(block: list[str]) -> str:
    """Extract message text from a sigtop message block, excluding metadata."""
    try:
        body_start = block.index("") + 1
    except ValueError:
        return ""

    body_lines = block[body_start:]

    # Quoted messages are prefixed with ``>``.  Keep only the sender's own
    # message after the quote, which starts after the next unprefixed blank.
    if body_lines and body_lines[0].startswith(">From:"):
        while body_lines and body_lines[0].startswith(">"):
            body_lines.pop(0)
        while body_lines and body_lines[0] == "":
            body_lines.pop(0)

    # Edited messages are represented as a version history prefixed with ``|``.
    # The first version is the latest. Extract its non-metadata body when present.
    if body_lines and body_lines[0].startswith("| Version:"):
        latest_version = []
        for line in body_lines[1:]:
            if line.startswith("| Version:"):
                break
            latest_version.append(line)
        body_lines = latest_version
        while body_lines and (
            body_lines[0].startswith(("| Attachment:", "| Sent:", "| >"))
            or body_lines[0] == "|"
        ):
            body_lines.pop(0)
        body_lines = [line[2:] if line.startswith("| ") else "" for line in body_lines]

    return "\n".join(body_lines).strip()


def parse_sigtop_text(text: str) -> pd.DataFrame:
    """Parse the default multi-line text format produced by ``sigtop msg``."""
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    starts = [
        index for index in range(len(lines)) if _is_sigtop_message_start(lines, index)
    ]
    messages = []

    for position, start in enumerate(starts):
        end = starts[position + 1] if position + 1 < len(starts) else len(lines)
        block = lines[start:end]
        author_match = _SIGTOP_FROM_RE.match(block[0])
        sent_match = next(
            (_SIGTOP_SENT_RE.match(line) for line in block if _SIGTOP_SENT_RE.match(line)),
            None,
        )
        if author_match is None or sent_match is None:
            continue

        timestamp = _parse_sigtop_timestamp(sent_match.group(1))
        message = _sigtop_message_body(block)
        if timestamp is None or not message:
            continue

        messages.append({
            "timestamp": timestamp,
            "author": _normalise_sigtop_author(author_match.group(1)),
            "message": message,
        })

    return pd.DataFrame(messages, columns=["timestamp", "author", "message"])


def _parse_with_chatminer(bytes_data: bytes, parser_class) -> pd.DataFrame:
    """Run a ChatMiner parser and return its pandas DataFrame."""
    with tempfile.NamedTemporaryFile(mode="wb") as temp:
        temp.write(bytes_data)
        temp.flush()
        parser = parser_class(temp.name)
        parser.parse_file()
        return parser.parsed_messages.get_df(as_pandas=True)


def _add_basic_features(df: pd.DataFrame) -> pd.DataFrame:
    """Normalise parser output and add features expected by the application."""
    if df.empty:
        return pd.DataFrame(columns=[
            "timestamp", "author", "message", "weekday", "hour", "words", "letters"
        ])

    result = df.loc[:, ["timestamp", "author", "message"]].copy()
    result["timestamp"] = pd.to_datetime(result["timestamp"], errors="coerce")
    result = result.dropna(subset=["timestamp", "author", "message"])
    result = result.sort_values("timestamp").reset_index(drop=True)
    result["weekday"] = result["timestamp"].dt.strftime("%A")
    result["hour"] = result["timestamp"].dt.hour
    result["words"] = result["message"].str.split().str.len()
    result["letters"] = result["message"].str.len()
    return result


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
    Read a WhatsApp, Signal, or sigtop text export file.

    Recognised sigtop exports are parsed directly. Other files are tried with
    ChatMiner's WhatsApp and Signal parsers in that order.

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
    bytes_data = file.getvalue()
    try:
        text = bytes_data.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = ""

    with st.spinner('This may take a while. Wait for it...'):
        # Try sigtop format first
        if text and _looks_like_sigtop(text):
            df = parse_sigtop_text(text)
        else:
            # Try WhatsApp with detailed error handling
            df = pd.DataFrame()
            whatsapp_error = None
            try:
                return _parse_whatsapp_file(bytes_data)
            except ParseError as e:
                # Store the WhatsApp error for potential re-raise
                whatsapp_error = e
                
            # If WhatsApp failed, try Signal as fallback
            try:
                df = _parse_with_chatminer(bytes_data, SignalParser)
            except Exception:
                # If Signal also failed, re-raise the original WhatsApp error
                if whatsapp_error is not None:
                    raise whatsapp_error
                df = pd.DataFrame()

    df = _add_basic_features(df)
    if df.empty:
        st.error("Could not parse this WhatsApp, Signal, or sigtop export.")
    return df
