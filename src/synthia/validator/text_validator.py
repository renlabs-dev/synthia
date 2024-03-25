"""
Module for validating text submissions on the Synthia subnet.

This class represents a validator module that runs on the Synthia subnet. It initializes a Wandb run to log validation data, and provides functions to retrieve metadata about the subnet and modules.
"""

# once we register the synthia subnet, we will update this value
from communex.module.module import Module  # type: ignore
from communex.client import CommuneClient  # type: ignore
from substrateinterface import Keypair  # type: ignore
from communex.module.client import serialize  # type: ignore
from communex.compat.types import Ss58Address  # type: ignore
from typing import cast
import time
from ._config import ValidatorSettings
import wandb

SYNTHIA_NETUID = 1

# TODO:
# Jairo
# - implement retry mechanism on question answer generation
# - make sure miner instructions are the same as answer generation of validator. WIth the same system instructions and tempreature
# - implement the main validation loop -> get question, get answer, loop through miners, ...  (without validation that is done by kelvin)
# after scoring set weights
# - query the `SYNTHIA_NETUID` dynamically from the chain name of the subnet

# Honza
# figure out a better prompt
# save the interaction between a validator and miner to a db
# making more robust, think about it

# Kelvin
# Implement scoring function based on vector difference using embedings


class TextValidator(Module):
    def __init__(self, key: Keypair, netuid: int) -> None:
        super().__init__()
        self.node_url = "wss://commune.api.onfinality.io/public-ws"
        self.client = CommuneClient(url=self.node_url)
        self.key = key
        self.netuid = netuid

    def get_synthia_netuid(self):
        """
        Retrives the netuid of the synthia subnet
        """
        return self.netuid

    def get_modules(self, client: CommuneClient, netuid: int) -> list[str]:
        """
        Retrives all module addresses from the subnet
        """
        module_addreses = client.query_map_address(netuid).values()
        return list(module_addreses)

    # TODO :
    # - Migrate from wandb to decentralized database, possibly ipfs, the server
    # has to check for the signature of the data. (This way is used even on S18, but we don't like it)
    def init_wandb(self, settings: ValidatorSettings, keypair: Keypair):
        # place holder, query later
        key = cast(Ss58Address, keypair.ss58_address)
        uid = self.client.get_uids(key=key)
        run_name = f"validator-{uid}"
        settings.uid = uid
        settings.key = keypair.ss58_address
        settings.run_name = run_name
        settings.type = "validator"
        settings.timestamp = time.time()
        config = settings.model_dump()
        signature = keypair.sign(serialize(config))
        config["signature"] = signature
        # Initialize the wandb run for the single project
        run = wandb.init(  #  type: ignore
            name=run_name,
            project=settings.project_name,
            entity="synthia-subnet",
            config=config,
            dir=settings.storage_path,
            reinit=True,
        )

    def main(self, settings: ValidatorSettings | None = None) -> None:
        if not settings:
            settings = ValidatorSettings()  # type: ignore
        self.init_wandb(settings, self.key)
