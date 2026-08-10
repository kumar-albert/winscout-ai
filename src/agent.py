import time

from langchain_ollama import ChatOllama
from langgraph.prebuilt import create_react_agent

from src.config import DEFAULT_AGENT_QUESTION, OLLAMA_MODEL, OLLAMA_NUM_CTX, OLLAMA_TEMPERATURE
from src.logger import get_logger
from src.tools import (
    get_windows_defender_status,
    get_windows_disk_usage,
    get_windows_event_log,
    get_windows_outgoing_connections,
    get_windows_resource_usage,
    get_windows_stopped_services,
    get_windows_top_processes,
)

logger = get_logger(__name__)

TOOLS = [
    get_windows_event_log,
    get_windows_resource_usage,
    get_windows_disk_usage,
    get_windows_top_processes,
    get_windows_stopped_services,
    get_windows_defender_status,
    get_windows_outgoing_connections,
]

SYSTEM_PROMPT = (
    "You are a Windows system health analyst. Use your tools to inspect the System, "
    "Application, and Security event logs, current CPU/memory usage, disk free space, "
    "top resource-consuming processes, services that should be running but aren't, "
    "Windows Defender status, and outgoing network connections. "
    "Base your findings ONLY on the data actually returned by the tool calls in this "
    "conversation -- never invent event IDs, messages, providers, process names, IP "
    "addresses, or numbers. If a tool call returns an empty list, say that check found "
    "nothing notable. "
    "Flag anomalies: unusual errors/warnings, high CPU/memory usage, low disk free "
    "space, auto-start services that are stopped, Defender/real-time-protection "
    "disabled, or a process holding an unusually large number of connections to one "
    "remote address/port. Group findings by category and severity, call out repeated "
    "events, and end with a short overall health verdict."
)


def build_agent():
    logger.info(
        "Building ReAct agent (model=%s, temperature=%s, num_ctx=%s, tools=%d)",
        OLLAMA_MODEL,
        OLLAMA_TEMPERATURE,
        OLLAMA_NUM_CTX,
        len(TOOLS),
    )
    llm = ChatOllama(model=OLLAMA_MODEL, temperature=OLLAMA_TEMPERATURE, num_ctx=OLLAMA_NUM_CTX)
    return create_react_agent(llm, tools=TOOLS, prompt=SYSTEM_PROMPT)


def run_agent(question: str = DEFAULT_AGENT_QUESTION) -> str:
    logger.info("Agent run started. Question: %s", question)
    started_at = time.monotonic()

    agent = build_agent()
    result = agent.invoke({"messages": [{"role": "user", "content": question}]})
    answer = result["messages"][-1].content

    tool_calls = sum(1 for m in result["messages"] if getattr(m, "tool_calls", None))
    elapsed_s = round(time.monotonic() - started_at, 1)
    logger.info(
        "Agent run finished in %.1fs (%d message(s), %d tool-calling step(s))",
        elapsed_s,
        len(result["messages"]),
        tool_calls,
    )
    return answer
