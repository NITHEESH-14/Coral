import json
import logging
from typing import Dict, Any, Tuple

# Constants
HOTKEY_SNIP = '<ctrl>+<shift>+s'
HOTKEY_GLOBAL = '<ctrl>+<shift>+g'
HOTKEY_RECORD = '<ctrl>+<shift>+x'
APP_NAME = "Coral"

PREV_HWND = None

# Extensions list for arrange_by_type
FILE_CATEGORIES = {
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"],
    "Documents": [".pdf", ".docx", ".xlsx", ".pptx", ".txt", ".csv"],
    "Videos": [".mp4", ".mov", ".avi", ".mkv", ".wmv"],
    "Audio": [".mp3", ".wav", ".flac", ".aac"]
}

# Color Theme
THEME = {
    "background": "#1E1E1E",
    "surface": "#2D2D2D",
    "primary": "#FF7F50", # Coral
    "text": "#FFFFFF",
    "text_muted": "#A0A0A0"
}

def setup_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    if not logger.handlers:
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        logger.addHandler(ch)
    return logger

def parse_groq_json(response_text: str) -> Tuple[str, Dict[str, Any]]:
    """
    Parses the response from Groq, expecting JSON.
    Returns (message, action_json).
    """
    try:
        data = json.loads(response_text)
        return data.get("message", "No message provided."), data.get("action_json") or {}
    except json.JSONDecodeError:
        # Fallback if Groq outputs markdown block
        if "```json" in response_text:
            try:
                block = response_text.split("```json")[1].split("```")[0].strip()
                data = json.loads(block)
                return data.get("message", "No message provided."), data.get("action_json") or {}
            except Exception:
                pass
        return "Sorry, I couldn't understand the response.", {}
