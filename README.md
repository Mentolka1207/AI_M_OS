# AI_M_OS

**AI_M_OS** — кастомная операционная система на базе Arch Linux с встроенным AI на уровне ядра.

![Alpha](https://img.shields.io/badge/version-Alpha%200.3.0-blue)
![Arch](https://img.shields.io/badge/base-Arch%20Linux-1793d1)
![GNOME](https://img.shields.io/badge/DE-GNOME%2050-4a86cf)
![License](https://img.shields.io/badge/license-MIT-green)

## Особенности

- **AI-планировщик** — Python daemon, мониторинг нагрузки в реальном времени
- **Go-демоны** — power, network, sensor мониторинг
- **Glassmorphism UI** — кастомная GNOME Shell тема
- **AIFS** — файловая система на базе btrfs с CoW и снапшотами
- **Языковой стек** — C++, Go, Python, C#, Java, JavaScript, PostgreSQL

## Архитектура





AI_M_OS/
├── iso-profile/          # archiso профиль для сборки ISO
│   ├── profiledef.sh
│   ├── packages.x86_64
│   ├── airootfs/         # Файлы live-системы
│   └── airootfs.sh       # Кастомизация chroot
├── go-daemons/           # Системные Go-демоны
│   ├── cmd/
│   │   ├── power-daemon/
│   │   ├── network-daemon/
│   │   └── sensor-daemon/
│   └── go.mod
├── docs/                 # Документация
└── scripts/              # Вспомогательные скрипты


## Требования для сборки

- Arch Linux (WSL2 или нативно)
- `archiso` пакет
- `go` 1.21+
- 10GB свободного места

## Быстрый старт

```bash
# Клонировать
git clone https://github.com/Mentolka1207/AI_M_OS.git
cd AI_M_OS

# Собрать Go-демоны
cd go-daemons
go build ./cmd/power-daemon/
go build ./cmd/network-daemon/
go build ./cmd/sensor-daemon/

# Собрать ISO
cd ..
sudo mkarchiso -v -w /tmp/aimos-work -o ./out iso-profile/
```

## Roadmap

| Версия | Статус | Описание |
|---|---|---|
| Alpha 0.1.0 | ✅ Готово | Base ISO, GNOME 50, Go-демоны, AI-daemon |
| Alpha 0.2.0 | ✅ Готово | C# GUI приложения, glassmorphism
| Alpha 0.3.0 | ✅ Готово | AI-daemon, PostgreSQL, scheduler heuristics | C# GUI приложения, glassmorphism улучшения |
| Beta 0.5.0 | 🔄 В разработке | AI-планировщик kernel module (C), GNOME Software, kernel_iface |
| RC 0.9.0 | ⏳ | Реальное железо, ARM64 |
| Release 1.0 | ⏳ 2030 | Стабильный релиз |

## Стек технологий

| Компонент | Технология |
|---|---|
| Ядро | Linux (Arch) + C++ patches |
| Системные демоны | Go |
| AI-демон | Python |
| GUI приложения | C# (.NET + GTK4) |
| Серверные компоненты | Java |
| Конфигурация | JavaScript |
| База данных | PostgreSQL |
| Файловая система | AIFS (btrfs-based) |

## Лицензия

MIT License — см. [LICENSE](LICENSE)
