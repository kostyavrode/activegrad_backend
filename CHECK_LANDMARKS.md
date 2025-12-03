# Как проверить достопримечательности пользователя

## Способ 1: Через API (GET запрос)

### Вариант A: Через URL path

```bash
curl -X GET http://87.228.97.188/api/landmarks/player/1/ \
  -H "Authorization: Bearer ВАШ_ACCESS_ТОКЕН"
```

**В Postman:**
- Method: **GET**
- URL: `http://87.228.97.188/api/landmarks/player/1/`
- Headers: `Authorization: Bearer ВАШ_ACCESS_ТОКЕН`

### Вариант B: Через query параметр

```bash
curl -X GET "http://87.228.97.188/api/landmarks/player/?player_id=1" \
  -H "Authorization: Bearer ВАШ_ACCESS_ТОКЕН"
```

**В Postman:**
- Method: **GET**
- URL: `http://87.228.97.188/api/landmarks/player/?player_id=1`
- Headers: `Authorization: Bearer ВАШ_ACCESS_ТОКЕН`

### Успешный ответ:

```json
{
  "success": true,
  "player_id": 1,
  "player_username": "testuser",
  "external_ids": ["384115"],
  "total_count": 1
}
```

## Способ 2: Через Django Admin

1. Зайдите в админ-панель: `http://87.228.97.188/admin/`
2. Войдите под учетной записью администратора
3. Перейдите в раздел **Player landmark observations**
4. Вы увидите все записи с полями:
   - **Player** - имя игрока
   - **External id** - ID достопримечательности (например, "384115")
   - **Observed at** - дата и время наблюдения

5. Можете отфильтровать по игроку, используя поиск по имени пользователя

## Способ 3: Через Django Shell (на сервере)

```bash
# Подключитесь к серверу и выполните:
cd /opt/activegrad_backend
source venv/bin/activate  # если используете venv
python manage.py shell
```

```python
from landmarks.models import PlayerLandmarkObservation
from accounts.models import CustomUser

# Проверка всех наблюдений
observations = PlayerLandmarkObservation.objects.all()
print(f"Всего наблюдений в базе: {observations.count()}")

for obs in observations:
    print(f"Игрок: {obs.player.username} (ID: {obs.player.id}), External ID: {obs.external_id}, Дата: {obs.observed_at}")

# Проверка достопримечательностей конкретного игрока (ID=1)
player = CustomUser.objects.get(id=1)
player_landmarks = PlayerLandmarkObservation.objects.filter(player=player)
print(f"\nДостопримечательности игрока {player.username} (ID: {player.id}):")
print(f"Всего: {player_landmarks.count()}")
for obs in player_landmarks:
    print(f"  - External ID: {obs.external_id} (наблюдено: {obs.observed_at})")

# Проверка конкретного external_id
external_id = "384115"
if PlayerLandmarkObservation.objects.filter(player=player, external_id=external_id).exists():
    print(f"\n✓ Достопримечательность {external_id} найдена для игрока {player.username}")
else:
    print(f"\n✗ Достопримечательность {external_id} НЕ найдена для игрока {player.username}")
```

## Способ 4: Через SQL запрос (если используете SQLite)

```bash
cd /opt/activegrad_backend
sqlite3 db.sqlite3
```

```sql
-- Показать все записи
SELECT * FROM landmarks_playerlandmarkobservation;

-- Показать достопримечательности конкретного игрока (ID=1)
SELECT 
    u.username,
    plo.external_id,
    plo.observed_at
FROM landmarks_playerlandmarkobservation plo
JOIN accounts_customuser u ON plo.player_id = u.id
WHERE plo.player_id = 1;

-- Проверить конкретный external_id
SELECT * FROM landmarks_playerlandmarkobservation 
WHERE player_id = 1 AND external_id = '384115';
```

## Быстрая проверка через curl

```bash
# Получите токен (если еще не получили)
TOKEN=$(curl -X POST http://87.228.97.188/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"ваш_username","password":"ваш_пароль"}' \
  | jq -r '.access')

# Проверьте достопримечательности игрока ID=1
curl -X GET http://87.228.97.188/api/landmarks/player/1/ \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.'
```

## Что должно быть в ответе

Если достопримечательность успешно добавлена, вы увидите:

```json
{
  "success": true,
  "player_id": 1,
  "player_username": "ваш_username",
  "external_ids": ["384115"],
  "total_count": 1
}
```

Если добавите еще достопримечательности, они появятся в массиве `external_ids`:

```json
{
  "success": true,
  "player_id": 1,
  "player_username": "ваш_username",
  "external_ids": ["384115", "Q12345", "Q67890"],
  "total_count": 3
}
```

## Проверка в Unity приложении

Если у вас есть метод для получения достопримечательностей в Unity:

```csharp
// Пример метода в APIService
public async Task<List<string>> GetPlayerLandmarks(int playerId)
{
    var url = $"{BaseUrl}landmarks/player/{playerId}/";
    var result = await SendRequest(url, "GET", null, requireAuth: true);
    
    if (result.success)
    {
        // Парсите JSON ответ
        var response = JsonUtility.FromJson<LandmarksResponse>(result.response);
        return response.external_ids;
    }
    return new List<string>();
}
```

## Важные замечания

1. **Дубликаты не создаются** - если попытаетесь добавить ту же достопримечательность дважды, она не добавится повторно
2. **external_id хранится как строка** - даже если передаете число, оно сохраняется как строка
3. **Сортировка** - достопримечательности отсортированы по дате (новые сначала)

## Если не видите достопримечательности

1. **Проверьте player_id** - убедитесь, что используете правильный ID игрока
2. **Проверьте токен** - убедитесь, что токен действителен
3. **Проверьте логи** - если что-то пошло не так, проверьте логи сервера
4. **Проверьте базу данных** - используйте Django shell для прямой проверки

