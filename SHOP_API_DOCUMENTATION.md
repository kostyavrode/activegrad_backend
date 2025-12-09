# API документация для магазина

## Обзор

Система магазина позволяет:
- Просматривать товары
- Покупать товары (с проверкой баланса)
- Получать промокоды после покупки
- Просматривать свои промокоды
- Удалять промокоды

## Endpoints

### 1. Получить список товаров

**GET** `/api/shop/items/`

Возвращает список всех активных товаров в магазине.

**Запрос:**
```bash
curl -X GET http://87.228.97.188/api/shop/items/ \
  -H "Authorization: Bearer ВАШ_ТОКЕН"
```

**Ответ (200):**
```json
{
  "success": true,
  "items": [
    {
      "id": 1,
      "name": "Премиум подписка",
      "description": "Месячная подписка на премиум функции",
      "image_url": "https://example.com/image.jpg",
      "price": 1000,
      "is_active": true,
      "created_at": "2025-12-01T10:00:00Z"
    }
  ],
  "total_count": 1
}
```

---

### 2. Купить товар

**POST** `/api/shop/purchase/`

Покупает товар, списывает деньги и выдает промокод.

**Запрос:**
```bash
curl -X POST http://87.228.97.188/api/shop/purchase/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ВАШ_ТОКЕН" \
  -d '{
    "item_id": 1
  }'
```

**Успешный ответ (200):**
```json
{
  "success": true,
  "message": "Successfully purchased Премиум подписка",
  "item_name": "Премиум подписка",
  "price_paid": 1000,
  "remaining_coins": 500,
  "promo_code": "PREM2025"
}
```

**Ошибка - недостаточно средств (400):**
```json
{
  "success": false,
  "error": "Insufficient funds",
  "message": "You have 500 coins, but need 1000 coins",
  "required": 1000,
  "available": 500
}
```

**Ошибка - товар не найден (404):**
```json
{
  "success": false,
  "error": "Item with ID 999 not found or not available"
}
```

---

### 3. Получить промокоды пользователя

**GET** `/api/shop/promo-codes/`

Возвращает список всех промокодов, купленных пользователем.

**Запрос:**
```bash
curl -X GET http://87.228.97.188/api/shop/promo-codes/ \
  -H "Authorization: Bearer ВАШ_ТОКЕН"
```

**Ответ (200):**
```json
{
  "success": true,
  "promo_codes": [
    {
      "id": 1,
      "shop_item_id": 1,
      "shop_item_name": "Премиум подписка",
      "promo_code": "PREM2025",
      "purchased_at": "2025-12-01T10:00:00Z"
    }
  ],
  "total_count": 1
}
```

---

### 4. Удалить промокод

**DELETE** `/api/shop/promo-codes/delete/<promo_code_id>/`

или

**POST** `/api/shop/promo-codes/delete/`

Удаляет промокод пользователя.

**Запрос (DELETE через URL):**
```bash
curl -X DELETE http://87.228.97.188/api/shop/promo-codes/delete/1/ \
  -H "Authorization: Bearer ВАШ_ТОКЕН"
```

**Запрос (POST с телом):**
```bash
curl -X POST http://87.228.97.188/api/shop/promo-codes/delete/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ВАШ_ТОКЕН" \
  -d '{
    "promo_code_id": 1
  }'
```

**Успешный ответ (200):**
```json
{
  "success": true,
  "message": "Promo code PREM2025 deleted successfully"
}
```

**Ошибка - промокод не найден (404):**
```json
{
  "success": false,
  "error": "Promo code with ID 999 not found or does not belong to you"
}
```

---

## Админ панель

### Управление товарами

1. Зайдите в админ панель: `http://87.228.97.188/admin/`
2. Перейдите в раздел **Shop items**
3. Нажмите **"Add Shop item"**
4. Заполните поля:
   - **Name** - название товара
   - **Description** - описание (опционально)
   - **Image URL** - URL картинки (опционально)
   - **Price** - стоимость в coins
   - **Promo code** - промокод, который получит пользователь
   - **Is active** - активен ли товар (показывать в магазине)
5. Сохраните

### Просмотр промокодов пользователей

1. Перейдите в раздел **User promo codes**
2. Увидите все купленные промокоды с информацией:
   - Пользователь
   - Товар
   - Промокод
   - Дата покупки

### История покупок

1. Перейдите в раздел **Purchase history**
2. Увидите полную историю всех покупок

---

## Использование в Unity

### Пример кода для покупки товара:

```csharp
public async Task<PurchaseResult> PurchaseItem(int itemId)
{
    var url = $"{BaseUrl}shop/purchase/";
    var payload = new { item_id = itemId };
    var result = await SendRequest(url, "POST", payload, requireAuth: true);
    
    if (result.success)
    {
        var purchaseResult = JsonUtility.FromJson<PurchaseResult>(result.response);
        Debug.Log($"Куплено! Промокод: {purchaseResult.promo_code}");
        return purchaseResult;
    }
    else
    {
        Debug.LogError($"Ошибка покупки: {result.response}");
        return null;
    }
}

[System.Serializable]
public class PurchaseResult
{
    public bool success;
    public string message;
    public string item_name;
    public int price_paid;
    public int remaining_coins;
    public string promo_code;
}
```

---

## Важные замечания

1. **Проверка баланса** - автоматически проверяется перед покупкой
2. **Списание денег** - происходит автоматически при успешной покупке
3. **Промокоды** - сохраняются у пользователя и могут быть удалены
4. **История покупок** - все покупки сохраняются для аналитики
5. **Активные товары** - только товары с `is_active=True` показываются в списке
6. **Дубликаты** - один товар можно купить несколько раз (если нужно ограничить, раскомментируйте проверку в коде)

---

## Полный пример использования

```bash
# 1. Получите токен
TOKEN=$(curl -X POST http://87.228.97.188/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"password123"}' \
  | jq -r '.access')

# 2. Получите список товаров
curl -X GET http://87.228.97.188/api/shop/items/ \
  -H "Authorization: Bearer $TOKEN" | jq '.'

# 3. Купите товар (ID=1)
curl -X POST http://87.228.97.188/api/shop/purchase/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"item_id": 1}' | jq '.'

# 4. Получите свои промокоды
curl -X GET http://87.228.97.188/api/shop/promo-codes/ \
  -H "Authorization: Bearer $TOKEN" | jq '.'

# 5. Удалите промокод (ID=1)
curl -X DELETE http://87.228.97.188/api/shop/promo-codes/delete/1/ \
  -H "Authorization: Bearer $TOKEN" | jq '.'
```

---

## Что нужно сделать на сервере

1. Загрузите все файлы приложения `shop`
2. Примените миграции:
   ```bash
   python manage.py migrate shop
   ```
3. Перезапустите gunicorn:
   ```bash
   sudo systemctl restart gunicorn
   ```
4. Создайте товары через админ панель

