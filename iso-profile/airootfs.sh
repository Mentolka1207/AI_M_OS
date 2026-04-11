#!/usr/bin/env bash
set -euo pipefail
echo "[AI_M_OS] airootfs.sh START"

# Locale
echo "en_US.UTF-8 UTF-8" > /etc/locale.gen
locale-gen
echo "LANG=en_US.UTF-8" > /etc/locale.conf

# Hostname
echo "AI_M_OS" > /etc/hostname
cat > /etc/hosts << 'HOSTS'
127.0.0.1   localhost
::1         localhost
127.0.1.1   AI_M_OS.localdomain AI_M_OS
HOSTS

# OS identity
cat > /etc/os-release << 'OSREL'
NAME="AI_M_OS"
PRETTY_NAME="AI_M_OS Alpha 0.1.0"
ID=aimos
ID_LIKE=arch
BUILD_ID=0.1.0
ANSI_COLOR="1;34"
HOME_URL="https://github.com/aimos"
OSREL

# Timezone
ln -sf /usr/share/zoneinfo/Europe/Kiev /etc/localtime

# Пользователь
useradd -m -G wheel,video,audio,storage -s /bin/bash aimos 2>/dev/null || true
echo "aimos:aimos" | chpasswd
echo "root:aimos" | chpasswd
echo "aimos ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/aimos
chmod 440 /etc/sudoers.d/aimos

# Сервисы
systemctl enable gdm.service
systemctl enable NetworkManager.service

# GDM автологин + Xorg
mkdir -p /etc/gdm
cat > /etc/gdm/custom.conf << 'GDM'
[daemon]
AutomaticLoginEnable=True
AutomaticLogin=aimos
WaylandEnable=false
GDM

# GNOME настройки для нового пользователя
mkdir -p /etc/dconf/db/local.d /etc/dconf/profile
cat > /etc/dconf/profile/user << 'DCONF'
user-db:user
system-db:local
DCONF
cat > /etc/dconf/db/local.d/00-aimos << 'DCONF'
[org/gnome/desktop/interface]
color-scheme='prefer-dark'
font-name='Noto Sans 11'
monospace-font-name='JetBrains Mono 11'
enable-animations=true

[org/gnome/desktop/background]
primary-color='#0d0d2b'
secondary-color='#1a1a3e'
color-shading-type='vertical'
picture-options='none'

[org/gnome/shell]
enabled-extensions=['aimos-glass@aimos']
disable-user-extensions=false
DCONF
dconf update 2>/dev/null || true

# MOTD
echo "AI_M_OS Alpha 0.1.0" > /etc/motd
echo "AI_M_OS Alpha 0.1.0" > /etc/issue

# AI Daemon
mkdir -p /usr/local/lib/aimos
cat > /usr/local/lib/aimos/ai_daemon.py << 'PY'
#!/usr/bin/env python3
import time, logging
logging.basicConfig(level=logging.INFO, format='[AI_M_OS] %(asctime)s: %(message)s')
def main():
    logging.info("AI Daemon Alpha v0.1.0 started")
    while True:
        with open('/proc/loadavg') as f:
            load = f.read().strip().split()[0]
        logging.info(f"load={load}")
        time.sleep(5)
if __name__ == '__main__':
    main()
PY
chmod +x /usr/local/lib/aimos/ai_daemon.py

cat > /etc/systemd/system/aimos-ai-daemon.service << 'SVC'
[Unit]
Description=AI_M_OS AI Daemon Alpha
After=network.target
[Service]
Type=simple
ExecStart=/usr/bin/python3 /usr/local/lib/aimos/ai_daemon.py
Restart=on-failure
[Install]
WantedBy=multi-user.target
SVC
systemctl enable aimos-ai-daemon.service

echo "[AI_M_OS] airootfs.sh DONE"
