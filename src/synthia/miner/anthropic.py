from fastapi import HTTPException
from anthropic import Anthropic, APIError
from communex.module.module import Module, endpoint  # type: ignore
from ._config import AnthropicSettings  # Import the AnthropicSettings class from config
from typing import Any


class AnthropicModule(Module):
    def __init__(self, settings: AnthropicSettings | None = None) -> None:
        super().__init__()
        self.settings = settings or AnthropicSettings()  # type: ignore
        self.client = Anthropic(api_key=self.settings.api_key)

    @endpoint
    def generate(self, prompt: str) -> dict[str, str]:
        try:
            system_prompt = (
                "You are an expert explanation generator. "
                "Generate an explanation based on the given instructions. "
                "Provide the output solely in the specified JSON format, without any extra text or deviations."
            )
            assistant_prompt = (
                "Output the answer strictly in the following JSON format:\n"
                '{"explanation": "replace this with your actual explanation."}\n'
                "Provide the output solely in the specified JSON format, without any extra text or deviations."
            )
            message = self.client.messages.create(
                model=self.settings.model,
                max_tokens=self.settings.max_tokens,
                temperature=self.settings.temperature,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": [{"type": "text", "text": prompt}]},
                    {
                        "role": "assistant",
                        "content": [{"type": "text", "text": assistant_prompt}],
                    },
                ],
            )
            return self._treat_response(message)
        except APIError as e:
            raise HTTPException(status_code=e.status_code, detail=str(e)) from e  # type: ignore

    def _treat_response(self, message: Any) -> dict[str, str]:
        content = message.messages[-1].content.strip()
        try:
            json_start = content.index("{")
            json_end = content.rindex("}")
            json_content = content[json_start : json_end + 1]
            return {"answer": json_content}
        except (ValueError, IndexError):
            raise HTTPException(
                status_code=400, detail="Invalid JSON format in the response"
            )
