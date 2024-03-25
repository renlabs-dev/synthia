from pydantic_settings import BaseSettings

class OpenAISettings(BaseSettings):
    api_key: str
    model: str = "gpt-3.5-turbo"
    max_tokens: int = 100
    temperature: float = 1.0

    class Config:
        env_prefix = "OPENAI_"
        env_file = "env/openai.env"

class AnthropicSettings(BaseSettings):
    api_key: str
    model: str = "claude-v1"
    max_tokens: int = 100
    temperature: float = 1.0

    class Config:
        env_prefix = "ANTHROPIC_"
        env_file = "env/anthropic.env"
