# API системы кланов

## Обзор

Система кланов позволяет игрокам создавать кланы, вступать в них, покидать и искать другие кланы. Также доступен рейтинг топ-10 лучших кланов.

## Валидация названия клана

- Максимальная длина: **20 символов**
- Запрещенные символы: `< > " ' & / \ { } [ ] | * ? % $ # @ ! \``
- Название должно быть уникальным (проверка выполняется без учета регистра - нельзя создать клан "MyClan" если уже существует "myclan")

## API Endpoints

Все endpoints требуют аутентификации (JWT токен в заголовке `Authorization: Bearer <token>`).

### 1. Создать клан

**POST** `/api/accounts/clans/create/`

**Request Body:**
```json
{
  "name": "MyClan",
  "description": "Описание клана (опционально)"
}
```

**Response (201 - успешное создание):**
```json
{
  "success": true,
  "message": "Clan created successfully",
  "clan": {
    "id": 1,
    "name": "MyClan",
    "description": "Описание клана",
    "created_at": "2024-01-01T12:00:00Z",
    "created_by_id": 5,
    "created_by_username": "player1",
    "member_count": 1,
    "captured_landmarks_count": 0
  }
}
```

**Response (400 - ошибка валидации):**
```json
{
  "success": false,
  "errors": {
    "name": ["Название клана не может быть длиннее 20 символов"]
  }
}
```

**Response (400 - клан с таким названием уже существует):**
```json
{
  "success": false,
  "errors": {
    "name": ["Клан с таким названием уже существует"]
  }
}
```

**Response (400 - пользователь уже в клане):**
```json
{
  "success": false,
  "error": "You are already in a clan. Leave your current clan first."
}
```

### 2. Вступить в клан

**POST** `/api/accounts/clans/join/`

**Request Body:**
```json
{
  "clan_id": 1
}
```

**Response (200 - успешное вступление):**
```json
{
  "success": true,
  "message": "You have joined the clan 'MyClan'",
  "clan": {
    "id": 1,
    "name": "MyClan",
    "description": "Описание клана",
    "created_at": "2024-01-01T12:00:00Z",
    "created_by_id": 5,
    "created_by_username": "player1",
    "member_count": 2,
    "captured_landmarks_count": 5
  }
}
```

**Response (400 - пользователь уже в клане):**
```json
{
  "success": false,
  "error": "You are already in another clan. Leave your current clan first."
}
```

**Response (404 - клан не найден):**
```json
{
  "success": false,
  "error": "Clan not found"
}
```

### 3. Покинуть клан

**POST** `/api/accounts/clans/leave/`

**Response (200 - успешное покидание):**
```json
{
  "success": true,
  "message": "You have left the clan 'MyClan'"
}
```

**Response (400 - пользователь не в клане):**
```json
{
  "success": false,
  "error": "You are not in any clan"
}
```

### 4. Поиск кланов

**GET** `/api/accounts/clans/search/?query=MyClan`

**Query Parameters:**
- `query` (обязательный) - поисковый запрос (часть названия клана)

**Response (200):**
```json
{
  "success": true,
  "clans": [
    {
      "id": 1,
      "name": "MyClan",
      "description": "Описание клана",
      "created_at": "2024-01-01T12:00:00Z",
      "created_by_id": 5,
      "created_by_username": "player1",
      "member_count": 10,
      "captured_landmarks_count": 25
    },
    {
      "id": 2,
      "name": "MyClan2",
      "description": "Другой клан",
      "created_at": "2024-01-02T10:00:00Z",
      "created_by_id": 6,
      "created_by_username": "player2",
      "member_count": 5,
      "captured_landmarks_count": 12
    }
  ],
  "total_count": 2,
  "query": "MyClan"
}
```

**Response (400 - отсутствует query):**
```json
{
  "success": false,
  "error": "Query parameter is required"
}
```

### 5. Топ-10 лучших кланов

**GET** `/api/accounts/clans/top/`

Возвращает топ-10 кланов, отсортированных по количеству участников (по убыванию).

**Response (200):**
```json
{
  "success": true,
  "top_clans": [
    {
      "id": 1,
      "name": "BestClan",
      "description": "Самый лучший клан",
      "created_at": "2024-01-01T12:00:00Z",
      "created_by_id": 5,
      "created_by_username": "player1",
      "member_count": 50,
      "captured_landmarks_count": 100
    },
    {
      "id": 2,
      "name": "SecondClan",
      "description": "Второй по величине",
      "created_at": "2024-01-02T10:00:00Z",
      "created_by_id": 6,
      "created_by_username": "player2",
      "member_count": 35,
      "captured_landmarks_count": 75
    }
  ],
  "total_count": 10
}
```

## Логика работы

### Создание клана
1. Пользователь должен быть не в клане
2. Название валидируется (длина, запрещенные символы, уникальность)
3. Создается клан с текущим пользователем как создателем
4. Пользователь автоматически присоединяется к созданному клану

### Вступление в клан
1. Пользователь должен быть не в клане (или покинуть текущий)
2. Клан должен существовать
3. Пользователь присоединяется к клану (поле `clan` в `CustomUser`)

### Покидание клана
1. Пользователь должен быть в клане
2. Поле `clan` устанавливается в `null`
3. Клан остается в базе (даже если стал пустым)

### Поиск кланов
- Поиск выполняется по частичному совпадению названия (без учета регистра)
- Возвращается до 20 результатов
- Результаты сортируются по названию

### Топ-10 кланов
- Рейтинг определяется по количеству участников (`member_count`)
- Если количество участников одинаковое, сортировка по дате создания (новые первыми)
- Показываются только кланы с хотя бы одним участником

## Интеграция с системой захвата достопримечательностей

При захвате достопримечательности:
- Информация о клане игрока автоматически сохраняется в `LandmarkCapture`
- Метод `get_captured_landmarks_count()` в модели `Clan` возвращает количество уникальных захваченных достопримечательностей

## Установка и применение миграций

После реализации необходимо создать и применить миграции:

```bash
# Создать миграции для accounts (изменение max_length для name в Clan)
python manage.py makemigrations accounts

# Применить миграции
python manage.py migrate accounts
```

## Запрещенные символы

Полный список запрещенных символов в названии клана:
`< > " ' & / \ { } [ ] | * ? % $ # @ ! ``

Эти символы могут вызывать проблемы в различных системах (SQL injection, XSS и т.д.), поэтому запрещены.

