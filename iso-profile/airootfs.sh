#!/usr/bin/env bash
set -e

# Генерируем все локали
locale-gen

# Создать /run/aimos при старте live-системы
mkdir -p /run/aimos

echo "AI_M_OS airootfs.sh complete"
