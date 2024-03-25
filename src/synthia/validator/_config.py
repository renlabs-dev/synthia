from pydantic_settings import BaseSettings

class ValidatorSettings(BaseSettings):
    api_key: str # openai key
    project_name: str = "synthia"
    # currently only limited to openai
    question_model: str = "gpt-3.5-turbo"
    answer_model: str = "gpt-4"

    class Config:
        env_prefix = "OPENAI_"
        env_file = "env/config.env"


    