# Уведомления о повышении уровня

## Обзор

Система автоматически уведомляет пользователя о повышении уровня через API ответы. Уровень повышается автоматически, когда опыт достигает 1000 единиц.

---

## 1. Уведомление при завершении квеста

### Endpoint: `POST /api/quests/{quest_id}/complete/`

Когда пользователь завершает квест и получает награду в виде опыта, система автоматически проверяет повышение уровня.

### Формат ответа при повышении уровня

**Если уровень повысился:**
```json
{
  "success": true,
  "message": "Quest completed! Level up! You reached level 2!",
  "reward_given": {
    "type": "experience",
    "amount": 500,
    "new_experience": 500
  },
  "player_stats": {
    "coins": 100,
    "experience": 500,
    "level": 2,
    "experience_to_next_level": 500,
    "level_up": {
      "new_level": 2,
      "levels_gained": 1
    }
  },
  "level_up_notification": {
    "new_level": 2,
    "levels_gained": 1
  }
}
```

**Если уровень НЕ повысился:**
```json
{
  "success": true,
  "message": "Quest completed successfully",
  "reward_given": {
    "type": "experience",
    "amount": 300,
    "new_experience": 800
  },
  "player_stats": {
    "coins": 100,
    "experience": 800,
    "level": 1,
    "experience_to_next_level": 200
  },
  "level_up_notification": null
}
```

### Поля для проверки повышения уровня

1. **`level_up_notification`** - явное уведомление о повышении уровня
   - `null` - уровень не повысился
   - Объект с полями:
     - `new_level` - новый уровень игрока
     - `levels_gained` - количество полученных уровней (может быть > 1)

2. **`player_stats.level_up`** - дублирует информацию из `level_up_notification`

3. **`message`** - текстовое сообщение содержит информацию о повышении уровня

---

## 2. Получение статистики пользователя

### Endpoint: `GET /api/me/stats/`

Получение текущей статистики авторизованного пользователя.

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response (200 OK):**
```json
{
  "success": true,
  "player_stats": {
    "id": 1,
    "player_id": 1,
    "username": "testuser",
    "coins": 500,
    "experience": 750,
    "level": 1,
    "experience_to_next_level": 250,
    "experience_per_level": 1000,
    "progress_to_next_level_percent": 75.0
  }
}
```

**Поля:**
- `coins` - текущее количество монет
- `experience` - текущий опыт
- `level` - текущий уровень
- `experience_to_next_level` - сколько опыта нужно до следующего уровня
- `experience_per_level` - константа (1000 опыта = 1 уровень)
- `progress_to_next_level_percent` - прогресс до следующего уровня в процентах

---

## 3. Обработка уведомлений в Unity (C#)

### Пример обработки ответа при завершении квеста

```csharp
[Serializable]
public class CompleteQuestResponse
{
    public bool success;
    public string message;
    public RewardGiven reward_given;
    public PlayerStats player_stats;
    public LevelUpNotification level_up_notification;  // ← Проверяйте это поле
}

[Serializable]
public class LevelUpNotification
{
    public int new_level;
    public int levels_gained;
}

[Serializable]
public class PlayerStats
{
    public int coins;
    public int experience;
    public int level;
    public int experience_to_next_level;
    public LevelUpInfo level_up;  // Альтернативный способ проверки
}

[Serializable]
public class LevelUpInfo
{
    public int new_level;
    public int levels_gained;
}

public async Task CompleteQuest(int questId, int playerId)
{
    var request = new CompleteQuestRequest { player_id = playerId };
    var response = await apiClient.PostAsync<CompleteQuestResponse>(
        $"/api/quests/{questId}/complete/", 
        request
    );
    
    if (response.success)
    {
        // Проверка на повышение уровня
        if (response.level_up_notification != null)
        {
            ShowLevelUpNotification(response.level_up_notification);
        }
        
        // Обновить статистику игрока
        UpdatePlayerStats(response.player_stats);
    }
}

private void ShowLevelUpNotification(LevelUpNotification notification)
{
    // Показать уведомление о повышении уровня
    string message = notification.levels_gained == 1
        ? $"Поздравляем! Вы достигли {notification.new_level} уровня!"
        : $"Поздравляем! Вы получили {notification.levels_gained} уровней и достигли {notification.new_level} уровня!";
    
    // Показать UI уведомление
    UIManager.Instance.ShowLevelUpPopup(
        level: notification.new_level,
        levelsGained: notification.levels_gained,
        message: message
    );
    
    // Воспроизвести звук/анимацию
    AudioManager.Instance.PlayLevelUpSound();
    AnimationManager.Instance.PlayLevelUpAnimation();
}

private void UpdatePlayerStats(PlayerStats stats)
{
    PlayerData.Instance.coins = stats.coins;
    PlayerData.Instance.experience = stats.experience;
    PlayerData.Instance.level = stats.level;
    PlayerData.Instance.experienceToNextLevel = stats.experience_to_next_level;
    
    // Обновить UI
    UIManager.Instance.UpdatePlayerStats(stats);
}
```

### Пример получения статистики пользователя

```csharp
[Serializable]
public class UserStatsResponse
{
    public bool success;
    public PlayerStats player_stats;
}

public async Task<UserStatsResponse> GetCurrentUserStats()
{
    return await apiClient.GetAsync<UserStatsResponse>("/api/me/stats/");
}

// Использование
public async void RefreshPlayerStats()
{
    var stats = await GetCurrentUserStats();
    if (stats.success)
    {
        UpdatePlayerStats(stats.player_stats);
    }
}
```

---

## 4. Логика повышения уровня

### Правила

1. **Опыт добавляется** через метод `add_experience(amount)`
2. **Проверка уровня:** Если опыт >= 1000, уровень повышается на 1, опыт уменьшается на 1000
3. **Множественное повышение:** Если опыт >= 2000, уровень повышается на 2, опыт уменьшается на 2000, и т.д.
4. **Остаток опыта:** Остаток опыта сохраняется (например, 1500 опыта → уровень +1, остаток 500)

### Примеры

**Пример 1: Одно повышение уровня**
- Было: уровень 1, опыт 800
- Добавили: 500 опыта
- Стало: уровень 2, опыт 300 (800 + 500 - 1000 = 300)

**Пример 2: Два повышения уровня**
- Было: уровень 1, опыт 500
- Добавили: 2000 опыта
- Стало: уровень 3, опыт 500 (500 + 2000 - 2000 = 500, два повышения)

**Пример 3: Без повышения уровня**
- Было: уровень 1, опыт 300
- Добавили: 400 опыта
- Стало: уровень 1, опыт 700 (300 + 400 = 700, меньше 1000)

---

## 5. Рекомендации для UI

### Что показывать при повышении уровня:

1. **Всплывающее окно/уведомление:**
   - Текст: "Поздравляем! Вы достигли уровня X!"
   - Анимация: эффект повышения уровня
   - Звук: звук повышения уровня

2. **Обновление статистики:**
   - Обновить отображение уровня
   - Обновить прогресс-бар опыта
   - Обновить количество монет (если изменилось)

3. **Дополнительные эффекты:**
   - Конфетти/частицы
   - Анимация числа уровня
   - Вибрация (на мобильных устройствах)

### Пример UI компонента

```csharp
public class LevelUpNotificationUI : MonoBehaviour
{
    [SerializeField] private GameObject levelUpPanel;
    [SerializeField] private Text levelText;
    [SerializeField] private Text messageText;
    [SerializeField] private Animator animator;
    
    public void ShowLevelUp(int newLevel, int levelsGained)
    {
        levelText.text = newLevel.ToString();
        
        string message = levelsGained == 1
            ? $"Поздравляем! Вы достигли {newLevel} уровня!"
            : $"Поздравляем! Вы получили {levelsGained} уровней и достигли {newLevel} уровня!";
        
        messageText.text = message;
        
        levelUpPanel.SetActive(true);
        animator.SetTrigger("LevelUp");
        
        // Автоматически скрыть через 3 секунды
        StartCoroutine(HideAfterDelay(3f));
    }
    
    private IEnumerator HideAfterDelay(float delay)
    {
        yield return new WaitForSeconds(delay);
        levelUpPanel.SetActive(false);
    }
}
```

---

## 6. Проверка повышения уровня в других местах

Если опыт добавляется в других местах (не через завершение квеста), проверяйте изменение уровня:

```csharp
// Сохранить старый уровень
int oldLevel = PlayerData.Instance.level;

// Добавить опыт (через API или локально)
// ...

// Проверить изменение уровня
if (PlayerData.Instance.level > oldLevel)
{
    int levelsGained = PlayerData.Instance.level - oldLevel;
    ShowLevelUpNotification(PlayerData.Instance.level, levelsGained);
}
```

---

## 7. Чек-лист для разработчика Unity

- [ ] Обработка поля `level_up_notification` в ответе завершения квеста
- [ ] UI компонент для отображения уведомления о повышении уровня
- [ ] Анимация повышения уровня
- [ ] Звуковой эффект при повышении уровня
- [ ] Обновление статистики игрока после повышения уровня
- [ ] Обновление прогресс-бара опыта
- [ ] Обработка множественного повышения уровня (levels_gained > 1)
- [ ] Интеграция endpoint `/api/me/stats/` для получения статистики

---

## 8. Примеры ответов API

### Пример 1: Повышение уровня на 1

```json
{
  "success": true,
  "message": "Quest completed! Level up! You reached level 2!",
  "reward_given": {
    "type": "experience",
    "amount": 500,
    "new_experience": 500
  },
  "player_stats": {
    "coins": 100,
    "experience": 500,
    "level": 2,
    "experience_to_next_level": 500,
    "level_up": {
      "new_level": 2,
      "levels_gained": 1
    }
  },
  "level_up_notification": {
    "new_level": 2,
    "levels_gained": 1
  }
}
```

### Пример 2: Повышение уровня на 2

```json
{
  "success": true,
  "message": "Quest completed! Level up! You gained 2 levels and reached level 3!",
  "reward_given": {
    "type": "experience",
    "amount": 2500,
    "new_experience": 500
  },
  "player_stats": {
    "coins": 100,
    "experience": 500,
    "level": 3,
    "experience_to_next_level": 500,
    "level_up": {
      "new_level": 3,
      "levels_gained": 2
    }
  },
  "level_up_notification": {
    "new_level": 3,
    "levels_gained": 2
  }
}
```

### Пример 3: Без повышения уровня

```json
{
  "success": true,
  "message": "Quest completed successfully",
  "reward_given": {
    "type": "coins",
    "amount": 100,
    "new_balance": 200
  },
  "player_stats": {
    "coins": 200,
    "experience": 750,
    "level": 1,
    "experience_to_next_level": 250
  },
  "level_up_notification": null
}
```

---

**Версия документа:** 1.0  
**Дата:** 2024  
**Статус:** Готово к использованию

