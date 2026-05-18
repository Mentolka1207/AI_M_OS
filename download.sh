#!/bin/bash
set -e

VERSION="1.0.1"
REPO="Mentolka1207/AI_M_OS"
OUT="AI_M_OS-${VERSION}-x86_64.iso"

echo "==> Downloading AI_M_OS v${VERSION}..."

curl -L --progress-bar \
  "https://github.com/${REPO}/releases/download/v${VERSION}/AI_M_OS-${VERSION}-x86_64.iso.partaa" \
  -o "AI_M_OS-${VERSION}.partaa"

curl -L --progress-bar \
  "https://github.com/${REPO}/releases/download/v${VERSION}/AI_M_OS-${VERSION}-x86_64.iso.partab" \
  -o "AI_M_OS-${VERSION}.partab"

echo "==> Assembling ISO..."
cat "AI_M_OS-${VERSION}.partaa" "AI_M_OS-${VERSION}.partab" > "${OUT}"

echo "==> Cleaning up parts..."
rm "AI_M_OS-${VERSION}.partaa" "AI_M_OS-${VERSION}.partab"

echo "==> Done: ${OUT} ($(du -h "${OUT}" | cut -f1))"
