from fastapi import HTTPException
from openai import OpenAI
from communex.module.module import Module, endpoint  # type: ignore
from ._config import OpenAISettings  # Import the OpenAISettings class from config


class OpenAIModule(Module):
    def __init__(self, settings: OpenAISettings | None = None) -> None:
        super().__init__()
        self.settings = settings or OpenAISettings()  # type: ignore
        self.client = OpenAI(api_key=self.settings.api_key)

    @endpoint
    def generate(self, prompt: str) -> dict[str, str]:
        response = self.client.chat.completions.create(
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

        for msg in response.choices:
            finish_reason = msg.finish_reason
            if finish_reason != "stop":
                raise HTTPException(418, finish_reason)

            content = msg.message.content
            if content:
                return {"answer": content}

        return {"answer": ""}
