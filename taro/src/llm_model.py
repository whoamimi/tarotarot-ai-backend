# Model ID is set to default
import ollama

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

LLM_MODEL_ID = "hf.co/bartowski/Llama-3.2-3B-Instruct-GGUF:Q5_K_S"

def setup_client(host_url: str = "http://localhost:11434"):
    try:
        client = ollama.Client(host_url)
        N = len(client.list().models)
        if N > 0 and LLM_MODEL_ID in tuple(m.model for m in client.list().models):
            return client
        raise ValueError("No downloaded models for ollama to load. Please download.")
    except ConnectionError as e:
        raise e
    except Exception as e:
        raise ValueError(f"Unexpected Error: {e}")

def send_prompt(client: ollama.Client, messages: list[dict], options: ollama._types.Options): # type: ignore
    """Load Ollama for chatting based on system/user prompt."""

    output = client.chat(model=LLM_MODEL_ID, messages=messages, stream=False, options=options)

    if not isinstance(output, (ollama.GenerateResponse, ollama.ChatResponse)):
        raise RuntimeError(f"Unexpected response type from Ollama: {type(output)}")

    # return output.message or `output.message['content']` if you want just the reply text
    print(f'Response from Ollama Client: {output}')
    return output.message['content']