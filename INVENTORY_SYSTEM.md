# Система инвентаря

## Обзор

У каждого игрока есть персональный инвентарь с:
- **3 типа ресурсов**: металл, дерево, чертежи
- **2 предмета**: меч (острота) и щит (стойкость)

Меч и щит крафтятся по рецептам, улучшаются с вероятностным успехом.

---

## API Endpoints

Все эндпоинты требуют аутентификации (Bearer token).

### 1. Получить инвентарь

```
GET /api/inventory/
```

**Ответ:**
```json
{
  "success": true,
  "inventory": {
    "resources": {
      "metal": 5,
      "wood": 3,
      "blueprints": 2
    },
    "items": {
      "sword": {
        "has_item": true,
        "sharpness": 2
      },
      "shield": {
        "has_item": false,
        "durability": null
      }
    }
  }
}
```

### 2. Получить рецепты крафта

```
GET /api/inventory/recipes/
```

**Ответ:**
```json
{
  "success": true,
  "recipes": {
    "sword": {
      "metal_required": 1,
      "wood_required": 1,
      "blueprints_required": 1
    },
    "shield": {
      "metal_required": 1,
      "wood_required": 1,
      "blueprints_required": 1
    }
  }
}
```

### 3. Скрафтить меч

```
POST /api/inventory/craft/sword/
```

Требует ресурсы по рецепту (по умолчанию: 1 металл, 1 дерево, 1 чертёж).

**Ответ при успехе:**
```json
{
  "success": true,
  "message": "Sword crafted successfully",
  "inventory": { ... }
}
```

**Ошибки:**
- 400: уже есть меч, недостаточно ресурсов

### 4. Скрафтить щит

```
POST /api/inventory/craft/shield/
```

Аналогично крафту меча.

### 5. Улучшить меч

```
POST /api/inventory/upgrade/sword/
Content-Type: application/json

{
  "metal": 2,
  "wood": 1,
  "blueprints": 1
}
```

Чем больше ресурсов — тем выше вероятность успеха. Вероятность настраивается в админке.

**Ответ:**
```json
{
  "success": true,
  "upgraded": true,
  "probability": 20.0,
  "roll": 15.3,
  "sword_sharpness": 3
}
```

- `upgraded`: true = улучшилось, false = нет (ресурсы не списываются при неудаче)
- `probability`: рассчитанная вероятность успеха (%)
- `roll`: случайное значение (для отладки)

### 6. Улучшить щит

```
POST /api/inventory/upgrade/shield/
```

Тело запроса и логика — аналогично улучшению меча.

---

## Админ-панель Django

### Инвентарь игроков (PlayerInventory)

- Просмотр/редактирование ресурсов: metal, wood, blueprints
- Просмотр/редактирование предметов: sword_sharpness, shield_durability
- Через админку можно выдать игроку ресурсы для тестирования

### Рецепты крафта (CraftRecipe)

- Настройка количества металла, дерева, чертежей для крафта меча и щита
- По умолчанию: 1 каждого ресурса
- `is_active` — можно отключить рецепт

### Настройки улучшения (UpgradeConfig)

- **base_probability** — базовая вероятность (0–100%) без ресурсов
- **metal_prob_per_unit** — сколько % вероятности добавляет 1 металл
- **wood_prob_per_unit** — за 1 дерево
- **blueprints_prob_per_unit** — за 1 чертёж
- **max_probability** — максимальная вероятность (обычно 95%)

**Формула:** `probability = min(max_probability, base + metal*M + wood*W + blueprints*B)`

**Пример:** 2 металла, 2 дерева, 2 чертежа при настройках 5% за единицу:
`0 + 2*5 + 2*5 + 2*5 = 30%` вероятность успеха.

---

## Добавление ресурсов игроку

Сейчас ресурсы можно:
1. Выдать через админ-панель (PlayerInventory → редактировать metal/wood/blueprints)
2. Добавить в будущем выдачу за квесты (расширить reward_type или добавить новый)

---

## Модели

| Модель | Описание |
|--------|----------|
| PlayerInventory | Инвентарь: ресурсы + меч/щит (если есть) |
| CraftRecipe | Рецепт крафта (настраивается в админке) |
| UpgradeConfig | Настройки вероятности улучшения |
