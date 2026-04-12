#!/usr/bin/env bash
set -e

# ── Locale ────────────────────────────────────────────────────────────────────
sed -i 's/^#en_US.UTF-8/en_US.UTF-8/' /etc/locale.gen
locale-gen

# ── Enable systemd services ───────────────────────────────────────────────────
systemctl enable gdm
systemctl enable NetworkManager
systemctl enable sshd
systemctl enable aimos-network-daemon
systemctl enable aimos-power-daemon
systemctl enable aimos-sensor-daemon
systemctl enable aimos-ai-daemon

# ── Create /run/aimos at boot ─────────────────────────────────────────────────
mkdir -p /run/aimos

# ── GNOME: disable initial setup ──────────────────────────────────────────────
ln -sf /dev/null /etc/systemd/system/gnome-initial-setup.service 2>/dev/null || true

# ── Auto-login as root in GDM ─────────────────────────────────────────────────
mkdir -p /etc/gdm
cat > /etc/gdm/custom.conf << 'GDMEOF'
[daemon]
AutomaticLoginEnable=True
AutomaticLogin=root
GDMEOF

# ── GNOME Shell extensions: enable aimos-glass ────────────────────────────────
mkdir -p /root/.config
cat > /root/.config/gnome-shell-extensions.conf << 'EXTEOF'
[org.gnome.shell]
enabled-extensions=['aimos-glass@aimos']
EXTEOF

# ── PostgreSQL: init DB for metrics ───────────────────────────────────────────
# (runs only if postgresql is available and not NO_DB mode)
if command -v initdb &>/dev/null; then
    mkdir -p /var/lib/postgres/data
    chown postgres:postgres /var/lib/postgres/data
    su -c "initdb -D /var/lib/postgres/data --locale=en_US.UTF-8" postgres || true
fi

echo "AI_M_OS customize_airootfs.sh complete"
