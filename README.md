# AI_M_OS

**AI_M_OS** is a custom operating system based on Arch Linux with AI integrated at the kernel level.

![version](https://img.shields.io/badge/version-Alpha%200.3.0-blue)
![base](https://img.shields.io/badge/base-Arch%20Linux-1793d1)
![DE](https://img.shields.io/badge/DE-GNOME%2050-4a86cf)
![kernel](https://img.shields.io/badge/kernel-6.19.14--arch1-orange)
![license](https://img.shields.io/badge/license-MIT-green)

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
| C# GTK4 System Monitor | 🔄 In progress |
| D-Bus integration + GNOME Shell extension | 🔄 In progress |
| PostgreSQL event logger | 🔄 In progress |
| AIFS filesystem (btrfs-based, CoW) | ⏳ Planned |
| ARM64 support | ⏳ Planned |
| Real hardware testing | ⏳ Planned |
| Stable Release 1.0 | ⏳ Planned |

---

## Features

- **AI Scheduler** — Python daemon with real-time CPU, RAM and load average monitoring. Applies `renice` heuristics automatically under high load.
- **Kernel Module** — `aimos_scheduler.ko` exposes `/proc/aimos_scheduler` for read/write. Python daemon communicates with the kernel directly; falls back to `os.setpriority()` if module is absent.
- **Go Daemons** — lightweight system daemons for power, network and sensor monitoring.
- **Glassmorphism UI** — custom GNOME Shell CSS theme with blur and transparency effects.
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
│   ├── dbus/                   # D-Bus service (in progress)
│   ├── db/                     # PostgreSQL event logger (in progress)
│   └── proto/                  # Protobuf client (planned)
├── csharp-apps/
│   └── SystemMonitor/          # C# GTK4 System Monitor (in progress)
├── go-daemons/
│   └── cmd/
│       ├── power-daemon/       # Power management ✅
│       ├── network-daemon/     # Network monitoring ✅
│       └── sensor-daemon/      # Temperature and fans ✅
├── kernel-modules/
│   └── aimos_scheduler/        # Kernel module C + DKMS ✅
├── iso-profile/                # archiso build profile ✅
├── desktop/                    # .desktop files (planned)
└── systemd/                    # systemd units (planned)
```

---

## How the kernel interface works

```
heuristics.py
     │
     │  renice_via_kernel(pid, nice)
     ▼
kernel_iface.py
     │
     │  write: "pid nice\n"       read: "status: active\n..."
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
- `python3`, `pip`
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

# Build and load kernel module
cd kernel-modules/aimos_scheduler
make
sudo insmod aimos_scheduler.ko
cat /proc/aimos_scheduler   # verify: status: active

# Run AI daemon (no DB mode)
cd ../../ai-daemon
AIMOS_NO_DB=1 sudo -E python3 daemon.py

# Build ISO (optional)
sudo mkarchiso -v -w /tmp/aimos-work -o ./out iso-profile/
```

---

## Kernel module autoload

The module is registered for autoload on boot via `modules-load.d`:

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
| GUI apps | C# (.NET + GTK4) |
| Desktop config | JavaScript |
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
| Beta 0.5.0 | 🔄 In progress | C# System Monitor, D-Bus, GNOME Shell extension, PostgreSQL logger |
| RC 0.9.0 | ⏳ Planned | Real hardware support, ARM64, DKMS packaging |
| Release 1.0 | ⏳ Planned | Stable release, AIFS filesystem, full documentation |

---

## License

MIT License — see [LICENSE](LICENSE)
