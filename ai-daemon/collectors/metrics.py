"""
Metrics collector for AI_M_OS AI-daemon.
Reads /proc/stat, /proc/meminfo directly.
Reads network/sensor data from Go daemon sockets.
"""
import time
from dataclasses import dataclass, field
from pathlib import Path
from proto.client import read_daemon


@dataclass
class SystemSnapshot:
    timestamp: float
    cpu_total_pct: float
    cpu_cores_pct: list[float]
    mem_total_kb: int
    mem_used_kb: int
    swap_total_kb: int
    swap_used_kb: int
    net_ifaces: dict   # {"eth0": {"rx_bps": .., "tx_bps": ..}}
    load_avg_1: float  # from /proc/loadavg


# ── CPU ──────────────────────────────────────────────────────────────────────

_prev_cpu: list[tuple[int, int]] = []  # [(total, idle), ...]

def _read_cpu_raw() -> list[tuple[int, int]]:
    results = []
    for line in Path("/proc/stat").read_text().splitlines():
        if not line.startswith("cpu"):
            break
        parts = line.split()
        vals = [int(x) for x in parts[1:]]
        user, nice, system, idle = vals[0], vals[1], vals[2], vals[3]
        iowait  = vals[4] if len(vals) > 4 else 0
        irq     = vals[5] if len(vals) > 5 else 0
        softirq = vals[6] if len(vals) > 6 else 0
        total = user + nice + system + idle + iowait + irq + softirq
        results.append((total, idle + iowait))
    return results

def read_cpu_usage() -> tuple[float, list[float]]:
    global _prev_cpu
    curr = _read_cpu_raw()
    if not _prev_cpu or len(_prev_cpu) != len(curr):
        _prev_cpu = curr
        return 0.0, [0.0] * max(0, len(curr) - 1)

    usages = []
    for (pt, pi), (ct, ci) in zip(_prev_cpu, curr):
        dt = ct - pt
        di = ci - pi
        usages.append((1.0 - di / dt) * 100.0 if dt > 0 else 0.0)

    _prev_cpu = curr
    total = usages[0] if usages else 0.0
    cores = usages[1:] if len(usages) > 1 else []
    return total, cores


# ── Memory ───────────────────────────────────────────────────────────────────

def read_meminfo() -> tuple[int, int, int, int]:
    """Returns (total_kb, used_kb, swap_total_kb, swap_used_kb)."""
    info: dict[str, int] = {}
    for line in Path("/proc/meminfo").read_text().splitlines():
        parts = line.split(":")
        if len(parts) == 2:
            info[parts[0].strip()] = int(parts[1].strip().split()[0])
    total     = info.get("MemTotal", 0)
    available = info.get("MemAvailable", 0)
    swap_tot  = info.get("SwapTotal", 0)
    swap_free = info.get("SwapFree", 0)
    return total, total - available, swap_tot, swap_tot - swap_free


# ── Load average ─────────────────────────────────────────────────────────────

def read_load_avg() -> float:
    return float(Path("/proc/loadavg").read_text().split()[0])


# ── Full snapshot ─────────────────────────────────────────────────────────────

def collect() -> SystemSnapshot:
    cpu_total, cpu_cores = read_cpu_usage()
    mem_total, mem_used, swap_total, swap_used = read_meminfo()
    net_data = read_daemon("network") or {}
    net_ifaces = net_data.get("ifaces", {})
    load = read_load_avg()

    return SystemSnapshot(
        timestamp=time.time(),
        cpu_total_pct=cpu_total,
        cpu_cores_pct=cpu_cores,
        mem_total_kb=mem_total,
        mem_used_kb=mem_used,
        swap_total_kb=swap_total,
        swap_used_kb=swap_used,
        net_ifaces=net_ifaces,
        load_avg_1=load,
    )
