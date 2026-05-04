# Changelog

All notable changes to AI_M_OS are documented here.

## [Unreleased] - RC 0.9.0 progress - 2026-05-04

### Added
- DKMS packaging for 'aimos_scheduler' - module auto-rebuilds on kernel update
- 'PKGBULD' for 'aimos-scheduler-dkms' Arch package
- PostgreSQL event logger completed - all 4 heuristic rules ('high_cpu', 'high_load', 'low_cpu_restore') write to 'scheduler_events' table
- 'schema.sql' applied: 'metrics_cpu', metrics_memory', 'metrics_network', 'scheduler_events' tables

### Fixed
- 'heuristics.py': 'log_scheduler_event()' now called for all 4 rules, not just 'high_cpu'
- 'dkms.conf': version updated to '0.5.0', added 'BUILT_MODULE_LOCATION[0]'

---

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

## [Alpha 0.3.0] - 2026-04-27

### Added
- 'aimos_scheduler.c' - kernel module exposing '/proc/aimos_scheduler' (read/write)
- 'aimos_scheduler.ko' built and tested on kernel 6.19.14-arch1-1
- Kernel module autoload via '/etc/modules-load.d/aimos_scheduler.conf'
- 'kernel_iface.py' - complete parser for '/proc/aimos_scheduler' output (6 fields: status, version, last_pid, last_nice, total_ops, last_error)
- 'heuristics.py' - CPU/RAM/load_avg scheduler heuristics with renice via kernel
- Fallback to `os.setpriority()` when kernel module is not loaded
- PostgreSQL integration for metrics storage (optional, `AIMOS_NO_DB=1` flag)

### Fixed
- Removed duplicate `kernel/scheduler/` directory (canonical: `kernel-modules/aimos_scheduler/`)
- Added kernel build artifacts to `.gitignore` (`.cmd`, `.o`, `.ko`, `.mod` files)

### Changed
- README rewritten as honest roadmap document (  Done /  In progress /  Planned)
- Version badge updated to Alpha 0.3.0

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
