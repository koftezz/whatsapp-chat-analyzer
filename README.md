# WhatsApp Chat Analyzer

A Streamlit app that analyzes your WhatsApp chat exports. Check it out [here](https://whats-chat-detective.streamlit.app/)!

## Features

### Message Analysis
- Counts media types: images, videos, GIFs, stickers, voice messages
- Detects deleted messages
- Detects edited messages (new!)
- Tracks links and location shares
- Emoji usage analysis

### Visualizations
- **Activity Heatmap** - See when you chat the most (day/hour)
- **Word Cloud** - Interactive with adjustable word length and count
- **Monthly Volume** - Track messaging trends over time
- **Response Matrix** - Who responds to whom
- **Time of Day** - When each person is most active
- **Day of Week** - Activity patterns by weekday

### Statistics
- Message counts and percentages per author
- Talkativeness ratings (5-tier: Very quiet → Very talkative)
- Messaging trends (3, 6, 12 month analysis)
- Response time analysis
- Consecutive message streaks
- Conversation starter detection

## Privacy

Your data stays on your device. Nothing is saved or sent to external servers.

## Supported Languages

- English
- Turkish
- German

Each language has full support for detecting:
- Deleted message notifications
- Edited message indicators
- Media placeholders

## Usage

1. Export your chat from WhatsApp (without media)
2. Upload the `.txt` file
3. Select participants to analyze
4. Choose your WhatsApp language
5. Click "Analyze Chat"

Works with both group chats and direct messages.

## Project Structure

```
whatsapp-chat-analyzer/
├── streamlit_app.py          # Main application
├── ui/                       # UI components
│   ├── sidebar.py           # File upload, config, actions
│   └── tabs/                # Tab components
│       ├── overview.py      # Summary metrics
│       ├── activity.py      # Time patterns
│       ├── authors.py       # Author statistics
│       └── content.py       # Word cloud, emojis
├── src/whatsapp_analyzer/    # Core library
│   ├── parsers/             # File reading
│   ├── preprocessors/       # Data processing
│   │   ├── language_config.py   # Language patterns
│   │   └── message_processor.py # Message detection
│   ├── analyzers/           # Statistical analysis
│   ├── visualizations/      # Chart generation
│   └── utils/               # Helper functions
├── tests/                   # Test suite
└── helpers.py               # Backwards compatibility
```

## Development

### Install dependencies

```bash
pip install -r requirements.txt
```

### Run locally

```bash
streamlit run streamlit_app.py
```

### Run tests

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

## Tech Stack

- **Streamlit** - Web interface
- **Pandas** - Data processing
- **Altair** - Interactive charts
- **chat-miner** - WhatsApp parsing
- **WordCloud** - Word cloud generation

## Contributing

Issues and pull requests welcome on [GitHub](https://github.com/koftezz/whatsapp-chat-analyzer).

## License

MIT
