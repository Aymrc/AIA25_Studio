import os
import json
import numpy as np
from server.config import client, embedding_model

# Load examples from local intent_examples.json
def load_intent_examples(path="knowledge/intent_examples.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# Compute vector embedding for any input text
def get_embedding(text: str) -> np.ndarray:
    response = client.embeddings.create(
        model=embedding_model,
        input=[text.strip()]
    )
    return np.array(response.data[0].embedding)

# Cosine similarity between two vectors
def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

# Classify intent using embedding similarity
def classify_intent_via_embeddings(user_input: str, examples: dict = None) -> tuple:
    try:
        if examples is None:
            examples = load_intent_examples()

        input_emb = get_embedding(user_input)
        best_intent, best_score = "general_query", -1

        for intent, samples in examples.items():
            for sample in samples:
                score = cosine_similarity(input_emb, get_embedding(sample))
                if score > best_score:
                    best_score, best_intent = score, intent

        return (best_intent, best_score) if best_score > 0.7 else ("general_query", best_score)

    except Exception as e:
        print(f"[❌ EMBEDDING INTENT ERROR] {e}")
        return ("general_query", 0.0)
