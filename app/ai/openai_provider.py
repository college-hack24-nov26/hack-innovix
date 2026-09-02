from app.ai.base import AIProvider
from app.ai.mock_provider import SAFETY_RULES


class OpenAIProvider(AIProvider):
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model

    def complete(self, system_prompt: str, user_prompt: str, temperature: float = 0.1) -> str:
        from openai import OpenAI

        client = OpenAI(api_key=self.api_key)
        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": f"{SAFETY_RULES}\n{system_prompt}"},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
        )
        return response.choices[0].message.content or ""


class LocalAIProvider(AIProvider):
    """Placeholder for a future local model endpoint."""

    def complete(self, system_prompt: str, user_prompt: str, temperature: float = 0.1) -> str:
        from app.ai.mock_provider import MockAIProvider

        return MockAIProvider().complete(system_prompt, user_prompt)
