# API для получения списка достопримечательностей игрока

## Endpoint: `GET /api/player/<player_id>/landmarks/`

Возвращает список всех достопримечательностей (external_ids) по ID пользователя.

## Запрос

```bash
curl -X GET http://87.228.97.188/api/player/1/landmarks/ \
  -H "Authorization: Bearer ВАШ_ACCESS_ТОКЕН"
```

**В Postman:**
- Method: **GET**
- URL: `http://87.228.97.188/api/player/1/landmarks/`
- Headers: `Authorization: Bearer ВАШ_ACCESS_ТОКЕН`

## Успешный ответ (200)

```json
{
  "success": true,
  "player_id": 1,
  "player_username": "testuser",
  "external_ids": ["384115", "Q12345", "Q67890"],
  "total_count": 3
}
```

## Ошибки

### Игрок не найден (404)

```json
{
  "success": false,
  "error": "Player with ID 999 not found"
}
```

### Невалидный player_id (400)

```json
{
  "success": false,
  "error": "player_id must be a valid integer"
}
```

### Нет токена аутентификации (401)

```json
{
  "detail": "Authentication credentials were not provided."
}
```

## Использование в Unity

```csharp
public async Task<List<string>> GetPlayerLandmarks(int playerId)
{
    var url = $"{BaseUrl}player/{playerId}/landmarks/";
    var result = await SendRequest(url, "GET", null, requireAuth: true);
    
    if (result.success)
    {
        var response = JsonUtility.FromJson<LandmarksResponse>(result.response);
        return response.external_ids.ToList();
    }
    else
    {
        Debug.LogError($"Failed to get landmarks: {result.response}");
        return new List<string>();
    }
}

// Структуры данных
[System.Serializable]
public class LandmarksResponse
{
    public bool success;
    public int player_id;
    public string player_username;
    public string[] external_ids;
    public int total_count;
}
```

## Пример использования

```bash
# Получите токен
TOKEN=$(curl -X POST http://87.228.97.188/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"password123"}' \
  | jq -r '.access')

# Получите список достопримечательностей игрока ID=1
curl -X GET http://87.228.97.188/api/player/1/landmarks/ \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.'
```

## Сравнение с другими endpoints

### 1. `/api/player/<player_id>/landmarks/` (новый)
**Возвращает:** Только список достопримечательностей
```json
{
  "success": true,
  "player_id": 1,
  "player_username": "testuser",
  "external_ids": ["384115", "Q12345"],
  "total_count": 2
}
```

### 2. `/api/player/<player_id>/` (полная информация)
**Возвращает:** Полную информацию об игроке + достопримечательности
```json
{
  "success": true,
  "player": {
    "id": 1,
    "username": "testuser",
    "first_name": "Иван",
    "last_name": "Иванов",
    "registration_date": "2025-12-01T10:00:00Z",
    "gender": "M",
    "landmarks": {
      "external_ids": ["384115", "Q12345"],
      "total_count": 2
    }
  }
}
```

### 3. `/api/landmarks/player/<player_id>/` (из landmarks app)
**Возвращает:** Список достопримечательностей (аналогично новому endpoint)
```json
{
  "success": true,
  "player_id": 1,
  "player_username": "testuser",
  "external_ids": ["384115", "Q12345"],
  "total_count": 2
}
```

## Когда использовать

- **`/api/player/<player_id>/landmarks/`** - когда нужен только список достопримечательностей (быстрее, меньше данных)
- **`/api/player/<player_id>/`** - когда нужна полная информация об игроке + достопримечательности
- **`/api/landmarks/player/<player_id>/`** - альтернативный endpoint для получения достопримечательностей

## Важные замечания

1. **Аутентификация обязательна** - требуется JWT токен
2. **Сортировка** - достопримечательности отсортированы по дате (новые сначала)
3. **Пустой список** - если у игрока нет достопримечательностей, `external_ids` будет пустым массивом
4. **external_ids** - это строковые ID из Wikipedia API (например, "384115", "Q12345")

## Чек-лист проверки

- [ ] GET `/api/player/<id>/landmarks/` возвращает список достопримечательностей
- [ ] В ответе присутствуют: player_id, player_username, external_ids, total_count
- [ ] Если игрок не найден, возвращается ошибка 404
- [ ] Если player_id невалидный, возвращается ошибка 400
- [ ] Аутентификация требуется для запроса
- [ ] Пустой список возвращается, если у игрока нет достопримечательностей

