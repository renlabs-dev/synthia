from communex.module.module import Module  # type: ignore
from communex.client import CommuneClient  # type: ignore
from substrateinterface import Keypair  # type: ignore
from communex.module._signer import sign  # type: ignore
from communex.module.client import serialize  # type: ignore
import time
from ._config import ValidatorSettings
import wandb


class TextValidator(Module):
    def __init__(self) -> None:
        super().__init__()
        self.node_url = "wss://commune.api.onfinality.io/public-ws"
        self.client = CommuneClient(url=self.node_url)

    def get_synthia_netuid(self, client: CommuneClient):
        """
        Retrives the netuid of the synthia subnet
        """
        pass

    def get_modules(self, client: CommuneClient):
        """
        Retrives all modules from the subnet
        """
        pass

    def init_wandb(
        self, clinet: CommuneClient, settings: ValidatorSettings, keypair: Keypair
    ):
        # place holder, query later
        uid = 0
        run_name = f"validator-{uid}"
        settings.uid = uid
        settings.key = keypair.ss58_address
        settings.run_name = run_name
        settings.type = "validator"
        settings.timestamp = time.time()
        config = settings.model_dump()
        signature = keypair.sign(serialize(config))
        # Initialize the wandb run for the single project
        run = wandb.init(  #  type: ignore
            name=run_name,
            project=settings.project_name,
            entity="synthia-subnet",
            config=config,
            dir=config.full_path,
            reinit=True,
        )

        # Sign the run to ensure it's from the correct hotkey
        signature = keypair.sign(run.id.encode()).hex()  #  type: ignore
        config.signature = signature
        wandb.config.update(config, allow_val_change=True)
