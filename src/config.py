import os

from dotenv import load_dotenv

load_dotenv()

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5")
OLLAMA_TEMPERATURE = float(os.getenv("OLLAMA_TEMPERATURE", "0"))
OLLAMA_NUM_CTX = int(os.getenv("OLLAMA_NUM_CTX", "8192"))

POWERSHELL_TIMEOUT_SECONDS = int(os.getenv("POWERSHELL_TIMEOUT_SECONDS", "30"))

DEFAULT_EVENT_LOG_MAX = int(os.getenv("DEFAULT_EVENT_LOG_MAX", "20"))
DEFAULT_TOP_PROCESSES = int(os.getenv("DEFAULT_TOP_PROCESSES", "10"))
DEFAULT_OUTGOING_CONNECTIONS_TOP_N = int(os.getenv("DEFAULT_OUTGOING_CONNECTIONS_TOP_N", "15"))

DEFAULT_AGENT_QUESTION = os.getenv(
    "DEFAULT_AGENT_QUESTION",
    "Check my Windows system for anomalies and summarize what you find.",
)

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
