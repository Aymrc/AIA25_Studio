import os
import json
import numpy as np
from server.config import client, embedding_model

# Global cache to avoid redundant computation
embedding_cache = {}

# Load examples
def load_intent_examples(path="knowledge/intent_examples.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# Embed input text
def get_embedding(text: str) -> np.ndarray:
    if text in embedding_cache:
        return embedding_cache[text]

    response = client.embeddings.create(
        model=embedding_model,
        input=[text.strip()]
    )
    vector = np.array(response.data[0].embedding)
    embedding_cache[text] = vector
    return vector

# Cosine similarity
def cosine_similarity(vec1, vec2):
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

# Pre-cache example embeddings once at startup
def preload_example_embeddings(examples: dict) -> dict:
    precomputed = {}
    for intent, samples in examples.items():
        precomputed[intent] = [get_embedding(s) for s in samples]
    return precomputed

# Intent classification with cached comparisons
def classify_intent_via_embeddings(user_input: str, examples: dict = None, precomputed: dict = None) -> tuple:
    try:
        if examples is None:
            examples = load_intent_examples()
        if precomputed is None:
            precomputed = preload_example_embeddings(examples)

        input_emb = get_embedding(user_input)
        best_intent, best_score = "general_query", -1

        for intent, sample_embeddings in precomputed.items():
            for sample_emb in sample_embeddings:
                score = cosine_similarity(input_emb, sample_emb)
                if score > best_score:
                    best_score, best_intent = score, intent

        print(f"[🔎 EMBEDDING INTENT] → {best_intent} (score={best_score:.4f})")
        return (best_intent, best_score) if best_score > 0.67 else ("general_query", best_score)

    except Exception as e:
        print(f"[❌ EMBEDDING INTENT ERROR] {e}")
        return ("general_query", 0.0)
