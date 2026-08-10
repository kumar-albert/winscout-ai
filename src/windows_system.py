from src.logger import get_logger
from src.powershell import parse_dotnet_date, run_powershell

logger = get_logger(__name__)


def get_resource_usage() -> dict:
    """Snapshot of CPU load, memory usage, and uptime."""
    logger.debug("Fetching CPU/memory resource usage snapshot")
    command = (
        "$os = Get-CimInstance Win32_OperatingSystem; "
        "$cpu = (Get-Counter '\\Processor(_Total)\\% Processor Time').CounterSamples[0].CookedValue; "
        "[PSCustomObject]@{"
        "CpuPercent = [math]::Round($cpu,1); "
        "TotalMemoryMB = [math]::Round($os.TotalVisibleMemorySize/1024); "
        "FreeMemoryMB = [math]::Round($os.FreePhysicalMemory/1024); "
        "MemoryUsedPercent = [math]::Round((1 - $os.FreePhysicalMemory/$os.TotalVisibleMemorySize)*100,1); "
        "LastBootUpTime = $os.LastBootUpTime; "
        "UptimeHours = [math]::Round(((Get-Date) - $os.LastBootUpTime).TotalHours,1)"
        "} | ConvertTo-Json"
    )
    data = run_powershell(command)
    if isinstance(data, dict) and "LastBootUpTime" in data:
        data["LastBootUpTime"] = parse_dotnet_date(data["LastBootUpTime"])
    logger.debug(
        "Resource usage: cpu=%s%% memory=%s%%",
        data.get("CpuPercent") if isinstance(data, dict) else "?",
        data.get("MemoryUsedPercent") if isinstance(data, dict) else "?",
    )
    return data


def get_disk_usage() -> list[dict]:
    """Free/used space per mounted drive letter."""
    logger.debug("Fetching disk usage per drive")
    command = (
        "Get-Volume | Where-Object { $_.DriveLetter } | "
        "Select-Object DriveLetter,"
        "@{n='SizeGB';e={[math]::Round($_.Size/1GB,1)}},"
        "@{n='FreeGB';e={[math]::Round($_.SizeRemaining/1GB,1)}},"
        "@{n='FreePercent';e={[math]::Round(($_.SizeRemaining/$_.Size)*100,1)}} "
        "| ConvertTo-Json"
    )
    data = run_powershell(command)
    drives = [data] if isinstance(data, dict) else data
    logger.debug("Fetched disk usage for %d drive(s)", len(drives))
    return drives


def get_top_processes(sort_by: str = "cpu", top_n: int = 10) -> list[dict]:
    """Top processes by CPU time or working-set memory."""
    logger.debug("Fetching top %d process(es) by %s", top_n, sort_by)
    sort_property = "CPU" if sort_by.lower() == "cpu" else "WorkingSet64"
    command = (
        f"Get-Process | Sort-Object {sort_property} -Descending | Select-Object -First {int(top_n)} "
        "Name,Id,@{n='CpuSeconds';e={[math]::Round($_.CPU,1)}},"
        "@{n='MemoryMB';e={[math]::Round($_.WorkingSet64/1MB,1)}} "
        "| ConvertTo-Json"
    )
    data = run_powershell(command)
    processes = [data] if isinstance(data, dict) else data
    logger.debug("Fetched %d top process(es)", len(processes))
    return processes


def get_stopped_automatic_services() -> list[dict]:
    """Services configured to auto-start that are not currently running -- a common anomaly signal."""
    logger.debug("Checking for auto-start services that are not running")
    command = (
        "Get-Service | Where-Object { $_.StartType -eq 'Automatic' -and $_.Status -ne 'Running' } | "
        "Select-Object Name,DisplayName,"
        "@{n='Status';e={$_.Status.ToString()}},"
        "@{n='StartType';e={$_.StartType.ToString()}} "
        "| ConvertTo-Json"
    )
    data = run_powershell(command)
    services = [data] if isinstance(data, dict) else data
    if services:
        logger.warning("Found %d stopped auto-start service(s)", len(services))
    else:
        logger.debug("No stopped auto-start services found")
    return services


def get_defender_status() -> dict:
    """Windows Defender antivirus / real-time protection status and signature freshness."""
    logger.debug("Checking Windows Defender status")
    command = (
        "Get-MpComputerStatus | Select-Object AntivirusEnabled,RealTimeProtectionEnabled,"
        "AntivirusSignatureAge,QuickScanAge | ConvertTo-Json"
    )
    data = run_powershell(command)
    if isinstance(data, dict) and not (data.get("AntivirusEnabled") and data.get("RealTimeProtectionEnabled")):
        logger.warning("Windows Defender is not fully enabled: %s", data)
    return data


def get_outgoing_connection_summary(top_n: int = 15) -> list[dict]:
    """Established outbound TCP connections grouped by process and remote port.

    Loopback addresses are excluded. Groups share the same process, remote port,
    and remote address so repeated bursts to the same endpoint collapse into one
    row with a connection count -- useful for spotting a process opening an
    unusually large number of connections to one destination.
    """
    logger.debug("Fetching outgoing connection summary (top %d)", top_n)
    command = (
        "$procs = Get-Process | Select-Object Id,Name; "
        "Get-NetTCPConnection -State Established | "
        "Where-Object { $_.RemoteAddress -notmatch '^(127\\.|::1)' } | "
        "Select-Object RemoteAddress,RemotePort,OwningProcess,"
        "@{n='ProcessName';e={ ($procs | Where-Object Id -eq $_.OwningProcess | "
        "Select-Object -First 1 -ExpandProperty Name) }} "
        "| ConvertTo-Json -Depth 3"
    )
    data = run_powershell(command)
    connections = [data] if isinstance(data, dict) else data
    logger.debug("Raw outgoing connections fetched: %d", len(connections))

    groups: dict[tuple[str, str, int], dict] = {}
    for conn in connections:
        process_name = conn.get("ProcessName") or f"pid:{conn.get('OwningProcess')}"
        key = (process_name, conn.get("RemoteAddress"), conn.get("RemotePort"))
        group = groups.setdefault(
            key,
            {
                "process": process_name,
                "pid": conn.get("OwningProcess"),
                "remote_address": conn.get("RemoteAddress"),
                "remote_port": conn.get("RemotePort"),
                "connection_count": 0,
            },
        )
        group["connection_count"] += 1

    summary = sorted(groups.values(), key=lambda g: g["connection_count"], reverse=True)[:top_n]
    logger.debug(
        "Grouped into %d connection group(s), returning top %d", len(groups), len(summary)
    )
    return summary
