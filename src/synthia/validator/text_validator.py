"""
Module for validating text submissions on the Synthia subnet.

This class represents a validator module that runs on the Synthia subnet. It initializes a Wandb run to log validation data, and provides functions to retrieve metadata about the subnet and modules.
"""

import re
from typing import cast, Any, Sequence
import time
import os
import json
2

# once we register the synthia subnet, we will update this value


import numpy as np
import wandb
from communex.module.module import Module  # type: ignore
from communex.client import CommuneClient  # type: ignore
from substrateinterface import Keypair  # type: ignore
from communex.module._signer import sign  # type: ignore
from communex.module.client import ModuleClient  # type: ignore
from communex.compat.types import Ss58Address  # type: ignore
import asyncio
from fuzzywuzzy import fuzz



from ._config import ValidatorSettings
from .generate_data import InputGenerator, explanation_prompt
from ..utils import retry
from .similarity import OpenAIEmbedder, OpenAISettings, euclidean_distance, Embedder
from ..miner._config import AnthropicSettings
from ..miner.anthropic import AnthropicModule
from .meta_prompt import get_miner_prompt


def score(val_answer: str, miner_answer: str) -> float:
    import random

    return float(random.randint(0, 1))


# TODO:
# Jairo
# - [x] implement retry mechanism on question answer generation
# - [x] make sure miner instructions are the same as answer generation of validator. WIth the same system instructions and tempreature
# - [ ]implement the main validation loop -> get question, get answer, loop through miners, ...  (without validation that is done by kelvin)
# after scoring set weights
#  [x] - query the `SYNTHIA_NETUID` dynamically from the chain name of the subnet

# 3/26 TODO:
# - [x] Make sure to send one question at a time to miner, if we run out of questions,
# iterate through the question list again
# - [ ] Generate new data every `settins.generation_interval`
# (this tells us: after N iterations are finish, generate new data)
# - [ ] make the validation loop run every `settings.iteration_interval` which is defined in seconds (basically time sleep)

# Honza
# - [ ] focus only on claude in the validation
# - [x] figure out a better prompt
# - [x] save the interaction between a validator and miner to a db
# - [ ] test wandb saving
# - [x] implement set_weights funciton

# Kelvin
# -[ ] Implement scoring function based on vector difference using embedings

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

    # client.vote(key=key, uids=uids, weights=weights, netuid=netuid)
    return  # delete this line in the future


def extract_address(string: str):
    """
    Extracts an address from a string.
    """
    return re.search(IP_REGEX, string)


def get_synthia_netuid(clinet: CommuneClient, subnet_name: str = "synthia"):
    """
    Retrieves the network UID of the Synthia subnet.

    Args:
        client (CommuneClient): The CommuneX client.
        subnet_name (str, optional): The name of the Synthia subnet. Defaults to "synthia".

    Returns:
        int: The network UID of the Synthia subnet.
    """

    subnets = clinet.query_map_subnet_names()
    for netuid, name in subnets.items():
        if name == subnet_name:
            return netuid
    raise ValueError(f"Subnet {subnet_name} not found")


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

    def __init__(
        self,
        key: Keypair,
        netuid: int,
        client: CommuneClient,
        embedder: Embedder | None = None,
    ) -> None:
        super().__init__()
        self.client = client
        self.key = key
        self.netuid = netuid
        if not embedder:
            embedder = OpenAIEmbedder(OpenAISettings())  # type: ignore
        self.embedder = embedder
        self.val_model = "claude-3-opus-20240229"

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

    def _get_validation_dataset(self, settings: ValidatorSettings):
        claude_settings = AnthropicSettings() # type: ignore
        claude_settings.temperature = settings.temperature
        claude_settings.max_tokens = settings.max_tokens
        claude_settings.model = self.val_model
        claude = AnthropicModule(claude_settings)
        ig = InputGenerator(claude)

        retrier = retry(4, [Exception])
        generate_explanations = retrier(ig.gen_explanation)

        explanations, prompt, criteria = generate_explanations()

        dataset: tuple[str, str] = (prompt, explanations)
        questions_age = time.time()
        return dataset, criteria, questions_age

    async def _get_miner_prediction(self, connection: list[str], question: str):
        module_ip, module_port = connection
        client = ModuleClient(module_ip, int(module_port), self.key)
        try:
            miner_answer = await client.call("generate", {"prompt": question})
            miner_answer = miner_answer['answer']
        except Exception as e:
            print(f"Miner {module_ip}:{module_port} failed to generate an answer")
            print(e)
            miner_answer = None
        return miner_answer

    def _get_unit_euclid_distance(
        self, embedded_miner_answer: list[float], embbeded_val_answer: list[float]
    ):
        distance = euclidean_distance(embedded_miner_answer, embbeded_val_answer)
        miner_norm = np.linalg.norm(embedded_miner_answer)
        val_norm = np.linalg.norm(embbeded_val_answer)
        normalized_distance = distance / (miner_norm + val_norm)
        return normalized_distance

    async def _score_miner(
        self, miner_answer: str | None, embbeded_val_answer: list[float]
    ):
        if not miner_answer:
            return 0
        embedded_miner_answer = self.embedder.get_embedding(miner_answer)
        normalized_distance = self._get_unit_euclid_distance(
            embedded_miner_answer, embbeded_val_answer
        )
        return 1 - normalized_distance

      
    async def validate_step(
        self, settings: ValidatorSettings, syntia_netuid: int
    ) -> None:
        """Performs a validation step.

        Generates questions based on the provided settings, prompts modules to
        generate answers, and scores the generated answers against the validator's
        own answers.

        Args:
            settings: The validator settings to use for this validation step.
            syntia_netuid: The netuid of the Synthia subnet.
        """
        # create the question : answer generator

        # while True
        modules_adresses = self.get_modules(self.client, syntia_netuid)
        modules_filtered_address = get_ip_port(modules_adresses)
        response_cache: list[str] = []
        score_dict: dict[int, float] = {}
        wandb_dict: dict[Any, Any] = {}
        # == Validation loop / Scoring ==
        # TODO: refactor passed questions, answers

        # tuples of questions and answers

        while True:

            dataset, criteria, _ = self._get_validation_dataset(settings)
            val_question, val_answer = dataset
            end_of_subject = val_answer.find("\n")
            subject = val_answer[:end_of_subject]
            val_answer = val_answer[end_of_subject + 1 :]
            miner_prompt = get_miner_prompt(criteria, subject, len(val_answer))
            embedded_val_answer = self.embedder.get_embedding(val_answer)
            for uid, connection in modules_filtered_address.items():
                miner_answer = await self._get_miner_prediction(connection, miner_prompt)
                score = await self._score_miner(
                    miner_answer, embedded_val_answer
                )
                breakpoint()
                for answer in response_cache:
                    similarity = fuzz.ratio(answer, miner_answer)
                    print(f"similarity: {similarity}")
                response_cache.append(miner_answer)

                time.sleep(1)
                continue
                # score has to be lower than 1, as one is the worse score
                assert score < 1
                score_dict[uid] = score

                wandb_dict["question"] = val_question
                wandb_dict["validator_answer"] = val_answer
                wandb_dict[f"miner_answer_{uid}"] = miner_answer

                # _ = set_weights(score_dict, self.netuid, self.client, self.key)

                # increase the dataset index, in a way we don't exceed the lenght of the dataset

        _ = set_weights(score_dict, self.netuid, self.client, self.key)

    # TODO :
    # - Migrate from wandb to decentralized database, possibly ipfs, the server
    # has to check for the signature of the data. (This way is used even on S18, but we don't like it)
    def init_wandb(self, settings: ValidatorSettings, keypair: Keypair) -> Any:
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

        return run

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
    node_url = "wss://testnet-commune-api-node-0.communeai.net"
    client = CommuneClient(node_url)
    SYNTHIA_NETUID = get_synthia_netuid(client)
    KEY_MNEMONIC = (
        "electric suffer nephew rough gentle decline fun body tray account vital clinic"
    )
    validator = TextValidator(
        Keypair.create_from_mnemonic(KEY_MNEMONIC), SYNTHIA_NETUID, client
    )
    setting = ValidatorSettings()  # type: ignore

    # validator.wandb_dict = {}
    # validator.init_wandb(ValidatorSettings(), validator.key)  #  type: ignore
    # exit()
    # scores = {1: 0, 12: 0.5, 3: 0.8, 4: 0.9, 5: 1}
    # print(set_weights(scores, SYNTHIA_NETUID, validator.client, validator.key))

    #print(get_synthia_netuid(validator.client))
    import asyncio

    x = asyncio.run(validator.validate_step(setting, SYNTHIA_NETUID))
    exit()
    validator.wandb_dict = {}
    validator.init_wandb(ValidatorSettings(), validator.key)  #  type: ignore
    scores = {1: 0, 12: 0.5, 3: 0.8, 4: 0.9, 5: 1}
    print(set_weights(scores, SYNTHIA_NETUID, validator.client, validator.key))

    # modules = validator.get_modules(validator.client, validator.get_synthia_netuid())
    # print(modules)
    # print("-------------")
    # modules_filtered_address = get_ip_port(modules)
    # print(modules_filtered_address)
