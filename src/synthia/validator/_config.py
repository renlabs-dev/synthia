from communex.compat.types import Ss58Address  #  type: ignore
from pydantic_settings import BaseSettings


class ValidatorSettings(BaseSettings):
    api_key: str  # openai key, used to generate questions and answers
    # == Text generation ==
    model: str = "claude-3-opus-20240229"
    temperature: float = 0.2
    max_tokens: int = 1000

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
    # sleep time between each iteration
    iteration_interval: int = 1200

    class Config:
        env_prefix = "ANTHROPIC_"
        env_file = "env/anthropic.env"
