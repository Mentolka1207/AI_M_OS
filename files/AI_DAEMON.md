# AI Daemon — Documentation

The `ai-daemon` is a Python service that collects system metrics, applies scheduling heuristics, logs events to PostgreSQL, and exposes process priority control via D-Bus and the `aimos_scheduler` kernel module.

**Source location:** `ai-daemon/` (development) and `iso-profile/airootfs/opt/aimos/ai-daemon/` (deployed in ISO)

---

## Table of Contents

1. [Architecture](#architecture)
2. [Entry point — daemon.py](#entry-point--daemonpy)
3. [Metrics collector — collectors/metrics.py](#metrics-collector--collectorsmetricspy)
4. [Kernel interface — scheduler/kernel_iface.py](#kernel-interface--schedulerkernel_ifacepy)
5. [Heuristics — scheduler/heuristics.py](#heuristics--schedulerheuristicspy)
6. [Database logger — db/logger.py](#database-logger--dbloggerpy)
7. [PostgreSQL schema — db/schema.sql](#postgresql-schema--dbschemasql)
8. [Go daemon client — proto/client.py](#go-daemon-client--protoclientpy)
9. [D-Bus service — dbus/scheduler_service.py](#d-bus-service--dbusscheduler_servicepy)
10. [GTK4 app — dbus/aimos_scheduler_app.py](#gtk4-app--dbusaimos_scheduler_apppy)
11. [/proc/aimos_scheduler interface](#procaimos_scheduler-interface)
12. [Systemd services](#systemd-services)
13. [Environment variables](#environment-variables)

---

## Architecture

```
daemon.py  (main loop, AIMOS_INTERVAL seconds, default 1s)
    │
    ├── collectors/metrics.py     → SystemSnapshot
    │       ├── /proc/stat        (CPU usage per core)
    │       ├── /proc/meminfo     (RAM, swap)
    │       ├── /proc/loadavg     (load average)
    │       └── proto/client.py   (network/sensor/power from Go daemons)
    │
    ├── scheduler/heuristics.py   → list[dict] events
    │       └── scheduler/kernel_iface.py
    │               ├── /proc/aimos_scheduler  (write "pid nice\n")
    │               └── os.setpriority()       (fallback)
    │
    └── db/logger.py              → PostgreSQL (psycopg2)
            ├── metrics_cpu
            ├── metrics_memory
            ├── metrics_network
            └── scheduler_events
```

---

## Entry point — daemon.py

**File:** `ai-daemon/daemon.py`

```bash
# With PostgreSQL
AIMOS_DB_DSN="postgresql://aimos:aimos@localhost/aimos_metrics" sudo -E python3 daemon.py

# Without PostgreSQL
AIMOS_NO_DB=1 sudo -E python3 daemon.py
```

The main loop:
1. Calls `collect()` → `SystemSnapshot`
2. If DB is available: calls `log_snapshot(conn, snap)`
3. Calls `run_heuristics(snap, db_conn)` → list of scheduler events
4. Logs each event via `logger.info()`
5. Sleeps `AIMOS_INTERVAL` seconds

Errors in a single tick are caught and logged; the loop continues.

---

## Metrics collector — collectors/metrics.py

**File:** `ai-daemon/collectors/metrics.py`

### `SystemSnapshot` dataclass

| Field | Type | Source |
|---|---|---|
| `timestamp` | `float` | `time.time()` |
| `cpu_total_pct` | `float` | `/proc/stat` aggregate `cpu` line |
| `cpu_cores_pct` | `list[float]` | `/proc/stat` per-core lines |
| `mem_total_kb` | `int` | `/proc/meminfo` `MemTotal` |
| `mem_used_kb` | `int` | `MemTotal - MemAvailable` |
| `swap_total_kb` | `int` | `/proc/meminfo` `SwapTotal` |
| `swap_used_kb` | `int` | `SwapTotal - SwapFree` |
| `net_ifaces` | `dict` | Go `network-daemon` socket |
| `load_avg_1` | `float` | `/proc/loadavg` field 0 |
| `cpu_temp_c` | `float` | Go `sensor-daemon` socket |
| `cpu_governor` | `str` | Go `power-daemon` socket |

### CPU calculation

Reads `/proc/stat`. For each `cpu*` line:
```
total = user + nice + system + idle + iowait + irq + softirq
usage = (1.0 - Δidle / Δtotal) × 100
```
Diffs against the previous snapshot stored in module-level `_prev_cpu`. Returns `0.0` on the first call.

---

## Kernel interface — scheduler/kernel_iface.py

**File:** `ai-daemon/scheduler/kernel_iface.py`

Proc interface path: `/proc/aimos_scheduler` (constant `PROC_IFACE`)

### `is_kernel_module_loaded() → bool`

```python
return os.path.exists("/proc/aimos_scheduler")
```

### `read_scheduler_status() → str | None`

Reads and returns the raw string from `/proc/aimos_scheduler`. Returns `None` if the module is not loaded or on `OSError`.

### `renice_via_kernel(pid: int, new_nice: int) → bool`

Primary code path:
```python
with open("/proc/aimos_scheduler", "w") as f:
    f.write(f"{pid} {new_nice}\n")
```

Falls back to `_renice_fallback()` if:
- `/proc/aimos_scheduler` does not exist
- `OSError` on write

### `_renice_fallback(pid: int, new_nice: int) → bool`

```python
os.setpriority(os.PRIO_PROCESS, pid, new_nice)
```

Returns `False` silently on `ProcessLookupError`. Returns `False` and logs a warning on `PermissionError` (requires root or `CAP_SYS_NICE` to set negative nice values).

### `get_scheduler_info() → dict`

Returns:
```python
{
    "loaded": bool,
    "active": bool,   # True if "active" in raw status string (case-insensitive)
    "raw": str
}
```

---

## Heuristics — scheduler/heuristics.py

**File:** `ai-daemon/scheduler/heuristics.py`

Constants:
```python
SYSTEM_UIDS = {0}   # processes owned by root are skipped
MAX_RENICE  = 10    # nice value is never raised above this
RENICE_STEP = 5     # added per trigger
```

### `run_heuristics(snap: SystemSnapshot, db_conn=None) → list[dict]`

Scans `/proc` for all non-root user processes, sorted by CPU time descending. Applies four rules:

| Rule | Trigger | Action |
|---|---|---|
| `high_cpu` | `cpu_total_pct > 85` | `renice` top process by `+RENICE_STEP` (capped at `MAX_RENICE`) |
| `high_mem` | `mem_used_kb / mem_total_kb > 90%` | `kill_suggestion` for the highest-RSS process |
| `high_load` | `load_avg_1 > num_cores × 1.5` | `renice` top process by `+RENICE_STEP` |
| `low_cpu_restore` | `cpu_total_pct < 20` | `renice` all processes with `nice > 0` back to `0` |

Each triggered rule appends a dict to the events list:
```python
{
    "rule":     str,   # "high_cpu" | "high_mem" | "high_load" | "low_cpu_restore"
    "pid":      int,
    "name":     str,
    "action":   str,   # "renice" | "kill_suggestion"
    "old_nice": int,
    "new_nice": int,
    "reason":   str,   # human-readable trigger description
    "applied":  bool   # result of renice_via_kernel() call
}
```

If `db_conn` is provided, each event is also written to `scheduler_events` via `log_scheduler_event()`.

### `ProcessInfo` dataclass

| Field | Source |
|---|---|
| `pid` | `/proc/<pid>/stat` field 0 |
| `name` | `/proc/<pid>/stat` field 1 (stripped of parentheses) |
| `uid` | `/proc/<pid>/status` `Uid:` first field |
| `cpu_time` | `utime + stime` (fields 13+14 in `/proc/<pid>/stat`) |
| `nice` | field 18 in `/proc/<pid>/stat` |
| `vm_rss` | `/proc/<pid>/status` `VmRSS:` in KB |

---

## Database logger — db/logger.py

**File:** `ai-daemon/db/logger.py`

Uses `psycopg2` (sync). Connection string from `AIMOS_DB_DSN` env var; default:
```
postgresql://aimos:aimos@localhost:5432/aimos_metrics
```

### `get_conn()`

Returns a `psycopg2` connection object.

### `init_schema(conn)`

Reads `db/schema.sql` and executes it. Safe to call multiple times (`CREATE TABLE IF NOT EXISTS`).

### `log_snapshot(conn, snap: SystemSnapshot)`

Inserts one row into each of:
- `metrics_cpu` — `total_pct`, `cores_pct` (array), `load_avg`
- `metrics_memory` — `total_kb`, `used_kb`, `swap_total_kb`, `swap_used_kb`
- `metrics_network` — one row per interface in `snap.net_ifaces`, using `execute_values()` for batch insert

Timestamps are inserted as `to_timestamp(%s)` from the Unix float `snap.timestamp`.

On any exception: calls `conn.rollback()` and logs the error. Does not raise.

### `log_scheduler_event(conn, pid, action, old_nice, new_nice, reason)`

Inserts one row into `scheduler_events`. Called by `heuristics.py` for all 4 rules when `db_conn` is not `None`.

---

## PostgreSQL schema — db/schema.sql

**File:** `ai-daemon/db/schema.sql` (PostgreSQL 15+)

```sql
metrics_cpu       (id, ts, total_pct REAL, cores_pct REAL[], load_avg REAL)
metrics_memory    (id, ts, total_kb, used_kb, swap_total_kb, swap_used_kb)
metrics_network   (id, ts, iface TEXT, rx_bps REAL, tx_bps REAL)
scheduler_events  (id, ts, pid INT, action TEXT, old_nice INT, new_nice INT, reason TEXT)
```

Indexes on `ts DESC` for all metric tables. No index on `scheduler_events`.

**Useful queries:**

```sql
-- Last 5 minutes of CPU
SELECT ts, total_pct, load_avg FROM metrics_cpu
WHERE ts > NOW() - INTERVAL '5 minutes'
ORDER BY ts DESC;

-- All scheduler events today
SELECT ts, pid, action, old_nice, new_nice, reason
FROM scheduler_events
WHERE ts > CURRENT_DATE
ORDER BY ts DESC;
```

---

## Go daemon client — proto/client.py

**File:** `ai-daemon/proto/client.py`

Unix socket paths:
```python
SOCKET_PATHS = {
    "network": "/run/aimos/network-daemon.sock",
    "power":   "/run/aimos/power-daemon.sock",
    "sensor":  "/run/aimos/sensor-daemon.sock",
}
```

### `read_daemon(name: str) → dict | None`

Connects to the socket, reads the complete JSON payload (each daemon writes one JSON object then closes), returns parsed dict. Returns `None` if the socket does not exist or on any error. Timeout: 2.0 seconds.

Expected response shapes:

**network-daemon:**
```json
{"timestamp": 1234567890, "ifaces": {"eth0": {"rx_bps": 12345.6, "tx_bps": 678.9}}}
```

**power-daemon:**
```json
{"cpu_governor": "schedutil", "cpu_freq_mhz": 3200, "mem_total_mb": 7980, "mem_used_mb": 4100, "uptime_seconds": 86400}
```

**sensor-daemon:**
```json
{"cpu_temp_c": 58.0, "load_avg_1min": 1.23, "load_avg_5min": 0.98, "load_avg_15min": 0.75, "disk_io_ops": {"sda": 1024}}
```

---

## D-Bus service — dbus/scheduler_service.py

**File:** `ai-daemon/dbus/scheduler_service.py`

Bus name: `org.aimos.Scheduler`
Object path: `/org/aimos/Scheduler`

Runs as user `aimos` (per `systemd/aimos-scheduler-dbus.service`).

### Methods

| Method | Signature | Description |
|---|---|---|
| `SetProcessPriority(pid, nice)` | `ii → b` | Validates `−20 ≤ nice ≤ 19`, calls `renice_via_kernel()`, emits `PriorityChanged` on success |
| `GetProcessPriority(pid)` | `i → i` | Returns `os.getpriority(PRIO_PROCESS, pid)` |
| `IsKernelModuleLoaded()` | `→ b` | Returns `os.path.exists("/proc/aimos_scheduler")` |

### Signal

| Signal | Signature | Emitted when |
|---|---|---|
| `PriorityChanged` | `iii` (pid, old_nice, new_nice) | `SetProcessPriority` succeeds |

### Property

| Property | Type | Value |
|---|---|---|
| `Version` | `s` | `"0.9.0"` (in `ai-daemon/dbus/scheduler_service.py`); `"0.5.0"` in the ISO-deployed copy |

### D-Bus policy

**File:** `dbus-policy/org.aimos.Scheduler.conf`

- User `aimos`: can own the bus name and send/receive
- All other users (`context="default"`): can send and receive (but not own)

---

## GTK4 app — dbus/aimos_scheduler_app.py

**File:** `ai-daemon/dbus/aimos_scheduler_app.py`

`Adw.ApplicationWindow` (`org.aimos.SchedulerApp`) displaying:
- D-Bus + kernel module status (via `IsKernelModuleLoaded()`)
- Scrollable list of all processes from `/proc` with PID and current nice value
- SpinButton for nice value (range −20 to 19)
- "Set Priority" button → `SetProcessPriority(pid, nice)` D-Bus call
- "Refresh" button

Launched from the GNOME Shell extension on indicator click, or directly:

```bash
python3 ai-daemon/dbus/aimos_scheduler_app.py
```

Desktop entry: `desktop/org.aimos.SchedulerApp.desktop`

---

## /proc/aimos_scheduler interface

Implemented in `kernel-modules/aimos_scheduler/aimos_scheduler.c`.

### Read

```bash
cat /proc/aimos_scheduler
```
Returns:
```
AI_M_OS Scheduler active. Write: <pid> <nice_value>
```

The C# `SchedulerWidget` also parses a richer format with 6 fields (`status:`, `version:`, `last_pid:`, `last_nice:`, `total_ops:`, `last_error:`). This extended format is planned for a future kernel module version.

### Write

```bash
echo "<pid> <nice>" | sudo tee /proc/aimos_scheduler
```

The kernel module:
1. Parses `pid` and `nice_val` from the input with `sscanf`
2. Validates `nice_val` in `[−20, 19]`
3. Calls `find_get_pid(pid)` → `pid_task()` → `set_user_nice(task, nice_val)`
4. Calls `put_pid()` to release the reference

Returns `EINVAL` for bad format or out-of-range nice value. Returns `ESRCH` if PID is not found.

### Module info

```bash
modinfo aimos_scheduler
# author:      Mentolka1207
# description: AI_M_OS AI Scheduler — adjusts process priorities via AI-daemon
# license:     GPL
# version:     0.1
```

---

## Systemd services

| Service file | Unit name | Description |
|---|---|---|
| `iso-profile/airootfs/etc/systemd/system/aimos-ai-daemon.service` | `aimos-ai-daemon` | Python AI daemon (`AIMOS_NO_DB=1` by default in ISO) |
| `systemd/aimos-scheduler-dbus.service` | `aimos-scheduler-dbus` | D-Bus scheduler service, runs as user `aimos` |
| `iso-profile/.../aimos-network-daemon.service` | `aimos-network-daemon` | Go network daemon |
| `iso-profile/.../aimos-power-daemon.service` | `aimos-power-daemon` | Go power daemon |
| `iso-profile/.../aimos-sensor-daemon.service` | `aimos-sensor-daemon` | Go sensor daemon |
| `iso-profile/.../aimos-scheduler-setup.service` | `aimos-scheduler-setup` | Runs `depmod -a` before module load at boot |

AI daemon service definition (ISO):
```ini
[Service]
Type=simple
Environment=AIMOS_NO_DB=1
Environment=AIMOS_INTERVAL=1
WorkingDirectory=/opt/aimos/ai-daemon
ExecStart=/usr/bin/python /opt/aimos/ai-daemon/daemon.py
Restart=on-failure
RestartSec=5
```

---

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `AIMOS_DB_DSN` | `postgresql://aimos:aimos@localhost:5432/aimos_metrics` | PostgreSQL connection string |
| `AIMOS_INTERVAL` | `1` | Metrics collection interval in seconds |
| `AIMOS_NO_DB` | *(unset)* | If set to any value, disables PostgreSQL logging |

---

*For installation, see [INSTALL.md](INSTALL.md).*
*For build instructions, see [BUILD.md](BUILD.md).*
