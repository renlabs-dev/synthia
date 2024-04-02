import json
from typing import cast, Any

from .meta_prompt import explanation_prompt
from ..miner.BaseLLM import BaseLLM

class InputGenerator:
    def __init__(self, llm: BaseLLM) -> None:
        self.llm = llm

    def gen_explanation(
        self,
    ):
        system_prompt = (
            "You are a supreme polymath renowned for your ability to explain"
            "complex concepts effectively to any audience from laypeople"
            "to fellow top experts. "
            "By principle, you always ensure factual accuracy."
            "You are master at adapting your explanation strategy as needed" 
            "based on the topic and target audience, using a wide array of"
            "tools such as examples, analogies and metaphors whenever and"
            "only when appropriate. Your goal is their comprehension of the"
            "explanation, according to their background expertise."
            "You always structure your explanations coherently and express"
            "yourself clear and concisely, crystallizing thoughts and"
            "key concepts. You only respond with the explanations themselves," 
            "eliminating redundant conversational additions."
            f"Try to keep your answer below {self.llm.max_tokens} tokens"
            )

        user_prompt, criteria = explanation_prompt()
        val_answer = self.llm.prompt(
            user_prompt=user_prompt, 
            system_prompt=system_prompt
            )
        match val_answer:
            case None, explanation:
                raise RuntimeError(f"Failed to generate explanation: {explanation}")
            case answer, _:
                return answer, user_prompt, criteria


if __name__ == "__main__":
    ig = InputGenerator()
    p = 5
    prompt, _ = explanation_prompt(p)
    response = ig.prompt_explanation_claude(ig.client, prompt, p)
    breakpoint()
    exit()
    prompt_questions = explanation_prompt(t=3, exp=p)
    questions: list[str] = cast(
        list[str], ig.prompt_question_gpt(prompt_questions, p)["Answer"][0]["questions"]
    )
    question_amount = len(questions)
    prompt_answers = answer_prompt(questions)
    answers = ig.prompt_answer_gpt(question_amount, prompt_answers)["Answer"][0][
        "answers"
    ]
    breakpoint()
    # question_list = [
    #     "What is RDF (Resource Description Framework) used for in the context of web development?",
    #     "Can you explain the basic structure of an RDF statement?",
    #     "How are ontologies used in the field of artificial intelligence?",
    #     "What is the role of genetic algorithms in the field of evolutionary computation?",
    #     "How do RDF triples differ from traditional data models?",
    #     "Why is it important to define ontologies when building intelligent systems?",
    #     "In genetic algorithms, what is the purpose of the crossover operation?",
    #     "How does RDF support interoperability on the web?",
    #     "What are some popular ontology languages used for developing ontologies?",
    #     "What are the key components of a genetic algorithm?",
    #     "How do you represent knowledge in RDF?",
    #     "What are some challenges associated with designing and maintaining ontologies?",
    #     "Why are genetic algorithms well-suited for optimization problems?",
    #     "How can ontologies be leveraged for semantic web applications?",
    #     "What role does mutation play in the genetic algorithm process?",
    #     "How does RDF support data integration across different systems?",
    #     "What are some real-world applications of genetic algorithms?",
    #     "How can ontologies facilitate natural language processing tasks?",
    #     "In what ways can genetic algorithms be personalized or customized for specific problem domains?",
    #     "What are some common tools and frameworks used for working with RDF data?",
    # ]
