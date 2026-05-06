# AI_M_OS

**AI_M_OS** is a custom operating system based on Arch Linux with AI integrated at the kernel level.

![version](https://img.shields.io/badge/version-RC%200.9.0-blue)
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
| AIFS filesystem (btrfs-based, CoW) | ⏳ Planned |
| ARM64 support | ⏳ Planned |
| Real hardware testing | ⏳ Planned |
| Stable Release 1.0 | ⏳ Planned |

---

## Features

- **AI Scheduler** — Python daemon with real-time CPU, RAM and load average monitoring. Applies `renice` heuristics automatically under high load.
- **Kernel Module** — `aimos_scheduler.ko` exposes `/proc/aimos_scheduler` for read/write. Python daemon communicates with the kernel directly; falls back to `os.setpriority()` if module is absent.
- **D-Bus Service** — `org.aimos.Scheduler` on the system bus. Exposes `SetProcessPriority`, `GetProcessPriority`, `IsKernelModuleLoaded` and emits `PriorityChanged` signal.
- **GNOME Shell Extension** — top bar indicator showing `󰒓 ACTIVE` / `󰒓 IDLE` / `✕ OFFLINE`. Subscribes to `PriorityChanged` signal in real time. Click to open the GTK4 process manager.
- **Go Daemons** — lightweight system daemons for power, network and sensor monitoring.
- **C# GTK4 System Monitor** — Glassmorphism UI with CPU, RAM, Disk, Network and Scheduler widgets.
-  **DKMS Packaging** — `aimos_scheduler` kernel module auto-rebuilds on kernel updates via DKMS.
- **AIFS** — planned btrfs-based filesystem with Copy-on-Write and snapshot support.

---

## Architecture

```
AI_M_OS/
├── ai-daemon/                  # Python AI daemon
│   ├── daemon.py               # Main loop, metrics collection
│   ├── scheduler/
│   │   ├── kernel_iface.py     # /proc/aimos_scheduler interface ✅
│   │   └── heuristics.py       # CPU/RAM/load heuristics ✅
│   ├── collectors/             # Metrics collectors
│   ├── dbus/                   # D-Bus service ✅
│   │   ├── scheduler_service.py    # org.aimos.Scheduler daemon
│   │   └── aimos_scheduler_app.py  # GTK4 process manager
│   ├── db/                     # PostgreSQL event logger ✅
│   └── proto/                  # Protobuf client (planned)
├── csharp-apps/
│   └── SystemMonitor/          # C# GTK4 System Monitor ✅
│       └── Widgets/
│           ├── CpuWidget.cs
│           ├── RamWidget.cs
│           ├── DiskWidget.cs
│           ├── NetworkWidget.cs
│           └── SchedulerWidget.cs  # reads /proc/aimos_scheduler ✅
├── gnome-extension/            # GNOME Shell extension ✅
│   ├── extension.js            # top bar indicator, D-Bus client
│   ├── metadata.json
│   └── stylesheet.css
├── go-daemons/
│   └── cmd/
│       ├── power-daemon/       # Power management ✅
│       ├── network-daemon/     # Network monitoring ✅
│       └── sensor-daemon/      # Temperature and fans ✅
├── kernel-modules/
│   └── aimos_scheduler/        # Kernel module C + DKMS ✅
├── dbus-policy/                # D-Bus security policy ✅
├── iso-profile/                # archiso build profile ✅
├── desktop/                    # .desktop files and metadata ✅
└── systemd/                    # systemd service units ✅
```

---

## How the full stack connects

'''
GNOME Shell extension
        │  D-Bus signal: PriorityChanged
        │  D-Bus call:   IsKernelModuleLoaded
        ▼
org.aimos.Scheduler  (scheduler_service.py)
        │
        │  renice_via_kernel(pid, nice)
        ▼
kernel_iface.py
        │
        │  write: "pid nice\n"     read: "status: active\n..."
        ▼
/proc/aimos_scheduler
        │
        ▼
aimos_scheduler.ko  →  set_user_nice()  [kernel]
```

If `aimos_scheduler.ko` is not loaded, `kernel_iface.py` falls back to `os.setpriority()` transparently.

---


## Build Requirements

- Arch Linux (WSL2 or native)
- `archiso`, `base-devel`, `linux-headers`
- `go` 1.21+
- `python3`, `python-dbus`, `pip`
- `dotnet-sdk` 10.0+
- 10 GB free disk space

---

## Quick Start

```bash
# Clone
git clone https://github.com/Mentolka1207/AI_M_OS.git
cd AI_M_OS

# Build Go daemons
cd go-daemons && go build ./cmd/... && cd ..

# Install Python AI daemon
cd ai-daemon && pip install -r requirements.txt && cd ..

# Build and load kernel module (via DKMS)
sudo cp -r kernel-modules/aimos_scheduler /usr/src/aimos_scheduler-0.5.0
sudo dkms add aimos_scheduler/0.5.0
sudo dkms build aimos_scheduler/0.5.0
sudo dkms install aimos_scheduler/0.5.0
cat /proc/aimos_scheduler   # verify: status: active

# Install D-Bus policy and service
sudo cp dbus-policy/org.aimos.Scheduler.conf /etc/dbus-1/system.d/
sudo cp systemd/aimos-scheduler-dbus.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now aimos-scheduler-dbus

# Install GNOME Shell extension
EXT=~/.local/share/gnome-shell/extensions/aimos-scheduler@aimos.ai-m-os
mkdir -p $EXT
cp gnome-extension/* $EXT/
gnome-extensions enable aimos-scheduler@aimos.ai-m-os

# Run AI daemon (with PostgreSQL)
cd ai-daemon
AIMOS_DB_DSN="postgresql://aimos:aimos@localhost/aimos_metrics" sudo -E python3 daemon.py

# Run AI daemon (no DB mode)
AIMOS_NO_DB=1 sudo -E python3 daemon.py

# Build ISO (optional)
sudo mkarchiso -v -w /tmp/aimos-work -o ./out iso-profile/
'''

---

## Kernel module autoload

```
/etc/modules-load.d/aimos_scheduler.conf
/lib/modules/$(uname -r)/extra/aimos_scheduler.ko
```

Verify with `modinfo aimos_scheduler` and `cat /proc/aimos_scheduler` after reboot.

---

## Tech Stack

| Component | Technology |
|---|---|
| Kernel interface | C (kernel module) |
| System daemons | Go |
| AI daemon + scheduler | Python |
| D-Bus service | Python (`python-dbus`) |
| GUI apps | C# (.NET + GTK4) |
| GNOME Shell extension | JavaScript (ESM) |
| Database | PostgreSQL |
| Filesystem | AIFS (btrfs-based, planned) |

---

## System Requirements

| | Minimum | Recommended |
|---|---|---|
| RAM | 4 GB | 8 GB |
| Disk | 30 GB | 50 GB |
| CPU | x86_64 | x86_64 multi-core |
| GPU | — | NVIDIA / AMD |

---

## Roadmap

| Version | Status | Description |
|---|---|---|
| Alpha 0.1.0 | ✅ Done | Base ISO, GNOME 50, Go daemons |
| Alpha 0.2.0 | ✅ Done | Glassmorphism UI, Python AI daemon |
| Alpha 0.3.0 | ✅ Done | Scheduler heuristics, `aimos_scheduler` kernel module, `/proc` interface |
| Beta 0.5.0 | ✅ Done | C# System Monitor, D-Bus service, GNOME Shell extension |
| RC 0.9.0 | 🔄 In Progress | PostgreSQL logger ✅, DKMS packaging ✅, real hardware support, ARM64 |
| Release 1.0 | ⏳ Planned | Stable release, AIFS filesystem, full documentation |

---

## Download

- **GitHub Releases:** [github.com/Mentolka1207/AI_M_OS/releases](https://github.com/Mentolka1207/AI_M_OS/releases)
- **SourceForge:** [sourceforge.net/projects/ai-m-os](https://sourceforge.net/projects/ai-m-os/files/)

---

## License

MIT License — see [LICENSE](LICENSE)
