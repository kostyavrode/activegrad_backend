# Документация для интеграции системы прокачки в Unity

Этот документ описывает изменения в backend API, чтобы другой разработчик/агент мог реализовать соответствующую логику в Unity проекте.

---

## 1. Обзор изменений

### Что добавлено на бэкенде

1. **Показатели прокачки у каждого игрока:**
   - `strength` (сила) — по умолчанию 1
   - `intelligence` (интеллект) — по умолчанию 1  
   - `agility` (ловкость) — по умолчанию 1

2. **Очки прокачки** (`stat_upgrade_points`):
   - Даются при повышении уровня (+1 очко за каждый новый уровень)
   - Тратятся при прокачке одного из трёх показателей
   - По умолчанию 0

3. **Логика:**
   - При повышении уровня игрок получает `stat_upgrade_points += levels_gained`
   - Прокачка показателя: `stat_upgrade_points -= 1`, выбранный показатель `+= 1`
   - Прокачка возможна только если `stat_upgrade_points > 0`

---

## 2. Где приходят новые данные

### 2.1. Логин (JWT) — `POST /api/login/`

**Ответ содержит:**
```json
{
  "access": "token...",
  "refresh": "token...",
  "user": {
    "id": 1,
    "player_id": 1,
    "username": "user",
    "experience": 500,
    "level": 3,
    "experience_to_next_level": 500,
    "strength": 2,
    "intelligence": 1,
    "agility": 1,
    "stat_upgrade_points": 1,
    "coins": 100,
    ...
  }
}
```

**Новые поля для Unity:** `strength`, `intelligence`, `agility`, `stat_upgrade_points`

---

### 2.2. Статистика игрока — `GET /api/player/stats/`

**Ответ:**
```json
{
  "success": true,
  "player_stats": {
    "id": 1,
    "player_id": 1,
    "username": "user",
    "coins": 100,
    "experience": 500,
    "level": 3,
    "experience_to_next_level": 500,
    "experience_per_level": 1000,
    "progress_to_next_level_percent": 50.0,
    "strength": 2,
    "intelligence": 1,
    "agility": 1,
    "stat_upgrade_points": 1
  }
}
```

**Новые поля:** `strength`, `intelligence`, `agility`, `stat_upgrade_points`

---

### 2.3. Информация о другом игроке — `GET /api/player/<player_id>/`

**Ответ:**
```json
{
  "success": true,
  "player": {
    "id": 40,
    "player_id": 40,
    "username": "fhvbnvbn",
    "level": 5,
    "strength": 3,
    "intelligence": 2,
    "agility": 1,
    "clan": {...},
    "landmarks": {...}
  }
}
```

**Новые поля:** `level`, `strength`, `intelligence`, `agility`  
*(stat_upgrade_points не отдаётся другим игрокам — это личный ресурс)*

---

### 2.4. Завершение квеста — `POST /api/quests/<quest_id>/complete/`

**Body:** `{"player_id": 1}`

**Ответ при получении опыта и повышении уровня:**
```json
{
  "success": true,
  "message": "Quest completed! Level up! You reached level 5!",
  "reward_given": {
    "type": "experience",
    "amount": 500,
    "new_experience": 200
  },
  "player_stats": {
    "coins": 100,
    "experience": 200,
    "level": 5,
    "experience_to_next_level": 800,
    "strength": 2,
    "intelligence": 1,
    "agility": 1,
    "stat_upgrade_points": 2,
    "level_up": {
      "new_level": 5,
      "levels_gained": 2,
      "stat_upgrade_points_gained": 2
    }
  },
  "level_up_notification": {
    "new_level": 5,
    "levels_gained": 2,
    "stat_upgrade_points_gained": 2
  }
}
```

**Важно:**
- `level_up_notification` — уведомление о повышении уровня
- `stat_upgrade_points_gained` — сколько очков прокачки добавлено (обычно = levels_gained)
- При level up нужно обновить счётчик очков прокачки на клиенте

---

## 3. API прокачки показателя

### Endpoint: `POST /api/player/upgrade-stat/`

**Требуется аутентификация:** Bearer token

**Request Body:**
```json
{
  "stat_type": "strength"
}
```

**Допустимые значения `stat_type`:** `"strength"` | `"intelligence"` | `"agility"`

**Успешный ответ (200):**
```json
{
  "success": true,
  "message": "Strength upgraded to 3",
  "stat_upgraded": "strength",
  "new_value": 3,
  "stat_upgrade_points_remaining": 0,
  "player_stats": {
    "strength": 3,
    "intelligence": 1,
    "agility": 1,
    "stat_upgrade_points": 0
  }
}
```

**Ошибка — нет очков (400):**
```json
{
  "success": false,
  "error": "No stat upgrade points available. Level up to gain more."
}
```

**Ошибка — неверный stat_type (400):**
```json
{
  "success": false,
  "errors": {
    "stat_type": ["\"invalid\" is not a valid choice."]
  }
}
```

---

## 4. Задачи для Unity

### 4.1. Модели данных

Добавить в модель игрока (PlayerData / UserData):

```csharp
// Показатели прокачки (по умолчанию 1)
public int strength;
public int intelligence;
public int agility;
// Очки для прокачки (даются при level up)
public int stat_upgrade_points;
```

### 4.2. Парсинг ответов

- При логине, запросе stats, информации об игроке — парсить `strength`, `intelligence`, `agility`, `stat_upgrade_points` (где они есть).
- При завершении квеста — проверять наличие `level_up_notification` и `stat_upgrade_points_gained`, при наличии обновлять локальные значения.

### 4.3. UI — отображение показателей

- Показывать силу, интеллект, ловкость в профиле/характеристиках.
- Показывать `stat_upgrade_points` как «доступные очки прокачки».

### 4.4. UI — прокачка показателя

- Кнопки/меню для прокачки strength / intelligence / agility.
- Перед запросом проверять `stat_upgrade_points > 0`.
- При `stat_upgrade_points == 0` — кнопки неактивны или скрыты.
- Запрос: `POST /api/player/upgrade-stat/` с `{"stat_type": "strength"}` (или intelligence/agility).

### 4.5. Обработка ответа прокачки

После успешного ответа:
- Обновить соответствующий показатель (strength/intelligence/agility) на `new_value`.
- Установить `stat_upgrade_points = stat_upgrade_points_remaining`.
- Показать уведомление (например, «Сила увеличена до 3»).

### 4.6. Обработка level up (квесты)

При получении ответа `CompleteQuest`:
- Если есть `level_up_notification`:
  - Показать уведомление о повышении уровня.
  - Увеличить `stat_upgrade_points` на `stat_upgrade_points_gained`.

---

## 5. Последовательность для Unity (псевдокод)

```csharp
// При логине / загрузке stats
void OnPlayerDataReceived(PlayerData data) {
    strength = data.strength;
    intelligence = data.intelligence;
    agility = data.agility;
    stat_upgrade_points = data.stat_upgrade_points;
    UpdateStatsUI();
}

// При нажатии "Прокачать силу"
void OnUpgradeStrengthClicked() {
    if (stat_upgrade_points <= 0) return;
    APIService.UpgradeStat("strength", (success, response) => {
        if (success) {
            strength = response.new_value;
            stat_upgrade_points = response.stat_upgrade_points_remaining;
            ShowNotification($"Сила увеличена до {strength}");
            UpdateStatsUI();
        }
    });
}

// При завершении квеста
void OnQuestComplete(QuestCompleteResponse response) {
    // Обновить stats из response.player_stats
    strength = response.player_stats.strength;
    intelligence = response.player_stats.intelligence;
    agility = response.player_stats.agility;
    stat_upgrade_points = response.player_stats.stat_upgrade_points;
    
    if (response.level_up_notification != null) {
        ShowLevelUpNotification(response.level_up_notification);
        // stat_upgrade_points уже обновлён из player_stats
    }
}
```

---

## 6. Резюме полей и endpoints

| Поле | Тип | Где приходит | Описание |
|------|-----|--------------|----------|
| strength | int | login, stats, player info, quest complete, upgrade-stat | Сила, default 1 |
| intelligence | int | то же | Интеллект, default 1 |
| agility | int | то же | Ловкость, default 1 |
| stat_upgrade_points | int | login, stats, quest complete, upgrade-stat | Очки для прокачки |
| stat_upgrade_points_gained | int | level_up_notification (квесты) | Сколько очков получено при level up |

| Endpoint | Метод | Описание |
|----------|-------|----------|
| /api/player/stats/ | GET | Текущая статистика (включая stats) |
| /api/player/upgrade-stat/ | POST | Прокачка strength/intelligence/agility |
| /api/quests/<id>/complete/ | POST | Завершение квеста (может дать level up + очки) |

---

## 7. Base URL

Для запросов используется base URL API (например, `http://87.228.97.188/api/`). Все endpoints требуют заголовок `Authorization: Bearer <access_token>` кроме логина.
