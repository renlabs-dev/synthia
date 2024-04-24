from typing import Protocol
from dataclasses import dataclass
from typing import Any

from pydantic_settings import BaseSettings
import openai
import numpy
import polars as pl
import polars_distance
from transformers import pipeline, Pipeline  # type: ignore

from ..utils import timeit


def _do_debug():
    from IPython import embed  # type: ignore

    embed()


examples = [
    (
        "It's not true at all that Bob understands the embeddings.",
        "The embeddings are not comprehended by Bob.",
    ),
    (
        "It's not true at all that Bob understands the embeddings.",
        "Bob doesn't comprehend the embeddings very well, but it's enough.",
    ),
    (
        "James was not right about Bob",
        "James did a wrong assessment of Bob's understanding",
    ),
    ("Commune will surpass Bitcoin", "Commune will be worth more than Bitcoin"),
    ("Im testing this", "You have to be very high IQ to understand ricky and morty"),
    (
        "I would like to know why the distance decreases when the context changes",
        "Why does the distance decreases with context changes?",
    ),
    (
        "I would like to know why the distance decreases when the context changes",
        "Why does the distance increases with context changes?",
    ),
]


class OpenAISettings(BaseSettings):
    api_key: str

    class Config:
        extra = "allow"
        env_prefix = "OPENAI_"
        env_file = "env/config.env"


@dataclass
class EmbeddingModelSpec:
    model_kind: str
    model_name: str

    def to_string(self):
        pass

    def from_string(self):
        pass


class Embedder(Protocol):
    def get_embedding(self, input: str) -> list[float]: ...


class Distancer(Protocol):
    def get_distance(self, input_1: str, input_2: str) -> float: ...


class OpenAIEmbedder(Embedder):
    def __init__(
        self, openai_settings: OpenAISettings, model: str = "text-embedding-3-small"
    ):
        self.openai_settings = openai_settings
        self.model = model
        self.client = openai.OpenAI(api_key=self.openai_settings.api_key)

    def get_embedding(self, input: str):
        response = self.client.embeddings.create(model=self.model, input=input)
        embedding = response.data[0].embedding
        return embedding


class JairiumDistancer(Distancer):
    def __init__(self) -> None:
        import gensim.downloader as gensim_api  # type: ignore

        super().__init__()
        word_vectors = gensim_api.load("glove-wiki-gigaword-100")  # type: ignore
        self.word_vectors = word_vectors

    def get_distance(self, input_1: str, input_2: str) -> float:
        dist: float = self.word_vectors.wmdistance(input_1, input_2)  # type: ignore
        return dist  # type: ignore


def do_classify(classifier: Pipeline, text: str) -> str | None:
    """Classify the given text using the provided classifier.

    Args:
        classifier: The classifier pipeline to use for classification.
        text: The text to classify.

    Returns:
        The original text if it is classified as "clean", otherwise None.
    """
    result: Any = classifier(text)
    if result[0]["label"] == "clean":
        return text


def get_classifier() -> Pipeline:
    """Get the classifier pipeline for gibberish detection.

    Returns:
        Pipeline: The classifier pipeline using the selected model.
    """
    selected_model = "madhurjindal/autonlp-Gibberish-Detector-492513457"
    classifier = pipeline("text-classification", model=selected_model)
    return classifier


def euclidean_distance(list_1: list[float], list_2: list[float]) -> float:
    vec_1 = numpy.array(list_1)
    vec_2 = numpy.array(list_2)
    norm = numpy.linalg.norm(vec_1 - vec_2)
    return float(norm)


def main(openai_settings: OpenAISettings):
    import numpy as np

    openai_embedder = OpenAIEmbedder(openai_settings)
    distancer = JairiumDistancer()
    ai_dist_list = []
    dist_dist_list = []
    classider = get_classifier()
    for example_items in examples:
        # Before validating with embedder,
        # make sure the text is not classified as gibberish (nonsense).
        is_classified = list(map(lambda x: do_classify(classider, x), example_items))
        # if it is, skip it
        if None in is_classified:
            continue

        embeddings = list(map(openai_embedder.get_embedding, example_items))
        embedding_a, embedding_b = embeddings
        ai_dist = euclidean_distance(embedding_a, embedding_b)
        ai_dist_list.append(ai_dist)
        # print(f"  AI_DIST: {ai_dist:.4f}")

        example_a, example_b = example_items
        dist = distancer.get_distance(example_a, example_b)
        dist_dist_list.append(dist)
        # print(f"DIST_DIST: {dist:.4f}")

    print(f"AI_DIST: {np.array(ai_dist_list)/sum(ai_dist_list)}")
    print(f"DIST_DIST: {np.array(dist_dist_list)/sum(dist_dist_list)}")

    # for example_items in examples:
    # embedding_a, embedding_b = embeddings
    # print(embedding_a, embedding_b)
    # polars_distance.


if __name__ == "__main__":
    openai_settings = OpenAISettings()  # type: ignore
    main(openai_settings)
