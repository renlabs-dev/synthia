from abc import ABC, abstractmethod

from communex.module.module import Module, endpoint  # type: ignore
from fastapi import HTTPException


class BaseLLM(ABC, Module):
    @abstractmethod
    def prompt(
            self, user_prompt: str, system_prompt: str | None = None
            ) -> tuple[str | None, str]:
        ...

    @property
    def max_tokens(self) -> int:
        ...

    @property
    def model(self) -> str:
        ...

    def get_context_prompt(self, max_tokens: int) -> str:
        prompt = (
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
            f"Try to keep your answer below {max_tokens} tokens"
        )
        return prompt
    
    @endpoint
    def generate(self, prompt: str) -> dict[str, str]:
        try:
            message = self.prompt(prompt, self.get_context_prompt(self.max_tokens))
        except Exception as e:
            status_code = getattr(e, 'status_code', 500)
            raise HTTPException(status_code=status_code, detail=str(e)) from e

        match message:
            case None, explanation:
                raise HTTPException(status_code=500, detail=explanation)
            case answer, _:
                return {"answer": answer}
            
    @endpoint
    def get_model(self):
        return {"model": self.model}