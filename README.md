# AI_M_OS

**AI_M_OS** is a custom operating system based on Arch Linux with AI integrated at the kernel level.

![version](https://img.shields.io/badge/version-1.0.0-brightgreen)
![base](https://img.shields.io/badge/base-Arch%20Linux-1793d1)
![DE](https://img.shields.io/badge/DE-GNOME%2050-4a86cf)
![kernel](https://img.shields.io/badge/kernel-6.19.14--arch1-orange)
![license](https://img.shields.io/badge/license-MIT-green)
[![Download AI_M_OS](https://img.shields.io/sourceforge/dm/ai-m-os.svg)](https://sourceforge.net/projects/ai-m-os/files/)
[![Download AI_M_OS](https://img.shields.io/sourceforge/dt/ai-m-os.svg)](https://sourceforge.net/projects/ai-m-os/files/)

[![Download AI_M_OS](https://a.fsdn.com/con/app/sf-download-button)](https://sourceforge.net/projects/ai-m-os/files/)

---

## Status

| Component | Status |
|---|---|
| Base ISO + GNOME 50 | ✅ Done |
| Go daemons (power, network, sensor) | ✅ Done |
| Python AI daemon + metrics | ✅ Done |
| Scheduler heuristics (CPU/RAM/load) | ✅ Done |
| `aimos_scheduler` kernel module | ✅ Done |
| `/proc/aimos_scheduler` kernel interface | ✅ Done |
| Glassmorphism GNOME theme (CSS) | ✅ Done |
| D-Bus service (`org.aimos.Scheduler`) | ✅ Done |
| GNOME Shell extension (top bar indicator) | ✅ Done |
| C# GTK4 System Monitor | ✅ Done |
| PostgreSQL event logger | ✅ Done |
| DKMS packaging (`aimos-scheduler-dkms`) | ✅ Done |
| AIFS filesystem (btrfs-based, CoW) | ✅ Done |
| Real hardware testing | ⏳ Planned |
| Stable Release 1.0 | ✅ Done |

---

## Features

- **AI Scheduler** — Python daemon with real-time CPU, RAM, and load average monitoring via `/proc/stat`, `/proc/meminfo`, `/proc/loadavg`. Automatically applies `renice` heuristics: throttles the highest-CPU user process when CPU > 85% or load > 1.5× core count; restores nice=0 when CPU < 20%.
- **Kernel Module** — `aimos_scheduler.ko` exposes `/proc/aimos_scheduler`. The daemon writes `<pid> <nice>\n`; the kernel calls `set_user_nice()`. Falls back to `os.setpriority()` transparently if module is absent.
- **D-Bus Service** — `org.aimos.Scheduler` on the system bus. Methods: `SetProcessPriority(ii)→b`, `GetProcessPriority(i)→i`, `IsKernelModuleLoaded()→b`. Signal: `PriorityChanged(iii)`.
- **GNOME Shell Extension** — top bar indicator (`[] ACTIVE` / `[] IDLE` / `X OFFLINE`). Polls D-Bus every 3 seconds. Subscribes to `PriorityChanged` signal. Spawns `aimos_scheduler_app.py` on click.
- **Go Daemons** — three daemons listening on Unix sockets at `/run/aimos/*.sock`, each returning one JSON payload per connection: power (CPU governor, freq, memory, uptime), network (`/proc/net/dev` rx/tx rates), sensor (CPU temp via hwmon/thermal, load avg, disk I/O ops).
- **C# GTK4 System Monitor** — Glassmorphism UI (`.NET 10`, `GirCore.Gtk-4.0`). Five widgets polling at 1–2 s intervals: CPU, RAM, Disk, Network, Scheduler. `SchedulerWidget` parses 6 fields from `/proc/aimos_scheduler`: `status`, `version`, `last_pid`, `last_nice`, `total_ops`, `last_error`.
- **DKMS** — `aimos-scheduler-dkms` PKGBUILD + `dkms.conf`. Module auto-rebuilds on kernel updates.
- **PostgreSQL Metrics** — four tables: `metrics_cpu`, `metrics_memory`, `metrics_network`, `scheduler_events`. Polled every 1 s (configurable via `AIMOS_INTERVAL`). Disable with `AIMOS_NO_DB=1`.

---

## Architecture

```
AI_M_OS/
├── ai-daemon/
│   ├── daemon.py                   # Main loop
│   ├── collectors/metrics.py       # /proc/stat, /proc/meminfo, Go sockets
│   ├── scheduler/
│   │   ├── kernel_iface.py         # /proc/aimos_scheduler read/write + fallback
│   │   └── heuristics.py           # 4 rules: high_cpu, high_mem, high_load, low_cpu_restore
│   ├── dbus/
│   │   ├── scheduler_service.py    # org.aimos.Scheduler service (system bus)
│   │   └── aimos_scheduler_app.py  # GTK4 process manager (Adw.ApplicationWindow)
│   ├── db/
│   │   ├── logger.py               # psycopg2, log_snapshot(), log_scheduler_event()
│   │   └── schema.sql              # PostgreSQL 15+ schema
│   └── proto/client.py             # Unix socket client for Go daemons
├── csharp-apps/SystemMonitor/
│   ├── Widgets/{Cpu,Ram,Disk,Network,Scheduler}Widget.cs
│   └── Services/SystemMetrics.cs   # /proc/stat, /proc/meminfo, /proc/net/dev, /proc/diskstats
├── gnome-extension/
│   ├── extension.js                # PanelMenu.Button, DBusProxy, 3-second poll
│   └── metadata.json               # uuid: aimos-scheduler@aimos.ai-m-os, shell 46–50
├── go-daemons/cmd/
│   ├── power-daemon/               # /sys/devices/system/cpu, /proc/meminfo, /proc/uptime
│   ├── network-daemon/             # /proc/net/dev with snapshot diffing
│   └── sensor-daemon/              # /sys/class/hwmon, /proc/loadavg, /proc/diskstats
├── kernel-modules/aimos_scheduler/
│   ├── aimos_scheduler.c           # proc_ops, set_user_nice(), MODULE_LICENSE("GPL")
│   ├── dkms.conf                   # PACKAGE_VERSION=0.5.0, AUTOINSTALL=yes
│   └── PKGBUILD                    # aimos-scheduler-dkms
├── dbus-policy/org.aimos.Scheduler.conf
├── iso-profile/                    # archiso profile, zstd level 1
│   ├── packages.x86_64
│   ├── profiledef.sh
│   └── airootfs/
│       ├── etc/systemd/system/     # aimos-ai-daemon, network/power/sensor daemons
│       ├── etc/modules-load.d/aimos_scheduler.conf
│       └── opt/aimos/ai-daemon/    # deployed daemon copy
└── systemd/aimos-scheduler-dbus.service
```

---

## Stack connection

```
GNOME Shell extension (extension.js)
        │  D-Bus: IsKernelModuleLoaded(), PriorityChanged signal
        ▼
scheduler_service.py  →  org.aimos.Scheduler (system bus)
        │
        ▼
kernel_iface.py  →  write "pid nice\n" to /proc/aimos_scheduler
        │                        OR  os.setpriority() fallback
        ▼
aimos_scheduler.ko  →  set_user_nice(task, nice_val)
```

---

## Build Requirements

| Tool | Version |
|---|---|
| Arch Linux (build host) | rolling |
| `archiso` | latest |
| `go` | 1.21+ (module: `aimos/daemons`, go 1.26.2) |
| `python3` | 3.12+ |
| `python-dbus`, `psycopg2-binary` | latest |
| `dotnet-sdk` | 10.0 (TargetFramework: net10.0) |
| Disk space for ISO build | 10 GB+ at `/root/aimos-work` |

---

## Quick Start

```bash
git clone https://github.com/Mentolka1207/AI_M_OS.git
cd AI_M_OS

# Go daemons
cd go-daemons && go build ./cmd/... && cd ..

# Python daemon dependencies
cd ai-daemon && pip install -r requirements.txt && cd ..
# requirements.txt: psycopg2-binary>=2.9

# Kernel module via DKMS
sudo cp -r kernel-modules/aimos_scheduler /usr/src/aimos_scheduler-0.5.0
sudo dkms add aimos_scheduler/0.5.0
sudo dkms build aimos_scheduler/0.5.0
sudo dkms install aimos_scheduler/0.5.0
cat /proc/aimos_scheduler
# Expected: "AI_M_OS Scheduler active. Write: <pid> <nice_value>"

# D-Bus service
sudo cp dbus-policy/org.aimos.Scheduler.conf /etc/dbus-1/system.d/
sudo cp systemd/aimos-scheduler-dbus.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now aimos-scheduler-dbus

# GNOME Shell extension
EXT_DIR=~/.local/share/gnome-shell/extensions/aimos-scheduler@aimos.ai-m-os
mkdir -p "$EXT_DIR" && cp gnome-extension/* "$EXT_DIR"/
gnome-extensions enable aimos-scheduler@aimos.ai-m-os

# AI daemon — with PostgreSQL
AIMOS_DB_DSN="postgresql://aimos:aimos@localhost/aimos_metrics" sudo -E python3 ai-daemon/daemon.py

# AI daemon — no DB
AIMOS_NO_DB=1 sudo -E python3 ai-daemon/daemon.py

# Build ISO
sudo mkarchiso -v -w /root/aimos-work -o ./out iso-profile/
```

---

## Tech Stack

| Component | Technology |
|---|---|
| Kernel module | C, GPL, `set_user_nice()` |
| System daemons | Go (`aimos/daemons`) |
| AI daemon | Python 3, psycopg2 |
| D-Bus service | Python, `python-dbus` |
| GUI | C# .NET 10, GTK4 via GirCore 0.5.0 |
| GNOME extension | JavaScript ESM, shell 48–50 |
| Database | PostgreSQL 15+ |
| IPC | Unix sockets `/run/aimos/*.sock` |
| ISO compression | squashfs, zstd level 1 |

---

## System Requirements

| | Minimum | Recommended |
|---|---|---|
| RAM | 4 GB | 8 GB |
| Disk | 30 GB | 50 GB |
| CPU | x86_64 | x86_64 multi-core |

---

## Roadmap

| Version | Status | Description |
|---|---|---|
| Alpha 0.1.0 | ✅ | Base ISO, GNOME 50, Go daemons |
| Alpha 0.2.0 | ✅ | Glassmorphism UI, Python AI daemon |
| Alpha 0.3.0 | ✅ | `aimos_scheduler` kernel module, heuristics, `/proc` interface |
| Beta 0.5.0 | ✅ | C# System Monitor, D-Bus, GNOME extension |
| RC 0.9.0 | ✅ | PostgreSQL ✅, DKMS ✅, AIFS ✅, real hardware ✅ |
| Release 1.0 | ✅ | Stable release |

---

## Download

- **GitHub Releases:** [github.com/Mentolka1207/AI_M_OS/releases](https://github.com/Mentolka1207/AI_M_OS/releases)
- **SourceForge:** [sourceforge.net/projects/ai-m-os](https://sourceforge.net/projects/ai-m-os/files/)

---

## License

MIT — see [LICENSE](LICENSE)
