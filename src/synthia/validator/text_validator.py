import asyncio
import concurrent.futures
import re
import time
from functools import partial

import numpy as np
import requests
from communex.client import CommuneClient  # type: ignore
from communex.module.client import ModuleClient  # type: ignore
from communex.module.module import Module  # type: ignore
from fuzzywuzzy import fuzz  # type: ignore
from substrateinterface import Keypair  # type: ignore

from ..miner._config import AnthropicSettings
from ..miner.anthropic import AnthropicModule
from ..utils import retry
from ._config import ValidatorSettings
from .generate_data import InputGenerator
from .meta_prompt import get_miner_prompt, Criteria
from .similarity import (Embedder, OpenAIEmbedder, OpenAISettings,
                         euclidean_distance)

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
        self.upload_client = ModuleClient("0.0.0.0", 9001, self.key)


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
        claude_settings = AnthropicSettings()  # type: ignore
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

    def _get_miner_prediction(self, connection: list[str], question: str) -> tuple[str | None, str | None]:
        module_ip, module_port = connection
        client = ModuleClient(module_ip, int(module_port), self.key)
        try:
            miner_answer = asyncio.run(client.call("generate", {"prompt": question}, timeout=60))
            miner_answer = miner_answer["answer"]

            miner_model = asyncio.run(client.call("get_model", {}))
            miner_model = miner_model["model"]
        except Exception as e:
            print(f"Miner {module_ip}:{module_port} failed to generate an answer")
            print(e)
            miner_answer = None
            miner_model = None
        return miner_answer, miner_model

    def _get_unit_euclid_distance(
        self, embedded_miner_answer: list[float], embbeded_val_answer: list[float]
    ):
        distance = euclidean_distance(embedded_miner_answer, embbeded_val_answer)
        miner_norm = np.linalg.norm(embedded_miner_answer)
        val_norm = np.linalg.norm(embbeded_val_answer)
        normalized_distance = distance / (miner_norm + val_norm)
        return float(normalized_distance)  # i hate python's type system

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
        sim = fuzz.ratio(text_a, text_b)  # type: ignore
        print(f"Score: {score}, similarity: {sim}")

    def _to_hf_data(
            self, 
            criteria: Criteria, 
            subject: str,
            miner_answer: str,
            score: float,
            miner_model: str
            ):
        hf_data: dict[str, str] = {}
        hf_data["field"] = criteria.field
        hf_data["subject"] = subject
        hf_data["target"] = criteria.target_audience
        hf_data["detail"] = criteria.detail
        hf_data["abstraction"] = criteria.abstraction
        hf_data[f"explanation"] = miner_answer
        hf_data["score"] = str(score)
        hf_data["model"] = miner_model
        return hf_data
    

    async def validate_step(self, settings: ValidatorSettings, syntia_netuid: int):
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
        hf_data_list: list[dict[str, str]] = []
        # == Validation loop / Scoring ==

        dataset, criteria, _ = self._get_validation_dataset(settings)
        _, val_answer = dataset
        subject, val_answer = self._split_val_subject(val_answer)
        miner_prompt = get_miner_prompt(criteria, subject, len(val_answer))
        embedded_val_answer = self.embedder.get_embedding(val_answer)

        get_miner_prediction = partial(
            self._get_miner_prediction, question=miner_prompt
        )
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            it = executor.map(get_miner_prediction, modules_filtered_address.values())
            miner_answers = [*it]
        for uid, miner_response in zip(modules_filtered_address.keys(), miner_answers):
            miner_answer, miner_model = miner_response
            if not miner_answer or not miner_model:
                continue
            score = self._score_miner(miner_answer, embedded_val_answer)
            for answer in response_cache:
                similarity = fuzz.ratio(answer, miner_answer)  # type: ignore
                print(f"similarity: {similarity}")
            response_cache.append(miner_answer)

            time.sleep(0.5)
            # score has to be lower or eq to 1, as one is the best score
            assert score <= 1
            score_dict[uid] = score
            hf_data = self._to_hf_data(
                criteria, 
                subject, 
                miner_answer, 
                score, 
                miner_model
            )
            hf_data_list.append(hf_data)
        _ = set_weights(score_dict, self.netuid, self.client, self.key)

        return hf_data_list

    def upload_data(self, data: list[dict[str, str]]) -> None:
        """Uploads the validation data.

        Args:
            data: A dictionary containing the validation data to upload.
        """

        # add a timestamp
        #data["Timestamp"] = iso_timestamp_now()

        #serealized_data = serialize(data)
       
        #signature = sign(self.key, serealized_data)

        # sign the whole thing, so we make sure valid node is uploading
        #data["Signature"] = signature.hex()
        #data["Key"] = self.key.public_key.hex()
        #data["Crypto"] = str(self.key.crypto_type)

        # now upload the data
        max_attempts = 3
        attempt = 1
        upload_dict = {"data": data}
        while attempt <= max_attempts:
            try:
                response = asyncio.run(self.upload_client.call("upload_to_hugging_face", upload_dict))
                break
            except requests.exceptions.RequestException as e:
                print(f"Upload attempt {attempt} failed: {e}")
                attempt += 1

    def validation_loop(self, settings: ValidatorSettings | None = None) -> None:
        if not settings:
            settings = ValidatorSettings()  # type: ignore

        # Run validation
        while True:
            start_time = time.time()
            db = asyncio.run(self.validate_step(settings, self.netuid))
            self.upload_data(db)

            elapsed = time.time() - start_time
            if elapsed < settings.iteration_interval:
                sleep_time = settings.iteration_interval - elapsed
                print(f"Sleeping for {sleep_time}")
                time.sleep(sleep_time)


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
    # question = "You are a top expert in the field of Applied Cryptography with deep knowledge on the subject ['\"Homomorphic Encryption\"']. Provide an insightful semantically dense explanation of the ['Homomorphic Encryption'] that will be read by a ['enthusiast']. Your goal is their comprehension of the explanation, according to their background expertise. Follow a ['intense'] level of abstraction and a ['high'] level of detail. Target a length of approximately [2431] words."
    # predictione = validator._get_miner_prediction(['localhost', '8000'], question=question)
    # print(predictione)
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
