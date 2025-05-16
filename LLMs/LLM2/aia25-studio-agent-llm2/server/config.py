import os
import sys
import random
from openai import OpenAI as OpenAIClient

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from server.keys import OPENAI_API_KEY

# Select mode: "local" or "openai"
mode = "local"

# Clients
local_client = OpenAIClient(base_url="http://localhost:1234/v1", api_key="lm_studio")
openai_client = OpenAIClient(api_key=OPENAI_API_KEY)

# Embedding Models
local_embedding_model = "text-embedding-nomic-embed-text-v1.5"
openai_embedding_model = "text-embedding-3-small"

# Local LLaMA 3.1 model (this is the one you want)
llama3 = [
    {
        "model": "llama-3.1-tulu-3.1-8b",
        "api_key": "lm_studio",
        "base_url": "http://127.0.0.1:1234",
        "cache_seed": random.randint(0, 100000),
    }
]

# OpenAI GPT-4o fallback
gpt4o = [
    {
        "model": "gpt-4o",
        "api_key": OPENAI_API_KEY,
        "cache_seed": random.randint(0, 100000),
    }
]

# Model selection logic
def api_mode(selected_mode):
    if selected_mode == "local":
        client = local_client
        completion_model = llama3[0]['model']
        embedding_model = local_embedding_model
        return client, completion_model, embedding_model

    elif selected_mode == "openai":
        client = openai_client
        completion_model = gpt4o[0]['model']
        embedding_model = openai_embedding_model
        return client, completion_model, embedding_model

    else:
        raise ValueError("Invalid mode. Use 'local' or 'openai'.")

# Initialize
client, completion_model, embedding_model = api_mode(mode)
