from pydantic_settings import BaseSettings


class ValidatorSettings(BaseSettings):
    api_key: str

    class Config:
        env_prefix = "OPENAI_"
        env_file = "env/config.env"