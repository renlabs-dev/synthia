from communex.compat.types import Ss58Address  #  type: ignore
from pydantic_settings import BaseSettings


class ValidatorSettings(BaseSettings):
    api_key: str  # openai key, used to generate questions and answers
    # == Text generation ==
    model: str | None = None
    temperature: int | None = None
    max_tokens: int | None = None
    # currently only limited to openai
    question_model: str = "gpt-3.5-turbo"
    answer_model: str = "gpt-4-turbo-preview"
    generation_interval: int = 3  # after N iterations are finish, generate new data
    # TODO: adjust the following values
    question_temperature: float = 0  # 0.85
    answer_temperature: float = 0.3
    # questions to generate in validation loop
    question_amount: int = 40
    # random themes to choose
    theme_amount: int = 3

    # == Wandb ==
    use_wandb: bool = False
    project_name: str = "synthia"
    type: str = "validator"
    # run settings
    uid: int | None = None
    key: Ss58Address | None = None
    run_name: str | None = None
    timestamp: float | None = None

    # == Scoring ==
    iteration_interval: int = 1200

    class Config:
        env_prefix = "OPENAI_"
        env_file = "env/openai.env"
