from abc import ABC, abstractmethod
from typing import Any, Dict


class AIProvider(ABC):
    @abstractmethod
    def name(self) -> str:
        ...

    @abstractmethod
    def health(self) -> Dict[str, Any]:
        ...

    @abstractmethod
    def chat(self, prompt: str) -> Dict[str, Any]:
        ...
