from communex.compat.types import Ss58Address  #  type: ignore
from pydantic_settings import BaseSettings


class ValidatorSettings(BaseSettings):
    api_key: str  # openai key, used to generate questions and answers
    # == Text generation ==
    model: str = "claude-3-opus-20240229"
    temperature: float = 0.2
    max_tokens: int = 1000

    # == Scoring ==
    # sleep time between each iteration
    # (we are aiming at 50 block subnet tempo, with 8 second block time)
    iteration_interval: int = 400
    hf_uploader_ss58: str = "5EX6ixabe8fiWHySw4SYaJAkaHLKeqSJ3rv7so2FrLC2cfGV"

    class Config:
        env_prefix = "ANTHROPIC_"
        env_file = "env/anthropic.env"
