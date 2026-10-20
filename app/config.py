import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

class Settings:
    PROJECT_NAME: str = "TripMind AI"
    VERSION: str = "2.0.0"
    DEFAULT_CURRENCY: str = "INR"
    
    @property
    def GEMINI_API_KEY(self) -> str | None:
        return os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

settings = Settings()

