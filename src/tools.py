import functools
import time

from langchain_core.tools import tool

from src.config import (
    DEFAULT_EVENT_LOG_MAX,
    DEFAULT_OUTGOING_CONNECTIONS_TOP_N,
    DEFAULT_TOP_PROCESSES,
)
from src.logger import get_logger
from src.windows_event_log import fetch_events
from src.windows_system import (
    get_defender_status,
    get_disk_usage,
    get_outgoing_connection_summary,
    get_resource_usage,
    get_stopped_automatic_services,
    get_top_processes,
)

logger = get_logger(__name__)


def log_tool_call(func):
    """Log every agent tool invocation: args in, duration, result shape, and errors."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger.debug("Tool call started: %s(%s)", func.__name__, kwargs or args)
        started_at = time.monotonic()
        try:
            result = func(*args, **kwargs)
        except Exception:
            elapsed_ms = round((time.monotonic() - started_at) * 1000)
            logger.exception("Tool call failed: %s after %d ms", func.__name__, elapsed_ms)
            raise

        elapsed_ms = round((time.monotonic() - started_at) * 1000)
        size = len(result) if isinstance(result, (list, dict)) else "n/a"
        logger.debug(
            "Tool call finished: %s in %d ms (result size=%s)", func.__name__, elapsed_ms, size
        )
        return result

    return wrapper


@tool
@log_tool_call
def get_windows_event_log(
    log_name: str = "System", max_events: int = DEFAULT_EVENT_LOG_MAX, level: str = ""
) -> list[dict]:
    """Fetch the most recent entries from a Windows Event Log.

    Args:
        log_name: Event log to read, e.g. "System", "Application", or "Security".
        max_events: Maximum number of events to return.
        level: Optional severity filter: "Critical", "Error", "Warning", "Information", or "Verbose".
    """
    return fetch_events(log_name=log_name, max_events=max_events, level=level or None)


@tool
@log_tool_call
def get_windows_resource_usage() -> dict:
    """Get a snapshot of current CPU load, memory usage, and system uptime."""
    return get_resource_usage()


@tool
@log_tool_call
def get_windows_disk_usage() -> list[dict]:
    """Get free/used disk space for every mounted drive letter."""
    return get_disk_usage()


@tool
@log_tool_call
def get_windows_top_processes(sort_by: str = "cpu", top_n: int = DEFAULT_TOP_PROCESSES) -> list[dict]:
    """List the top resource-consuming Windows processes.

    Args:
        sort_by: "cpu" to sort by CPU time, or "memory" to sort by working-set memory.
        top_n: How many processes to return.
    """
    return get_top_processes(sort_by=sort_by, top_n=top_n)


@tool
@log_tool_call
def get_windows_stopped_services() -> list[dict]:
    """List Windows services configured to auto-start that are not currently running.

    A service in this list is a strong anomaly signal -- it should be running but isn't.
    """
    return get_stopped_automatic_services()


@tool
@log_tool_call
def get_windows_defender_status() -> dict:
    """Get Windows Defender antivirus status: whether it's enabled, real-time protection
    is on, and how old the virus signatures / last quick scan are."""
    return get_defender_status()


@tool
@log_tool_call
def get_windows_outgoing_connections(top_n: int = DEFAULT_OUTGOING_CONNECTIONS_TOP_N) -> list[dict]:
    """Summarize established outgoing TCP connections grouped by process, remote
    address, and remote port, with a connection count per group.

    Args:
        top_n: How many top groups to return, sorted by connection count descending.
    """
    return get_outgoing_connection_summary(top_n=top_n)
