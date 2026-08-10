from src.logger import get_logger
from src.powershell import parse_dotnet_date, run_powershell

logger = get_logger(__name__)

LEVEL_MAP = {
    "critical": 1,
    "error": 2,
    "warning": 3,
    "information": 4,
    "verbose": 5,
}


def fetch_events(log_name: str = "System", max_events: int = 20, level: str | None = None) -> list[dict]:
    """Fetch the most recent events from a Windows Event Log via PowerShell's Get-WinEvent."""
    logger.debug("Fetching up to %d event(s) from '%s' (level=%s)", max_events, log_name, level or "any")

    filter_parts = [f"LogName='{log_name}'"]
    if level:
        level_num = LEVEL_MAP.get(level.lower())
        if level_num is None:
            logger.error("Unknown event log level requested: %s", level)
            raise ValueError(f"Unknown level '{level}'. Use one of {list(LEVEL_MAP)}.")
        filter_parts.append(f"Level={level_num}")
    filter_hashtable = "@{" + "; ".join(filter_parts) + "}"

    command = (
        f"Get-WinEvent -FilterHashtable {filter_hashtable} -MaxEvents {int(max_events)} "
        "| Select-Object TimeCreated,Id,LevelDisplayName,ProviderName,Message "
        "| ConvertTo-Json -Depth 3"
    )

    data = run_powershell(command, ignore_stderr_substrings=("NoMatchingEventsFound",))
    if isinstance(data, dict):
        data = [data]

    logger.debug("Fetched %d event(s) from '%s'", len(data), log_name)

    return [
        {
            "time": parse_dotnet_date(item.get("TimeCreated")),
            "id": item.get("Id"),
            "level": item.get("LevelDisplayName"),
            "provider": item.get("ProviderName"),
            "message": (item.get("Message") or "").strip(),
        }
        for item in data
    ]
