from abc import ABC, abstractmethod


class AIProvider(ABC):
    @abstractmethod
    def complete(self, system_prompt: str, user_prompt: str, temperature: float = 0.1) -> str:
        raise NotImplementedError
