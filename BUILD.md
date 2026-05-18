# Build Guide — AI_M_OS

## Table of Contents

1. [Build environment](#build-environment)
2. [Dependencies](#dependencies)
3. [Clone the repository](#clone-the-repository)
4. [Build the ISO](#build-the-iso)
5. [Build the kernel module](#build-the-kernel-module)
6. [Build Go daemons](#build-go-daemons)
7. [Build the C# System Monitor](#build-the-c-system-monitor)
8. [Splitting the ISO for release](#splitting-the-iso-for-release)
9. [Troubleshooting](#troubleshooting)

---

## Build environment

| Requirement | Details |
|---|---|
| Build host OS | **Arch Linux** (native or VM) |
| Tested on | Arch Linux in VMware Workstation on Windows 11 Pro |
| WSL2 | Ubuntu WSL2 can be used for Go/C# compilation, but ISO build requires native Arch |
| ISO work directory | `/var/tmp/aimos-build` — **required**, see below |

> `archiso` must run on Arch Linux. Building on Ubuntu or Debian is not supported.

---

## Dependencies

```bash
sudo pacman -Syu
sudo pacman -S archiso base-devel linux-headers \
               go dotnet-sdk python python-pip \
               python-dbus python-psycopg2 \
               dkms git
```

---

## Clone the repository

```bash
git clone git@github.com:Mentolka1207/AI_M_OS.git
cd AI_M_OS
```

---

## Build the ISO

The build profile is in `iso-profile/`. Key settings from `profiledef.sh`:

| Setting | Value |
|---|---|
| `iso_name` | `AI_M_OS` |
| `iso_label` | `AIMOS_BETA` |
| `iso_version` | `1.0.1` |
| `airootfs_image_type` | `squashfs` |
| Compression | `zstd` level `1` (fast decompress, ~2.9 GB output) |
| Boot modes | `bios.syslinux` + `uefi.systemd-boot` |

### Step 1 — Prepare the work directory

The work directory **must be** `/var/tmp/aimos-build`. Using `/tmp` causes tmpfs exhaustion because `/tmp` is a tmpfs and the squashfs build requires several GB of scratch space.

```bash
sudo mkdir -p /var/tmp/aimos-build
sudo rm -rf /var/tmp/aimos-build/*
```

### Step 2 — Run mkarchiso

```bash
sudo mkarchiso -v -m iso \
  -w /var/tmp/aimos-build \
  -o ./out \
  iso-profile/
```

### Step 3 — Verify output

```bash
ls -lh out/*.iso
# Expected: AI_M_OS-*.iso  ~2.9 GB
```

### What the build does

`customize_airootfs.sh` runs inside the chroot during build and:
- Generates locales (`locale-gen`)
- Enables systemd services: `gdm`, `NetworkManager`, `sshd`, `aimos-network-daemon`, `aimos-power-daemon`, `aimos-sensor-daemon`, `aimos-ai-daemon`
- Configures GDM auto-login as root
- Enables the `aimos-glass@aimos` GNOME Shell extension
- Optionally initializes PostgreSQL data directory

The AI daemon is deployed to `/opt/aimos/ai-daemon/` inside the ISO with permissions set in `profiledef.sh`:
```
["/opt/aimos/ai-daemon/daemon.py"]="0:0:755"
```

The kernel module autoloads via:
```
iso-profile/airootfs/etc/modules-load.d/aimos_scheduler.conf
```
Contents: `aimos_scheduler`

---

## Build the kernel module

The module source is in `kernel-modules/aimos_scheduler/`. It uses a standard out-of-tree Makefile:

```makefile
obj-m += aimos_scheduler.o
KDIR := /lib/modules/$(shell uname -r)/build
```

### Manual build (for testing)

```bash
cd kernel-modules/aimos_scheduler/
make
# Output: aimos_scheduler.ko

sudo insmod aimos_scheduler.ko
cat /proc/aimos_scheduler
# Expected: "AI_M_OS Scheduler active. Write: <pid> <nice_value>"

sudo rmmod aimos_scheduler
make clean
```

### DKMS build (for production / ISO)

`dkms.conf` settings:

| Key | Value |
|---|---|
| `PACKAGE_NAME` | `aimos_scheduler` |
| `PACKAGE_VERSION` | `0.5.0` |
| `AUTOINSTALL` | `yes` |
| `DEST_MODULE_LOCATION` | `/updates/dkms` |

```bash
sudo cp -r kernel-modules/aimos_scheduler /usr/src/aimos_scheduler-0.5.0
sudo dkms add aimos_scheduler/0.5.0
sudo dkms build aimos_scheduler/0.5.0
sudo dkms install aimos_scheduler/0.5.0

# Verify
dkms status
# Expected: aimos_scheduler/0.5.0, <kernel>: installed
```

### Arch package (PKGBUILD)

```bash
cd kernel-modules/aimos_scheduler/
makepkg -si
# Installs: aimos-scheduler-dkms
```

---

## Build Go daemons

Go module: `aimos/daemons` (`go-daemons/go.mod`)

Three daemons under `go-daemons/cmd/`:

| Daemon | Socket |
|---|---|
| `network-daemon` | `/run/aimos/network-daemon.sock` |
| `power-daemon` | `/run/aimos/power-daemon.sock` |
| `sensor-daemon` | `/run/aimos/sensor-daemon.sock` |

```bash
cd go-daemons
go build ./cmd/network-daemon -o build/network-daemon
go build ./cmd/power-daemon   -o build/power-daemon
go build ./cmd/sensor-daemon  -o build/sensor-daemon

# Or build all at once
go build ./cmd/...
```

For inclusion in the ISO, binaries are placed at:
```
iso-profile/airootfs/usr/local/bin/network-daemon
iso-profile/airootfs/usr/local/bin/power-daemon
iso-profile/airootfs/usr/local/bin/sensor-daemon
```
Permissions are set in `profiledef.sh` (`0:0:755`).

---

## Build the C# System Monitor

Project: `csharp-apps/SystemMonitor/SystemMonitor.csproj`

| Setting | Value |
|---|---|
| `TargetFramework` | `net10.0` |
| `AssemblyName` | `ai-m-os-sysmon` |
| Dependencies | `GirCore.Gtk-4.0 0.5.0`, `GirCore.Adw-1 0.5.0` |

```bash
cd csharp-apps/SystemMonitor
dotnet build
dotnet publish -c Release -o publish/

# Run
./publish/ai-m-os-sysmon
```

The glassmorphism CSS theme is loaded at runtime from `themes/glassmorphism.css` (copied to output via `<CopyToOutputDirectory>PreserveNewest</CopyToOutputDirectory>`). If the file is absent, an inline fallback CSS is used.

---

## Splitting the ISO for release

GitHub enforces a 2 GB per-asset limit. Split before upload:

```bash
# Split into 1.9 GB parts
split -b 1900M out/AI_M_OS-*.iso AI_M_OS.part

# Rename
mv AI_M_OS.partaa AI_M_OS.part1
mv AI_M_OS.partab AI_M_OS.part2

# Generate checksum
sha256sum AI_M_OS-*.iso > AI_M_OS.iso.sha256
```

Upload `part1`, `part2`, and `.sha256` to the GitHub release. The ISO SHA256 from Release 1.0.0 (2026-05-16):

```
6666792162ddf020e8676b41b810d99aebf59ddc1f485fdc0ebcf54d9e52e6331
```

### Publish via gh CLI

```bash
git tag -a v1.0.1 -m "Release 1.0.1"
git push origin v1.0.1

gh release create v1.0.1 \
  AI_M_OS.part1 \
  AI_M_OS.part2 \
  AI_M_OS.iso.sha256 \
  --title "AI_M_OS Release 1.0.1" \
  --notes-file CHANGELOG.md
```

---

## Troubleshooting

### tmpfs exhaustion during ISO build

**Symptom:** `No space left on device` during `mkarchiso`

**Cause:** work directory is on tmpfs (e.g. `/tmp`).

**Fix:** always use `/var/tmp/aimos-build`:
```bash
df -h /root   # verify ≥10 GB free
sudo rm -rf /var/tmp/aimos-build && sudo mkdir /var/tmp/aimos-build
```

### Package not found during ISO build

**Symptom:** `error: target not found: <package>`

**Fix:** check the package name in `packages.x86_64`:
```bash
pacman -Ss <package-name>
```

### Kernel module version mismatch

**Symptom:** `ERROR: could not insert module: Invalid module format`

**Cause:** module was built against a different kernel.

**Fix:**
```bash
uname -r   # note running kernel
sudo pacman -S linux-headers
cd kernel-modules/aimos_scheduler/
make clean && make
sudo insmod aimos_scheduler.ko
```

### ISO boots to black screen in VMware

Enable 3D acceleration in the VM's Display settings before booting.

---

*For installation instructions, see [INSTALL.md](INSTALL.md).*
*For AI daemon API, see [AI_DAEMON.md](AI_DAEMON.md).*
