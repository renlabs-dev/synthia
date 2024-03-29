from fastapi import HTTPException
from openai import OpenAI, APIError
from communex.module.module import Module, endpoint  # type: ignore
from ._config import OpenAISettings  # Import the OpenAISettings class from config
from typing import Any


class OpenAIModule(Module):
    def __init__(self, settings: OpenAISettings | None = None) -> None:
        super().__init__()
        self.settings = settings or OpenAISettings()  # type: ignore
        self.client = OpenAI(api_key=self.settings.api_key)

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
            response = self.client.chat.completions.create(
                model=self.settings.model,
                max_tokens=self.settings.max_tokens,
                temperature=self.settings.temperature,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                    {"role": "assistant", "content": assistant_prompt},
                ],
            )
            return self._treat_response(response)
        except APIError as e:
            raise HTTPException(status_code=e.status_code, detail=str(e)) from e  # type: ignore

    def _treat_response(self, response: Any) -> dict[str, str]:
        content = response.choices[0].message.content.strip()
        try:
            json_start = content.index("{")
            json_end = content.rindex("}")
            json_content = content[json_start : json_end + 1]
            return {"answer": json_content}
        except (ValueError, IndexError):
            raise HTTPException(
                status_code=400, detail="Invalid JSON format in the response"
            )
