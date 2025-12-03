# Решение ошибки 500 Internal Server Error

## Проблема

Получаете ошибку 500 при отправке POST запроса на `/api/landmarks/save/`.

## Шаги для диагностики

### 1. Проверьте логи gunicorn на сервере

```bash
# Проверьте логи ошибок gunicorn
sudo tail -f /var/log/gunicorn/error.log

# Или если логи в другом месте:
journalctl -u gunicorn -f --no-pager

# Или если запускали вручную, проверьте вывод процесса
```

### 2. Проверьте логи Django

Если у вас настроено логирование Django:

```bash
# Обычно логи находятся в:
tail -f /opt/activegrad_backend/logs/django.log
# или
tail -f /var/log/django/error.log
```

### 3. Проверьте, что миграции применены

```bash
cd /opt/activegrad_backend
source venv/bin/activate  # если используете venv
python manage.py showmigrations landmarks
```

Все миграции должны быть отмечены как `[X]` (применены).

Если нет, выполните:
```bash
python manage.py migrate landmarks
```

### 4. Проверьте структуру базы данных

```bash
python manage.py shell
```

```python
from landmarks.models import PlayerLandmarkObservation
from django.db import connection

# Проверьте, что таблица существует
cursor = connection.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='landmarks_playerlandmarkobservation';")
print(cursor.fetchone())

# Проверьте структуру таблицы
cursor.execute("PRAGMA table_info(landmarks_playerlandmarkobservation);")
print(cursor.fetchall())
```

### 5. Проверьте через тестовый endpoint

Сначала проверьте, работает ли тестовый endpoint:

```bash
curl -X POST http://87.228.97.188/api/landmarks/test/ \
  -H "Authorization: Bearer ВАШ_ТОКЕН" \
  -H "Content-Type: application/json"
```

Если тестовый endpoint работает, значит проблема в конкретном `save/` endpoint.

### 6. Проверьте данные запроса

Убедитесь, что отправляете правильный формат:

```json
{
  "player_id": 1,
  "external_ids": ["384115"]
}
```

**Важно:**
- `player_id` должен быть числом
- `external_ids` должен быть массивом строк (даже если это числа, оберните в кавычки)

### 7. Проверьте права доступа к базе данных

```bash
# Если используете SQLite
ls -la /opt/activegrad_backend/db.sqlite3
# Убедитесь, что у пользователя, под которым запущен gunicorn, есть права на запись
```

## Возможные причины ошибки 500

### 1. Миграции не применены

**Решение:**
```bash
cd /opt/activegrad_backend
python manage.py migrate
```

### 2. Проблема с базой данных

**Решение:**
```bash
python manage.py check --database default
```

### 3. Ошибка в коде (теперь должна логироваться)

Я добавил обработку ошибок и логирование. Проверьте логи, чтобы увидеть точную ошибку.

### 4. Проблема с сериализацией данных

Убедитесь, что `external_ids` - это массив строк:
- ✅ Правильно: `["384115"]` или `["Q12345"]`
- ❌ Неправильно: `[384115]` (массив чисел)

## Временное решение для отладки

Я добавил улучшенную обработку ошибок. Теперь:

1. **Перезапустите gunicorn:**
   ```bash
   sudo systemctl restart gunicorn
   ```

2. **Попробуйте запрос снова**

3. **Проверьте логи сразу после запроса:**
   ```bash
   sudo tail -20 /var/log/gunicorn/error.log
   ```

4. **Если видите ошибку в логах**, пришлите её мне для дальнейшей диагностики.

## Формат запроса для тестирования

```bash
# Получите токен
TOKEN=$(curl -X POST http://87.228.97.188/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"ваш_username","password":"ваш_пароль"}' \
  | jq -r '.access')

# Отправьте запрос
curl -X POST http://87.228.97.188/api/landmarks/save/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"player_id": 1, "external_ids": ["384115"]}' \
  -v
```

Флаг `-v` покажет подробную информацию о запросе и ответе.

## Что я изменил в коде

1. Добавил обработку всех исключений
2. Добавил логирование ошибок
3. Добавил преобразование `external_id` в строку (на случай, если приходит число)
4. Добавил обработку `IntegrityError` (дубликаты)

Теперь ошибки должны логироваться, и вы сможете увидеть точную причину проблемы в логах.

