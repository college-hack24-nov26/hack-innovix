from flask import current_app

from app.ai.base import AIProvider
from app.ai.mock_provider import MockAIProvider
from app.ai.openai_provider import LocalAIProvider, OpenAIProvider


def get_ai_provider() -> AIProvider:
    name = current_app.config.get("AI_PROVIDER", "mock").lower()
    key = current_app.config.get("OPENAI_API_KEY") or ""
    if name == "openai" and key:
        return OpenAIProvider(key, current_app.config.get("OPENAI_MODEL", "gpt-4o-mini"))
    if name == "local":
        return LocalAIProvider()
    return MockAIProvider()
