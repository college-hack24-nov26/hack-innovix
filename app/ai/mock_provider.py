from app.ai.base import AIProvider

NOT_REPORTED = "Not reported"
NOT_AVAILABLE = "Not available"

SAFETY_RULES = """You are a clinical documentation assistant, not a clinician.
Never invent patient information, test results, or medications.
Never diagnose. Never prescribe. Never change a medical record autonomously.
If a field is missing, write exactly "Not reported" or "Not available".
Label every summary as an AI-generated draft requiring physician verification.
Do not make exaggerated medical claims.
"""


class MockAIProvider(AIProvider):
    def complete(self, system_prompt: str, user_prompt: str, temperature: float = 0.1) -> str:
        return (
            "AI-generated draft — physician verification required.\n\n"
            "The following summary uses only supplied source material. "
            "Missing items are marked Not reported / Not available.\n\n"
            f"{user_prompt[:4000]}"
        )
