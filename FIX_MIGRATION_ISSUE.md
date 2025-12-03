# Решение проблемы: no such column: external_id

## Проблема

Ошибка `no such column: landmarks_playerlandmarkobservation.external_id` означает, что миграции не были применены на сервере, или структура базы данных не соответствует модели.

## Решение

### Шаг 1: Подключитесь к серверу

```bash
ssh ваш_пользователь@87.228.97.188
```

### Шаг 2: Перейдите в директорию проекта

```bash
cd /opt/activegrad_backend
```

### Шаг 3: Активируйте виртуальное окружение (если используется)

```bash
source venv/bin/activate
```

### Шаг 4: Проверьте статус миграций

```bash
python manage.py showmigrations landmarks
```

Вы должны увидеть что-то вроде:
```
landmarks
 [X] 0001_initial
 [X] 0002_auto_20251203_2217
```

Если видите `[ ]` (не применено), нужно применить миграции.

### Шаг 5: Примените миграции

```bash
python manage.py migrate landmarks
```

Или примените все миграции:
```bash
python manage.py migrate
```

### Шаг 6: Проверьте структуру таблицы

```bash
python manage.py shell
```

```python
from django.db import connection

cursor = connection.cursor()
cursor.execute("PRAGMA table_info(landmarks_playerlandmarkobservation);")
columns = cursor.fetchall()
for col in columns:
    print(col)
```

Должны увидеть колонки:
- `id`
- `player_id`
- `external_id` ← эта колонка должна быть!
- `observed_at`

### Шаг 7: Перезапустите gunicorn

```bash
sudo systemctl restart gunicorn
```

## Если миграции не найдены

Если при проверке миграций вы видите, что они не существуют, нужно создать их заново:

```bash
# Убедитесь, что код обновлен на сервере
cd /opt/activegrad_backend
git pull  # или как вы обновляете код

# Создайте миграции
python manage.py makemigrations landmarks

# Примените их
python manage.py migrate landmarks
```

## Если проблема с существующими данными

Если в таблице уже есть данные со старой структурой (с колонкой `landmark_id` вместо `external_id`), нужно:

### Вариант 1: Удалить старые данные (если они не важны)

```bash
python manage.py shell
```

```python
from landmarks.models import PlayerLandmarkObservation
PlayerLandmarkObservation.objects.all().delete()
```

Затем примените миграции:
```bash
python manage.py migrate landmarks
```

### Вариант 2: Создать миграцию данных (если данные важны)

Если нужно сохранить данные, создайте кастомную миграцию для переноса данных из старой структуры в новую.

## Быстрая проверка после исправления

```bash
# Проверьте через API
curl -X GET http://87.228.97.188/api/landmarks/player/1/ \
  -H "Authorization: Bearer ВАШ_ТОКЕН"

# Или через админку
# Откройте: http://87.228.97.188/admin/landmarks/playerlandmarkobservation/
```

## Полная последовательность команд

```bash
# 1. Подключитесь к серверу
ssh ваш_пользователь@87.228.97.188

# 2. Перейдите в проект
cd /opt/activegrad_backend
source venv/bin/activate  # если используется venv

# 3. Проверьте миграции
python manage.py showmigrations landmarks

# 4. Примените миграции
python manage.py migrate landmarks

# 5. Проверьте структуру таблицы
python manage.py shell
# В shell выполните:
# from django.db import connection
# cursor = connection.cursor()
# cursor.execute("PRAGMA table_info(landmarks_playerlandmarkobservation);")
# print(cursor.fetchall())

# 6. Перезапустите gunicorn
sudo systemctl restart gunicorn

# 7. Проверьте админку
# Откройте: http://87.228.97.188/admin/landmarks/playerlandmarkobservation/
```

## Если ничего не помогает

Если проблема сохраняется, возможно нужно пересоздать миграции:

```bash
# 1. Удалите старые миграции (кроме __init__.py)
cd /opt/activegrad_backend/landmarks/migrations
rm 000*.py  # НЕ удаляйте __init__.py!

# 2. Создайте новые миграции
cd /opt/activegrad_backend
python manage.py makemigrations landmarks

# 3. Примените их
python manage.py migrate landmarks
```

**ВНИМАНИЕ:** Это удалит все данные из таблицы `landmarks_playerlandmarkobservation`! Используйте только если данные не важны.

