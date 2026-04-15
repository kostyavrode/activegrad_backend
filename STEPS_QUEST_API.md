# Квест «Шаги» — API

## 1. POST /api/player/daily-steps/

Синхронизация шагов игрока. Вызывать **перед** завершением квеста по шагам.

```
POST /api/player/daily-steps/
Authorization: Bearer <token>
Content-Type: application/json

{
  "daily_steps": 600
}
```

**Ответ:** 200 OK
```json
{"success": true}
```

---

## 2. POST /api/quests/{id}/complete/

Завершение квеста. Для квеста типа `steps` можно передать `steps` в теле — они пойдут в проверку вместо `player.daily_steps`.

```
POST /api/quests/6/complete/
Authorization: Bearer <token>
Content-Type: application/json

{
  "player_id": 44,
  "steps": 600
}
```

**Логика для steps:**
- Если в запросе есть `steps` — используется это значение
- Если `steps` нет — используется `player.daily_steps` (после вызова POST /api/player/daily-steps/)
- Выполнено, если `effective_steps >= quest.count`

**Рекомендуемый порядок вызовов:**
1. `POST /api/player/daily-steps/` с актуальным `daily_steps`
2. `POST /api/quests/{id}/complete/` с `player_id` и `steps`
