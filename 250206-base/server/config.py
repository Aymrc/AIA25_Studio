import sys
import os
import random
from openai import OpenAI as OpenAIClient
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# from server.keys import OPENAI_API_KEY

# Mode
mode = "local" #"openai"  or "openai" or "cloudflare"

# API
local_client = OpenAIClient(base_url="http://localhost:1234/v1", api_key="lm_studio")
# openai_client = OpenAIClient(api_key=OPENAI_API_KEY)
#cloudflare_client = OpenAI(base_url = f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/ai/v1", api_key = CLOUDFLARE_API_KEY)

# Embedding Models
local_embedding_model = "text-embedding-nomic-embed-text-v1.5"
#cloudflare_embedding_model = "@cf/baai/bge-base-en-v1.5"
# openai_embedding_model = "text-embedding-3-small"

# Notice how this model is not running locally. It uses an OpenAI key.
# gpt4o = [
#         {
#             "model": "gpt-4o",
#             "api_key": OPENAI_API_KEY,
#             "cache_seed": random.randint(0, 100000),
#         }
# ]

# Notice how this model is running locally. Uses local server with LMStudio
llama3 = [
        {
            "model": "llama-3.1-tulu-3-8b", #change this to point to a new model
            'api_key': 'any string here is fine',
            'api_type': 'openai',
            'base_url': "http://127.0.0.1:1234",
            "cache_seed": random.randint(0, 100000),
        }
]

# Notice how this model is running locally. Uses local server with LMStudio
# llava_llama = [
#         {
#             "model": "llava-llama-3-8b-v1_1-imat", #change this to point to a new model
#             'api_key': OPENAI_API_KEY,
#             'api_type': 'openai',
#             'base_url': "http://127.0.0.1:1234",
#             "cache_seed": random.randint(0, 100000),
#         }
# ]


# qwen3_8b = [
#         {
#             "model": "qwen3-8b", #change this to point to a new model
#             'api_key': 'any string here is fine',
#             'api_type': 'openai',
#             'base_url': "http://127.0.0.1:1234",
#             "cache_seed": random.randint(0, 100000),
#         }
# ]

# This is a cloudflare model
#cloudflare_model = "@hf/nousresearch/hermes-2-pro-mistral-7b"

# Define what models to use according to chosen "mode"
def api_mode (mode):
    if mode == "local":
        client = local_client
        completion_model = llama3[0]['model']
        embedding_model = local_embedding_model
        return client, completion_model, embedding_model
    
    # if mode == "cloudflare":
    #     client = cloudflare_client
    #     completion_model = cloudflare_model
    #     embedding_model = cloudflare_embedding_model
    #     return client, completion_model, embedding_model
    
    # elif mode == "openai":
    #     client = openai_client
    #     completion_model = gpt4o
    #     completion_model = completion_model[0]['model']
    #     embedding_model = openai_embedding_model

        return client, completion_model, embedding_model
    else:
        raise ValueError("Please specify if you want to run local or openai models")

client, completion_model, embedding_model = api_mode(mode)