#!/bin/bash
set -e

# Start VNC server
vncserver :1 -geometry 1920x1080 -depth 24 -localhost no

# Start noVNC web client on port 6080
websockify --web /usr/share/novnc/ 6080 localhost:5900 &

# Start AI daemon
AIMOS_NO_DB=1 AIMOS_INTERVAL=2 \
  python /opt/aimos/ai-daemon/daemon.py &

echo "AI_M_OS Desktop running:"
echo "  VNC:   localhost:5900  (password: aimos)"
echo "  Web:   http://localhost:6080"

tail -f /dev/null
