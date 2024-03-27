"""
Module for validating text submissions on the Synthia subnet.

This class represents a validator module that runs on the Synthia subnet. It initializes a Wandb run to log validation data, and provides functions to retrieve metadata about the subnet and modules.
"""

import re
from typing import cast, Any
import time
import os
import json

# once we register the synthia subnet, we will update this value


from communex.module.module import Module  # type: ignore
from communex.client import CommuneClient  # type: ignore
from substrateinterface import Keypair  # type: ignore
from communex.module.client import serialize  # type: ignore
from communex.module._signer import sign  # type: ignore
from communex.module.client import ModuleClient  # type: ignore
from communex.compat.types import Ss58Address  # type: ignore
import wandb

from ._config import ValidatorSettings
from .generate_data import InputGenerator, question_prompt, answer_prompt


def score(val_answer: str, miner_answer: str) -> float:
    import random

    return float(random.randint(0, 100))


SYNTHIA_NETUID = 1

# TODO:
# Jairo
# - implement retry mechanism on question answer generation
# - make sure miner instructions are the same as answer generation of validator. WIth the same system instructions and tempreature
# - implement the main validation loop -> get question, get answer, loop through miners, ...  (without validation that is done by kelvin)
# after scoring set weights
# - query the `SYNTHIA_NETUID` dynamically from the chain name of the subnet

# 3/26 TODO:
# - [ ] Make sure to send one question at a time to miner, if we run out of questions,
# iterate through the question list again
# - [ ] Generate new data every `settins.generation_interval`
# (this tells us: after N iterations are finish, generate new data)
# - [ ] make the validation loop run every `settings.iteration_interval` which is defined in seconds (basically time sleep)

# Honza
# - [x] figure out a better prompt
# - [x] save the interaction between a validator and miner to a db
# - [ ] test wandb saving
# - [x] implement set_weights funciton

# Kelvin
# Implement scoring function based on vector difference using embedings

# TODO: make it match ipv6
IP_REGEX = re.compile(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+")


def set_weights(
    score_dict: dict[int, float], netuid: int, client: CommuneClient, key: Keypair
) -> None:
    """Set weights for miners based on their scores.

    The lower the score, the higher the weight.

    Args:
        score_dict (dict[int, float]): A dictionary mapping miner UIDs to their scores.
        netuid (int): The network UID.
        client (CommuneClient): The CommuneX client.
        key (Keypair): The keypair for signing transactions.
    """
    # Create a new dictionary to store the weighted scores
    weighted_scores: dict[int, int] = {}

    # Calculate the sum of all inverted scores
    total_inverted_score = sum(1 - score for score in score_dict.values())

    # Iterate over the items in the score_dict
    for uid, score in score_dict.items():
        # Calculate the normalized weight as an integer
        weight = int((1 - score) / total_inverted_score * 100)

        # Add the weighted score to the new dictionary
        weighted_scores[uid] = weight

    # filter out 0 weights
    weighted_scores = {k: v for k, v in weighted_scores.items() if v != 0}

    uids = list(weighted_scores.keys())
    weights = list(weighted_scores.values())

    return  # delete this line in the future
    client.vote(key=key, uids=uids, weights=weights, netuid=netuid)


def extract_address(string: str):
    """
    Extracts an address from a string.
    """
    return re.search(IP_REGEX, string)


def get_ip_port(modules_adresses: dict[int, str]):
    filtered_addr = {id: extract_address(addr) for id, addr in modules_adresses.items()}
    ip_port = {
        id: x.group(0).split(":") for id, x in filtered_addr.items() if x is not None
    }
    return ip_port


class TextValidator(Module):
    """A class for validating text data using a Synthia network.

    This class provides methods for generating questions and answers, scoring miner
    answers, and validating text data using a Synthia network. It interacts with a
    Communex module client to communicate with the Synthia network.

    Attributes:
        client: A Communex module client instance for communicating with the Synthia
            network.
        settings: A ValidatorSettings instance containing configuration settings for
            the validator.
        input_generator: An InputGenerator instance for generating input data.
        question_prompt: A string containing the prompt for generating questions.
        answer_prompt: A string containing the prompt for generating answers.
        SYNTHIA_NETUID: An integer representing the unique identifier of the Synthia
            network.

    Methods:
        __init__(self, settings: ValidatorSettings): Initializes a new instance of
            the TextValidator class with the specified settings.
        run(self): Runs the text validation process.
        score(self, val_answer: str, miner_answer: str) -> int: Scores a miner's
            answer against the validator's answer.
        extract_address(self, string: str) -> re.Match: Extracts an IP address and
            port from a string.
        get_ip_port(self, addresses: List[str]) -> List[Tuple[str, str]]: Extracts
            IP addresses and ports from a list of strings.
    """

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

    def get_modules(self, client: CommuneClient, netuid: int) -> dict[int, str]:
        """Retrieves all module addresses from the subnet.

        Args:
            client: The CommuneClient instance used to query the subnet.
            netuid: The unique identifier of the subnet.

        Returns:
            A list of module addresses as strings.
        """
        module_addreses = client.query_map_address(netuid)
        return module_addreses

    async def validate_step(self, settings: ValidatorSettings, syntia_netuid: int):
        """Performs a validation step.

        Generates questions based on the provided settings, prompts modules to
        generate answers, and scores the generated answers against the validator's
        own answers.

        Args:
            settings: The validator settings to use for this validation step.
            syntia_netuid: The netuid of the Synthia subnet.
        """
        # create the question : answer generator
        ig = InputGenerator()

        modules_adresses = self.get_modules(self.client, syntia_netuid)
        modules_filtered_address = get_ip_port(modules_adresses)
        breakpoint()
        # == Question generation ==
        question_model = settings.question_model
        q = settings.question_amount
        prompt = question_prompt(t=settings.theme_amount, q=q)
        questions = ig.prompt_question_gpt(
            text=prompt, question_amount=q, model=question_model
        )["Answer"][0]["questions"]
        question_amount = len(questions)

        # == Answer generation ==
        answer_model = settings.answer_model
        prompt_answers = answer_prompt(questions)
        validator_answer = ig.prompt_answer_gpt(
            question_amount, prompt_answers, model=answer_model
        )["Answer"][0]["answers"]

        score_dict: dict[int, float] = {}
        wandb_dict: dict[Any, Any] = {}
        # == Validation loop / Scoring ==
        # TODO: refactor passed questions, answers

        # tuples of questions and answers
        dataset: list[tuple[str, str]] = list(zip(questions, validator_answer))
        dataset_index = 0

        for uid, connection in modules_filtered_address.items():
            module_ip, module_port = connection
            # testing purposes
            module_ip = "127.0.0.1"
            module_port = "8000"

            try:
                client = ModuleClient(module_ip, int(module_port), self.key)
                question, answer = dataset[dataset_index]
                miner_answer = await client.call("generate", {"prompt": question})
            except Exception as e:
                print(f"caught exception {e} on module {module_ip}:{module_port}")
                continue

            weight_score = score(answer, miner_answer)
            # score has to be lower than 1, as one is the worse score
            if weight_score < 1:
                score_dict[uid] = weight_score

            wandb_dict["question"] = question
            wandb_dict["validator_answer"] = answer
            wandb_dict[f"miner_answer_{uid}"] = miner_answer

            _ = set_weights(score_dict, self.netuid, self.client, self.key)

            # increase the dataset index, in a way we don't exceed the lenght of the dataset
            dataset_index = (dataset_index + 1) % len(dataset)

    # TODO :
    # - Migrate from wandb to decentralized database, possibly ipfs, the server
    # has to check for the signature of the data. (This way is used even on S18, but we don't like it)
    def init_wandb(self, settings: ValidatorSettings, keypair: Keypair):
        # key = cast(Ss58Address, keypair.ss58_address)

        uid = 0  # ! place holder, take this out in prod
        # uid = self.client.get_uids(key=key)
        # # Make sure key is registered on the network
        # assert uid is not None, "Key is not registered on the network"

        run_name = f"validator-{uid}"
        settings.run_name = run_name
        settings.uid = uid
        settings.key = cast(Ss58Address, keypair.ss58_address)
        settings.timestamp = time.time()
        # convert settings to dict
        config_dict = settings.model_dump()

        # sign the config, to make sure the validator is registered on our netuid
        signature = sign(keypair, json.dumps(config_dict).encode("utf-8"))

        # convert the signature to a hexadecimal string
        signature_hex = signature.hex()

        # add the signature to the config_dict
        config_dict["signature"] = signature_hex

        # Avoid saving locally
        os.environ["WANDB_MODE"] = "online"

        run = wandb.init(  # type: ignore
            name=run_name,
            project=settings.project_name,
            entity="synthia-subnet",
            config=config_dict,  # Pass config_dict directly, not config
            reinit=True,
        )

        # Log the wandb_dict information to wandb after the run is complete
        run.log(self.wandb_dict)  # type: ignore
        run.finish()  # type: ignore

    def main(self, settings: ValidatorSettings | None = None) -> None:
        if not settings:
            settings = ValidatorSettings()  # type: ignore

        # Storage
        if settings.use_wandb:
            run = self.init_wandb(settings, self.key)
        else:
            run = None

        # Run validation
        self.wandb_dict = {}  # Initialize wandb_dict as an empty dictionary
        asyncio.run(self.validate_step(settings, self.netuid))

        if run:
            run.log(self.wandb_dict)  # type: ignore
            run.finish()  # type: ignore


if __name__ == "__main__":

    KEY_MNEMONIC = (
        "electric suffer nephew rough gentle decline fun body tray account vital clinic"
    )
    validator = TextValidator(
        Keypair.create_from_mnemonic(KEY_MNEMONIC), SYNTHIA_NETUID
    )
    validator.wandb_dict = {}
    validator.init_wandb(ValidatorSettings(), validator.key)  #  type: ignore
    exit()
    scores = {1: 0, 12: 0.5, 3: 0.8, 4: 0.9, 5: 1}
    print(set_weights(scores, SYNTHIA_NETUID, validator.client, validator.key))

    # modules = validator.get_modules(validator.client, validator.get_synthia_netuid())
    # print(modules)
    # print("-------------")
    # modules_filtered_address = get_ip_port(modules)
    # print(modules_filtered_address)
    import asyncio

    setting = ValidatorSettings()
    netuid = validator.get_synthia_netuid()
    x = asyncio.run(validator.validate_step(setting, netuid))
