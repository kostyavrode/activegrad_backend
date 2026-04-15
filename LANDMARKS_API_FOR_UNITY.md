# Landmarks API — документация для Unity

## Общая информация

- **Base URL:** `http://87.228.97.188/api/` (или `https://` в продакшене)
- **Аутентификация:** Bearer token (JWT) в заголовке `Authorization`
- **Content-Type:** `application/json`

```
Authorization: Bearer <access_token>
Content-Type: application/json
```

---

## 1. Сохранить отметки на достопримечательностях

Игрок отмечается, что посетил достопримечательность. **За каждую новую отметку выдаются ресурсы** (metal, wood, blueprints) — случайное количество от 0 до 10 для каждого типа.

### Запрос

```
POST /api/landmarks/save/
```

**Body:**
```json
{
  "player_id": 1,
  "external_ids": ["12345", "67890", "11111"]
}
```

| Поле | Тип | Обязательно | Описание |
|------|-----|-------------|----------|
| `player_id` | int | Да | ID игрока (должен совпадать с текущим пользователем) |
| `external_ids` | string[] | Да | Список ID достопримечательностей (из Wikipedia API) |

### Ответ при успехе (200)

```json
{
  "success": true,
  "message": "Successfully saved 2 landmark observation(s)",
  "player_id": 1,
  "saved_external_ids": ["12345", "67890"],
  "total_saved": 2,
  "resources_gained": {
    "metal": 7,
    "wood": 12,
    "blueprints": 5
  }
}
```

| Поле | Тип | Описание |
|------|-----|----------|
| `success` | bool | Успешность операции |
| `message` | string | Сообщение |
| `player_id` | int | ID игрока |
| `saved_external_ids` | string[] | ID достопримечательностей, которые были **впервые** сохранены |
| `total_saved` | int | Количество новых отметок |
| `resources_gained` | object | **Только если есть новые отметки.** Ресурсы за каждую новую отметку (metal, wood, blueprints — от 0 до 10 каждое, случайно) |

**Важно:** `resources_gained` присутствует только если `total_saved > 0`. Повторные отметки на уже посещённые достопримечательности не дают ресурсов.

### Ошибки

| Код | Условие |
|-----|---------|
| 400 | Неверные данные (errors в ответе) |
| 404 | Игрок не найден |
| 500 | Внутренняя ошибка сервера |

---

## 2. Получить достопримечательности игрока

Возвращает список external_id достопримечательностей, где был игрок.

### Запрос (вариант 1 — player_id в URL)

```
GET /api/landmarks/player/1/
```

### Запрос (вариант 2 — player_id в query)

```
GET /api/landmarks/player/?player_id=1
```

### Ответ при успехе (200)

```json
{
  "success": true,
  "player_id": 1,
  "player_username": "PlayerName",
  "external_ids": ["12345", "67890", "11111"],
  "total_count": 3
}
```

| Поле | Тип | Описание |
|------|-----|----------|
| `external_ids` | string[] | Список ID посещённых достопримечательностей |
| `total_count` | int | Количество |

---

## 3. Захватить достопримечательность

Захват достопримечательности (смена владельца).

**Логика:**
1. **Меч обязателен** — без меча захват невозможен (400 Sword required).
2. **30 минут неприступности** — после захвата в течение 30 минут никто не может перехватить.
3. **5 минут после неудачи** — если попытка провалилась (по вероятности), следующая попытка возможна через 5 минут.
4. **После снятия блокировок** — успех зависит от **уровня меча атакующего** и **уровня щита владельца**:
   - Меч атакующего ≥ Щит защитника + 2 → **100%** успех
   - Меч на 1 выше щита → **80%**
   - Равные уровни → **50%**
   - Щит на 1 выше меча → **25%**
   - Щит ≥ Меч + 2 → **5%**
3. Без меча/щита уровень считается 0.

### Запрос

```
POST /api/landmarks/capture/
```

**Body:**
```json
{
  "external_id": "12345"
}
```

### Ответ при успехе (201)

```json
{
  "success": true,
  "message": "Landmark captured successfully. Owner changed.",
  "capture": {
    "id": 1,
    "external_id": "12345",
    "captured_by": {
      "id": 1,
      "username": "PlayerName"
    },
    "captured_at": "2026-02-15T16:30:00.000000Z",
    "clan": {
      "id": 1,
      "name": "ClanName"
    }
  }
}
```

`clan` может быть `null`, если игрок не в клане.

**Важно:** после успешного захвата обновите UI данными из `response.capture` (в т.ч. `captured_by`) или вызовите `GET /api/landmarks/{external_id}/capture/` заново, иначе может отображаться старый владелец.

### Ошибка — нет меча (400)

Захват без меча невозможен.

```json
{
  "success": false,
  "error": "Sword required",
  "message": "Для захвата достопримечательности нужен меч. Скрафтите меч в инвентаре."
}
```

### Ошибка — достопримечательность под защитой (400)

Две причины блокировки:
- **invulnerability** — 30 минут после захвата
- **failed_capture_cooldown** — 5 минут после неудачной попытки

```json
{
  "success": false,
  "error": "Landmark cannot be captured now",
  "message": "Достопримечательность под защитой. Попытка перехвата возможна через 25 мин 30 сек",
  "can_capture_now": false,
  "block_reason": "invulnerability",
  "current_owner": {
    "id": 2,
    "username": "OtherPlayer"
  },
  "captured_at": "2026-02-15T15:00:00.000000Z",
  "time_until_next_capture_minutes": 25,
  "time_until_next_capture_seconds": 30
}
```

При `block_reason: "failed_capture_cooldown"` сообщение: «Последняя попытка захвата не удалась. Повторная попытка возможна через X мин Y сек».

### Ошибка — захват не удался (400)

Проверка вероятности (меч vs щит) не прошла. **Повторная попытка возможна только через 5 минут.**

```json
{
  "success": false,
  "error": "Capture failed",
  "message": "Захват не удался. Повторная попытка возможна через 5 минут.",
  "capture_failed": true,
  "probability": 25.0,
  "roll": 67.3,
  "attacker_sword_level": 1,
  "defender_shield_level": 2,
  "retry_available_in_minutes": 5,
  "retry_available_in_seconds": 300
}
```

| Поле | Описание |
|------|----------|
| `capture_failed` | true — провал по вероятности |
| `probability` | Вероятность успеха (%) |
| `attacker_sword_level` | Уровень меча атакующего |
| `defender_shield_level` | Уровень щита защитника |
| `retry_available_in_minutes` | Через сколько минут можно попробовать снова |
| `retry_available_in_seconds` | То же в секундах |

---

## 4. Информация о захвате достопримечательности

Проверить, кто захватил достопримечательность и можно ли её захватить.

### Запрос

```
GET /api/landmarks/{external_id}/capture/
```

Пример: `GET /api/landmarks/12345/capture/`

### Ответ — ещё не захватывалась (200)

```json
{
  "success": true,
  "captured": false,
  "can_capture_now": true,
  "captured_by": null,
  "captured_at": null,
  "clan": null
}
```

### Ответ — захвачена (200)

Всегда приходит **`defender_shield_level`** — уровень щита текущего владельца (для UI: «Защита: щит N уровня»).

Когда `can_capture_now: false` — дополнительно: `time_until_next_capture_minutes`, `time_until_next_capture_seconds`, `block_reason` (`invulnerability` или `failed_capture_cooldown`).

```json
{
  "success": true,
  "captured": true,
  "can_capture_now": false,
  "captured_by": {
    "id": 1,
    "username": "PlayerName"
  },
  "captured_at": "2026-02-15T16:00:00.000000Z",
  "clan": {
    "id": 1,
    "name": "ClanName"
  },
  "defender_shield_level": 3,
  "time_until_next_capture_minutes": 15,
  "time_until_next_capture_seconds": 42,
  "block_reason": "invulnerability"
}
```

| Поле | Описание |
|------|----------|
| `defender_shield_level` | Уровень щита владельца (0 если щита нет) |
| `block_reason` | Причина блокировки при `can_capture_now: false` |

---

## 5. Ресурсы и инвентарь

Ресурсы (metal, wood, blueprints), полученные за отметки, хранятся в инвентаре. Для отображения и крафта используется Inventory API.

### Получить инвентарь

```
GET /api/inventory/
```

**Ответ:**
```json
{
  "success": true,
  "resources": [
    {"id": "metal", "amount": 25, "display_name": "Металл"},
    {"id": "wood", "amount": 18, "display_name": "Дерево"},
    {"id": "blueprints", "amount": 10, "display_name": "Чертежи"}
  ],
  "items": [
    {"id": "sword", "display_name": "Меч", "has_item": true, "sharpness": 2},
    {"id": "shield", "display_name": "Щит", "has_item": false, "durability": null}
  ]
}
```

**Рекомендация:** после успешного `POST /api/landmarks/save/` с `resources_gained` — обновить локальное отображение ресурсов (можно вызвать `GET /api/inventory/` или прибавить `resources_gained` к текущим значениям).

---

## Пример C# для Unity

```csharp
[Serializable]
public class SaveLandmarksRequest
{
    public int player_id;
    public string[] external_ids;
}

[Serializable]
public class SaveLandmarksResponse
{
    public bool success;
    public string message;
    public int player_id;
    public string[] saved_external_ids;
    public int total_saved;
    public ResourcesGained resources_gained;
}

[Serializable]
public class ResourcesGained
{
    public int metal;
    public int wood;
    public int blueprints;
}

// Вызов при отметке на достопримечательности
public async Task<SaveLandmarksResponse> SaveLandmarks(int playerId, string[] externalIds)
{
    var request = new SaveLandmarksRequest
    {
        player_id = playerId,
        external_ids = externalIds
    };
    
    var response = await apiClient.PostAsync<SaveLandmarksResponse>(
        "/api/landmarks/save/", 
        request
    );
    
    if (response.success && response.resources_gained != null)
    {
        // Обновить UI ресурсов
        PlayerData.Instance.AddMetal(response.resources_gained.metal);
        PlayerData.Instance.AddWood(response.resources_gained.wood);
        PlayerData.Instance.AddBlueprints(response.resources_gained.blueprints);
    }
    
    return response;
}
```

---

## Краткая сводка эндпоинтов

| Метод | URL | Описание |
|-------|-----|----------|
| POST | `/api/landmarks/save/` | Сохранить отметки, получить ресурсы за новые |
| GET | `/api/landmarks/player/{id}/` | Список посещённых достопримечательностей |
| GET | `/api/landmarks/player/?player_id={id}` | То же через query |
| POST | `/api/landmarks/capture/` | Захватить достопримечательность |
| GET | `/api/landmarks/{external_id}/capture/` | Информация о захвате |
| GET | `/api/inventory/` | Инвентарь и ресурсы игрока |
