from fastapi import HTTPException
from openai import OpenAI
from communex.module.module import Module, endpoint  # type: ignore
from ._config import OpenAISettings  # Import the OpenAISettings class from config.py
import json

openai_settings = OpenAISettings()  # type: ignore


class OpenAIModule(Module):
    def __init__(self) -> None:
        super().__init__()
        self.settings = openai_settings
        self.client = OpenAI(api_key=self.settings.api_key)

    @endpoint
    def generate(self, prompt: str):
        print("Prompting OpenAI")
        return {"a":"a"}
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

        answers: list[str] = []

        for msg in response.choices:
            finish_reason = msg.finish_reason
            if finish_reason != "stop":
                raise HTTPException(418, finish_reason)

            content = msg.message.content
            if content:
                json_data = json.loads(content)
                answer = json_data.get("answer")
                if answer:
                    answers.append(answer)

        return {"Answer": answers}


# if __name__ == "__main__":
#     text = "What is the meaning of life?"
#     output = OpenAIModule().generate(text)
#     print(output)   
