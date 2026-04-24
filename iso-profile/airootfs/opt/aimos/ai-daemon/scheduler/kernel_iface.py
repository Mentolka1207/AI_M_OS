"""
kernel_iface.py - Python AI-daemon interface with aimos_scheduler kernel module.
Fallback: os.setpriority() if module not loaded.
"""

import os
import logging

logger = logging.getLogger(__name__)

PROC_IFACE = "/proc/aimos_scheduler"


def is_kernel_module_loaded() -> bool:
    return os.path.exists(PROC_IFACE)


def read_scheduler_status():
    if not os.path.exists(PROC_IFACE):
        logger.debug("Kernel module not loaded")
        return None
    try:
        with open(PROC_IFACE, "r") as f:
            status = f.read().strip()
        logger.debug("kernel status: %s", status)
        return status
    except OSError as e:
        logger.warning("Failed to read kernel status: %s", e)
        return None


def renice_via_kernel(pid: int, new_nice: int) -> bool:
    if not os.path.exists(PROC_IFACE):
        logger.debug("Kernel module not loaded, using os.setpriority()")
        return _renice_fallback(pid, new_nice)
    try:
        with open(PROC_IFACE, "w") as f:
            f.write(f"{pid} {new_nice}\n")
        logger.info("kernel renice: pid=%d nice=%d", pid, new_nice)
        return True
    except OSError as e:
        logger.warning("kernel renice failed: %s, falling back", e)
        return _renice_fallback(pid, new_nice)


def _renice_fallback(pid: int, new_nice: int) -> bool:
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
