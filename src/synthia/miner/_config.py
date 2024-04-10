from pydantic_settings import BaseSettings

class OpenAISettings(BaseSettings):
    api_key: str
    model: str = "gpt-3.5-turbo"
    max_tokens: int = 100
    temperature: float = 0.5

    class Config:
        env_prefix = "OPENAI_"
        env_file = "env/config.env"

class AnthropicSettings(BaseSettings):
    api_key: str
    model: str = "claude-3-opus-20240229"
    max_tokens: int = 1000
    temperature: float = 0.5

    class Config:
        env_prefix = "ANTHROPIC_"
        env_file = "env/config.env"
