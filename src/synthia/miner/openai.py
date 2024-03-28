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
        """Generates an answer based on the given prompt using OpenAI's chat completion API.

        Args:
            prompt: The question or prompt to generate an answer for.

        Returns:
            A dictionary containing the generated answer with the key "answer".

        Raises:
            HTTPException: If the API response has a finish_reason other than "stop".
        """

        system_prompt = (
            "You are an expert at answering questions."
            "Answer the given question thoroughly and accurately."
            "Output your answer in the JSON format specified."
        )

        assistant_prompt = (
            "Provide your answer in this JSON format, with no other text:\n"
            '{"answer": "Replace this with your actual answer to the question."}'
        )

        response = self.client.chat.completions.create(
            model=self.settings.model,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "assistant",
                    "content": assistant_prompt,
                },
                {
                    "role": "user",
                    "content": prompt,
                },
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
if __name__ == "__main__":
    from communex.module.server import ModuleServer
    from substrateinterface import Keypair

    import uvicorn
    KEY_MNEMONIC = "electric suffer nephew rough gentle decline fun body tray account vital clinic"
    key = Keypair.create_from_mnemonic(KEY_MNEMONIC)
    openai = OpenAIModule()
    server = ModuleServer(openai, key)
    app = server.get_fastapi_app()
    uvicorn.run(app, host="127.0.0.1", port=8000)