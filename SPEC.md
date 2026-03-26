# MCP Knowledge Base Server — Спецификация

## 📋 Концепция

**Назначение:** MCP-сервер для управления знаниями и требованиями по проектам с быстрым полнотекстовым поиском.

**Архитектура данных:**
```
Проект (Project)
    └── Требование (Requirement)
            └── Запись знания (KnowledgeEntry)
                    └── Тег (Tag)
```

**Ключевые принципы:**
1. **Проекто-центричность** — всё привязано к проекту
2. **Полнотекстовый поиск** — SQLite FTS5 для мгновенного поиска
3. **Минимализм** — простая структура, быстрый старт
4. **CLI-first** — управление через командную строку + MCP tools

---

## 🏗️ Архитектура системы

```
┌─────────────────────────────────────────────────────────────┐
│                      MCP Server                             │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   CLI Tool  │  │ MCP Tools   │  │  HTTP/REST API      │  │
│  │  (typer)    │  │  (tools)    │  │  (optional)         │  │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘  │
│         │                │                    │             │
│  ┌──────▼────────────────▼────────────────────▼──────────┐  │
│  │                  Service Layer                        │  │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────────┐   │  │
│  │  │ ProjectSvc  │ │ RequireSvc  │ │ KnowledgeSvc    │   │  │
│  │  └─────────────┘ └─────────────┘ └─────────────────┘   │  │
│  └──────────────────────────┬────────────────────────────┘  │
│                              │                               │
│  ┌──────────────────────────▼────────────────────────────┐  │
│  │               Repository Layer                         │  │
│  │  ┌─────────────────────────────────────────────────┐   │  │
│  │  │              SQLite + FTS5                      │   │  │
│  │  └─────────────────────────────────────────────────┘   │  │
│  └─────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 🗄️ Модель данных (SQLite)

### Таблица `projects`
```sql
CREATE TABLE projects (
    id TEXT PRIMARY KEY,           -- UUID
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE VIRTUAL TABLE projects_fts USING fts5(
    name, description, 
    content='projects', 
    content_rowid='rowid'
);
```

### Таблица `requirements`
```sql
CREATE TABLE requirements (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id),
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    priority TEXT CHECK(priority IN ('high', 'medium', 'low')),
    status TEXT DEFAULT 'open',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE VIRTUAL TABLE requirements_fts USING fts5(
    title, content,
    content='requirements',
    content_rowid='rowid'
);
```

### Таблица `knowledge_entries`
```sql
CREATE TABLE knowledge_entries (
    id TEXT PRIMARY KEY,
    requirement_id TEXT REFERENCES requirements(id),
    project_id TEXT NOT NULL REFERENCES projects(id),
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    source_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE VIRTUAL TABLE knowledge_fts USING fts5(
    title, content,
    content='knowledge_entries',
    content_rowid='rowid'
);
```

### Таблица `tags`
```sql
CREATE TABLE tags (
    id TEXT PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    color TEXT DEFAULT '#808080'
);

CREATE TABLE entry_tags (
    entry_id TEXT REFERENCES knowledge_entries(id),
    tag_id TEXT REFERENCES tags(id),
    PRIMARY KEY (entry_id, tag_id)
);
```

---

## 🔧 MCP Tools (Инструменты)

### Проекты (Projects)
| Tool | Описание | Параметры |
|------|----------|-----------|
| `projects_list` | Список всех проектов | `limit`, `offset` |
| `project_create` | Создать проект | `name`, `description` |
| `project_get` | Получить проект | `project_id` |
| `project_update` | Обновить проект | `project_id`, `name`, `description` |
| `project_delete` | Удалить проект | `project_id` |
| `project_search` | Поиск по проектам | `query` |

### Требования (Requirements)
| Tool | Описание | Параметры |
|------|----------|-----------|
| `requirements_list` | Список требований проекта | `project_id`, `status`, `priority` |
| `requirement_create` | Создать требование | `project_id`, `title`, `content`, `priority` |
| `requirement_get` | Получить требование | `requirement_id` |
| `requirement_update` | Обновить требование | `requirement_id`, `title`, `content`, `status` |
| `requirement_delete` | Удалить требование | `requirement_id` |

### Записи знаний (Knowledge)
| Tool | Описание | Параметры |
|------|----------|-----------|
| `knowledge_list` | Список записей | `project_id`, `requirement_id`, `tags` |
| `knowledge_create` | Создать запись | `project_id`, `requirement_id`, `title`, `content`, `tags` |
| `knowledge_get` | Получить запись | `entry_id` |
| `knowledge_update` | Обновить запись | `entry_id`, `title`, `content` |
| `knowledge_delete` | Удалить запись | `entry_id` |
| `knowledge_search` | Полнотекстовый поиск | `query`, `project_id`, `limit` |

### Теги (Tags)
| Tool | Описание | Параметры |
|------|----------|-----------|
| `tags_list` | Список всех тегов | - |
| `tag_create` | Создать тег | `name`, `color` |
| `tag_delete` | Удалить тег | `tag_id` |

---

## 💡 Примеры использования

### CLI команды
```bash
# Проекты
kb project create "E-Commerce Platform" "Основной сайт продаж"
kb project list
kb project search "E-Commerce"

# Требования
kb req create "project-uuid" "Авторизация" "Реализовать OAuth2" --priority high
kb req list "project-uuid" --status open

# Знания
kb add "project-uuid" "API Docs" "Документация REST API v2" --tags api,docs
kb search "authentication"

# Поиск
kb search "OAuth2" --project "project-uuid"
```

### MCP Tools (JSON-RPC)
```json
// knowledge_search
{
  "tool": "knowledge_search",
  "args": {
    "query": "OAuth2 authentication",
    "project_id": "project-uuid",
    "limit": 10
  }
}
```

---

## 📁 Структура проекта

```
kb-mcp-server/
├── SPEC.md
├── pyproject.toml
├── src/
│   └── kb_mcp/
│       ├── __init__.py
│       ├── main.py              # Точка входа MCP
│       ├── cli.py               # CLI интерфейс
│       ├── config.py            # Конфигурация
│       ├── models/
│       │   ├── __init__.py
│       │   ├── project.py
│       │   ├── requirement.py
│       │   ├── knowledge.py
│       │   └── tag.py
│       ├── db/
│       │   ├── __init__.py
│       │   ├── database.py      # SQLite connection
│       │   ├── schema.py        # Миграции
│       │   └── repositories/
│       │       ├── __init__.py
│       │       ├── project_repo.py
│       │       ├── requirement_repo.py
│       │       ├── knowledge_repo.py
│       │       └── tag_repo.py
│       ├── services/
│       │   ├── __init__.py
│       │   ├── project_service.py
│       │   ├── requirement_service.py
│       │   ├── knowledge_service.py
│       │   └── search_service.py
│       └── mcp/
│           ├── __init__.py
│           └── tools.py         # MCP tools definitions
├── data/
│   └── kb.db                    # SQLite database
└── tests/
    └── ...
```

---

## 🔄 Поток данных

```
Пользователь/AI
     │
     ▼
┌─────────────┐
│   CLI или   │
│   MCP Tool  │
└──────┬──────┘
       │ Request
       ▼
┌─────────────┐
│   Service   │
│   Layer     │
└──────┬──────┘
       │ CRUD + Search
       ▼
┌─────────────┐     ┌─────────────┐
│ Repository  │────▶│    FTS5     │
│   Layer     │     │   Index     │
└──────┬──────┘     └─────────────┘
       │
       ▼
┌─────────────┐
│   SQLite    │
│   Database  │
└─────────────┘
```

---

## 🎯 Приоритеты реализации

1. **MVP (Minimal Viable Product):**
   - SQLite + FTS5 база
   - CRUD для проектов
   - CRUD для знаний
   - Полнотекстовый поиск
   - MCP tools

2. **v1.1:**
   - Требования (requirements)
   - Теги
   - CLI интерфейс

3. **v1.2+:**
   - HTTP API
   - Импорт/экспорт
   - Интеграция с Obsidian
   - Markdown рендеринг
