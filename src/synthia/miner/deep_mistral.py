import requests
import json
from typing import Any

from .BaseLLM import BaseLLM
from ._config import DeepInfraSettings

class DeepMistral(BaseLLM):
    def __init__(self, settings: DeepInfraSettings | None = None) -> None:
        super().__init__()
        self.settings = settings or DeepInfraSettings() # type: ignore
        self._max_tokens = self.settings.max_tokens

    @property
    def max_tokens(self) -> int:
        return self._max_tokens
    
    @property
    def model(self) -> str:
        return self.settings.model
    
    def prompt(self, user_prompt: str, system_prompt: str | None = None):
        context_prompt = system_prompt or self.get_context_prompt(self.max_tokens)
        prompt = {

            "model": f"{self.settings.model}",
            "messages": [
                {"role": "system", "content": context_prompt},
                {"role": "user", "content": user_prompt},
            ],

            "max_tokens": self.max_tokens
        }
        
        response = requests.post(
        url="https://api.deepinfra.com/v1/openai/chat/completions",
        headers={
        "Authorization": f"Bearer {self.settings.api_key}",
        "Content-Type": "application/json"
        },
        data=json.dumps(prompt)
        )

        json_response: dict[Any, Any] = response.json()
        answer = json_response["choices"][0]
        finish_reason = answer['finish_reason']
        if finish_reason != "stop":
            return None, f"Could not get a complete answer: {finish_reason}"
        print(answer["message"]["content"]                                                          )
        return answer["message"]["content"], ""
    

if __name__ == "__main__":
    from communex.module.server import ModuleServer
    from substrateinterface import Keypair
    mistral = DeepMistral()

    import uvicorn

    # test key
    KEY_MNEMONIC = (
        "electric suffer nephew rough gentle decline fun body tray account vital clinic"
    )
    key = Keypair.create_from_mnemonic(KEY_MNEMONIC)
    server = ModuleServer(mistral, key)
    app = server.get_fastapi_app()
    uvicorn.run(app, host="127.0.0.1", port=8000)
