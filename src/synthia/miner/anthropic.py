from fastapi import HTTPException
from anthropic import Anthropic, APIError
from communex.module.module import Module, endpoint  # type: ignore
from ._config import AnthropicSettings  # Import the AnthropicSettings class from config


class AnthropicModule(Module):
    def __init__(self, settings: AnthropicSettings | None = None) -> None:
        super().__init__()
        self.settings = settings or AnthropicSettings()  # type: ignore
        self.client = Anthropic(api_key=self.settings.api_key)

    @endpoint
    def generate(self, prompt: str) -> dict[str, str]:
        try:
            system_prompt = (
                "You are an expert at answering questions."
                "Answer the given question thoroughly and accurately."
                "Output your answer in the JSON format specified."
            )
            assistant_prompt = (
                "Provide your answer in this JSON format, with no other text:\n"
                '{"answer": "Replace this with your actual answer to the question."}'
            )

            response = self.client.completions.create(
                model=self.settings.model,
                prompt=f"{system_prompt}\n{assistant_prompt}\n\nHuman: {prompt}\nAssistant:",
                max_tokens_to_sample=self.settings.max_tokens,
                temperature=self.settings.temperature,
                stop_sequences=["\nHuman:"],
            )
            completion = response.completion
            if completion.endswith("\nHuman:"):
                content = completion[:-7].strip()
            else:
                content = completion.strip()

            # Extract the JSON content from the completion
            try:
                json_start = content.index("{")
                json_end = content.rindex("}")
                json_content = content[json_start : json_end + 1]
                return {"answer": json_content}
            except (ValueError, IndexError):
                raise HTTPException(
                    status_code=400, detail="Invalid JSON format in the response"
                )

        except APIError as e:
            raise HTTPException(status_code=e.status_code, detail=str(e)) from e  # type: ignore
