# Архив кода

Небольшой учебный проект: REST API на FastAPI, который умеет смотреть Python-код как «архив».

Что делает сервис:
- читает `.py` файлы из папки `sample_code`;
- через `ast` находит функции и классы;
- сохраняет их в `SQLite` (`code_archive.db`);
- отдает результаты через API.

## Из чего состоит проект

- `indexer.py` — индексация файлов и запись в БД.
- `database.py` — подключение к SQLite и SQL-запросы.
- `main.py` — API на FastAPI.
- `schemas.py` — модели ответов.
- `sample_code/` — тестовые Python-файлы.

## База данных

Две таблицы:

1. `files`
- `id`
- `path`
- `name`

2. `symbols`
- `id`
- `file_id`
- `name`
- `type` (`function` или `class`)
- `start_line`
- `end_line`
- `docstring`

Индексы:
- по имени символа;
- по типу символа;
- по имени файла.

Это нужно, чтобы поиск работал быстрее.

## Как запустить

```bash
pip install -r requirements.txt
python indexer.py sample_code
uvicorn main:app --reload
```

Документация Swagger:
- `http://127.0.0.1:8000/docs`

## Docker

```bash
docker build -t code-archive .
docker run -p 8000:8000 code-archive
```

## API

### `GET /api/files`
Список файлов и сколько в каждом функций/классов.

### `GET /api/files/{name}/structure`
Структура конкретного файла.

### `GET /api/search?q=auth`
Поиск по имени и docstring.

Дополнительно:
- `type=class` или `type=function`
- `limit`, `offset` для пагинации

### `GET /api/stats`
Общая статистика по базе.

## Важный момент

Если ничего не найдено, API возвращает `[]`.
Ошибку 500 в таких случаях сервис не отдает.
