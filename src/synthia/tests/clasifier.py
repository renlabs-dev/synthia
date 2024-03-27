from transformers import pipeline

selected_model = "madhurjindal/autonlp-Gibberish-Detector-492513457"
classifier = pipeline("text-classification", model=selected_model)

result = classifier("I love Machine Learning!")
assert result[0]["label"] == "clean", "The text should be classified as clean."