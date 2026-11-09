from typing import Protocol


class AIProvider(Protocol):
    def generate(
        self,
        *,
        model: str,
        prompt: str,
        temperature: float,
        max_output_tokens: int,
        response_mime_type: str | None = None,
    ) -> str:
        ...
