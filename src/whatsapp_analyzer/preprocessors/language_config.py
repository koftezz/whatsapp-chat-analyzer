"""
Language configuration for WhatsApp chat analysis.

Supports English, Turkish, and German with patterns for:
- Media types (image, video, gif, audio, sticker)
- Deleted messages
- Edited messages (NEW)
- Location sharing
- Generic media placeholder
"""

from typing import Dict, List, Any

SUPPORTED_LANGUAGES = ["English", "Turkish", "German"]

# Language-specific patterns for WhatsApp message detection
LANGUAGE_SETTINGS: Dict[str, Dict[str, Any]] = {
    "English": {
        "image": "image omitted",
        "video": "video omitted",
        "gif": "GIF omitted",
        "audio": "audio omitted",
        "sticker": "sticker omitted",
        "deleted": [
            "This message was deleted.",
            "You deleted this message.",
            "This message was deleted"
        ],
        "edited": [
            "This message was edited",
            "You edited this message"
        ],
        "location": "Location https://",
        "media": "<Media omitted>",
    },
    "Turkish": {
        "image": "görüntü dahil edilmedi",
        "video": "video dahil edilmedi",
        "gif": "GIF dahil edilmedi",
        "audio": "ses dahil edilmedi",
        "sticker": "Çıkartma dahil edilmedi",
        "deleted": [
            "Bu mesaj silindi.",
            "Bu mesajı sildiniz."
        ],
        "edited": [
            "Bu mesaj düzenlendi",
            "Bu mesajı düzenlediniz"
        ],
        "location": "Konum https://",
        "media": "<görüntü dahil edilmedi>"
    },
    "German": {
        "image": "Bild weggelassen",
        "video": "Video weggelassen",
        "gif": "GIF weggelassen",
        "audio": "Audio weggelassen",
        "sticker": "Sticker weggelassen",
        "deleted": [
            "Diese Nachricht wurde gelöscht.",
            "Du hast diese Nachricht gelöscht."
        ],
        "edited": [
            "Diese Nachricht wurde bearbeitet",
            "Du hast diese Nachricht bearbeitet"
        ],
        "location": "Standort https://",
        "media": "<Medien weggelassen>"
    }
}


def get_language_settings(selected_lang: str) -> Dict[str, Any]:
    """
    Get language-specific patterns for WhatsApp message detection.

    Args:
        selected_lang: Language name ("English", "Turkish", or "German")

    Returns:
        Dictionary containing patterns for the selected language

    Raises:
        ValueError: If the language is not supported
    """
    if selected_lang not in SUPPORTED_LANGUAGES:
        raise ValueError(
            f"Unsupported language: {selected_lang}. "
            f"Supported languages: {', '.join(SUPPORTED_LANGUAGES)}"
        )
    return LANGUAGE_SETTINGS[selected_lang]
