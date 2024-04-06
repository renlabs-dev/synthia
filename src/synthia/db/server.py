import requests

payload = {
    "field": "abstract models of computation",
    "subject": "expressiveness of symmetric interaction combinators compared to turing machines",
    "target": "graduate_student",
    "detail": "high",
    "abstraction": "moderate",
    "explanation": "so basically",
    "score": "0.782",
    "signature": "x",
    "timestamp": "2022-01-01T00:00:00Z",
}

response = requests.post("http://localhost:8000/upload/", json=payload)
print(response.json())
