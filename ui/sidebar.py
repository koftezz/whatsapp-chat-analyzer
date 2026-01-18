"""
Sidebar component for WhatsApp Chat Analyzer.

Handles file upload, configuration, and action buttons.
"""

import hashlib
import streamlit as st
import pandas as pd
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from whatsapp_analyzer.parsers import read_file
from whatsapp_analyzer.preprocessors import SUPPORTED_LANGUAGES


def render_sidebar():
    """
    Render the sidebar with file upload, configuration, and actions.

    Returns:
        dict: Configuration state including:
            - file_uploaded: bool
            - ready_to_analyze: bool
            - analysis_requested: bool
            - selected_authors: list
            - selected_lang: str
    """
    with st.sidebar:
        st.header("WhatsApp Chat Analyzer")

        # Upload Section
        _render_upload_section()

        st.divider()

        # Configuration Section (when file uploaded)
        config = _render_config_section()

        st.divider()

        # Actions Section (when analysis done)
        _render_actions_section()

        st.divider()

        # Info Section
        _render_info_section()

        return config


def _render_upload_section():
    """Render the file upload section."""
    st.subheader("Upload")

    file = st.file_uploader(
        "Upload WhatsApp chat file (.txt)",
        type="txt",
        help="Export your chat without media from WhatsApp"
    )

    if file is not None:
        # Calculate file hash for change detection
        file_hash = hashlib.md5(file.getvalue()).hexdigest()

        # Only process if file changed
        if file_hash != st.session_state.get('file_hash'):
            with st.status("Processing file...", expanded=True) as status:
                status.update(label="Reading file...")
                df = read_file(file)

                status.update(label="Preparing data...")
                df["timestamp"] = pd.to_datetime(df["timestamp"])
                df = df.sort_values("timestamp")
                # Skip first three entries (typically group creation messages)
                df = df[3:]

                # Store in session state
                st.session_state.raw_data = df
                st.session_state.file_hash = file_hash
                st.session_state.processed_data = None  # Clear old processed data
                st.session_state.locations = None

                status.update(label="File uploaded!", state="complete")

            st.toast("File uploaded successfully!")

    # Sample data download
    st.download_button(
        label="Download sample file",
        data=_get_sample_data(),
        file_name='sample_chat.txt',
        mime='text/plain',
        help="Use this sample file to try the app"
    )


@st.cache_data
def _get_sample_data():
    """Load and cache sample data."""
    df = pd.read_csv(
        "https://raw.githubusercontent.com/koftezz/whatsapp-chat-analyzer/0aee084ffb8b8ec4869da540dc95401b8e16b7dd/data/sample_file.txt",
        header=None
    )
    return df.to_csv(index=False).encode('utf-8')


def _render_config_section():
    """Render the configuration section."""
    config = {
        'file_uploaded': False,
        'ready_to_analyze': False,
        'analysis_requested': False,
        'selected_authors': [],
        'selected_lang': 'English'
    }

    if st.session_state.get('raw_data') is None:
        st.info("Upload a file to configure analysis")
        return config

    config['file_uploaded'] = True
    df = st.session_state.raw_data

    st.subheader("Configuration")

    # Author selection
    author_list = df["author"].drop_duplicates().tolist()
    selected_authors = st.multiselect(
        "Select authors to include",
        author_list,
        default=author_list,
        help="Choose which chat participants to analyze"
    )
    config['selected_authors'] = selected_authors

    # Language selection
    selected_lang = st.radio(
        "Chat language",
        SUPPORTED_LANGUAGES,
        help="Select the language used in your WhatsApp"
    )
    config['selected_lang'] = selected_lang

    # Validate and show analyze button
    if len(selected_authors) >= 2:
        config['ready_to_analyze'] = True

        # Determine button label
        if st.session_state.get('processed_data') is not None:
            button_label = "Re-analyze"
            button_type = "secondary"
        else:
            button_label = "Analyze Chat"
            button_type = "primary"

        if st.button(button_label, type=button_type, use_container_width=True):
            config['analysis_requested'] = True
    else:
        st.warning("Select at least 2 authors to analyze")

    return config


def _render_actions_section():
    """Render the actions section."""
    if st.session_state.get('processed_data') is None:
        return

    st.subheader("Actions")

    df = st.session_state.processed_data

    # Export CSV
    csv_data = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Export as CSV",
        data=csv_data,
        file_name="whatsapp_analysis.csv",
        mime="text/csv",
        use_container_width=True
    )

    # Reset button
    if st.button("Start Over", use_container_width=True):
        # Clear all session state
        for key in ['raw_data', 'processed_data', 'locations', 'file_hash']:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()


def _render_info_section():
    """Render the info section with about and help."""
    st.subheader("Info")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("About", use_container_width=True):
            _show_about_dialog()

    with col2:
        if st.button("Help", use_container_width=True):
            _show_help_dialog()

    # GitHub sponsor link
    st.link_button(
        "Sponsor on GitHub",
        "https://github.com/sponsors/koftezz",
        use_container_width=True
    )


@st.dialog("About WhatsApp Chat Analyzer")
def _show_about_dialog():
    """Show the about dialog."""
    st.markdown("""
    ### Privacy First
    Your data stays on your device. We don't store any of your chat data.

    ### Supported Languages
    - English
    - Turkish
    - German

    ### Features
    - Group and direct message analysis
    - Message trends and patterns
    - Author statistics and comparisons
    - Word clouds and emoji analysis

    ### Acknowledgements
    - [chat-miner](https://github.com/joweich/chat-miner) for WhatsApp parsing
    - [Dinesh Vatvani](https://dvatvani.github.io/whatsapp-analysis.html) for inspiration
    """)

    st.link_button(
        "View Source on GitHub",
        "https://github.com/koftezz/whatsapp-chat-analyzer"
    )


@st.dialog("How to Use")
def _show_help_dialog():
    """Show the help dialog."""
    st.markdown("""
    ### Quick Start

    1. **Export your chat** from WhatsApp:
       - Open a chat in WhatsApp
       - Tap menu (...) > More > Export chat
       - Choose "Without Media"

    2. **Upload the .txt file** using the upload button

    3. **Configure your analysis**:
       - Select which participants to include
       - Choose your WhatsApp language

    4. **Click "Analyze Chat"** to see your results!

    ### Tips
    - Processing may take 1-2 minutes for large files
    - Use the tabs to explore different insights
    - Export your analysis as CSV for further exploration
    """)
