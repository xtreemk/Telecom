from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings:
    APP_NAME = "LiveBox AI Telecom MVP v0.4"
    APP_VERSION = "0.4.0"
    DB_PATH = Path(os.getenv("LIVEBOX_DB_PATH", BASE_DIR / "livebox.db"))
    ALLOWED_ORIGINS = [
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "http://127.0.0.1:5501",
        "http://localhost:5501",
    ]
    MOCK_TELECOM_MODE = os.getenv("LIVEBOX_MOCK_TELECOM", "true").lower() == "true"
    VOICE_SESSION_TIMEOUT_MINUTES = int(os.getenv("LIVEBOX_VOICE_SESSION_TIMEOUT", "30"))
    PROACTIVE_OFFERS_ENABLED = os.getenv("LIVEBOX_PROACTIVE_OFFERS", "true").lower() == "true"


settings = Settings()
