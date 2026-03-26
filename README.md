# 🗄️ Knowledge Base MCP Server

**MCP-сервер для управления знаниями и требованиями по проектам с мгновенным полнотекстовым поиском.**

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## 🎯 Возможности

| Фича | Описание |
|------|----------|
| **Проекты** | Создание и управление проектами |
| **Требования** | Требования с приоритетами и статусами |
| **Знания** | Записи с тегами и полнотекстовым поиском |
| **FTS5** | Мгновенный поиск через SQLite FTS5 |
| **CLI** | Удобный интерфейс командной строки |
| **MCP** | 19 инструментов для AI-ассистентов |

## 📦 Установка

```bash
# Клонирование
git clone https://github.com/aisho-alex/knowledge_base_mcp.git
cd knowledge_base_mcp

# Создание виртуального окружения
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или: venv\Scripts\activate  # Windows

# Установка
pip install -e .
```

## 🚀 Быстрый старт

### 1. Инициализация

```bash
python -m kb_mcp.cli init
```

### 2. Создание проекта

```bash
python -m kb_mcp.cli project create "E-Commerce Platform" \
    --desc "Платформа электронной коммерции"
```

**Результат:**
```
✅ Project created!
Name: E-Commerce Platform
ID: 3d8e96cc-3e0f-4329-980b-1376dfa8314e
```

### 3. Добавление знаний

```bash
# С тегами
python -m kb_mcp.cli kb add \
    "3d8e96cc-3e0f-4329-980b-1376dfa8314e" \
    "OAuth2 Authentication" \
    "Flow: Authorization Code Grant. Providers: Google, GitHub." \
    --tags auth,security,oauth2

# Без тегов
python -m kb_mcp.cli kb add \
    "3d8e96cc-3e0f-4329-980b-1376dfa8314e" \
    "API Endpoints" \
    "REST API: GET /users, POST /orders, DELETE /products"
```

### 4. Поиск

```bash
# Поиск по всем сущностям
python -m kb_mcp.cli search "OAuth2"

# Поиск только в знаниях
python -m kb_mcp.cli kb search "API"

# Фильтрация по тегам
python -m kb_mcp.cli kb list --tags auth,security
```

## 📋 Справка по командам

### Проекты

| Команда | Описание |
|---------|----------|
| `project list` | Список всех проектов |
| `project create <name>` | Создать проект |
| `project get <id>` | Детали проекта |
| `project search <query>` | Поиск проектов |
| `project delete <id>` | Удалить проект |

### Требования

| Команда | Описание |
|---------|----------|
| `req list <project_id>` | Список требований |
| `req create <project_id> <title> <content>` | Создать требование |
| `req get <id>` | Детали требования |

**Приоритеты:** `high`, `medium`, `low`

```bash
python -m kb_mcp.cli req create \
    "3d8e96cc-..." \
    "Авторизация" \
    "Реализовать OAuth2 через Google и GitHub" \
    --priority high
```

### Знания (Knowledge)

| Команда | Описание |
|---------|----------|
| `kb list` | Все записи (опционально: `--project`, `--tags`) |
| `kb add <project_id> <title> <content>` | Добавить запись |
| `kb get <id>` | Детали записи |
| `kb search <query>` | Полнотекстовый поиск |

**Опции:**
- `--tags` — теги через запятую (например: `--tags api,docs`)
- `--req` — привязать к требованию

### Универсальный поиск

```bash
python -m kb_mcp.cli search "OAuth2" --limit 20
```

Ищет по всем проектам, требованиям и знаниям одновременно.

## 🏗️ Архитектура

```
┌─────────────────────────────────────────────────────────────┐
│                         CLI / MCP                           │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                     Service Layer                           │
│  ┌────────────┐ ┌────────────┐ ┌────────────────────────┐  │
│  │  Project   │ │Requirement │ │       Knowledge        │  │
│  │  Service   │ │  Service   │ │        Service         │  │
│  └────────────┘ └────────────┘ └────────────────────────┘  │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                     Repository Layer                         │
│  ┌────────────────────────────────────────────────────────┐  │
│  │              SQLite + FTS5                            │  │
│  │  projects │ requirements │ knowledge_entries │ tags  │  │
│  └────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Модель данных

```
Проект (Project)
    │
    ├── Требование (Requirement)
    │       └── title, content, priority, status
    │
    └── Запись знания (KnowledgeEntry)
            └── title, content, tags[], source_url
```

## 🔧 MCP Tools

Сервер предоставляет **19 инструментов** для интеграции с AI-ассистентами:

### Проекты
- `projects_list` — список проектов
- `project_create` — создать проект
- `project_get` — получить проект
- `project_update` — обновить проект
- `project_delete` — удалить проект
- `project_search` — поиск проектов

### Требования
- `requirements_list` — список требований
- `requirement_create` — создать требование
- `requirement_get` — получить требование
- `requirement_update` — обновить требование
- `requirement_delete` — удалить требование

### Знания
- `knowledge_list` — список записей
- `knowledge_create` — создать запись
- `knowledge_get` — получить запись
- `knowledge_update` — обновить запись
- `knowledge_delete` — удалить запись
- `knowledge_search` — полнотекстовый поиск

### Утилиты
- `unified_search` — универсальный поиск
- `tags_list` — список тегов

### Подключение к Claude Desktop

Добавьте в `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "kb-mcp": {
      "command": "python",
      "args": ["-m", "kb_mcp.main"]
    }
  }
}
```

## 📁 Структура проекта

```
kb-mcp-server/
├── README.md              # Этот файл
├── SPEC.md               # Техническая спецификация
├── pyproject.toml       # Конфигурация Python-пакета
├── .gitignore
├── data/
│   └── kb.db            # SQLite база данных
└── src/
    └── kb_mcp/
        ├── __init__.py
        ├── main.py          # Точка входа MCP
        ├── cli.py           # CLI интерфейс
        ├── config.py       # Конфигурация
        ├── models/          # Pydantic модели
        ├── db/             # SQLite + FTS5
        │   ├── database.py
        │   ├── schema.py
        │   └── repositories/
        ├── services/        # Бизнес-логика
        └── mcp/
            └── tools.py     # MCP инструменты
```

## 🔍 Примеры использования

### Управление требованиями проекта

```bash
# Создаём требования
PROJECT_ID="3d8e96cc-..."

python -m kb_mcp.cli req create "$PROJECT_ID" \
    "FR-001: Авторизация" \
    "Реализовать вход через Google OAuth2" \
    --priority high

python -m kb_mcp.cli req create "$PROJECT_ID" \
    "FR-002: Каталог товаров" \
    "Отображение товаров с пагинацией" \
    --priority medium

python -m kb_mcp.cli req create "$PROJECT_ID" \
    "FR-003: Корзина" \
    "Добавление, удаление, изменение количества товаров" \
    --priority high

# Смотрим требования
python -m kb_mcp.cli req list "$PROJECT_ID"
```

**Результат:**
```
              Requirements (3)              
┏━━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┓
┃ Priority    ┃ Status      ┃ Title          ┃
┡━━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━┩
│ high        │ open        │ FR-001: Автор │
│ medium      │ open        │ FR-002: Катало│
│ high        │ open        │ FR-003: Корзи │
└─────────────┴─────────────┴────────────────┘
```

### Добавление документации

```bash
# API документация
python -m kb_mcp.cli kb add "$PROJECT_ID" \
    "REST API v2" \
    "Base URL: /api/v2
    
    Endpoints:
    GET  /products - список товаров
    GET  /products/{id} - товар по ID
    POST /orders - создать заказ
    GET  /users/me - текущий пользователь" \
    --tags api,docs,rest

# Техническая заметка
python -m kb_mcp.cli kb add "$PROJECT_ID" \
    "Авторизация Google OAuth2" \
    "Scopes: openid, email, profile
    
    Endpoints:
    Authorization: https://accounts.google.com/o/oauth2/v2/auth
    Token: https://oauth2.googleapis.com/token" \
    --tags auth,google,oauth2

# Заметка о микросервисах
python -m kb_mcp.cli kb add "$PROJECT_ID" \
    "Архитектура микросервисов" \
    "Services:
    - auth-service: :8001 (OAuth2)
    - product-service: :8002
    - order-service: :8003
    - notification-service: :8004
    
    Message Broker: Redis Streams" \
    --tags architecture,microservices
```

### Поиск по тегам

```bash
# Все записи с тегом auth
python -m kb_mcp.cli kb list --tags auth

# Записи с несколькими тегами
python -m kb_mcp.cli kb list --tags api,docs

# Все записи проекта
python -m kb_mcp.cli kb list --project "$PROJECT_ID"
```

## ⚙️ Конфигурация

### Переменные окружения

| Переменная | По умолчанию | Описание |
|-----------|---------------|---------|
| `KB_DB_PATH` | `data/kb.db` | Путь к базе данных |
| `KB_DATA_DIR` | `data/` | Директория для данных |

```bash
# Пример с кастомным путём
export KB_DB_PATH=/home/user/my_kb.db
python -m kb_mcp.cli init
```

## 🛠️ Разработка

```bash
# Установка зависимостей для разработки
pip install -e ".[dev]"

# Запуск тестов
pytest tests/

# Проверка кода
ruff check src/
mypy src/
```

## 📄 Лицензия

MIT License — используйте свободно!

## 🤝 Разработка

1. Fork репозитория
2. Создайте ветку (`git checkout -b feature/amazing-feature`)
3. Commit (`git commit -m 'feat: add amazing feature'`)
4. Push (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

**Made with ❤️ for better knowledge management**
