# API для работы с информацией об игроках

## 1. Получение player_id при логине

Теперь при логине в ответе автоматически возвращается `player_id`.

### Endpoint: `POST /api/login/`

**Запрос:**
```bash
curl -X POST http://87.228.97.188/api/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "password123"
  }'
```

**Ответ:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "player_id": 1,
    "username": "testuser",
    "first_name": "Иван",
    "last_name": "Иванов",
    "coins": 100,
    "registration_date": "2025-12-01T10:00:00Z",
    "boots": 0,
    "pants": 0,
    "tshirt": 0,
    "cap": 0
  }
}
```

**Важно:** Поле `player_id` теперь явно присутствует в ответе и равно `id` пользователя.

## 2. Поиск информации о другом игроке

### Endpoint: `GET /api/player/<player_id>/`

Возвращает полную информацию об игроке, включая его достопримечательности.

**Запрос:**
```bash
curl -X GET http://87.228.97.188/api/player/1/ \
  -H "Authorization: Bearer ВАШ_ACCESS_ТОКЕН"
```

**Успешный ответ (200):**
```json
{
  "success": true,
  "player": {
    "id": 1,
    "player_id": 1,
    "username": "testuser",
    "first_name": "Иван",
    "last_name": "Иванов",
    "registration_date": "2025-12-01T10:00:00Z",
    "gender": "M",
    "landmarks": {
      "external_ids": ["384115", "Q12345", "Q67890"],
      "total_count": 3
    }
  }
}
```

**Если игрок не найден (404):**
```json
{
  "success": false,
  "error": "Player with ID 999 not found"
}
```

**Если player_id невалидный (400):**
```json
{
  "success": false,
  "error": "player_id must be a valid integer"
}
```

## Использование в Postman

### Получение информации об игроке:

1. **Method:** GET
2. **URL:** `http://87.228.97.188/api/player/1/`
3. **Headers:**
   - `Authorization: Bearer ВАШ_ACCESS_ТОКЕН`

## Использование в Unity

### Пример кода для получения информации об игроке:

```csharp
public async Task<PlayerInfo> GetPlayerInfo(int playerId)
{
    var url = $"{BaseUrl}player/{playerId}/";
    var result = await SendRequest(url, "GET", null, requireAuth: true);
    
    if (result.success)
    {
        var playerInfo = JsonUtility.FromJson<PlayerInfoResponse>(result.response);
        return playerInfo.player;
    }
    else
    {
        Debug.LogError($"Failed to get player info: {result.response}");
        return null;
    }
}

// Структуры данных
[System.Serializable]
public class PlayerInfoResponse
{
    public bool success;
    public PlayerInfo player;
}

[System.Serializable]
public class PlayerInfo
{
    public int id;
    public int player_id;
    public string username;
    public string first_name;
    public string last_name;
    public string registration_date;
    public string gender;
    public LandmarksInfo landmarks;
}

[System.Serializable]
public class LandmarksInfo
{
    public string[] external_ids;
    public int total_count;
}
```

## Полный пример использования

```bash
# 1. Логин и получение player_id
TOKEN=$(curl -X POST http://87.228.97.188/api/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"password123"}' \
  | jq -r '.access')

PLAYER_ID=$(curl -X POST http://87.228.97.188/api/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"password123"}' \
  | jq -r '.user.player_id')

echo "Ваш player_id: $PLAYER_ID"

# 2. Получение информации о себе
curl -X GET http://87.228.97.188/api/player/$PLAYER_ID/ \
  -H "Authorization: Bearer $TOKEN" | jq '.'

# 3. Получение информации о другом игроке (ID=2)
curl -X GET http://87.228.97.188/api/player/2/ \
  -H "Authorization: Bearer $TOKEN" | jq '.'
```

## Структура ответа

### Поля игрока:

- `id` / `player_id` - ID игрока (одинаковые значения)
- `username` - никнейм игрока
- `first_name` - имя
- `last_name` - фамилия
- `registration_date` - дата регистрации (ISO 8601 формат)
- `gender` - пол ("M" для мужского, "F" для женского, `null` если не указан)

### Поля достопримечательностей:

- `landmarks.external_ids` - массив ID достопримечательностей (из Wikipedia API)
- `landmarks.total_count` - общее количество достопримечательностей

## Обработка ошибок

### Игрок не найден:

```json
{
  "success": false,
  "error": "Player with ID 999 not found"
}
```

**HTTP статус:** 404

### Невалидный player_id:

```json
{
  "success": false,
  "error": "player_id must be a valid integer"
}
```

**HTTP статус:** 400

### Нет токена аутентификации:

```json
{
  "detail": "Authentication credentials were not provided."
}
```

**HTTP статус:** 401

## Важные замечания

1. **Аутентификация обязательна** - все endpoints требуют JWT токен
2. **player_id = id** - это одно и то же значение, добавлено для удобства
3. **Пустые поля** - `first_name`, `last_name` могут быть пустыми строками, `gender` может быть `null`
4. **Достопримечательности** - если у игрока нет достопримечательностей, `external_ids` будет пустым массивом
5. **Дата регистрации** - возвращается в формате ISO 8601 (например, "2025-12-01T10:00:00Z")

## Чек-лист проверки

- [ ] При логине возвращается `player_id` в ответе
- [ ] GET `/api/player/<id>/` возвращает полную информацию об игроке
- [ ] В ответе присутствуют все поля: username, first_name, last_name, registration_date, gender
- [ ] В ответе присутствует список достопримечательностей (external_ids)
- [ ] Если игрок не найден, возвращается ошибка 404
- [ ] Если player_id невалидный, возвращается ошибка 400
- [ ] Аутентификация требуется для всех запросов

