# Changelog

All notable changes to AI_M_OS are documented here.

## [RC 0.9.0] - 2026-04-26

##Changed
- Rebuilt ISO with squashfs compression level 1 for faster boot
- ISO size reduced: 3.1 GB -> 2.9 GB

### Fixed
- Stable squashfs build pipeline via mkarchiso

### Checksums
| File | SHA256 |
|---|---|
| AI_M_OS-2026.04.26-x86_64.iso | 'ab48b36ea6664644c114b477a73c49108b626e1ff00317d71daa795b88181a51' |

---

## [RC 0.9.0] - 2026-04-24

### Added
- Real hardware support (x86_64)
- AI scheduler kernel module (`aimos_scheduler.ko`) via DKMS
- D-Bus scheduler service with GNOME Shell integration
- C# GTK4 System Monitor with Glassmorphism UI
- PostgreSQL metrics logger in AI daemon
- Protobuf client for daemon communication
- systemd service units for all daemons

### Changed
- Kernel module integrated with AI daemon via `/proc`
- Go daemons switched to Unix socket IPC

--

## [Alpha 0.3.0] - 2026-04

### Added
- AI daemon scheduler heuristics (`heuristics.py`)
- PostgreSQL integration for metrics storage
- 'kernel_iface.py' - Python <-> kernel module interface

---

## [Alpha 0.2.0] - 2026-04

## Added
- C# SystemMonitor GTK4 application
- Glassmorphism CSS theme
- CPU, RAM, Disk, Network widgets

---

## [Alpha 0.1.0] - 2026-04-11

### Added
- Initial release
- Base Arch Linux ISO via archiso
- GNOME 50 desktop environment
- Go daemons: power, network, sensor
- Python AI daemon (base)
- AIFS filesystem (btrfs-based)
