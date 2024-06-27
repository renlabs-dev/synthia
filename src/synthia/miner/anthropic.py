import json
from typing import Any

import requests
from anthropic import Anthropic
from anthropic._types import NotGiven

from ._config import (  # Import the AnthropicSettings class from config
    AnthropicSettings, OpenrouterSettings)
from .BaseLLM import BaseLLM
from synthia.utils import log


class AnthropicModule(BaseLLM):
    def __init__(self, settings: AnthropicSettings | None = None) -> None:
        super().__init__()
        self.settings = settings or AnthropicSettings()  # type: ignore
        self.client = Anthropic(api_key=self.settings.api_key)
        self.system_prompt = (
            "You are a supreme polymath renowned for your ability to explain "
            "complex concepts effectively to any audience from laypeople "
            "to fellow top experts. "
            "By principle, you always ensure factual accuracy. "
            "You are master at adapting your explanation strategy as needed "
            "based on the field and target audience, using a wide array of "
            "tools such as examples, analogies and metaphors whenever and "
            "only when appropriate. Your goal is their comprehension of the "
            "explanation, according to their background expertise. "
            "You always structure your explanations coherently and express "
            "yourself clear and concisely, crystallizing thoughts and "
            "key concepts. You only respond with the explanations themselves, "
            "eliminating redundant conversational additions. "
            f"Keep your answer below {int(self.settings.max_tokens * 0.75)} tokens"
        )

    def prompt(self, user_prompt: str, system_prompt: str | None | NotGiven = None):
        if not system_prompt:
            system_prompt = self.system_prompt
        message = self.client.messages.create(
            model=self.settings.model,
            max_tokens=self.settings.max_tokens,
            temperature=self.settings.temperature,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt},
            ],
        )
        treated_message = self._treat_response(message)
        return treated_message

    def _treat_response(self, message: Any):
        # TODO: use result ADT
        message_dict = message.dict()
        if (
            message_dict["stop_sequence"] is not None
            or message_dict["stop_reason"] != "end_turn"
        ):
            return (
                None,
                f"Could not generate an answer. Stop reason {message_dict['stop_reason']}"
            )

        blocks = message_dict["content"]
        answer = "".join([block["text"] for block in blocks])
        return answer, ""

    @property
    def max_tokens(self) -> int:
        return self.settings.max_tokens

    @property
    def model(self) -> str:
        return self.settings.model


class OpenrouterModule(BaseLLM):

    module_map: dict[str, str] = {
        "claude-3-opus-20240229": "anthropic/claude-3-opus",
        "anthropic/claude-3-opus": "anthropic/claude-3-opus",
        "anthropic/claude-3.5-sonnet": "anthropic/claude-3.5-sonnet",
        "claude-3-5-sonnet-20240620": "anthropic/claude-3.5-sonnet",
    }

    def __init__(self, settings: OpenrouterSettings | None = None) -> None:
        super().__init__()
        self.settings = settings or OpenrouterSettings()  # type: ignore
        self._max_tokens = self.settings.max_tokens
        if self.settings.model not in self.module_map:
            raise ValueError(
                f"Model {self.settings.model} not supported on Openrouter"
            )

    @property
    def max_tokens(self) -> int:
        return self._max_tokens

    @property
    def model(self) -> str:
        model_name = self.module_name_mapping(self.settings.model)
        return model_name

    def module_name_mapping(self, model_name: str) -> str:
        return self.module_map[model_name]

    def prompt(self, user_prompt: str, system_prompt: str | None = None):
        context_prompt = system_prompt or self.get_context_prompt(
            self.max_tokens)
        model = self.model
        prompt = {
            "model": model,
            "messages": [
                {"role": "system", "content": context_prompt},
                {"role": "user", "content": user_prompt},
            ]
        }
        key = self.settings.api_key
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {key}",
            },
            data=json.dumps(prompt)
        )

        json_response: dict[Any, Any] = response.json()
        error = json_response.get("error")
        if error is not None and error.get("code") == 402:
            message = "Insufficient credits"
            log(message)
            return None, message
        answer = json_response["choices"][0]
        finish_reason = answer['finish_reason']
        if finish_reason != "end_turn":
            return None, f"Could not get a complete answer: {finish_reason}"
        return answer["message"]["content"], ""
