from fastapi import HTTPException
from anthropic import Anthropic
from communex.module.module import Module, endpoint  # type: ignore
from ._config import AnthropicSettings


class AnthropicModule(Module):
    def __init__(self, settings: AnthropicSettings | None = None) -> None:
        super().__init__()
        self.settings = settings or AnthropicSettings()  # type: ignore
        self.client = Anthropic(api_key=self.settings.api_key)

    @endpoint
    def generate(self, prompt: str) -> dict[str, str]:
        response = self.client.chat.completions.create(  # type: ignore
            model=self.settings.model,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant designed to output JSON.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=self.settings.max_tokens,
            temperature=self.settings.temperature,
        )

        for msg in response.choices:  # type: ignore
            finish_reason = msg.finish_reason  # type: ignore
            if finish_reason != "stop":
                raise HTTPException(418, finish_reason)

            content = msg.message.content  # type: ignore
            if content:
                return {"answer": content}

        return {"answer": ""}
