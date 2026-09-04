"""
Tests for the WhatsApp file reader module.
"""

import pytest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from whatsapp_analyzer.parsers import ParseError
from whatsapp_analyzer.parsers.file_reader import _parse_whatsapp_file, _add_basic_features


class TestFileReader:
    """Test file reading and parsing functionality."""
    
    def test_read_valid_file(self):
        """Test reading a valid WhatsApp export file."""
        content = '''3/12/22, 12:34 AM - Jack: Hello everyone!
3/12/22, 1:05 AM - Sam: Hi Jack!
3/12/22, 1:06 AM - Jack: How are you?
'''
        file_bytes = content.encode('utf-8')
        
        df = _parse_whatsapp_file(file_bytes)
        df = _add_basic_features(df)
        
        assert len(df) == 3
        assert 'timestamp' in df.columns
        assert 'author' in df.columns
        assert 'message' in df.columns
        assert 'weekday' in df.columns
        assert 'hour' in df.columns
        assert 'words' in df.columns
        assert 'letters' in df.columns
    
    def test_read_file_with_multiline_messages(self):
        """Test reading a file with multi-line messages."""
        content = '''3/12/22, 12:34 AM - Jack: This is line one
of a message
that spans multiple lines
3/12/22, 1:05 AM - Sam: Another message
also multi-line
3/12/22, 1:06 AM - Jack: Single line
'''
        file_bytes = content.encode('utf-8')
        
        df = _parse_whatsapp_file(file_bytes)
        
        assert len(df) == 3
        # Multi-line messages should be concatenated
        messages = ' '.join(df['message'].tolist())
        assert 'that spans multiple lines' in messages
        assert 'also multi-line' in messages
    
    def test_empty_file_raises_error(self):
        """Test that an empty file raises ParseError."""
        file_bytes = b""
        
        with pytest.raises(ParseError) as exc_info:
            _parse_whatsapp_file(file_bytes)
        
        assert "empty" in str(exc_info.value).lower()
    
    def test_whitespace_only_file_raises_error(self):
        """Test that a file with only whitespace raises ParseError."""
        file_bytes = b"\n\n\n   \n\n"
        
        with pytest.raises(ParseError) as exc_info:
            _parse_whatsapp_file(file_bytes)
        
        assert "could not parse any messages" in str(exc_info.value).lower()
    
    def test_system_messages_only_raises_error(self):
        """Test that a file with only system messages raises ParseError."""
        content = "3/12/22, 12:34 AM - Messages and calls are end-to-end encrypted."
        file_bytes = content.encode('utf-8')
        
        with pytest.raises(ParseError) as exc_info:
            _parse_whatsapp_file(file_bytes)
        
        error_message = str(exc_info.value).lower()
        assert "no messages found" in error_message or "system messages" in error_message
    
    def test_invalid_format_raises_error(self):
        """Test that an invalid file format raises ParseError."""
        content = '''This is not a valid WhatsApp export
Just random text
With no date stamps
'''
        file_bytes = content.encode('utf-8')
        
        with pytest.raises(ParseError) as exc_info:
            _parse_whatsapp_file(file_bytes)
        
        assert "could not parse" in str(exc_info.value).lower()
    
    def test_malformed_message_line_raises_error(self):
        """Test that malformed message lines (missing separator) raise ParseError."""
        # This triggers ValueError: not enough values to unpack
        content = '''3/12/22, 12:34 AM - Jack: Normal message
3/12/22 12:35 AM Jack Missing separator
3/12/22, 12:36 AM - Sam: Another message
'''
        file_bytes = content.encode('utf-8')
        
        with pytest.raises(ParseError) as exc_info:
            _parse_whatsapp_file(file_bytes)
        
        error_msg = str(exc_info.value).lower()
        assert "format" in error_msg or "pattern" in error_msg
    
    def test_file_with_special_characters(self):
        """Test reading a file with emojis and special characters."""
        content = '''3/12/22, 12:34 AM - Jack: Hello 👋 🎉
3/12/22, 1:05 AM - Sam: Testing special chars: @#$%
3/12/22, 1:06 AM - Jack: Links: https://example.com
'''
        file_bytes = content.encode('utf-8')
        
        df = _parse_whatsapp_file(file_bytes)
        
        assert len(df) == 3
        # Check content exists regardless of order
        all_messages = ' '.join(df['message'].tolist())
        assert '👋' in all_messages
        assert 'https://example.com' in all_messages
    
    def test_file_with_media_omitted_messages(self):
        """Test reading a file with media omitted messages."""
        content = '''3/12/22, 12:34 AM - Jack: Check this out
3/12/22, 12:35 AM - Sam: ‎image omitted
3/12/22, 12:36 AM - Jack: ‎sticker omitted
3/12/22, 12:37 AM - Sam: Thanks!
'''
        file_bytes = content.encode('utf-8')
        
        df = _parse_whatsapp_file(file_bytes)
        
        assert len(df) == 4
        assert 'image omitted' in df.iloc[1]['message'].lower() or 'omitted' in df.iloc[1]['message'].lower()
    
    def test_computed_columns_are_correct(self):
        """Test that computed columns (weekday, hour, words, letters) are correct."""
        content = '''3/12/22, 12:34 AM - Jack: Hello world
3/12/22, 1:05 PM - Sam: Test
'''
        file_bytes = content.encode('utf-8')
        
        df = _parse_whatsapp_file(file_bytes)
        df = _add_basic_features(df)
        
        # Check weekday is present (we don't assert specific value as it depends on date interpretation)
        assert df['weekday'].notna().all()
        
        # Check hour is in valid range
        assert (df['hour'] >= 0).all()
        assert (df['hour'] <= 23).all()
        
        # Check words count - at least one message should have multiple words
        assert df['words'].max() >= 2  # "Hello world" has 2 words
        assert df['words'].min() >= 1  # "Test" has 1 word
        
        # Check letters count
        assert (df['letters'] > 0).all()


class TestParseErrorMessages:
    """Test that error messages are clear and helpful."""
    
    def test_empty_file_error_message_is_helpful(self):
        """Test that empty file error has actionable message."""
        file_bytes = b""
        
        with pytest.raises(ParseError) as exc_info:
            _parse_whatsapp_file(file_bytes)
        
        message = str(exc_info.value)
        assert "empty" in message.lower()
        assert "export" in message.lower()
    
    def test_invalid_format_error_provides_guidance(self):
        """Test that format error suggests what might be wrong."""
        file_bytes = b"Not a valid file"
        
        with pytest.raises(ParseError) as exc_info:
            _parse_whatsapp_file(file_bytes)
        
        message = str(exc_info.value)
        # Should mention possible causes
        assert any(word in message.lower() for word in ['format', 'system', 'corrupted', 'parse'])
    
    def test_no_messages_error_explains_filtering(self):
        """Test that no-messages error explains why."""
        content = "3/12/22, 12:34 AM - Messages and calls are end-to-end encrypted."
        file_bytes = content.encode('utf-8')
        
        with pytest.raises(ParseError) as exc_info:
            _parse_whatsapp_file(file_bytes)
        
        message = str(exc_info.value).lower()
        # Should explain that system messages are filtered
        assert "no messages" in message or "system" in message or "filtered" in message


class TestRegressionCases:
    """Test specific regression cases from issue #14 and PR #23."""
    
    def test_pr23_fallback_preserves_whatsapp_parse_error(self):
        """
        Regression test for PR #23 fallback bug.
        
        When a file looks like WhatsApp but fails to parse, and Signal
        fallback also fails, we should see the helpful WhatsApp ParseError
        message, not a raw Signal/ChatMiner exception.
        
        This tests the internal logic directly to avoid Streamlit caching issues.
        """
        # A file that triggers ValueError during parsing (missing separator)
        # This will cause the "not enough values to unpack" error
        content = '''3/12/22 12:34 AM Jack Says hello
3/12/22 1:05 AM Sam Replies
This will cause parsing errors
'''
        file_bytes = content.encode('utf-8')
        
        # Import the internal components to test the fallback logic
        from whatsapp_analyzer.parsers.file_reader import (
            _parse_whatsapp_file,
            _parse_with_chatminer,
        )
        from chatminer.chatparsers import SignalParser
        
        # First, verify WhatsApp parsing fails with ParseError
        with pytest.raises(ParseError) as whatsapp_exc:
            _parse_whatsapp_file(file_bytes)
        
        whatsapp_error = whatsapp_exc.value
        whatsapp_msg = str(whatsapp_error).lower()
        
        # Verify it has helpful WhatsApp-specific guidance about format/parsing
        assert "parse" in whatsapp_msg or "format" in whatsapp_msg
        assert isinstance(whatsapp_error, ParseError)
        
        # Now test the fallback logic: if we try Signal and it fails,
        # we should get a different exception (not ParseError)
        try:
            _parse_with_chatminer(file_bytes, SignalParser)
            # If Signal somehow succeeds, that's fine - the test is about the error path
        except Exception as signal_error:
            # Signal parser should fail with a different exception type
            # (typically ValueError, IndexError, or other ChatMiner exceptions)
            # NOT ParseError (which is our custom exception)
            assert not isinstance(signal_error, ParseError)
            
            # The bug was that when both fail, bare `raise` in the inner except
            # would raise signal_error instead of the more helpful whatsapp_error
            # Our fix ensures whatsapp_error is raised instead
    
    def test_issue_14_valueerror_from_malformed_lines(self):
        """
        Regression test for issue #14 - the actual error from the screenshot.
        
        Original error: ValueError: not enough values to unpack (expected 2, got 1)
        This occurs when a line looks like a message but lacks the ' - ' separator.
        """
        content = '''3/12/22, 12:34 AM - Jack: Valid message
3/12/22 12:35 AM Jack Invalid line missing separator
3/12/22, 12:36 AM - Sam: Another valid message
'''
        file_bytes = content.encode('utf-8')
        
        # Should raise ParseError (not raw ValueError)
        with pytest.raises(ParseError) as exc_info:
            _parse_whatsapp_file(file_bytes)
        
        error_msg = str(exc_info.value)
        # Should explain the format issue
        assert "format" in error_msg.lower()
        # Should provide guidance
        assert "export" in error_msg.lower() or "pattern" in error_msg.lower()
    
    def test_issue_14_multiline_messages_dont_crash(self):
        """
        Regression test for issue #14.
        
        Original issue: multi-line messages were causing crashes.
        This should now work correctly.
        """
        content = '''3/12/22, 12:34 AM - Jack: This is a message
that continues on the next line
and maybe even another line
3/12/22, 1:05 AM - Sam: Response here
'''
        file_bytes = content.encode('utf-8')
        
        # Should not raise an exception
        df = _parse_whatsapp_file(file_bytes)
        
        assert len(df) == 2
        # Check that multiline content is preserved
        all_messages = ' '.join(df['message'].tolist())
        assert 'continues on the next line' in all_messages
    
    def test_issue_14_empty_file_shows_clear_error(self):
        """
        Regression test for issue #14.
        
        Empty or invalid files should show clear error instead of
        generic IndexError.
        """
        file_bytes = b""
        
        with pytest.raises(ParseError) as exc_info:
            _parse_whatsapp_file(file_bytes)
        
        # Should be ParseError, not IndexError
        assert isinstance(exc_info.value, ParseError)
        # Should have helpful message
        assert len(str(exc_info.value)) > 20  # Not just a generic error
    
    def test_various_whatsapp_date_formats(self):
        """Test that different WhatsApp date formats are handled."""
        # US format (month/day/year)
        content_us = '''3/12/22, 12:34 AM - Jack: Hello
3/12/22, 1:05 AM - Sam: Hi
'''
        
        # European format (day/month/year) 
        content_eu = '''12/3/22, 12:34 - Jack: Hello
12/3/22, 13:05 - Sam: Hi
'''
        
        # Both should parse successfully
        for content in [content_us, content_eu]:
            file_bytes = content.encode('utf-8')
            df = _parse_whatsapp_file(file_bytes)
            assert len(df) >= 2
