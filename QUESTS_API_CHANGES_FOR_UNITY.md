# Изменения API квестов для интеграции в Unity

## Обзор изменений

Backend API для квестов был полностью обновлен согласно новым требованиям. Все изменения обратно совместимы, но **критически важно** обновить клиент для корректной работы с новыми полями.

---

## 1. Структура данных квеста

### Обязательные поля в ответе API

Каждый квест теперь **ОБЯЗАТЕЛЬНО** содержит следующие поля:

```json
{
  "id": 1,                    // int - уникальный идентификатор квеста
  "type": "mark_sights",       // string - КРИТИЧЕСКИ ВАЖНО! Тип условия квеста
  "title": "Отметься в 3 местах",  // string - название квеста
  "description": "Посети 3 разные достопримечательности",  // string - описание
  "count": 3,                 // int - требуемое количество для выполнения
  "reward_type": "coins",     // string - тип награды: "coins", "experience", "item"
  "reward_amount": 100        // int - количество награды
}
```

### ⚠️ КРИТИЧЕСКИ ВАЖНО: Поле `type`

- **Поле `type` ОБЯЗАТЕЛЬНО** присутствует в каждом квесте
- **Поле `type` НЕ МОЖЕТ быть пустым** или null
- Без поля `type` квест **НЕ БУДЕТ** обработан на клиенте
- Если квест не имеет `type`, он будет отфильтрован на сервере

---

## 2. Типы условий квестов (type)

| Значение | Описание | Пример использования |
|----------|----------|---------------------|
| `mark_sights` | Отметка в достопримечательностях | Отметься в N местах |
| `visit_sights` | Альтернативное название (автоматически маппится на `mark_sights`) | То же что mark_sights |
| `steps` | Пройти N шагов | Пройди 10000 шагов |
| `collect_coins` | Собрать N монет | Собери 500 монет |
| `level_up` | Достичь уровня N | Достигни 5 уровня |

**Важно:** На сервере `visit_sights` автоматически преобразуется в `mark_sights`. Клиент может использовать оба значения, но рекомендуется использовать `mark_sights`.

---

## 3. Типы наград (reward_type)

| Значение | Описание | Дополнительные поля |
|----------|----------|-------------------|
| `coins` | Монеты | - |
| `experience` | Опыт | - |
| `item` | Предмет | Требует `item_id` (пока не реализовано на сервере) |

---

## 4. API Endpoints

### 4.1. Получение ежедневных квестов

**Endpoint:** `GET /api/quests/daily/`

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response (200 OK):**
```json
{
  "quests": [
    {
      "id": 1,
      "type": "mark_sights",
      "title": "Отметься в 3 местах",
      "description": "Посети 3 разные достопримечательности",
      "count": 3,
      "reward_type": "coins",
      "reward_amount": 100
    },
    {
      "id": 2,
      "type": "steps",
      "title": "Пройди 10000 шагов",
      "description": "Сделай 10000 шагов за день",
      "count": 10000,
      "reward_type": "experience",
      "reward_amount": 50
    },
    {
      "id": 3,
      "type": "collect_coins",
      "title": "Собери 500 монет",
      "description": "Заработай 500 монет",
      "count": 500,
      "reward_type": "coins",
      "reward_amount": 200
    }
  ]
}
```

**Response (400 Bad Request):**
```json
{
  "error": "Not enough quests in database. Need at least 3 active quests with valid type."
}
```

**Response (401 Unauthorized):**
```json
{
  "detail": "Authentication credentials were not provided."
}
```

**Особенности:**
- Квесты обновляются ежедневно (новые квесты каждый день)
- Все квесты имеют поле `type` (не пустое, не null)
- Количество квестов: обычно 3-5 в день
- Квесты без `type` автоматически отфильтровываются

---

### 4.2. Подтверждение выполнения квеста (НОВЫЙ)

**Endpoint:** `POST /api/quests/{quest_id}/complete/`

**Headers:**
```
Authorization: Bearer {access_token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "player_id": 123
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Quest completed successfully",
  "reward_given": {
    "type": "coins",
    "amount": 100
  },
  "player_stats": {
    "coins": 500
  }
}
```

**Response (400 Bad Request):**
```json
{
  "success": false,
  "message": "Quest already completed and reward claimed"
}
```

или

```json
{
  "success": false,
  "message": "Quest not completed. Progress: 2/3"
}
```

**Response (403 Forbidden):**
```json
{
  "success": false,
  "message": "player_id does not match authenticated user"
}
```

**Response (404 Not Found):**
```json
{
  "success": false,
  "message": "Quest not found"
}
```

**Примечание:** Этот endpoint опционален. Клиент может отслеживать выполнение локально и выдавать награды автоматически. Но рекомендуется для синхронизации с сервером.

---

### 4.3. Получение прогресса квестов (НОВЫЙ)

**Endpoint:** `GET /api/quests/progress/`

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response (200 OK):**
```json
{
  "quests_progress": [
    {
      "quest_id": 1,
      "current_progress": 2,
      "required_count": 3,
      "is_completed": false,
      "reward_claimed": false
    },
    {
      "quest_id": 2,
      "current_progress": 5,
      "required_count": 5,
      "is_completed": true,
      "reward_claimed": true
    }
  ]
}
```

**Примечание:** Этот endpoint опционален, так как клиент сохраняет прогресс локально. Может быть полезен для синхронизации между устройствами.

---

## 5. Изменения в структуре данных

### 5.1. Старая структура (до изменений)

```json
{
  "id": 1,
  "title": "Отметься в 3 местах",
  "description": "Посети 3 разные достопримечательности",
  "count": 3
}
```

### 5.2. Новая структура (после изменений)

```json
{
  "id": 1,
  "type": "mark_sights",           // ← НОВОЕ ОБЯЗАТЕЛЬНОЕ ПОЛЕ
  "title": "Отметься в 3 местах",
  "description": "Посети 3 разные достопримечательности",
  "count": 3,
  "reward_type": "coins",          // ← НОВОЕ ОБЯЗАТЕЛЬНОЕ ПОЛЕ
  "reward_amount": 100            // ← НОВОЕ ОБЯЗАТЕЛЬНОЕ ПОЛЕ
}
```

---

## 6. Что нужно изменить в Unity

### 6.1. Модель данных квеста (C# класс)

**Старый класс:**
```csharp
[Serializable]
public class Quest
{
    public int id;
    public string title;
    public string description;
    public int count;
}
```

**Новый класс (обновленный):**
```csharp
[Serializable]
public class Quest
{
    public int id;
    public string type;              // ← ДОБАВИТЬ (обязательное)
    public string title;
    public string description;
    public int count;
    public string reward_type;       // ← ДОБАВИТЬ (обязательное)
    public int reward_amount;        // ← ДОБАВИТЬ (обязательное)
}
```

### 6.2. Валидация квестов на клиенте

**Добавить проверку при получении квестов:**

```csharp
public void ProcessQuests(QuestResponse response)
{
    foreach (var quest in response.quests)
    {
        // КРИТИЧЕСКИ ВАЖНО: Проверка наличия поля type
        if (string.IsNullOrEmpty(quest.type))
        {
            Debug.LogWarning($"Quest {quest.id} has no type field! Skipping...");
            continue; // Пропускаем квест без type
        }
        
        // Обработка квеста по типу
        switch (quest.type)
        {
            case "mark_sights":
            case "visit_sights":
                // Логика для отметки в достопримечательностях
                break;
            case "steps":
                // Логика для шагов
                break;
            case "collect_coins":
                // Логика для сбора монет
                break;
            case "level_up":
                // Логика для повышения уровня
                break;
            default:
                Debug.LogWarning($"Unknown quest type: {quest.type}");
                break;
        }
    }
}
```

### 6.3. Обработка наград

**Добавить логику выдачи наград:**

```csharp
public void GiveReward(string rewardType, int rewardAmount)
{
    switch (rewardType)
    {
        case "coins":
            PlayerData.Instance.AddCoins(rewardAmount);
            break;
        case "experience":
            PlayerData.Instance.AddExperience(rewardAmount);
            break;
        case "item":
            // TODO: Выдача предмета по item_id
            break;
        default:
            Debug.LogWarning($"Unknown reward type: {rewardType}");
            break;
    }
}
```

### 6.4. Использование новых endpoints (опционально)

**Завершение квеста на сервере:**

```csharp
public async Task CompleteQuest(int questId, int playerId)
{
    var request = new CompleteQuestRequest
    {
        player_id = playerId
    };
    
    var response = await apiClient.PostAsync<CompleteQuestResponse>(
        $"/api/quests/{questId}/complete/", 
        request
    );
    
    if (response.success)
    {
        // Выдать награду локально
        GiveReward(response.reward_given.type, response.reward_given.amount);
        
        // Обновить статистику игрока
        PlayerData.Instance.coins = response.player_stats.coins;
    }
}
```

**Получение прогресса квестов:**

```csharp
public async Task<QuestProgressResponse> GetQuestProgress()
{
    return await apiClient.GetAsync<QuestProgressResponse>("/api/quests/progress/");
}
```

---

## 7. Примеры полных ответов API

### Пример 1: Успешное получение квестов

**Request:**
```http
GET /api/quests/daily/ HTTP/1.1
Host: 87.228.97.188
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

**Response:**
```json
{
  "quests": [
    {
      "id": 1,
      "type": "mark_sights",
      "title": "Отметься в 3 местах",
      "description": "Посети 3 разные достопримечательности",
      "count": 3,
      "reward_type": "coins",
      "reward_amount": 100
    },
    {
      "id": 2,
      "type": "mark_sights",
      "title": "Отметься в 5 местах",
      "description": "Посети 5 разные достопримечательности",
      "count": 5,
      "reward_type": "experience",
      "reward_amount": 50
    },
    {
      "id": 3,
      "type": "steps",
      "title": "Пройди 10000 шагов",
      "description": "Сделай 10000 шагов за день",
      "count": 10000,
      "reward_type": "coins",
      "reward_amount": 200
    },
    {
      "id": 4,
      "type": "collect_coins",
      "title": "Собери 500 монет",
      "description": "Заработай 500 монет",
      "count": 500,
      "reward_type": "experience",
      "reward_amount": 100
    }
  ]
}
```

### Пример 2: Завершение квеста

**Request:**
```http
POST /api/quests/1/complete/ HTTP/1.1
Host: 87.228.97.188
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
Content-Type: application/json

{
  "player_id": 123
}
```

**Response:**
```json
{
  "success": true,
  "message": "Quest completed successfully",
  "reward_given": {
    "type": "coins",
    "amount": 100
  },
  "player_stats": {
    "coins": 500
  }
}
```

---

## 8. Чек-лист для Unity разработчика

### Обязательные изменения:

- [ ] Обновить модель `Quest` - добавить поля `type`, `reward_type`, `reward_amount`
- [ ] Добавить валидацию: проверять наличие поля `type` при получении квестов
- [ ] Реализовать обработку всех типов квестов (`mark_sights`, `steps`, `collect_coins`, `level_up`)
- [ ] Реализовать выдачу наград по типам (`coins`, `experience`, `item`)
- [ ] Обновить UI для отображения типа награды и количества
- [ ] Добавить обработку ошибок (квест без `type`)

### Опциональные изменения:

- [ ] Интегрировать endpoint `/api/quests/{quest_id}/complete/` для синхронизации с сервером
- [ ] Интегрировать endpoint `/api/quests/progress/` для синхронизации прогресса
- [ ] Добавить синхронизацию прогресса между устройствами

---

## 9. Обратная совместимость

### Что работает как раньше:

- ✅ Endpoint `/api/quests/daily/` работает (но теперь возвращает дополнительные поля)
- ✅ Структура базовых полей (`id`, `title`, `description`, `count`) не изменилась
- ✅ Аутентификация работает так же

### Что изменилось:

- ⚠️ Добавлены обязательные поля `type`, `reward_type`, `reward_amount`
- ⚠️ Квесты без `type` отфильтровываются на сервере (не возвращаются)
- ⚠️ Добавлены новые опциональные endpoints

### Рекомендации:

1. **Обновить клиент как можно скорее** - старые версии могут не работать корректно
2. **Добавить проверку на наличие `type`** - защита от ошибок
3. **Использовать новые endpoints** для лучшей синхронизации

---

## 10. Типичные ошибки и их решения

### Ошибка 1: "Quest has no type field"

**Причина:** Клиент пытается обработать квест без поля `type`

**Решение:** 
```csharp
if (string.IsNullOrEmpty(quest.type))
{
    Debug.LogWarning($"Skipping quest {quest.id} - no type field");
    continue;
}
```

### Ошибка 2: "Unknown quest type"

**Причина:** Клиент получил неизвестный тип квеста

**Решение:** Добавить обработку всех типов или использовать default case

### Ошибка 3: Квесты не отображаются

**Причина:** Все квесты отфильтрованы из-за отсутствия `type`

**Решение:** Проверить, что на сервере все квесты имеют поле `type` (через админ-панель)

---

## 11. Примеры кода для Unity (C#)

### Класс для ответа API

```csharp
[Serializable]
public class QuestResponse
{
    public Quest[] quests;
}

[Serializable]
public class Quest
{
    public int id;
    public string type;              // ОБЯЗАТЕЛЬНО
    public string title;
    public string description;
    public int count;
    public string reward_type;       // ОБЯЗАТЕЛЬНО
    public int reward_amount;        // ОБЯЗАТЕЛЬНО
}

[Serializable]
public class CompleteQuestRequest
{
    public int player_id;
}

[Serializable]
public class CompleteQuestResponse
{
    public bool success;
    public string message;
    public RewardGiven reward_given;
    public PlayerStats player_stats;
}

[Serializable]
public class RewardGiven
{
    public string type;
    public int amount;
}

[Serializable]
public class PlayerStats
{
    public int coins;
}

[Serializable]
public class QuestProgressResponse
{
    public QuestProgress[] quests_progress;
}

[Serializable]
public class QuestProgress
{
    public int quest_id;
    public int current_progress;
    public int required_count;
    public bool is_completed;
    public bool reward_claimed;
}
```

### Обработчик квестов

```csharp
public class QuestManager : MonoBehaviour
{
    private List<Quest> currentQuests = new List<Quest>();
    
    public async Task LoadDailyQuests()
    {
        var response = await apiClient.GetAsync<QuestResponse>("/api/quests/daily/");
        
        if (response != null && response.quests != null)
        {
            currentQuests.Clear();
            
            foreach (var quest in response.quests)
            {
                // ВАЛИДАЦИЯ: Проверка наличия type
                if (string.IsNullOrEmpty(quest.type))
                {
                    Debug.LogWarning($"Quest {quest.id} skipped - no type field");
                    continue;
                }
                
                currentQuests.Add(quest);
                RegisterQuestHandler(quest);
            }
        }
    }
    
    private void RegisterQuestHandler(Quest quest)
    {
        switch (quest.type)
        {
            case "mark_sights":
            case "visit_sights":
                // Подписаться на события отметки достопримечательностей
                LandmarkManager.OnLandmarkMarked += (landmarkId) => 
                {
                    UpdateQuestProgress(quest.id, 1);
                };
                break;
                
            case "steps":
                // Подписаться на события шагов
                StepCounter.OnStepsUpdated += (steps) => 
                {
                    UpdateQuestProgress(quest.id, steps);
                };
                break;
                
            case "collect_coins":
                // Подписаться на события сбора монет
                CoinManager.OnCoinsCollected += (amount) => 
                {
                    UpdateQuestProgress(quest.id, amount);
                };
                break;
                
            case "level_up":
                // Подписаться на события повышения уровня
                PlayerLevel.OnLevelUp += (level) => 
                {
                    if (level >= quest.count)
                    {
                        CompleteQuest(quest.id);
                    }
                };
                break;
        }
    }
    
    private void UpdateQuestProgress(int questId, int progress)
    {
        var quest = currentQuests.FirstOrDefault(q => q.id == questId);
        if (quest != null)
        {
            // Обновить локальный прогресс
            // Проверить выполнение
            if (progress >= quest.count)
            {
                CompleteQuest(questId);
            }
        }
    }
    
    private async void CompleteQuest(int questId)
    {
        var quest = currentQuests.FirstOrDefault(q => q.id == questId);
        if (quest == null) return;
        
        // Выдать награду локально
        GiveReward(quest.reward_type, quest.reward_amount);
        
        // Опционально: синхронизировать с сервером
        try
        {
            var request = new CompleteQuestRequest
            {
                player_id = PlayerData.Instance.playerId
            };
            
            var response = await apiClient.PostAsync<CompleteQuestResponse>(
                $"/api/quests/{questId}/complete/", 
                request
            );
            
            if (response.success)
            {
                Debug.Log($"Quest {questId} completed! Reward: {response.reward_given.amount} {response.reward_given.type}");
            }
        }
        catch (Exception e)
        {
            Debug.LogError($"Failed to sync quest completion: {e.Message}");
            // Награда уже выдана локально, так что это не критично
        }
    }
    
    private void GiveReward(string rewardType, int rewardAmount)
    {
        switch (rewardType)
        {
            case "coins":
                PlayerData.Instance.AddCoins(rewardAmount);
                break;
            case "experience":
                PlayerData.Instance.AddExperience(rewardAmount);
                break;
            case "item":
                // TODO: Выдача предмета
                break;
        }
    }
}
```

---

## 12. Константы для использования в Unity

```csharp
public static class QuestTypes
{
    public const string MARK_SIGHTS = "mark_sights";
    public const string VISIT_SIGHTS = "visit_sights";  // Маппится на mark_sights
    public const string STEPS = "steps";
    public const string COLLECT_COINS = "collect_coins";
    public const string LEVEL_UP = "level_up";
}

public static class RewardTypes
{
    public const string COINS = "coins";
    public const string EXPERIENCE = "experience";
    public const string ITEM = "item";
}
```

---

## 13. Важные замечания

### ⚠️ Критически важно:

1. **Поле `type` ОБЯЗАТЕЛЬНО** - без него квест не будет обработан
2. **Поле `type` не может быть пустым** - пустая строка = ошибка
3. **Поле `type` не может быть null** - null = ошибка
4. **Все типы должны быть обработаны** - неизвестные типы должны логироваться

### ✅ Рекомендуется:

1. Использовать константы для типов квестов и наград
2. Валидировать данные при получении с сервера
3. Логировать предупреждения при получении невалидных данных
4. Использовать новые endpoints для синхронизации (опционально)

---

## 14. Контакты и поддержка

Если возникнут вопросы по интеграции:

1. Проверьте этот документ
2. Проверьте логи клиента при загрузке квестов
3. Убедитесь, что все обязательные поля присутствуют в ответе API
4. Проверьте Swagger документацию: `http://87.228.97.188/api/docs/`

---

**Версия документа:** 1.0  
**Дата:** 2024  
**Статус:** Готово к интеграции

