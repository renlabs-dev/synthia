import requests
import json
from typing import Any

from .BaseLLM import BaseLLM
from ._config import OpenRouterSettings

class Mistral(BaseLLM):
    def __init__(self, settings: OpenRouterSettings | None = None) -> None:
        super().__init__()
        self.settings = settings or OpenRouterSettings() # type: ignore
        self._max_tokens = self.settings.max_tokens

    @property
    def max_tokens(self) -> int:
        return self._max_tokens
    
    
    def prompt(self, user_prompt: str, system_prompt: str | None = None):
        context_prompt = system_prompt or self.get_context_prompt(self.max_tokens)
        prompt = {
            "model": self.settings.model,
            "messages": [
                {"role": "system", "content": context_prompt},
                {"role": "user", "content": user_prompt},
            ]
        }
        response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
        "Authorization": f"Bearer {self.settings.api_key}",
        },
        data=json.dumps(prompt)
        )

        json_response: dict[Any, Any] = response.json()
        answer = json_response["choices"][0]
        finish_reason = answer['finish_reason']
        if finish_reason:
            return None, f"Could not get a complete answer: {finish_reason}"
        return answer["content"], ""
    

if __name__ == "__main__":
    from communex.module.server import ModuleServer
    from substrateinterface import Keypair
    mistral = Mistral()

    import uvicorn

    # test key
    KEY_MNEMONIC = (
        "electric suffer nephew rough gentle decline fun body tray account vital clinic"
    )
    key = Keypair.create_from_mnemonic(KEY_MNEMONIC)
    server = ModuleServer(mistral, key)
    app = server.get_fastapi_app()
    uvicorn.run(app, host="127.0.0.1", port=8000)
