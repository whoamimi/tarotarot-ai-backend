"""
utils/settings.py

"""

from dataclasses import dataclass, field

@dataclass(frozen=True)
class AgentServer:
    ollama: os.getenv("LLM_SERVER_URL", "localhost:11413")

@dataclass(frozen=True)
class DataBaseConfig:
    session: str = "session"
    model: str = "llm-prompt-chain"

@dataclass
class Setting:
    server: AgentServer = field(init=False)


setting = Setting()
