# Инструкция по созданию миграции для поля clan

## Проблема
Django не видит изменений в модели (`No changes detected`), но поле `clan` должно быть добавлено в базу данных.

## Решение

### Вариант 1: Принудительное создание миграции

На сервере выполните:

```bash
cd /opt/activegrad_backend
python manage.py makemigrations accounts --empty --name add_clan_field
```

Это создаст пустую миграцию. Затем откройте созданный файл и добавьте операцию:

```python
operations = [
    migrations.AddField(
        model_name='customuser',
        name='clan',
        field=models.ForeignKey(
            blank=True,
            null=True,
            on_delete=django.db.models.deletion.SET_NULL,
            related_name='members',
            to='clans.clan',
            verbose_name='Клан'
        ),
    ),
]
```

### Вариант 2: Проверка состояния БД

Сначала проверьте, есть ли поле в базе:

```bash
python manage.py shell
```

```python
from django.db import connection
cursor = connection.cursor()

# Для SQLite:
cursor.execute("PRAGMA table_info(accounts_customuser);")
columns = [col[1] for col in cursor.fetchall()]  # col[1] - это имя колонки
print("Колонки в accounts_customuser:", columns)

if 'clan_id' in columns:
    print("✓ Поле clan_id уже существует в базе данных")
else:
    print("✗ Поле clan_id отсутствует - нужно создать миграцию")
```

### Вариант 3: Прямое добавление через SQL (если миграции не работают)

```bash
python manage.py dbshell
```

```sql
-- Проверьте, есть ли поле
PRAGMA table_info(accounts_customuser);

-- Если поля нет, добавьте его (только для SQLite):
-- ВНИМАНИЕ: Это не рекомендуется, лучше использовать миграции!
-- ALTER TABLE accounts_customuser ADD COLUMN clan_id INTEGER REFERENCES clans_clan(id);
```

### Вариант 4: Проверка примененных миграций

```bash
python manage.py showmigrations accounts
```

Если видите миграцию с `[X]`, которая должна добавлять поле `clan`, но поля нет в БД, возможно миграция была откачена или применена некорректно.

### После создания/применения миграции

```bash
python manage.py migrate accounts
python manage.py migrate clans  # Убедитесь, что миграции clans тоже применены
```

### Проверка работы

```bash
python manage.py shell
```

```python
from accounts.models import CustomUser
from clans.models import Clan

# Проверьте, что поле доступно
user = CustomUser.objects.first()
print("Has clan attribute:", hasattr(user, 'clan'))
print("Clan value:", user.clan)

# Попробуйте получить клан
if user.clan:
    print("User clan:", user.clan.name)
else:
    print("User has no clan")
```

