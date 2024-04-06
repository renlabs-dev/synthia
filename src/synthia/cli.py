import typer
from typing import Annotated
from rich.console import Console
from communex._common import get_node_url
from communex.client import CommuneClient
from communex.compat.key import classic_load_key
from communex.cli._common import get_use_testnet

from synthia.validator.text_validator import (
    TextValidator, 
    ValidatorSettings,
    get_synthia_netuid
    )


app = typer.Typer()


@app.command('serve-synthia')
def serve(
    anthropic_api_key: Annotated[
        str,
        typer.Argument(
            help="The API key for the Anthropic API"
            )
    ],
    commune_key: Annotated[
        str, 
        typer.Argument(
            help="Name of the key present in `~/.commune/key`"
            )
        ],
    temperature: float = 0.2,
    max_tokens: int = 1000,
    iteration_interval: int = 1200,
    ):
    print(anthropic_api_key)
    keypair = classic_load_key(commune_key) # type: ignore
    settings = ValidatorSettings(
        api_key=anthropic_api_key,
        temperature=temperature,
        max_tokens=max_tokens,
        iteration_interval=iteration_interval,
    )
    get_use_testnet(True)
    breakpoint()
    c_client = CommuneClient(get_node_url())
    synthia_uid = get_synthia_netuid(c_client)
    validator = TextValidator(keypair, synthia_uid, c_client)
    validator.validation_loop(settings)

if __name__ == "__main__":
    typer.run(serve)