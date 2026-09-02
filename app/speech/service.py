"""Backend speech abstraction for future Indian-language ASR/TTS."""


class SpeechService:
    def transcribe(self, audio_bytes: bytes, language: str = "en") -> str:
        return ""

    def synthesize(self, text: str, language: str = "en") -> bytes:
        return b""
