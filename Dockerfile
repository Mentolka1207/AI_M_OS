FROM archlinux:base

# System update + base tools
RUN pacman -Syu --noconfirm && \
    pacman -S --noconfirm \
    xorg-server xorg-xinit xterm \
    tigervnc \
    python-websockify \
    gnome gnome-terminal nautilus gdm \
    python python-pip python-psycopg2 \
    networkmanager pipewire pipewire-pulse wireplumber \
    fastfetch nano && \
    pacman -Scc --noconfirm

# Copy AI_M_OS components
COPY ai-daemon/ /opt/aimos/ai-daemon/
COPY aifs/ /opt/aimos/aifs/

# VNC setup (password: aimos)
RUN mkdir -p /root/.vnc && \
    echo "aimos" | vncpasswd -f > /root/.vnc/passwd && \
    chmod 600 /root/.vnc/passwd && \
    printf '#!/bin/sh\nexec gnome-session\n' > /root/.vnc/xstartup && \
    chmod +x /root/.vnc/xstartup

# GDM autologin
RUN mkdir -p /etc/gdm && \
    printf '[daemon]\nAutomaticLoginEnable=True\nAutomaticLogin=root\n' \
    > /etc/gdm/custom.conf

EXPOSE 5900 6080

COPY docker-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

CMD ["/entrypoint.sh"]
