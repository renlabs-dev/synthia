"""
Module for validating text submissions on the Synthia subnet.

This class represents a validator module that runs on the Synthia subnet. It initializes a Wandb run to log validation data, and provides functions to retrieve metadata about the subnet and modules.
"""

import re
from typing import cast
import time
# once we register the synthia subnet, we will update this value


from communex.module.module import Module  # type: ignore
from communex.client import CommuneClient  # type: ignore
from substrateinterface import Keypair  # type: ignore
from communex.module.client import serialize  # type: ignore
from communex.module.client import ModuleClient
from communex.compat.types import Ss58Address  # type: ignore
import wandb

from ._config import ValidatorSettings
from .generate_data import InputGenerator, create_prompt


def score(val_answer: str, miner_answer: str):
    import random
    return random.randint(0, 100)

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

# TODO: make it match ipv6
IP_REGEX = re.compile(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+')
def extract_address(string: str):
    """
    Extracts an address from a string.
    """
    return re.search(IP_REGEX, string)

def get_ip_port(adresses: list[str]):
    filtered_addr = map(extract_address, adresses)
    ip_port = [x.group(0).split(":") for x in filtered_addr if x is not None]
    return ip_port
     


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
    
    async def validate_step(self):
        syntia_netuid = self.get_synthia_netuid()
        modules_adresses = self.get_modules(self.client, syntia_netuid)
        modules_filtered_address = get_ip_port(modules_adresses)
        ig = InputGenerator()
        q = 3
        prompt = create_prompt(t = 3, q = q)
        questions = ig.prompt_question_gpt(prompt, q)['Answer'][0]['questions']
        questions = '\n'.join(questions)
        validator_answer = ig.prompt_answer_gpt(questions)['Answer'][0]
        answer_list: list[str] = []
        for sublist in validator_answer.values():
            for elem in sublist:
                answer_list.append(elem)
        val_answers = '\n'.join(answer_list)
        for module_ip, module_port in modules_filtered_address:
            #testing purposes
            module_ip = "127.0.0.1"
            module_port = "8000"
            
            try:
                client = ModuleClient(module_ip, int(module_port), self.key)
                answers = await client.call("generate", {"prompt": questions})
            except Exception as e:
                print(f"caught exception {e} on module {module_ip}:{module_port}")
                continue
            weight_score = score(val_answers, answers)
            print(weight_score)

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

if __name__ == "__main__":
    KEY_MNEMONIC = "dev01"
    validator = TextValidator(
        Keypair.create_from_mnemonic(
            KEY_MNEMONIC
        ),
        SYNTHIA_NETUID
    )
    # modules = validator.get_modules(validator.client, validator.get_synthia_netuid())
    # print(modules)
    # print("-------------")
    # modules_filtered_address = get_ip_port(modules)
    # print(modules_filtered_address)
    import asyncio
    x = asyncio.run(validator.validate_step())
    