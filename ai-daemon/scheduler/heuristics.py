"""
AI_M_OS Simple scheduler heuristics.

Rules (эвристики):
  1. Если CPU > 85% — найти процесс с наибольшим CPU, renice +5
  2. Если RAM > 90% — логировать предупреждение (kill — только suggestion)
  3. Если load_avg > num_cores * 1.5 — renice самый тяжёлый non-system процесс
  4. Если CPU < 20% — renice обратно (nice → 0) ранее заниженные процессы

Источник данных: /proc/<pid>/stat, /proc/<pid>/status
"""
import os
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

SYSTEM_UIDS = {0}          # root процессы не трогаем
MAX_RENICE  = 10           # максимальный nice который мы выставляем
RENICE_STEP = 5


@dataclass
class ProcessInfo:
    pid:      int
    name:     str
    uid:      int
    cpu_time: int   # utime + stime из /proc/pid/stat
    nice:     int
    vm_rss:   int   # KB, из /proc/pid/status


def list_processes() -> list[ProcessInfo]:
    procs = []
    for entry in os.scandir("/proc"):
        if not entry.name.isdigit():
            continue
        pid = int(entry.name)
        try:
            procs.append(_read_proc(pid))
        except (FileNotFoundError, ProcessLookupError, ValueError):
            pass  # процесс завершился пока читали
    return procs


def _read_proc(pid: int) -> ProcessInfo:
    stat_path   = f"/proc/{pid}/stat"
    status_path = f"/proc/{pid}/status"

    stat = open(stat_path).read().split()
    # Поле 2 — имя в скобках, может содержать пробелы
    name_end = stat[1].rstrip(")")
    name = name_end.lstrip("(")
    utime    = int(stat[13])
    stime    = int(stat[14])
    nice_val = int(stat[18])

    uid = 65534  # nobody по умолчанию
    vm_rss = 0
    for line in open(status_path):
        if line.startswith("Uid:"):
            uid = int(line.split()[1])
        elif line.startswith("VmRSS:"):
            vm_rss = int(line.split()[1])

    return ProcessInfo(pid, name, uid, utime + stime, nice_val, vm_rss)


def renice(pid: int, new_nice: int) -> bool:
    """Выставить nice через os.setpriority. Требует root."""
    try:
        old = os.getpriority(os.PRIO_PROCESS, pid)
        os.setpriority(os.PRIO_PROCESS, pid, new_nice)
        logger.info("renice pid=%d: %d → %d", pid, old, new_nice)
        return True
    except PermissionError:
        logger.warning("No permission to renice pid=%d", pid)
        return False
    except ProcessLookupError:
        return False


def run_heuristics(snap, db_conn=None) -> list[dict]:
    """
    Применяет эвристики к текущему снапшоту.
    Возвращает список событий для логирования.
    """
    from db.logger import log_scheduler_event

    events = []
    num_cores = max(len(snap.cpu_cores_pct), 1)
    procs = list_processes()
    # Сортируем по CPU time убыванию, исключаем системные
    user_procs = sorted(
        [p for p in procs if p.uid not in SYSTEM_UIDS],
        key=lambda p: p.cpu_time, reverse=True
    )

    # ── Rule 1: High CPU ──────────────────────────────────────────────────────
    if snap.cpu_total_pct > 85 and user_procs:
        target = user_procs[0]
        new_nice = min(target.nice + RENICE_STEP, MAX_RENICE)
        if new_nice != target.nice:
            ok = renice(target.pid, new_nice)
            event = {
                "rule":     "high_cpu",
                "pid":      target.pid,
                "name":     target.name,
                "action":   "renice",
                "old_nice": target.nice,
                "new_nice": new_nice,
                "reason":   f"CPU {snap.cpu_total_pct:.1f}% > 85%",
                "applied":  ok,
            }
            events.append(event)
            if db_conn:
                log_scheduler_event(db_conn, target.pid, "renice",
                                    target.nice, new_nice, event["reason"])

    # ── Rule 2: High RAM ──────────────────────────────────────────────────────
    if snap.mem_total_kb > 0:
        mem_pct = snap.mem_used_kb / snap.mem_total_kb * 100
        if mem_pct > 90:
            top_mem = sorted(user_procs, key=lambda p: p.vm_rss, reverse=True)
            if top_mem:
                event = {
                    "rule":   "high_mem",
                    "pid":    top_mem[0].pid,
                    "name":   top_mem[0].name,
                    "action": "kill_suggestion",
                    "reason": f"RAM {mem_pct:.1f}% > 90%",
                }
                events.append(event)
                logger.warning("High memory: suggest reviewing pid=%d (%s)",
                               top_mem[0].pid, top_mem[0].name)

    # ── Rule 3: High load average ─────────────────────────────────────────────
    if snap.load_avg_1 > num_cores * 1.5 and user_procs:
        target = user_procs[0]
        new_nice = min(target.nice + RENICE_STEP, MAX_RENICE)
        if new_nice != target.nice:
            ok = renice(target.pid, new_nice)
            event = {
                "rule":     "high_load",
                "pid":      target.pid,
                "name":     target.name,
                "action":   "renice",
                "old_nice": target.nice,
                "new_nice": new_nice,
                "reason":   f"load_avg {snap.load_avg_1:.2f} > {num_cores * 1.5:.1f}",
                "applied":  ok,
            }
            events.append(event)

    # ── Rule 4: Low CPU — restore nice ───────────────────────────────────────
    if snap.cpu_total_pct < 20:
        for p in user_procs:
            if p.nice > 0:
                renice(p.pid, 0)
                events.append({
                    "rule":     "low_cpu_restore",
                    "pid":      p.pid,
                    "name":     p.name,
                    "action":   "renice",
                    "old_nice": p.nice,
                    "new_nice": 0,
                    "reason":   f"CPU {snap.cpu_total_pct:.1f}% < 20%, restoring",
                })

    return events
