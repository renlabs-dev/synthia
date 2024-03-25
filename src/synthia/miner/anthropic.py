from fastapi import HTTPException

from anthropic import Anthropic, APIError

from communex.module.module import Module, endpoint  # type: ignore

from ._config import (
    AnthropicSettings,
)  # Import the AnthropicSettings class from config 


class AnthropicModule(Module):

    def __init__(self, settings: AnthropicSettings | None = None) -> None:
        super().__init__()
        self.settings = settings or AnthropicSettings()  # type: ignore
        self.client = Anthropic(api_key=self.settings.api_key)

    @endpoint
    def generate(self, prompt: str) -> dict[str, str]:
        try:
            response = self.client.completions.create(
                model=self.settings.model,
                prompt=f"\nHuman: {prompt}\nAssistant:",
                max_tokens_to_sample=self.settings.max_tokens,
                temperature=self.settings.temperature,
                stop_sequences=["\nHuman:"],
            )

            completion = response.completion

            if completion.endswith("\nHuman:"):
                content = completion[:-7].strip()
            else:
                content = completion.strip()

            return {"answer": content}
        except APIError as e:
            raise HTTPException(status_code=e.status_code, detail=str(e)) from e  # type: ignore
