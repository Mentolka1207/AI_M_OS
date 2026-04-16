"""
AI_M_OS Kernel Scheduler Interface
Пишет <pid> <nice> в /proc/aimos_scheduler (kernel module).
Fallback: os.setpriority() если модуль не загружен.
"""
import os
import logging

logger = logging.getLogger(__name__)

PROC_IFACE = "/proc/aimos_scheduler"


def renice_via_kernel(pid: int, new_nice: int) -> bool:
    """Выставить nice через kernel module /proc/aimos_scheduler."""
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
    """Fallback: os.setpriority()."""
    try:
        old = os.getpriority(os.PRIO_PROCESS, pid)
        os.setpriority(os.PRIO_PROCESS, pid, new_nice)
        logger.info("fallback renice pid=%d: %d → %d", pid, old, new_nice)
        return True
    except PermissionError:
        logger.warning("No permission to renice pid=%d", pid)
        return False
    except ProcessLookupError:
        return False


def is_kernel_module_loaded() -> bool:
    return os.path.exists(PROC_IFACE)
