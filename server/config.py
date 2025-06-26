import os
import sys
import random
from openai import OpenAI as OpenAIClient

# Add project root to import path (if needed elsewhere)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mode: only "local" is supported
mode = "local"

# Local LM Studio client
local_client = OpenAIClient(
    base_url="http://127.0.0.1:1234/v1", 
    api_key="lm_studio"  # LM Studio accepts any string
)

# Default local model settings
local_embedding_model = "text-embedding-nomic-embed-text-v1.5"
llama3 = [
    {
        "model": "llama-3-groq-8b-tool-use",  # Model1
        # "model": "Qwen3 4B",  # Model2
        # "model": "nombre",  # Model3 to be defined
        "api_key": "any",  # Placeholder, not used by LM Studio
        "api_type": "openai",
        "base_url": "http://127.0.0.1:1234",
        "cache_seed": random.randint(0, 100000),
    }
]

# Runtime model selector
def api_mode(mode):
    if mode == "local":
        client = local_client
        completion_model = llama3[0]["model"]
        embedding_model = local_embedding_model
        return client, completion_model, embedding_model
    else:
        raise ValueError("Only 'local' mode is supported in this configuration.")

# Initialize global settings
client, completion_model, embedding_model = api_mode(mode)
