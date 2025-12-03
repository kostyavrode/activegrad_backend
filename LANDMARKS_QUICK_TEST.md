# Быстрая инструкция по тестированию Landmarks API

## Что нужно перед началом

1. **JWT токен** - получите его через `/api/token/`
2. **ID игрока** - ID пользователя, для которого сохраняются достопримечательности

---

## 1. Добавление достопримечательности для игрока

### Endpoint: `POST /api/landmarks/save/`

Сохраняет факт того, что игрок был в достопримечательностях с указанными ID из Wikipedia.

### Шаг 1: Получите JWT токен

```bash
curl -X POST http://ваш-сервер/api/token/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "ваш_username",
    "password": "ваш_пароль"
  }'
```

**Скопируйте значение `access` из ответа** - это ваш токен.

### Шаг 2: Отправьте запрос на добавление достопримечательностей

**Формат запроса:**
```bash
curl -X POST http://ваш-сервер/api/landmarks/save/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ВАШ_ACCESS_ТОКЕН" \
  -d '{
    "player_id": 1,
    "external_ids": ["Q12345", "Q67890", "Q11111"]
  }'
```

**Пример с реальными данными:**
```bash
curl -X POST http://localhost:8000/api/landmarks/save/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..." \
  -d '{
    "player_id": 1,
    "external_ids": ["Q12345", "Q67890"]
  }'
```

### Успешный ответ (200):

```json
{
  "success": true,
  "message": "Successfully saved 2 landmark observation(s)",
  "player_id": 1,
  "saved_external_ids": ["Q12345", "Q67890"],
  "total_saved": 2
}
```

### Возможные ошибки:

**Игрок не найден (404):**
```json
{
  "success": false,
  "error": "Player with ID 999 not found"
}
```

**Невалидные данные (400):**
```json
{
  "success": false,
  "errors": {
    "player_id": ["This field is required."],
    "external_ids": ["This list may not be empty."]
  }
}
```

**Нет токена (401):**
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### Тестирование через Postman:

1. **Метод:** POST
2. **URL:** `http://ваш-сервер/api/landmarks/save/`
3. **Headers:**
   - `Content-Type: application/json`
   - `Authorization: Bearer ВАШ_ACCESS_ТОКЕН`
4. **Body (raw JSON):**
   ```json
   {
     "player_id": 1,
     "external_ids": ["Q12345", "Q67890", "Q11111"]
   }
   ```

---

## 2. Получение достопримечательностей другого игрока

### Endpoint: `GET /api/landmarks/player/<player_id>/`

Возвращает список ID достопримечательностей (external_ids), где был указанный игрок.

### Вариант 1: Через URL path

```bash
curl -X GET http://ваш-сервер/api/landmarks/player/1/ \
  -H "Authorization: Bearer ВАШ_ACCESS_ТОКЕН"
```

**Пример:**
```bash
curl -X GET http://localhost:8000/api/landmarks/player/1/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..."
```

### Вариант 2: Через query параметр

```bash
curl -X GET "http://ваш-сервер/api/landmarks/player/?player_id=1" \
  -H "Authorization: Bearer ВАШ_ACCESS_ТОКЕН"
```

**Пример:**
```bash
curl -X GET "http://localhost:8000/api/landmarks/player/?player_id=1" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..."
```

### Успешный ответ (200):

```json
{
  "success": true,
  "player_id": 1,
  "player_username": "testuser",
  "external_ids": ["Q12345", "Q67890", "Q11111", "Q22222"],
  "total_count": 4
}
```

### Возможные ошибки:

**Игрок не найден (404):**
```json
{
  "success": false,
  "error": "Player with ID 999 not found"
}
```

**player_id не указан (400):**
```json
{
  "success": false,
  "error": "player_id is required"
}
```

**Нет токена (401):**
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### Тестирование через Postman:

1. **Метод:** GET
2. **URL:** `http://ваш-сервер/api/landmarks/player/1/` (или с query параметром)
3. **Headers:**
   - `Authorization: Bearer ВАШ_ACCESS_ТОКЕН`
4. **Body:** не требуется

---

## Полный пример тестирования

### Сценарий: Добавить достопримечательности игроку и проверить список

```bash
# 1. Получаем токен
TOKEN=$(curl -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"testpass"}' \
  | jq -r '.access')

echo "Токен получен: $TOKEN"

# 2. Добавляем достопримечательности для игрока ID=1
echo "Добавляем достопримечательности..."
curl -X POST http://localhost:8000/api/landmarks/save/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "player_id": 1,
    "external_ids": ["Q12345", "Q67890", "Q11111"]
  }'

# 3. Получаем список достопримечательностей игрока ID=1
echo -e "\nПолучаем список достопримечательностей игрока..."
curl -X GET http://localhost:8000/api/landmarks/player/1/ \
  -H "Authorization: Bearer $TOKEN"

# 4. Получаем список достопримечательностей другого игрока (ID=2)
echo -e "\nПолучаем список достопримечательностей другого игрока..."
curl -X GET http://localhost:8000/api/landmarks/player/2/ \
  -H "Authorization: Bearer $TOKEN"
```

---

## Что означают external_ids?

`external_ids` - это идентификаторы достопримечательностей из Wikipedia API (Wikidata).

**Примеры:**
- `Q12345` - ID достопримечательности в Wikidata
- `Q67890` - ID другой достопримечательности
- Можно использовать любые строковые идентификаторы

**Важно:** 
- Unity приложение получает эти ID из Wikipedia API
- Unity приложение передает их в ваш API для сохранения
- При получении списка `external_ids`, Unity приложение снова обращается к Wikipedia API, чтобы получить названия и описания достопримечательностей

---

## Проверка в базе данных

### Через Django Shell:

```bash
python manage.py shell
```

```python
from landmarks.models import PlayerLandmarkObservation
from accounts.models import CustomUser

# Проверка всех наблюдений
observations = PlayerLandmarkObservation.objects.all()
print(f"Всего наблюдений: {observations.count()}")

for obs in observations:
    print(f"Игрок: {obs.player.username} (ID: {obs.player.id}), External ID: {obs.external_id}, Дата: {obs.observed_at}")

# Проверка достопримечательностей конкретного игрока
player = CustomUser.objects.get(id=1)
player_landmarks = PlayerLandmarkObservation.objects.filter(player=player)
print(f"\nExternal IDs игрока {player.username} (ID: {player.id}):")
for obs in player_landmarks:
    print(f"  - {obs.external_id} (наблюдено: {obs.observed_at})")
```

### Через Django Admin:

1. Зайдите в админ-панель: `http://ваш-сервер/admin/`
2. Перейдите в **Player landmark observations**
3. Увидите все записи с полями:
   - **Player** - имя игрока
   - **External id** - ID достопримечательности
   - **Observed at** - дата и время наблюдения

---

## Частые проблемы

### "Authentication credentials were not provided"
**Решение:** Добавьте заголовок `Authorization: Bearer ВАШ_ТОКЕН`

### "Player with ID X not found"
**Решение:** Убедитесь, что пользователь с таким ID существует. Проверьте через админку или Django shell.

### "This field is required" для external_ids
**Решение:** Убедитесь, что передаете массив строк, например: `["Q12345", "Q67890"]`, а не `[1, 2, 3]`

### Дубликаты не создаются
**Это нормально!** Если игрок уже был в достопримечательности, повторная запись не создастся. В ответе `saved_external_ids` будет содержать только новые записи.

---

## Краткая шпаргалка

**Добавить достопримечательности:**
```bash
POST /api/landmarks/save/
Body: {"player_id": 1, "external_ids": ["Q12345", "Q67890"]}
```

**Получить достопримечательности игрока:**
```bash
GET /api/landmarks/player/1/
или
GET /api/landmarks/player/?player_id=1
```

**Все запросы требуют:**
- Header: `Authorization: Bearer ВАШ_ТОКЕН`

