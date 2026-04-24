#!/usr/bin/env bash
# shellcheck disable=SC2034

iso_name="AI_M_OS"
iso_label="AIMOS_BETA"
iso_publisher="AI_M_OS Project"
iso_application="AI_M_OS Beta 0.5.0"
iso_version="$(date --date="@${SOURCE_DATE_EPOCH:-$(date +%s)}" +%Y.%m.%d)"
install_dir="arch"
buildmodes=('iso')
bootmodes=('bios.syslinux'
           'uefi.systemd-boot')
pacman_conf="pacman.conf"
airootfs_image_type="squashfs"
airootfs_image_tool_options=('-comp' 'zstd' '-Xcompression-level' '1')
bootstrap_tarball_compression=('zstd' '-c' '-T0' '--auto-threads=logical' '--long' '-19')
file_permissions=(
  ["/etc/shadow"]="0:0:400"
  ["/root"]="0:0:750"
  ["/root/.automated_script.sh"]="0:0:755"
  ["/root/.gnupg"]="0:0:700"
  ["/root/customize_airootfs.sh"]="0:0:755"
  ["/usr/local/bin/choose-mirror"]="0:0:755"
  ["/usr/local/bin/power-daemon"]="0:0:755"
  ["/usr/local/bin/network-daemon"]="0:0:755"
  ["/usr/local/bin/sensor-daemon"]="0:0:755"
  ["/usr/local/bin/Installation_guide"]="0:0:755"
  ["/usr/local/bin/livecd-sound"]="0:0:755"
)

# AI-daemon
file_permissions+=(
  ["/opt/aimos/ai-daemon/daemon.py"]="0:0:755"
)
