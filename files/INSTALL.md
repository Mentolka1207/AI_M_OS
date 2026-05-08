# Installation Guide — AI_M_OS

## Table of Contents

1. [Requirements](#requirements)
2. [Download and reassemble the ISO](#download-and-reassemble-the-iso)
3. [Create bootable media](#create-bootable-media)
4. [Virtual machine setup (VMware)](#virtual-machine-setup-vmware)
5. [Boot and install](#boot-and-install)
6. [Post-installation](#post-installation)
7. [Troubleshooting](#troubleshooting)

---

## Requirements

| | Minimum | Recommended |
|---|---|---|
| CPU | x86_64, 2 cores | x86_64, 4+ cores |
| RAM | 4 GB | 8 GB |
| Disk | 30 GB | 50 GB SSD |
| Firmware | UEFI or Legacy BIOS | UEFI |

---

## Download and reassemble the ISO

Download the two parts from the [GitHub Releases](https://github.com/Mentolka1207/AI_M_OS/releases) page or [SourceForge](https://sourceforge.net/projects/ai-m-os/files/).

The ISO is split into two parts because GitHub enforces a 2 GB per-asset limit.

**Linux / WSL / macOS:**
```bash
cat AI_M_OS-*.part1 AI_M_OS-*.part2 > AI_M_OS.iso
```

**Windows (PowerShell):**
```powershell
Get-Content AI_M_OS.part1, AI_M_OS.part2 `
  -Encoding Byte -Raw | Set-Content AI_M_OS.iso -Encoding Byte
```

**Verify the checksum** (compare against the `.sha256` file from the release):
```bash
sha256sum AI_M_OS.iso
```

---

## Create bootable media

**Linux:**
```bash
# Verify your device with lsblk before writing
sudo dd if=AI_M_OS.iso of=/dev/sdX bs=4M status=progress oflag=sync
```

**Windows:** use [Rufus](https://rufus.ie/) or [balenaEtcher](https://etcher.balena.io/). In Rufus: select GPT + DD Image mode for UEFI targets.

---

## Virtual machine setup (VMware)

AI_M_OS is developed and tested in VMware Workstation on Windows 11 Pro. This is the recommended evaluation environment.

1. **New Virtual Machine → Custom (advanced)**
2. Guest OS: `Linux` → `Other Linux 6.x kernel 64-bit`
3. Hardware:
   - Memory: 4 GB minimum (8 GB recommended)
   - Processors: 2 cores minimum
   - Hard disk: 50 GB, single file
   - Network: NAT
4. CD/DVD: point to the reassembled ISO
5. Display: enable **3D acceleration**

`open-vm-tools` is included in the ISO and enabled via `vmtoolsd.service` and `vmware-vmblock-fuse.service`.

---

## Boot and install

The ISO boots into a live GNOME environment with auto-login as root.

1. Boot from the ISO — GRUB shows:
   - `AI_M_OS (x86_64, UEFI/BIOS)` — default
   - `AI_M_OS with speech` — speakup screen reader
2. Open a terminal (GNOME Terminal is included)
3. Run the installer:

```bash
archinstall
```

Recommended settings:

| Setting | Value |
|---|---|
| Disk | your target disk, `ext4` |
| Bootloader | `grub` |
| Profile | `gnome` |
| Audio | `pipewire` |
| Network | `NetworkManager` |
| Language | `en_US.UTF-8` (or your locale) |

4. Confirm and install. Reboot when complete.

---

## Post-installation

### 1. Verify the kernel module loaded

The ISO is configured to autoload `aimos_scheduler` via `/etc/modules-load.d/aimos_scheduler.conf`. After reboot:

```bash
lsmod | grep aimos_scheduler
cat /proc/aimos_scheduler
# Expected: "AI_M_OS Scheduler active. Write: <pid> <nice_value>"
```

If the module is not loaded (e.g., after a kernel update):
```bash
sudo dkms install aimos_scheduler/0.5.0
sudo modprobe aimos_scheduler
```

### 2. Check the AI daemon

```bash
systemctl status aimos-ai-daemon.service
journalctl -u aimos-ai-daemon.service -f
```

The daemon runs with `AIMOS_NO_DB=1` by default in the ISO (`/etc/systemd/system/aimos-ai-daemon.service`). To enable PostgreSQL:

```bash
sudo systemctl edit aimos-ai-daemon.service
# Add:
# [Service]
# Environment=AIMOS_NO_DB=
# Environment=AIMOS_DB_DSN=postgresql://aimos:aimos@localhost/aimos_metrics
```

### 3. Check the D-Bus scheduler service

```bash
systemctl status aimos-scheduler-dbus.service
# Verify D-Bus name is registered:
busctl list | grep aimos
```

### 4. Verify Go daemons

```bash
systemctl status aimos-network-daemon aimos-power-daemon aimos-sensor-daemon
# Check sockets exist:
ls /run/aimos/
# Expected: network-daemon.sock  power-daemon.sock  sensor-daemon.sock
```

### 5. Check the GNOME Shell extension

The top bar should show `[] ACTIVE` if the kernel module is loaded. If the indicator shows `X OFFLINE`:

```bash
journalctl /usr/bin/gnome-shell -f
gnome-extensions list --enabled | grep aimos
```

### 6. Update the system

```bash
sudo pacman -Syu
```

> **Note:** After a kernel update, DKMS will automatically rebuild `aimos_scheduler.ko`. Verify with `dkms status`.

---

## Troubleshooting

### Kernel module version mismatch after update

```bash
dkms status
# If module shows "broken":
sudo dkms remove aimos_scheduler/0.5.0 --all
sudo dkms add /usr/src/aimos_scheduler-0.5.0
sudo dkms install aimos_scheduler/0.5.0
```

### No audio

PipeWire is the audio server. Check:
```bash
systemctl --user status pipewire pipewire-pulse wireplumber
systemctl --user restart pipewire pipewire-pulse wireplumber
```

### No network in VM

```bash
systemctl status NetworkManager
sudo systemctl restart NetworkManager
```

### Black screen after boot (VMware)

Enable 3D acceleration in VM settings → Display. As a temporary boot fix, add `nomodeset` to kernel parameters in GRUB.

### D-Bus service fails to start

The service runs as user `aimos` (defined in `systemd/aimos-scheduler-dbus.service`). Ensure the user exists:
```bash
id aimos
# If not: sudo useradd -r -s /usr/bin/nologin aimos
```

---

*For build instructions, see [BUILD.md](BUILD.md).*
*For AI daemon API, see [AI_DAEMON.md](AI_DAEMON.md).*
