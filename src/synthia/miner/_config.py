from pydantic_settings import BaseSettings


class OpenAISettings(BaseSettings):
    api_key: str
    model: str = "gpt-3.5-turbo"
    max_tokens: int = 100
    temperature: float = 1.0

    class Config:
        env_prefix = "OPENAI_"
        env_file = "env/config.env"


class ClaudeSettings(BaseSettings):
    api_key: str
    model: str = "claude-v1"
    max_tokens: int = 100
    temperature: float = 1.0

    class Config:
        env_prefix = "CLAUDE_"
        env_file = "env/config.env"


class GeminiSettings(BaseSettings):
    api_key: str
    model: str = "gemini-v1"
    max_tokens: int = 100
    temperature: float = 1.0

    class Config:
        env_prefix = "GEMINI_"
        env_file = "env/config.env"


class Settings(BaseSettings):
    openai: OpenAISettings
    claude: ClaudeSettings
    gemini: GeminiSettings

    class Config:
        env_file = "env/config.env"
