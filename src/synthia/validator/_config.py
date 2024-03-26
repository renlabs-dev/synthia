from pydantic_settings import BaseSettings


class ValidatorSettings(BaseSettings):
    api_key: str  # openai key, used to generate questions and answers
    # place holders, in case user uses the same env file to run the validator and the miner
    model: str | None = None
    temperature: int | None = None
    max_tokens: int | None = None
    # wandb
    project_name: str = "synthia"
    storage_path: str = "/synthia/db"
    # currently only limited to openai
    question_model: str = "gpt-3.5-turbo"
    answer_model: str = "gpt-4"
    # TODO:
    # adjust on scoring
    question_temperature: float = 0 #0.85
    answer_temperature: float = 0.3

    class Config:
        env_prefix = "OPENAI_"
        env_file = "env/openai.env"
