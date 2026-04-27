"""
kernel_iface.py — Python AI-daemon interface with aimos_scheduler kernel module.

/proc/aimos_scheduler format (defined by aimos_scheduler.c):
    status: active
    version: 0.1
    last_pid: 1234
    last_nice: 5
    total_ops: 42
    last_error: none

Fallback: os.setpriority() when module is not loaded.
"""

import os
import logging

logger = logging.getLogger(__name__)

PROC_IFACE = "/proc/aimos_scheduler"


# ── module presence ──────────────────────────────────────────────────────────

def is_kernel_module_loaded() -> bool:
    return os.path.exists(PROC_IFACE)


# ── raw read ─────────────────────────────────────────────────────────────────

def read_scheduler_status() -> str | None:
    """
    Read raw text from /proc/aimos_scheduler.
    Returns None if the module is not loaded or an OS error occurs.
    """
    if not os.path.exists(PROC_IFACE):
        logger.debug("Kernel module not loaded")
        return None
    try:
        with open(PROC_IFACE, "r") as f:
            raw = f.read().strip()
        logger.debug("kernel status raw: %s", raw)
        return raw
    except OSError as e:
        logger.warning("Failed to read %s: %s", PROC_IFACE, e)
        return None


# ── parser ───────────────────────────────────────────────────────────────────

def parse_scheduler_status(raw: str) -> dict:
    """
    Parse the key:value output produced by aimos_scheduler.c.

    Expected input (all fields optional — module may evolve):
        status: active
        version: 0.1
        last_pid: 1234
        last_nice: 5
        total_ops: 42
        last_error: none

    Returns a dict with typed values:
        {
            "active":     bool,
            "version":    str,
            "last_pid":   int,   # -1 if never set
            "last_nice":  int,
            "total_ops":  int,
            "last_error": str,
            "raw":        str,
        }
    """
    result: dict = {
        "active":     False,
        "version":    "unknown",
        "last_pid":   -1,
        "last_nice":  0,
        "total_ops":  0,
        "last_error": "none",
        "raw":        raw,
    }

    if not raw:
        return result

    for line in raw.splitlines():
        line = line.strip()
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key   = key.strip().lower()
        value = value.strip()

        if key == "status":
            result["active"] = (value.lower() == "active")
        elif key == "version":
            result["version"] = value
        elif key == "last_pid":
            try:
                result["last_pid"] = int(value)
            except ValueError:
                logger.debug("parse: bad last_pid value %r", value)
        elif key == "last_nice":
            try:
                result["last_nice"] = int(value)
            except ValueError:
                logger.debug("parse: bad last_nice value %r", value)
        elif key == "total_ops":
            try:
                result["total_ops"] = int(value)
            except ValueError:
                logger.debug("parse: bad total_ops value %r", value)
        elif key == "last_error":
            result["last_error"] = value

    return result


# ── renice ───────────────────────────────────────────────────────────────────

def renice_via_kernel(pid: int, new_nice: int) -> bool:
    """
    Renice *pid* to *new_nice* via /proc/aimos_scheduler (if loaded),
    otherwise fall back to os.setpriority().
    """
    if not os.path.exists(PROC_IFACE):
        logger.debug("Kernel module not loaded, using os.setpriority()")
        return _renice_fallback(pid, new_nice)

    try:
        with open(PROC_IFACE, "w") as f:
            f.write(f"{pid} {new_nice}\n")
        logger.info("kernel renice: pid=%d nice=%d", pid, new_nice)
        return True
    except OSError as e:
        logger.warning("kernel renice failed (%s), falling back to os.setpriority()", e)
        return _renice_fallback(pid, new_nice)


def _renice_fallback(pid: int, new_nice: int) -> bool:
    """Userspace fallback via os.setpriority()."""
    try:
        old = os.getpriority(os.PRIO_PROCESS, pid)
        os.setpriority(os.PRIO_PROCESS, pid, new_nice)
        logger.info("fallback renice pid=%d: %d -> %d", pid, old, new_nice)
        return True
    except PermissionError:
        logger.warning("No permission to renice pid=%d", pid)
        return False
    except ProcessLookupError:
        return False


# ── combined status ──────────────────────────────────────────────────────────

def get_scheduler_info() -> dict:
    """
    Return combined kernel module status dict.

    Keys: loaded, active, version, last_pid, last_nice, total_ops, last_error, raw.
    When module is not loaded, all non-loaded fields are safe defaults.
    """
    if not is_kernel_module_loaded():
        return {
            "loaded":     False,
            "active":     False,
            "version":    "unknown",
            "last_pid":   -1,
            "last_nice":  0,
            "total_ops":  0,
            "last_error": "module_not_loaded",
            "raw":        "",
        }

    raw  = read_scheduler_status()
    info = parse_scheduler_status(raw or "")
    info["loaded"] = True
    return info
