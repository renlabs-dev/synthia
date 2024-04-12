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

class OpenRouterSettings(BaseSettings):
    api_key: str
    model: str = "mistralai/mistral-7b-instruct:free"
    max_tokens: int = 1000

    class Config:
        env_prefix = "OPENROUTER_"
        env_file = "env/config.env"

class DeepInfraSettings(BaseSettings):
    api_key: str
    model: str = "mistralai/Mixtral-8x22B-v0.1"
    max_tokens: int = 1000

    class Config:
        env_prefix = "DEEPINFRA_"
        env_file = "env/config.env"