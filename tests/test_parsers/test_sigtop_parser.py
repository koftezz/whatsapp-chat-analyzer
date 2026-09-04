"""Tests for sigtop's default multi-line text export format."""

from datetime import datetime

from whatsapp_analyzer.parsers.file_reader import _add_basic_features, parse_sigtop_text


def test_parse_sigtop_multiline_messages_and_ignore_metadata():
    export = """Conversation: Project group

From: Alice (+4912345)
Type: incoming
Sent: Thu, 24 Apr 2025 12:34:56 +0200
Received: Thu, 24 Apr 2025 12:34:57 +0200
Attachment: picture.jpg (image/jpeg, 123 bytes)
Reaction: 👍 from Bob (+4998765)

First line
Second line

From: You
Type: outgoing
Sent: Thu, 24 Apr 2025 06:00:00 -0700

Reply
"""

    result = parse_sigtop_text(export)

    assert result.to_dict("records") == [
        {
            "timestamp": datetime(2025, 4, 24, 12, 34, 56),
            "author": "Alice",
            "message": "First line\nSecond line",
        },
        {
            "timestamp": datetime(2025, 4, 24, 6, 0),
            "author": "You",
            "message": "Reply",
        },
    ]


def test_parse_sigtop_uses_own_text_not_quoted_message():
    export = """Conversation: Alice

From: You
Type: outgoing
Sent: Thu, 24 Apr 2025 12:34:56 +0200

>From: Alice (+4912345)
>Sent: Thu, 24 Apr 2025 12:30:00 +0200
>
>Quoted text

Own reply
"""

    result = parse_sigtop_text(export)

    assert result.loc[0, "message"] == "Own reply"


def test_parse_sigtop_does_not_treat_body_from_line_as_new_message():
    export = """Conversation: Alice

From: Alice
Type: incoming
Sent: Thu, 24 Apr 2025 12:34:56 +0200

From: this is still message text
and so is this
"""

    result = parse_sigtop_text(export)

    assert result.loc[0, "message"] == "From: this is still message text\nand so is this"


def test_parse_sigtop_skips_records_without_body_or_valid_timestamp():
    export = """Conversation: Alice

From: Alice
Type: incoming
Sent: unknown
Received: unknown

No usable timestamp

From: You
Type: outgoing
Sent: Thu, 24 Apr 2025 12:34:56 +0200
Attachment: picture.jpg (image/jpeg, 123 bytes)

"""

    result = parse_sigtop_text(export)

    assert result.empty


def test_basic_features_match_application_contract():
    parsed = parse_sigtop_text("""Conversation: Alice

From: Alice
Type: incoming
Sent: Thu, 24 Apr 2025 12:34:56 +0200

Two words
""")

    result = _add_basic_features(parsed)

    assert result.loc[0, "weekday"] == "Thursday"
    assert result.loc[0, "hour"] == 12
    assert result.loc[0, "words"] == 2
    assert result.loc[0, "letters"] == 9
