# Решение проблемы 404 для /api/landmarks/save/

## Проверка URL структуры

Ваш URL должен быть: `http://87.228.97.188/api/landmarks/save/`

**Важно:** Обратите внимание на trailing slash (`/`) в конце!

## Возможные причины 404:

### 1. Отсутствует trailing slash

Django может требовать trailing slash. Попробуйте оба варианта:
- `http://87.228.97.188/api/landmarks/save/` (с `/` в конце) ✅
- `http://87.228.97.188/api/landmarks/save` (без `/` в конце)

### 2. Сервер не перезагружен

После изменений в коде нужно перезагрузить Django сервер:
```bash
# Остановите сервер (Ctrl+C) и запустите снова
python manage.py runserver 0.0.0.0:8000
```

### 3. Проблема с настройками сервера (nginx/apache)

Если вы используете nginx или apache как reverse proxy, проверьте конфигурацию.

### 4. Проверка через Django shell

Проверьте, что URL правильно зарегистрирован:

```python
python manage.py shell
```

```python
from django.urls import reverse
print(reverse('save-player-landmarks'))
# Должно вывести: /api/landmarks/save/
```

### 5. Проверка через curl локально

Сначала проверьте локально:

```bash
# Получите токен
TOKEN=$(curl -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"ваш_username","password":"ваш_пароль"}' \
  | jq -r '.access')

# Проверьте endpoint
curl -X POST http://localhost:8000/api/landmarks/save/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "player_id": 1,
    "external_ids": ["Q12345"]
  }'
```

## Правильный формат запроса в Postman:

1. **Method:** POST
2. **URL:** `http://87.228.97.188/api/landmarks/save/` (с `/` в конце!)
3. **Headers:**
   - `Content-Type: application/json`
   - `Authorization: Bearer ВАШ_ACCESS_ТОКЕН`
4. **Body (raw JSON):**
   ```json
   {
     "player_id": 1,
     "external_ids": ["Q12345", "Q67890"]
   }
   ```

## Альтернативный способ проверки

Если проблема сохраняется, попробуйте добавить простой тестовый endpoint для проверки:

```python
# В landmarks/views.py добавьте временно:
class TestView(APIView):
    def get(self, request):
        return Response({"status": "OK", "message": "Landmarks app is working"})

# В landmarks/urls.py добавьте:
path('test/', TestView.as_view(), name='test-landmarks'),
```

Затем проверьте: `http://87.228.97.188/api/landmarks/test/`

Если это работает, значит проблема в конкретном endpoint `save/`.

