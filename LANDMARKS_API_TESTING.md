# Инструкция по тестированию Landmarks API

## Предварительные требования

1. Убедитесь, что все миграции применены:
   ```bash
   python manage.py migrate
   ```

2. Убедитесь, что у вас есть:
   - Активный пользователь в системе (для получения JWT токена)
   - JWT токен для аутентификации

## Шаг 1: Создание тестовых данных (Landmarks)

### Вариант A: Через Django Admin

1. Зайдите в админ-панель: `http://ваш-сервер/admin/`
2. Войдите под учетной записью администратора
3. Перейдите в раздел **Landmarks**
4. Создайте несколько landmarks:
   - Нажмите "Add Landmark"
   - Заполните поля:
     - **Name**: "Центральная площадь"
     - **Description**: "Главная площадь города" (опционально)
     - **External ID**: "landmark_001" (опционально)
   - Сохраните
5. Создайте еще 2-3 landmarks для тестирования

### Вариант B: Через Django Shell

```bash
python manage.py shell
```

```python
from landmarks.models import Landmark

# Создание landmarks
Landmark.objects.create(name="Центральная площадь", description="Главная площадь", external_id="landmark_001")
Landmark.objects.create(name="Парк культуры", description="Городской парк", external_id="landmark_002")
Landmark.objects.create(name="Музей истории", description="Краеведческий музей", external_id="landmark_003")
Landmark.objects.create(name="Стадион", description="Главный стадион города", external_id="landmark_004")

# Проверка созданных landmarks
print(f"Создано landmarks: {Landmark.objects.count()}")
for lm in Landmark.objects.all():
    print(f"ID: {lm.id}, Name: {lm.name}")
```

## Шаг 2: Получение JWT токена

### Получение токена через API:

```bash
# Замените username и password на реальные данные
curl -X POST http://ваш-сервер/api/token/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "ваш_username",
    "password": "ваш_пароль"
  }'
```

**Ответ:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Сохраните `access` токен** - он понадобится для всех запросов к landmarks API.

## Шаг 3: Тестирование POST API - Сохранение landmarks для игрока

### Endpoint: `POST /api/landmarks/save/`

Этот API сохраняет landmarks, где игрок был замечен.

**Запрос:**
```bash
curl -X POST http://ваш-сервер/api/landmarks/save/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ВАШ_ACCESS_ТОКЕН" \
  -d '{
    "player_id": 1,
    "landmark_ids": [1, 2, 3]
  }'
```

**Успешный ответ (200):**
```json
{
  "success": true,
  "message": "Successfully saved 3 landmark observation(s)",
  "player_id": 1,
  "saved_landmark_ids": [1, 2, 3]
}
```

**Если некоторые landmarks не найдены (207):**
```json
{
  "success": true,
  "message": "Successfully saved 2 landmark observation(s) with 1 error(s)",
  "player_id": 1,
  "saved_landmark_ids": [1, 2],
  "errors": ["Landmark with ID 3 not found"]
}
```

**Ошибка - игрок не найден (404):**
```json
{
  "success": false,
  "error": "Player with ID 999 not found"
}
```

**Ошибка - невалидные данные (400):**
```json
{
  "success": false,
  "errors": {
    "player_id": ["This field is required."],
    "landmark_ids": ["This list may not be empty."]
  }
}
```

### Проверка через Postman:

1. Метод: **POST**
2. URL: `http://ваш-сервер/api/landmarks/save/`
3. Headers:
   - `Content-Type: application/json`
   - `Authorization: Bearer ВАШ_ACCESS_ТОКЕН`
4. Body (raw JSON):
   ```json
   {
     "player_id": 1,
     "landmark_ids": [1, 2, 3, 4]
   }
   ```

## Шаг 4: Тестирование GET API - Получение landmarks игрока

### Endpoint 1: `GET /api/landmarks/player/<player_id>/`

Получение через URL path.

**Запрос:**
```bash
curl -X GET http://ваш-сервер/api/landmarks/player/1/ \
  -H "Authorization: Bearer ВАШ_ACCESS_ТОКЕН"
```

**Успешный ответ (200):**
```json
{
  "success": true,
  "player_id": 1,
  "player_username": "testuser",
  "landmarks": [
    {
      "id": 1,
      "name": "Центральная площадь",
      "description": "Главная площадь города",
      "external_id": "landmark_001"
    },
    {
      "id": 2,
      "name": "Парк культуры",
      "description": "Городской парк",
      "external_id": "landmark_002"
    },
    {
      "id": 3,
      "name": "Музей истории",
      "description": "Краеведческий музей",
      "external_id": "landmark_003"
    }
  ],
  "total_count": 3
}
```

### Endpoint 2: `GET /api/landmarks/player/?player_id=1`

Получение через query parameter.

**Запрос:**
```bash
curl -X GET "http://ваш-сервер/api/landmarks/player/?player_id=1" \
  -H "Authorization: Bearer ВАШ_ACCESS_ТОКЕН"
```

**Если игрок не найден (404):**
```json
{
  "success": false,
  "error": "Player with ID 999 not found"
}
```

**Если player_id не указан (400):**
```json
{
  "success": false,
  "error": "player_id is required"
}
```

### Проверка через Postman:

1. Метод: **GET**
2. URL: `http://ваш-сервер/api/landmarks/player/1/` (или с query параметром)
3. Headers:
   - `Authorization: Bearer ВАШ_ACCESS_ТОКЕН`

## Шаг 5: Проверка в базе данных

### Через Django Shell:

```bash
python manage.py shell
```

```python
from landmarks.models import PlayerLandmarkObservation, Landmark
from accounts.models import CustomUser

# Проверка всех наблюдений
observations = PlayerLandmarkObservation.objects.all()
print(f"Всего наблюдений: {observations.count()}")

for obs in observations:
    print(f"Игрок: {obs.player.username}, Landmark: {obs.landmark.name}, Дата: {obs.observed_at}")

# Проверка landmarks конкретного игрока
player = CustomUser.objects.get(id=1)
player_landmarks = PlayerLandmarkObservation.objects.filter(player=player)
print(f"\nLandmarks игрока {player.username}:")
for obs in player_landmarks:
    print(f"  - {obs.landmark.name} (ID: {obs.landmark.id})")
```

### Через Django Admin:

1. Зайдите в админ-панель
2. Перейдите в **Player landmark observations**
3. Проверьте созданные записи

## Шаг 6: Проверка защиты от дубликатов

API автоматически предотвращает создание дубликатов благодаря `unique_together` в модели.

**Тест:**
1. Отправьте POST запрос с теми же `player_id` и `landmark_ids`
2. В ответе `saved_landmark_ids` будет пустым массивом (так как записи уже существуют)
3. В базе данных не создадутся дубликаты

**Запрос:**
```bash
curl -X POST http://ваш-сервер/api/landmarks/save/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ВАШ_ACCESS_ТОКЕН" \
  -d '{
    "player_id": 1,
    "landmark_ids": [1, 2]
  }'
```

**Ответ (дубликаты не созданы):**
```json
{
  "success": true,
  "message": "Successfully saved 0 landmark observation(s)",
  "player_id": 1,
  "saved_landmark_ids": []
}
```

## Шаг 7: Проверка аутентификации

Все endpoints требуют аутентификации. Без токена запрос вернет ошибку:

**Запрос без токена:**
```bash
curl -X GET http://ваш-сервер/api/landmarks/player/1/
```

**Ответ (401):**
```json
{
  "detail": "Authentication credentials were not provided."
}
```

## Чек-лист проверки

- [ ] Миграции применены успешно
- [ ] Создано минимум 3-4 тестовых landmark через админку
- [ ] Получен JWT токен для аутентификации
- [ ] POST `/api/landmarks/save/` успешно сохраняет landmarks
- [ ] GET `/api/landmarks/player/<id>/` возвращает список landmarks игрока
- [ ] GET `/api/landmarks/player/?player_id=<id>` работает через query параметр
- [ ] Обработка ошибок работает (игрок не найден, landmark не найден)
- [ ] Дубликаты не создаются
- [ ] Аутентификация требуется для всех endpoints
- [ ] Данные корректно сохраняются в базе данных

## Пример полного тестового сценария

```bash
# 1. Получение токена
TOKEN=$(curl -X POST http://ваш-сервер/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"testpass"}' \
  | jq -r '.access')

# 2. Сохранение landmarks для игрока ID=1
curl -X POST http://ваш-сервер/api/landmarks/save/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"player_id": 1, "landmark_ids": [1, 2, 3]}'

# 3. Получение landmarks игрока ID=1
curl -X GET http://ваш-сервер/api/landmarks/player/1/ \
  -H "Authorization: Bearer $TOKEN"

# 4. Попытка сохранить те же landmarks (должно вернуть 0 новых записей)
curl -X POST http://ваш-сервер/api/landmarks/save/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"player_id": 1, "landmark_ids": [1, 2, 3]}'
```

## Возможные проблемы и решения

### Проблема: "No module named 'landmarks'"
**Решение:** Убедитесь, что `'landmarks'` добавлен в `INSTALLED_APPS` в `settings.py`

### Проблема: "Table 'landmarks_landmark' doesn't exist"
**Решение:** Выполните `python manage.py migrate landmarks`

### Проблема: "Authentication credentials were not provided"
**Решение:** Убедитесь, что передаете заголовок `Authorization: Bearer <токен>`

### Проблема: "Player with ID X not found"
**Решение:** Убедитесь, что пользователь с таким ID существует в базе данных

### Проблема: "Landmark with ID X not found"
**Решение:** Создайте landmarks через админку или Django shell перед тестированием

