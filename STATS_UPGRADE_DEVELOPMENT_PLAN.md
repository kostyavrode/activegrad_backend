# План разработки: показатели прокачки и уведомления о повышении уровня

## Анализ текущего состояния кода

### ✅ Что уже есть

1. **Опыт и уровень у каждого пользователя** (`accounts/models.CustomUser`):
   - `experience` (default=0)
   - `level` (default=1)
   - `EXPERIENCE_PER_LEVEL = 1000`

2. **Логика повышения уровня** (`add_experience` в `accounts/models.py`):
   - При достижении 1000 опыта уровень повышается
   - Поддержка нескольких уровней за один раз (while loop)
   - Возвращает: `experience`, `level`, `leveled_up`, `levels_gained`

3. **Уведомление о повышении уровня при получении опыта**:
   - **Только в CompleteQuestView** (quests) — при награде за квест типом `experience`
   - В ответе: `level_up_notification`, `player_stats.level_up`, кастомное сообщение

### ❌ Чего нет

1. **Уведомление о повышении уровня в других местах**:
   - Login / JWT — только текущие experience, level, experience_to_next_level
   - GetCurrentUserStatsView — только статистика, без уведомлений
   - Других мест добавления опыта нет (только квесты)

2. **Показатели прокачки**: сила, интеллект, ловкость

3. **Возможность прокачки** (счётчик очков после уровня)

4. **API прокачки** с проверкой наличия очков

---

## Этапы разработки

### Этап 1: Миграция модели — добавление полей прокачки

**Цель:** Добавить в `CustomUser` поля силы, интеллекта, ловкости и счётчик очков прокачки.

**Изменения:**
- `strength` (IntegerField, default=1)
- `intelligence` (IntegerField, default=1)
- `agility` (IntegerField, default=1)
- `stat_upgrade_points` (IntegerField, default=0) — очки для прокачки (выдаются при повышении уровня)

**Файлы:**
- `accounts/models.py`
- `accounts/migrations/00XX_customuser_stats.py` (новый)

**Логика:** При вызове `add_experience` и повышении уровня: `stat_upgrade_points += levels_gained`.

---

### Этап 2: Обновление логики повышения уровня

**Цель:** При повышении уровня начислять `stat_upgrade_points` (1 очко за каждый новый уровень).

**Изменения в `accounts/models.py`:**
- В методе `add_experience`: при `levels_gained > 0` добавлять `self.stat_upgrade_points += levels_gained`
- Сохранять поле `stat_upgrade_points` в `update_fields`

---

### Этап 3: Уведомления о повышении уровня во всех ответах

**Цель:** Все endpoints, возвращающие статистику игрока, должны включать:
- `level_up_notification` — если было повышение уровня в рамках текущего запроса (для квестов — уже есть)
- Для Login/Stats — показывать только текущие значения; уведомление о level up — только при действиях, которые дают опыт (квесты)

**Важно:** Уведомление о level up имеет смысл только там, где опыт добавляется. Сейчас это только CompleteQuestView — там уже реализовано.

**Дополнительно:** Добавить в ответы квестов `stat_upgrade_points_gained` при level up (сколько очков прокачки получил пользователь).

**Файлы:**
- `quests/views.py` — в `level_info` добавить `stat_upgrade_points_gained: levels_gained`

---

### Этап 4: API прокачки показателей

**Цель:** Endpoint `POST /api/player/upgrade-stat/` для прокачки силы/интеллекта/ловкости.

**Логика:**
1. Проверить `stat_upgrade_points > 0`
2. Принять `stat_type`: `"strength"` | `"intelligence"` | `"agility"`
3. Увеличить соответствующий показатель на 1
4. Уменьшить `stat_upgrade_points` на 1
5. Вернуть обновлённые значения

**Файлы:**
- `accounts/views.py` — новый `UpgradeStatView`
- `accounts/serializers.py` — `UpgradeStatSerializer`
- `accounts/urls.py` — добавить маршрут
- `myproject/urls.py` — если нужно

---

### Этап 5: Включение новых полей во все ответы

**Цель:** Все ответы с данными пользователя должны включать:
- `strength`, `intelligence`, `agility`
- `stat_upgrade_points` (сколько очков можно потратить)

**Файлы:**
- `accounts/serializers.py` — CustomTokenObtainPairSerializer, UserBasicSerializer
- `accounts/views.py` — LoginAPIView, GetCurrentUserStatsView, GetPlayerInfoView
- `quests/views.py` — player_stats в CompleteQuestView

---

### Этап 6: Уведомление при прокачке показателя (в ответе на upgrade-stat)

**Цель:** В ответе `POST /api/player/upgrade-stat/` включить:
- `stat_upgraded`: какой показатель прокачан
- `new_value`: новое значение
- `stat_upgrade_points_remaining`: сколько очков осталось

Клиент при получении этого ответа уменьшает счётчик возможности прокачки на своей стороне (или синхронизируется с сервером).

---

## Краткая сводка этапов

| Этап | Описание | Оценка |
|------|----------|--------|
| 1 | Миграция: strength, intelligence, agility, stat_upgrade_points | Малый |
| 2 | add_experience: начислять stat_upgrade_points при level up | Малый |
| 3 | level_up_notification + stat_upgrade_points_gained в квестах | Малый |
| 4 | API UpgradeStatView с проверкой stat_upgrade_points | Средний |
| 5 | Добавить stats во все ответы API | Малый |
| 6 | Уведомление в ответе upgrade-stat (уже в этапе 4) | — |

---

## Миграция на сервере с конфликтом

Если на сервере уже есть миграции 0003-0007 (например, clan), возможен конфликт. В таком случае:

```bash
# Вариант 1: переименовать локальную миграцию и указать зависимость
# Переименовать 0003_customuser_stats.py в 0008_customuser_stats.py
# и изменить dependencies на [('accounts', '0007_delete_clan')]

# Вариант 2: создать миграцию на сервере
python manage.py makemigrations accounts
python manage.py migrate accounts
```

## Порядок реализации (рекомендуемый)

1. **Этап 1** — миграция
2. **Этап 2** — обновить `add_experience`
3. **Этап 5** — добавить поля в ответы (чтобы клиент видел 1/1/1 и 0 очков)
4. **Этап 4** — API прокачки (включая логику из этапа 6)
5. **Этап 3** — доработать level_up_notification в квестах (stat_upgrade_points_gained)

---

## Примеры ответов API после реализации

### Login / JWT
```json
{
  "user": {
    "id": 1,
    "level": 5,
    "experience": 300,
    "experience_to_next_level": 700,
    "strength": 3,
    "intelligence": 2,
    "agility": 1,
    "stat_upgrade_points": 2
  }
}
```

### POST /api/player/upgrade-stat/ {"stat_type": "strength"}
```json
{
  "success": true,
  "message": "Strength upgraded to 4",
  "stat_upgraded": "strength",
  "new_value": 4,
  "stat_upgrade_points_remaining": 1,
  "player_stats": {
    "strength": 4,
    "intelligence": 2,
    "agility": 1,
    "stat_upgrade_points": 1
  }
}
```

### Ошибка: нет очков для прокачки
```json
{
  "success": false,
  "error": "No stat upgrade points available. Level up to gain more."
}
```
