# AI_M_OS

**AI_M_OS** is a custom operating system based on Arch Linux with AI integrated at the kernel level.

![version](https://img.shields.io/badge/version-RC%200.9.0-blue)
![base](https://img.shields.io/badge/base-Arch%20Linux-1793d1)
![DE](https://img.shields.io/badge/DE-GNOME%2050-4a86cf)
![license](https://img.shields.io/badge/license-MIT-green)

## Features

- **AI Scheduler** — Python daemon with real-time load monitoring
- **Kernel Module** — `aimos_scheduler.ko`, integrated with AI daemon via `/proc`
- **Go Daemons** — power, network, sensor monitoring via Unix sockets
- **C# System Monitor** — GTK4 app with Glassmorphism UI
- **D-Bus Integration** — GNOME Shell extension for the scheduler
- **AIFS** — btrfs-based filesystem with CoW and snapshots

- ## Architecture

AI_M_OS/
├── ai-daemon/              # Python AI daemon
│   ├── scheduler/          # Scheduler (kernel_iface.py, heuristics.py)
│   ├── collectors/         # Metrics collectors
│   ├── dbus/               # D-Bus service and GTK4 app
│   ├── db/                 # PostgreSQL logger
│   └── proto/              # Protobuf client
├── csharp-apps/
│   └── SystemMonitor/      # C# GTK4 System Monitor
│       ├── Widgets/        # CPU, RAM, Disk, Network widgets
│       ├── Services/       # SystemMetrics service
│       └── themes/         # Glassmorphism CSS
├── go-daemons/
│   └── cmd/
│       ├── power-daemon/   # Power management
│       ├── network-daemon/ # Network monitoring
│       └── sensor-daemon/  # Temperature and fans
├── kernel-modules/
│   └── aimos_scheduler/    # Kernel module (C + DKMS)
├── iso-profile/            # archiso build profile
├── desktop/                # .desktop files and metadata
└── systemd/                # systemd services

## Build Requirements

- Arch Linux (WSL2 or native)
- `archiso`, `base-devel`, `linux-headers`
- `go` 1.21+
- `python3`, `pip`
- `dotnet-sdk` 10.0+
- 10 GB free disk space

## Quick Start

```bash
# Clone the repository
git clone https://github.com/Mentolka1207/AI_M_OS.git
cd AI_M_OS

# Build Go daemons
cd go-daemons && go build ./cmd/... && cd ..

# Install Python AI daemon
cd ai-daemon && pip install -r requirements.txt && cd ..

# Build C# System Monitor
cd csharp-apps/SystemMonitor && dotnet build && cd ../..

# Build kernel module
cd kernel-modules/aimos_scheduler && make && sudo insmod aimos_scheduler.ko && cd ../..

# Build ISO
sudo mkarchiso -v -w /tmp/aimos-work -o ./out iso-profile/
```

## Download

| File | Size | Link |
|---|---|---|
| ISO Image | 2.9 GB | [SourceForge](https://sourceforge.net/projects/aimos/) |
| Torrent | 15 KB | [GitHub](https://github.com/Mentolka1207/AI_M_OS/raw/master/AI_M_OS-2026.04.26-x86_64.torrent) |

> **SHA256:**
> `ab48b36ea6664644c114b477a73c49108b626e1ff00317d71daa795b88181a51`

## Roadmap

| Version | Status | Description |
|---|---|---|
| Alpha 0.1.0 | ✅ Done | Base ISO, GNOME 50, Go daemons, AI daemon |
| Alpha 0.2.0 | ✅ Done | C# GUI apps, Glassmorphism UI |
| Alpha 0.3.0 | ✅ Done | AI daemon, PostgreSQL, scheduler heuristics |
| Beta 0.5.0 | ✅ Done | AI scheduler kernel module, D-Bus, GNOME integration |
| RC 0.9.0 | ✅ Done | Real hardware support, x86_64 |
| Release 1.0 | ⏳ | Stable release |

## Tech Stack

| Component | Technology |
|---|---|
| Kernel | Linux (Arch) + kernel module (C) |
| System daemons | Go |
| AI daemon | Python |
| GUI apps | C# (.NET + GTK4) |
| Configuration | JavaScript |
| Database | PostgreSQL |
| Filesystem | AIFS (btrfs-based) |

## System Requirements

| | Minimum | Recommended |
|---|---|---|
| RAM | 4 GB | 8 GB |
| Disk | 30 GB | 50 GB |
| CPU | x86_64 | x86_64 multi-core |
| GPU | — | NVIDIA/AMD |

## License

MIT License — see [LICENSE](LICENSE)
