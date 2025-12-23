# Простая инструкция по миграции clans

## Шаг 1: Убедитесь, что файл миграции существует

Проверьте, что на сервере есть файл:
```
clans/migrations/0001_initial.py
```

Если его нет, скопируйте его с локальной машины.

## Шаг 2: Примените миграцию

```bash
python manage.py migrate clans
```

Если миграция успешно применена, вы увидите:
```
Running migrations:
  Applying clans.0001_initial... OK
```

## Шаг 3: Если возникает ошибка о существующей таблице

Если вы видите ошибку типа "table already exists", это означает, что таблица `clans_clan` уже существует. В этом случае:

### Вариант A: Использовать --fake (если таблица уже создана вручную)

```bash
python manage.py migrate clans --fake
```

### Вариант B: Если таблица называется accounts_clan

Если на сервере есть таблица `accounts_clan` вместо `clans_clan`, нужно её переименовать. Создайте временный скрипт:

```python
# rename_clan_table.py
import sqlite3
import os
from django.conf import settings

db_path = settings.DATABASES['default']['NAME']
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Проверяем, существует ли accounts_clan
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='accounts_clan'")
if cursor.fetchone():
    # Переименовываем таблицу
    cursor.execute("ALTER TABLE accounts_clan RENAME TO clans_clan")
    conn.commit()
    print("Table renamed successfully")
else:
    print("Table accounts_clan does not exist")

conn.close()
```

Затем выполните:
```bash
python manage.py shell < rename_clan_table.py
```

Или используйте Django shell напрямую:
```bash
python manage.py shell
```

В shell выполните:
```python
from django.db import connection
cursor = connection.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='accounts_clan'")
if cursor.fetchone():
    cursor.execute("ALTER TABLE accounts_clan RENAME TO clans_clan")
    connection.commit()
    print("Table renamed")
```

## Шаг 4: Создайте миграции для accounts и landmarks (если нужно)

После успешной миграции clans:

```bash
python manage.py makemigrations accounts
python manage.py makemigrations landmarks
python manage.py migrate
```

## Шаг 5: Перезапустите сервер

```bash
sudo systemctl restart gunicorn
```

## Проверка

После применения миграций попробуйте создать клан через API. Если всё работает, значит миграция прошла успешно.

