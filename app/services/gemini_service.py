import json
import logging
from typing import Dict, Any, Optional, List
import httpx

from app.config import settings

logger = logging.getLogger(__name__)

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

class GeminiService:
    @staticmethod
    def get_effective_key(custom_key: Optional[str] = None) -> Optional[str]:
        if custom_key and len(custom_key.strip()) > 10:
            return custom_key.strip()
        if settings.GEMINI_API_KEY:
            return settings.GEMINI_API_KEY.strip()
        return None

    @classmethod
    async def generate_json(
        cls, 
        prompt: str, 
        system_instruction: str, 
        custom_key: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        api_key = cls.get_effective_key(custom_key)
        if not api_key:
            logger.info("No Gemini API key configured. Utilizing local agent heuristics.")
            return None

        url = f"{GEMINI_API_URL}?key={api_key}"
        payload = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ],
            "system_instruction": {
                "parts": [{"text": system_instruction}]
            },
            "generationConfig": {
                "response_mime_type": "application/json",
                "temperature": 0.4,
                "topP": 0.8
            }
        }

        try:
            async with httpx.AsyncClient(timeout=25.0) as client:
                response = await client.post(url, json=payload)
                if response.status_code == 200:
                    data = response.json()
                    candidates = data.get("candidates", [])
                    if candidates and "content" in candidates[0]:
                        parts = candidates[0]["content"].get("parts", [])
                        if parts and "text" in parts[0]:
                            text_content = parts[0]["text"]
                            return json.loads(text_content)
                else:
                    logger.warning(
                        f"Gemini API returned status {response.status_code}: {response.text[:200]}"
                    )
        except Exception as e:
            logger.error(f"Error calling Gemini API: {e}")

        return None

