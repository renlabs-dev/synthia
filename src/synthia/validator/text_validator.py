"""
Module for validating text submissions on the Synthia subnet.

This class represents a validator module that runs on the Synthia subnet. It initializes a Wandb run to log validation data, and provides functions to retrieve metadata about the subnet and modules.
"""

import re
from typing import cast, Any
import time
import os
import json
from functools import partial
import concurrent.futures


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
from .generate_data import InputGenerator
from ..utils import retry
from .similarity import OpenAIEmbedder, OpenAISettings, euclidean_distance, Embedder
from ..miner._config import AnthropicSettings
from ..miner.anthropic import AnthropicModule
from .meta_prompt import get_miner_prompt


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
    scores = sum(score_dict.values())

    # Iterate over the items in the score_dict
    for uid, score in score_dict.items():
        # Calculate the normalized weight as an integer
        weight = int(score / scores * 100)

        # Add the weighted score to the new dictionary
        weighted_scores[uid] = weight

    # filter out 0 weights
    weighted_scores = {k: v for k, v in weighted_scores.items() if v != 0}

    uids = list(weighted_scores.keys())
    weights = list(weighted_scores.values())
    client.vote(key=key, uids=uids, weights=weights, netuid=netuid)


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

    def _get_miner_prediction(
            self, 
            connection: list[str], 
            question: str
        ) -> str | None:
        module_ip, module_port = connection
        client = ModuleClient(module_ip, int(module_port), self.key)
        try:
            miner_answer = asyncio.run(client.call("generate", {"prompt": question}))
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
        return float(normalized_distance) # i hate python's type system

    def _score_miner(
        self, miner_answer: str | None, embbeded_val_answer: list[float]
    ) -> float:
        if not miner_answer:
            return 0
        embedded_miner_answer = self.embedder.get_embedding(miner_answer)
        normalized_distance = self._get_unit_euclid_distance(
            embedded_miner_answer, embbeded_val_answer
        )
        return 1 - normalized_distance

    def _split_val_subject(self, val_answer: str):
        end_of_subject = val_answer.find("\n")
        subject = val_answer[:end_of_subject]
        val_answer = val_answer[end_of_subject + 1 :]
        return subject, val_answer

    def _test_score(self, text_a: str, text_b: str):
        embbeded_a = self.embedder.get_embedding(text_a)
        score = self._score_miner(text_b, embbeded_a)
        sim = fuzz.ratio(text_a, text_b)
        print(f"Score: {score}, similarity: {sim}")

    async def validate_step(
        self, settings: ValidatorSettings, syntia_netuid: int
    ):
        """Performs a validation step.

        Generates questions based on the provided settings, prompts modules to
        generate answers, and scores the generated answers against the validator's
        own answers.

        Args:
            settings: The validator settings to use for this validation step.
            syntia_netuid: The netuid of the Synthia subnet.
        """

        modules_adresses = self.get_modules(self.client, syntia_netuid)
        modules_filtered_address = get_ip_port(modules_adresses)
        response_cache: list[str] = []
        score_dict: dict[int, float] = {}
        wandb_dict: dict[str, str] = {}
        # == Validation loop / Scoring ==

        dataset, criteria, _ = self._get_validation_dataset(settings)
        val_prompt, val_answer = dataset
        subject, val_answer = self._split_val_subject(val_answer)
        miner_prompt = get_miner_prompt(criteria, subject, len(val_answer))
        embedded_val_answer = self.embedder.get_embedding(val_answer)
        
        get_miner_prediction = partial(self._get_miner_prediction, question=miner_prompt)
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            it = executor.map(get_miner_prediction, modules_filtered_address.values())
            miner_answers = [*it]
        for uid, miner_answer in zip(modules_filtered_address.keys(), miner_answers):
            if not miner_answer:
                continue
            score = self._score_miner(
                miner_answer, embedded_val_answer
            )
            for answer in response_cache:
                similarity = fuzz.ratio(answer, miner_answer) # type: ignore
                print(f"similarity: {similarity}")
            response_cache.append(miner_answer)

            time.sleep(0.5)
            # score has to be lower than 1, as one is the best score
            assert score < 1
            score_dict[uid] = score
            wandb_dict["prompt"] = val_prompt
            wandb_dict["validator_answer"] = val_answer
            wandb_dict[f"miner_answer_{uid}"] = miner_answer
            
        _ = set_weights(score_dict, self.netuid, self.client, self.key)
        
        return wandb_dict

    def init_wandb(self, settings: ValidatorSettings, keypair: Keypair) -> Any:
        # TODO :
        # - Migrate from wandb to decentralized database, possibly ipfs, the server
        # has to check for the signature of the data. (This way is used even on S18, but we don't like it)
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

    def validation_loop(self, settings: ValidatorSettings | None = None) -> None:
        if not settings:
            settings = ValidatorSettings()  # type: ignore

        # Storage
        if settings.use_wandb:
            run = self.init_wandb(settings, self.key)
        else:
            run = None

        self.wandb_dict: dict[str, str] = {}  # Initialize wandb_dict as an empty dictionary
        # Run validation
        while True:
            start_time = time.time()
            wandb = asyncio.run(self.validate_step(settings, self.netuid))
            self.wandb_dict.update(wandb)
            if run:
                run.log(self.wandb_dict)  # type: ignore
                run.finish()  # type: ignore
            elapsed = time.time() - start_time
            if elapsed < settings.iteration_interval:
                time.sleep(settings.iteration_interval - elapsed)


if __name__ == "__main__":
    node_url = "wss://testnet-commune-api-node-0.communeai.net"
    client = CommuneClient(node_url)
    SYNTHIA_NETUID = get_synthia_netuid(client)
    print(f"SYNTHIA_NETUID: {SYNTHIA_NETUID}")
    KEY_MNEMONIC = (
        "electric suffer nephew rough gentle decline fun body tray account vital clinic"
    )
    validator = TextValidator(
        Keypair.create_from_mnemonic(KEY_MNEMONIC), SYNTHIA_NETUID, client
    )
    setting = ValidatorSettings()  # type: ignore
    validator.validation_loop(setting)
    # examples = [

    # (
    #     "It's not true at all that Bob understands the embeddings.",
    #     "The embeddings are not comprehended by Bob.",
    #     "SHOULD BE SIMILAR"
    # ),
    # (
    #     "It's not true at all that Bob understands the embeddings.",
    #     "Bob doesn't comprehend the embeddings very well, but it's enough.",
    #     "SHOULDN'T BE VERY SIMILAR"
    # ),
    # (
    #     "James was not right about Bob",
    #     "James did a wrong assessment of Bob's understanding",
    #     "SHOULD BE SIMILAR"
    # ),
    # (
    #     "Commune will surpass Bitcoin", 
    #     "Commune will be worth more than Bitcoin",
    #     "SHOULD BE SIMILAR"
    # ),
    # (
    #     "Im testing this", 
    #     "You have to be very high IQ to understand ricky and morty",
    #     "SHOULDN'T BE SIMILAR"
    # ),
    # (
    #     "I would like to know why the distance decreases when the context changes",
    #     "Why does the distance decreases with context changes?",
    #     "SHOULD BE SIMILAR",
    # ),
    # (
    #     "I would like to know why the distance decreases when the context changes",
    #     "Why does the distance increases with context changes?",
    #     "SHOULDN'T BE SIMILAR",
    # ),
    # ]
    # for a, b, c in examples:
    #     validator._test_score(a, b)
    #     print(c)
    #     print("----------------------")