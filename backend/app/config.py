"""Shared configuration helpers for loading backend/.env safely."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BACKEND_DIR / ".env"

# Always load the backend-local .env, regardless of the process working directory.
load_dotenv(ENV_PATH)

_PLACEHOLDERS = {
    "your_groq_api_key_here",
    "your_gemini_api_key_here",
    "your_email@gmail.com",
    "your_16_char_app_password",
}


def get_env(name: str, default: str = "") -> str:
    value = (os.getenv(name, default) or "").strip()
    if value in _PLACEHOLDERS:
        return ""
    return value
