"""
AI_M_OS Simple scheduler heuristics.
"""

import os
import logging
from dataclasses import dataclass
from scheduler.kernel_iface import renice_via_kernel as renice

logger = logging.getLogger(__name__)
SYSTEM_UIDS = {0}
MAX_RENICE  = 10
RENICE_STEP = 5


@dataclass
class ProcessInfo:
    pid:      int
    name:     str
    uid:      int
    cpu_time: int
    nice:     int
    vm_rss:   int


def list_processes() -> list[ProcessInfo]:
    procs = []
    for entry in os.scandir("/proc"):
        if not entry.name.isdigit():
            continue
        pid = int(entry.name)
        try:
            procs.append(_read_proc(pid))
        except (FileNotFoundError, ProcessLookupError, ValueError):
            pass
    return procs


def _read_proc(pid: int) -> ProcessInfo:
    stat = open(f"/proc/{pid}/stat").read().split()
    name = stat[1].lstrip("(").rstrip(")")
    utime, stime, nice_val = int(stat[13]), int(stat[14]), int(stat[18])
    uid, vm_rss = 65534, 0
    for line in open(f"/proc/{pid}/status"):
        if line.startswith("Uid:"):
            uid = int(line.split()[1])
        elif line.startswith("VmRSS:"):
            vm_rss = int(line.split()[1])
    return ProcessInfo(pid, name, uid, utime + stime, nice_val, vm_rss)


def run_heuristics(snap, db_conn=None) -> list[dict]:
    from db.logger import log_scheduler_event
    events = []
    num_cores = max(len(snap.cpu_cores_pct), 1)
    user_procs = sorted(
        [p for p in list_processes() if p.uid not in SYSTEM_UIDS],
        key=lambda p: p.cpu_time, reverse=True)

    # Rule 1: high_cpu
    if snap.cpu_total_pct > 85 and user_procs:
        t = user_procs[0]
        new_nice = min(t.nice + RENICE_STEP, MAX_RENICE)
        if new_nice != t.nice:
            ok = renice(t.pid, new_nice)
            ev = {"rule": "high_cpu", "pid": t.pid, "name": t.name,
                  "action": "renice", "old_nice": t.nice, "new_nice": new_nice,
                  "reason": f"CPU {snap.cpu_total_pct:.1f}% > 85%", "applied": ok}
            events.append(ev)
            if db_conn:
                log_scheduler_event(db_conn, t.pid, "renice",
                                    t.nice, new_nice, ev["reason"])

    # Rule 2: high_mem
    if snap.mem_total_kb > 0:
        mem_pct = snap.mem_used_kb / snap.mem_total_kb * 100
        if mem_pct > 90:
            top = sorted(user_procs, key=lambda p: p.vm_rss, reverse=True)
            if top:
                ev = {"rule": "high_mem", "pid": top[0].pid, "name": top[0].name,
                      "action": "kill_suggestion", "old_nice": 0, "new_nice": 0,
                      "reason": f"RAM {mem_pct:.1f}% > 90%"}
                events.append(ev)
                if db_conn:
                    log_scheduler_event(db_conn, top[0].pid, "kill_suggestion",
                                        0, 0, ev["reason"])

    # Rule 3: high_load
    if snap.load_avg_1 > num_cores * 1.5 and user_procs:
        t = user_procs[0]
        new_nice = min(t.nice + RENICE_STEP, MAX_RENICE)
        if new_nice != t.nice:
            ok = renice(t.pid, new_nice)
            ev = {"rule": "high_load", "pid": t.pid, "name": t.name,
                  "action": "renice", "old_nice": t.nice, "new_nice": new_nice,
                  "reason": f"load_avg {snap.load_avg_1:.2f} > {num_cores * 1.5:.1f}",
                  "applied": ok}
            events.append(ev)
            if db_conn:
                log_scheduler_event(db_conn, t.pid, "renice",
                                    t.nice, new_nice, ev["reason"])

    # Rule 4: low_cpu_restore
    if snap.cpu_total_pct < 20:
        for p in user_procs:
            if p.nice > 0:
                renice(p.pid, 0)
                ev = {"rule": "low_cpu_restore", "pid": p.pid, "name": p.name,
                      "action": "renice", "old_nice": p.nice, "new_nice": 0,
                      "reason": f"CPU {snap.cpu_total_pct:.1f}% < 20%, restoring"}
                events.append(ev)
                if db_conn:
                    log_scheduler_event(db_conn, p.pid, "renice",
                                        p.nice, 0, ev["reason"])

    return events
