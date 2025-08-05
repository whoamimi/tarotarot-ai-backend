"""
src/llm_model.py

"""

import os
import ollama
from utils.woodpecker import BadOllamaSetup, setup_logger

logger = setup_logger(__name__)
# Initial Decoder Configurations
OPTIONS = ollama._types.Options( # type: ignore
    # runtime options
    num_keep=5,
    seed=42,
    num_predict=300,
    temperature=0.8,
    top_k=50,
    top_p=0.9,
    repeat_last_n=33,
    repeat_penalty=1.1,
    presence_penalty=1.5,
    frequency_penalty=0.5,
    # loadtime options
    num_ctx=2048,
)

LLM_MODEL_ID = os.getenv('LLM_ID', "hf.co/bartowski/Llama-3.2-3B-Instruct-GGUF:Q5_K_S")
# "http://localhost:11434"

def setup_client(host_url: str = "http://minis_ollama:11434"):
    """ Check and setups client connection to Ollama container from docker-compose. """

    client = ollama.Client(host_url)
    N = len(client.list().models)
    if N > 0 and LLM_MODEL_ID in tuple(m.model for m in client.list().models):
        return client
    raise BadOllamaSetup
