from typing import Annotated, Optional
from enum import Enum

import typer
from communex.compat.key import classic_load_key
from communex.module.server import ModuleServer
from communex.balance import to_nano
from communex.module._rate_limiters.limiters import StakeLimiterParams # type: ignore
import uvicorn

from synthia.miner.anthropic import OpenrouterModule, AnthropicModule


class ClaudeProviders(Enum):
    ANTHROPIC = "anthropic"
    OPENROUTER = "openrouter"


app = typer.Typer()


def stake_to_ratio(stake: int, multiplier: int = 1) -> float:
    max_ratio = 4
    base_ratio = 2
    if multiplier <= 1/max_ratio:
        raise ValueError(
            f"Given multiplier {multiplier} would set 0 tokens for all stakes"
        )
    
    def mult_2(x: int) -> int:
        return x * 2

    # 10x engineer switch case (btw, this actually optimizes)
    match stake:
        case _ if stake < to_nano(10_000):
            return 0
        case _ if stake < to_nano(500_000):  # 20 * 10 ** -1 request per 4000 * 10 ** -1 second
            return base_ratio * multiplier
        case _:
            return mult_2(base_ratio) * multiplier  # 30 * 10 ** -1 requests per 4000 * 10 ** -1 second



def provider_callback(value: str):
    value = value.lower()
    allowed_providers = ["anthropic", "openrouter"]
    if value not in allowed_providers:
        raise typer.BadParameter(
            f"Invalid provider. Allowed providers are: {', '.join(allowed_providers)}"
        )
    return value

@app.command('serve-miner')
def serve(
    commune_key: Annotated[
        str, 
        typer.Argument(
            help="Name of the key present in `~/.commune/key`"
            )
        ],
    provider: Optional[str] = typer.Option(
        default="anthropic", callback=provider_callback
    ),
    ip: Optional[str] = None,
    port: Optional[int] = None,

    ):
    provider_enumerated = ClaudeProviders(provider)
    keypair = classic_load_key(commune_key) # type: ignore
    match provider_enumerated:
        case ClaudeProviders.ANTHROPIC:
            module = AnthropicModule()
        case ClaudeProviders.OPENROUTER:
            module = OpenrouterModule()

    stake_limiter = StakeLimiterParams(
        epoch=800, 
        cache_age=600,
        get_refill_per_epoch=stake_to_ratio,
    )
    server = ModuleServer(
        module, keypair, subnets_whitelist=[3], limiter = stake_limiter
    )
    miner_app = server.get_fastapi_app()
    host = ip or "127.0.0.1"
    port_ = port or 8000
    uvicorn.run(miner_app, host=host, port=port_)

if __name__ == "__main__":
    typer.run(serve)