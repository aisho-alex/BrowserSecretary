# 📚 BrowserSecretary

**Браузерное расширение для сохранения знаний с AI-помощником и графом связей**

Сохраняйте статьи, документацию, сниппеты кода и заметки с любых веб-страниц. Задавайте вопросы — AI найдёт ответ в вашей базе знаний. Визуализируйте связи между записями.

---

## ✨ Возможности

| Функция | Описание |
|---------|----------|
| 📝 **Сохранение** | Выделите текст → ПКМ → "Save to Knowledge Base" или через popup |
| 🔍 **Поиск** | Полнотекстовый поиск по всем записям (SQLite FTS5) |
| 🤖 **Q&A** | Задайте вопрос — AI ответит на основе вашей базы знаний |
| 🕸️ **Граф** | Интерактивная визуализация связей между записями |
| 🏷️ **Теги** | Организация записей с помощью тегов |
| 📂 **Проекты** | Группировка записей по проектам |

---

## 🚀 Быстрый старт

### 1. Запуск сервера

```bash
cd server

# Создаём venv
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или: venv\Scripts\activate  # Windows

# Установка зависимостей
pip install -r requirements.txt

# Конфигурация
cp .env.example .env
# Отредактируйте .env — добавьте LLM_API_KEY

# Запуск
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

### 2. Установка расширения

**Chrome / Edge:**
1. Откройте `chrome://extensions/`
2. Включите "Режим разработчика"
3. Нажмите "Загрузить распакованное расширение"
4. Выберите папку `extension`

**Firefox:**
1. Откройте `about:debugging#/runtime/this-firefox`
2. Нажмите "Load Temporary Add-on"
3. Выберите `extension/manifest.json`

### 3. Иконки

Создайте иконки в `extension/icons/`:
- `icon16.png` (16×16)
- `icon48.png` (48×48)
- `icon128.png` (128×128)

---

## 🏗️ Архитектура

```
┌─────────────────────────────────────────────────────────────────┐
│                   Браузерное расширение (MV3)                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐    │
│  │  Popup   │  │ Content  │  │Background│  │    Graph     │    │
│  │   UI     │  │  Script  │  │ Worker   │  │   (vis.js)   │    │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └──────┬───────┘    │
└───────┼─────────────┼─────────────┼───────────────┼─────────────┘
        │             │             │               │
        └─────────────┴──────┬──────┴───────────────┘
                             │ HTTP REST API
┌────────────────────────────▼────────────────────────────────────┐
│                      FastAPI Backend                             │
│                                                                  │
│  /api/projects/    — CRUD для проектов                          │
│  /api/knowledge/   — CRUD для записей + поиск                   │
│  /api/tags/        — Управление тегами                          │
│  /api/qa/          — Q&A с LLM                                  │
│  /api/graph/       — Данные для графа знаний                    │
│                                                                  │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│               SQLite + FTS5 (полнотекстовый поиск)               │
│                                                                  │
│  projects | knowledge_entries | tags | entry_tags | relations   │
└──────────────────────────────────────────────────────────────────┘
```

---

## 📁 Структура проекта

```
BrowserSecretary/
│
├── server/                         # FastAPI Backend
│   ├── main.py                     # Точка входа
│   ├── config.py                   # Настройки из .env
│   ├── requirements.txt            # Зависимости Python
│   ├── .env.example                # Шаблон конфигурации
│   │
│   ├── routers/
│   │   ├── projects.py             # API проектов
│   │   ├── knowledge.py            # API записей + поиск
│   │   ├── tags.py                 # API тегов
│   │   ├── qa.py                   # Q&A с LLM
│   │   └── graph.py                # API графа
│   │
│   └── services/
│       └── kb_client.py            # Клиент базы знаний
│
├── extension/                      # Browser Extension (Manifest V3)
│   ├── manifest.json               # Манифест расширения
│   │
│   ├── background/
│   │   └── background.js           # Service Worker (context menu)
│   │
│   ├── content/
│   │   ├── content.js              # Content script (inline popup)
│   │   └── content.css             # Стили
│   │
│   ├── popup/
│   │   ├── popup.html              # UI попапа
│   │   └── popup.js                # Логика (Save, Search, Q&A)
│   │
│   ├── graph/
│   │   └── graph.html              # Визуализация графа (vis.js)
│   │
│   └── icons/                      # Иконки расширения
│       ├── icon16.png
│       ├── icon48.png
│       └── icon128.png
│
└── src/kb_mcp/                     # MCP server (опционально)
```

---

## 🔧 Использование

### Сохранение с веб-страницы

**Способ 1: Context Menu**
1. Выделите текст на странице
2. Правый клик → "📚 Save to Knowledge Base"
3. Заполните форму и нажмите Save

**Способ 2: Popup**
1. Кликните на иконку расширения
2. Вкладка "Save"
3. Выберите проект, введите title, content, tags
4. Нажмите "Save Entry"

### Поиск

1. Кликните на иконку расширения
2. Вкладка "Search"
3. Введите запрос — результаты появятся мгновенно

### Вопрос-ответ (Q&A)

1. Кликните на иконку расширения
2. Вкладка "Q&A"
3. Задайте вопрос на естественном языке
4. AI найдёт релевантные записи и сформирует ответ

### Граф знаний

1. Кликните на иконку расширения
2. Вкладка "Graph"
3. Выберите проект (или "All Projects")
4. Нажмите "Open Graph View"
5. Исследуйте связи между записями

---

## ⚙️ Конфигурация

### .env файл

```bash
# Server
HOST=127.0.0.1
PORT=8000
DEBUG=true

# Knowledge Base
KB_DB_PATH=data/kb.db
KB_DATA_DIR=data

# LLM API (OpenAI-compatible)
LLM_API_URL=https://api.openai.com/v1/chat/completions
LLM_API_KEY=sk-your-key-here
LLM_MODEL=gpt-4o-mini

# CORS для расширения
CORS_ORIGINS=chrome-extension://*,moz-extension://*
```

### Поддерживаемые LLM провайдеры

| Провайдер | API URL |
|-----------|---------|
| OpenAI | `https://api.openai.com/v1/chat/completions` |
| Together AI | `https://api.together.xyz/v1/chat/completions` |
| Groq | `https://api.groq.com/openai/v1/chat/completions` |
| OpenRouter | `https://openrouter.ai/api/v1/chat/completions` |
| Ollama (local) | `http://localhost:11434/v1/chat/completions` |

---

## 📊 API Endpoints

| Method | Endpoint | Описание |
|--------|----------|----------|
| `GET` | `/api/projects/` | Список проектов |
| `POST` | `/api/projects/` | Создать проект |
| `GET` | `/api/knowledge/` | Список записей |
| `POST` | `/api/knowledge/` | Создать запись |
| `GET` | `/api/knowledge/search/{query}` | Поиск |
| `GET` | `/api/knowledge/unified/{query}` | Универсальный поиск |
| `POST` | `/api/qa/` | Задать вопрос LLM |
| `GET` | `/api/graph/` | Данные графа |
| `GET` | `/api/tags/` | Список тегов |

---

## 📝 Лицензия

MIT License
