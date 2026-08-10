import json
import re
import subprocess
import time
from datetime import datetime, timezone

from src.config import POWERSHELL_TIMEOUT_SECONDS
from src.logger import get_logger

logger = get_logger(__name__)

_DOTNET_DATE_RE = re.compile(r"/Date\((\d+)\)/")


def parse_dotnet_date(value: str | None) -> str | None:
    match = _DOTNET_DATE_RE.match(value or "")
    if not match:
        return value
    return datetime.fromtimestamp(int(match.group(1)) / 1000, tz=timezone.utc).isoformat()


def run_powershell(command: str, ignore_stderr_substrings: tuple[str, ...] = ()) -> list | dict:
    logger.debug("Running PowerShell command: %s", command)
    started_at = time.monotonic()

    result = subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", command],
        capture_output=True,
        text=True,
        timeout=POWERSHELL_TIMEOUT_SECONDS,
    )
    elapsed_ms = round((time.monotonic() - started_at) * 1000)

    if result.returncode != 0:
        if any(marker in result.stderr for marker in ignore_stderr_substrings):
            logger.debug("PowerShell command returned no matching data (%d ms)", elapsed_ms)
            return []
        logger.error(
            "PowerShell command failed after %d ms: %s", elapsed_ms, result.stderr.strip()
        )
        raise RuntimeError(f"PowerShell command failed: {result.stderr.strip()}")

    output = result.stdout.strip()
    if not output:
        logger.debug("PowerShell command returned empty output (%d ms)", elapsed_ms)
        return []

    data = json.loads(output)
    count = len(data) if isinstance(data, list) else 1
    logger.debug("PowerShell command succeeded in %d ms (%d record(s))", elapsed_ms, count)
    return data
