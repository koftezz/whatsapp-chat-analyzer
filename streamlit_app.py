"""
WhatsApp Chat Analyzer - Streamlit Application

A comprehensive tool for analyzing WhatsApp chat exports with support for
English, Turkish, and German languages.
"""

import os
import sys

import streamlit as st

# Add paths for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ui.sidebar import render_sidebar
from ui.tabs import render_tabs
from ui.compat import safe_status, safe_toast
from whatsapp_analyzer.preprocessors import preprocess_data

# Page configuration
st.set_page_config(
    page_title="WhatsApp Chat Analyzer",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Report a bug': "https://github.com/koftezz/whatsapp-chat-analyzer/issues",
        'About': "# WhatsApp Chat Analyzer\nAnalyze your chat exports with ease!"
    }
)


def initialize_session_state():
    """Initialize session state variables if they don't exist."""
    defaults = {
        'raw_data': None,
        'processed_data': None,
        'locations': None,
        'file_hash': None,
    }

    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value


def main():
    """Main application entry point."""
    # Initialize session state
    initialize_session_state()

    # Render sidebar and get configuration
    config = render_sidebar()

    # Main content area
    if config['analysis_requested']:
        # Process the data
        _run_analysis(config)

    elif st.session_state.processed_data is not None:
        # Show existing analysis
        _show_analysis()

    else:
        # Show welcome screen
        _show_welcome()


def _run_analysis(config):
    """Run the analysis pipeline and store results."""
    with safe_status("Analyzing your chat...", expanded=True) as status:
        status.update(label="Preprocessing data...")

        df, locations = preprocess_data(
            df=st.session_state.raw_data.copy(),
            selected_lang=config['selected_lang'],
            selected_authors=config['selected_authors']
        )

        # Store processed data in session state
        st.session_state.processed_data = df
        st.session_state.locations = locations

        status.update(label="Analysis complete!", state="complete")

    safe_toast("Analysis complete!")

    # Show the analysis
    _show_analysis()


def _show_analysis():
    """Display the analysis results."""
    st.title("💬 WhatsApp Chat Analysis")

    df = st.session_state.processed_data
    locations = st.session_state.locations

    # Render tabs with analysis
    render_tabs(df, locations)


def _show_welcome():
    """Show welcome screen when no data is loaded."""
    st.title("💬 WhatsApp Chat Analyzer")

    st.markdown("""
    ### Welcome!

    Upload your WhatsApp chat export to discover insights about your conversations.

    **Features:**
    - 📊 Message statistics and trends
    - 👥 Author comparisons and rankings
    - ⏰ Activity patterns by time and day
    - 💬 Response time analysis
    - ☁️ Word clouds and emoji analysis

    **Getting Started:**
    1. Export your chat from WhatsApp (without media)
    2. Upload the .txt file using the sidebar
    3. Select participants and language
    4. Click "Analyze Chat"

    ---
    """)

    # Show info expanders
    col1, col2 = st.columns(2)

    with col1:
        with st.expander("🔒 Privacy & Security"):
            st.markdown("""
            - Your data stays on your device
            - We don't store any chat data
            - Processing happens locally in your browser
            - No data is sent to external servers
            """)

    with col2:
        with st.expander("🌍 Supported Languages"):
            st.markdown("""
            The analyzer supports chats in:
            - 🇬🇧 English
            - 🇹🇷 Turkish
            - 🇩🇪 German

            Select your WhatsApp language in the sidebar for accurate detection.
            """)

    with st.expander("📱 How to Export Your Chat"):
        st.markdown("""
        **On iPhone:**
        1. Open the chat in WhatsApp
        2. Tap the contact/group name at the top
        3. Scroll down and tap "Export Chat"
        4. Choose "Without Media"
        5. Save or share the .txt file

        **On Android:**
        1. Open the chat in WhatsApp
        2. Tap the three dots (⋮) menu
        3. Select "More" → "Export Chat"
        4. Choose "Without Media"
        5. Save or share the .txt file
        """)

    # Footer
    st.markdown("---")
    st.markdown(
        "Made with ❤️ using [Streamlit](https://streamlit.io) | "
        "[View Source](https://github.com/koftezz/whatsapp-chat-analyzer) | "
        "[Report Issues](https://github.com/koftezz/whatsapp-chat-analyzer/issues)"
    )


if __name__ == "__main__":
    main()
