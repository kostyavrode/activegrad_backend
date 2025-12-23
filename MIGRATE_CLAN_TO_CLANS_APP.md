# Инструкция по миграции Clan из accounts в clans

Если на сервере уже существует таблица `accounts_clan`, нужно выполнить следующие шаги:

## Шаг 1: Проверить существующие таблицы

```bash
python manage.py dbshell
```

В SQLite shell выполните:
```sql
.tables
```

Проверьте, есть ли таблица `accounts_clan`.

## Шаг 2: Если таблица accounts_clan существует

### Вариант A: Перенести данные (если есть важные данные)

```bash
python manage.py dbshell
```

В SQLite shell:
```sql
-- 1. Переименовать старую таблицу
ALTER TABLE accounts_clan RENAME TO accounts_clan_backup;

-- 2. Выйти из dbshell
.exit
```

Затем выполните миграции:
```bash
python manage.py migrate clans
```

Затем вернитесь в dbshell и перенесите данные:
```sql
-- 3. Скопировать данные из backup в новую таблицу
INSERT INTO clans_clan (id, name, description, created_at, created_by_id)
SELECT id, name, description, created_at, created_by_id
FROM accounts_clan_backup;

-- 4. Обновить sequence для автоинкремента (если нужно)
UPDATE sqlite_sequence SET seq = (SELECT MAX(id) FROM clans_clan) WHERE name = 'clans_clan';

-- 5. Удалить backup таблицу (после проверки)
DROP TABLE accounts_clan_backup;
```

### Вариант B: Удалить старую таблицу (если данных нет или они не важны)

```bash
python manage.py dbshell
```

```sql
DROP TABLE IF EXISTS accounts_clan;
.exit
```

Затем:
```bash
python manage.py migrate clans
```

## Шаг 3: Создать миграции для изменений в accounts и landmarks

После того, как таблица clans_clan создана, нужно обновить ссылки в accounts и landmarks:

```bash
python manage.py makemigrations accounts
python manage.py makemigrations landmarks
python manage.py migrate accounts
python manage.py migrate landmarks
```

## Шаг 4: Проверить

```bash
python manage.py dbshell
```

```sql
.schema clans_clan
.tables
```

Убедитесь, что:
- Таблица `clans_clan` существует
- Таблица `accounts_clan` удалена (если она была)
- Все внешние ключи правильно ссылаются на `clans_clan`

