from typing import Protocol


from anthropic._types import NotGiven

class BaseLLM(Protocol):
    def prompt(
            self, user_prompt: str, system_prompt: str | None | NotGiven = None
            ) -> tuple[str | None, str]:
        ...

    @property
    def max_tokens(self) -> int:
        ...
