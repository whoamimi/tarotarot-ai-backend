"""
utils/settings.py

"""

from dataclasses import dataclass, field

@dataclass(frozen=True)
class AgentServer:
    ollama: str = field(init=False, default_factory=os.getenv("LLM_SERVER_URL", "localhost:11413"))

@dataclass(frozen=True)
class DataBaseConfig:
    session: str = "session"
    model: str = "llm-prompt-chain"

@dataclass
class Setting:
    server: AgentServer = field(init=False)
    db: DataBaseConfig = field(init=False, default_factory=DataBaseConfig)
    llm_id: str = field(init=False, default_factory=os.getenv('LLM_ID', "hf.co/bartowski/Llama-3.2-3B-Instruct-GGUF:Q5_K_S"))

setting = Setting()
