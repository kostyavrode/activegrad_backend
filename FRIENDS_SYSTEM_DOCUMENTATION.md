# Система друзей - Документация API

## Обзор

Реализована полная система управления друзьями с запросами дружбы. Пользователи могут отправлять запросы дружбы, принимать/отклонять их, просматривать список друзей и удалять друзей.

## Модели

### FriendRequest
Модель для запросов дружбы:
- `from_user` - отправитель запроса
- `to_user` - получатель запроса
- `status` - статус запроса (pending, accepted, rejected, cancelled)
- `created_at` - дата создания
- `updated_at` - дата обновления

### Friendship
Модель для подтверждённых дружеских отношений:
- `user1` - первый пользователь
- `user2` - второй пользователь
- `created_at` - дата создания дружбы

## API Endpoints

Все endpoints требуют аутентификации (JWT токен в заголовке `Authorization: Bearer <token>`).

### 1. Отправить запрос дружбы
**POST** `/api/accounts/friends/requests/send/`

**Request Body:**
```json
{
  "to_user_id": 123
}
```

**Response (201):**
```json
{
  "success": true,
  "message": "Friend request sent successfully",
  "friend_request": {
    "id": 1,
    "from_user": {
      "id": 1,
      "username": "user1",
      "first_name": "John",
      "last_name": "Doe",
      "level": 5,
      "gender": "M"
    },
    "to_user": {
      "id": 123,
      "username": "user2",
      "first_name": "Jane",
      "last_name": "Smith",
      "level": 3,
      "gender": "F"
    },
    "status": "pending",
    "created_at": "2024-01-01T12:00:00Z",
    "updated_at": "2024-01-01T12:00:00Z"
  }
}
```

### 2. Принять запрос дружбы
**POST** `/api/accounts/friends/requests/<request_id>/accept/`

**Response (200):**
```json
{
  "success": true,
  "message": "Friend request accepted",
  "friendship": {
    "id": 1,
    "friend": {
      "id": 1,
      "username": "user1",
      "first_name": "John",
      "last_name": "Doe",
      "level": 5,
      "gender": "M"
    },
    "created_at": "2024-01-01T12:05:00Z"
  }
}
```

### 3. Отклонить запрос дружбы
**POST** `/api/accounts/friends/requests/<request_id>/reject/`

**Response (200):**
```json
{
  "success": true,
  "message": "Friend request rejected"
}
```

### 4. Получить список друзей
**GET** `/api/accounts/friends/`

**Response (200):**
```json
{
  "success": true,
  "friends": [
    {
      "id": 1,
      "username": "user1",
      "first_name": "John",
      "last_name": "Doe",
      "level": 5,
      "gender": "M"
    },
    {
      "id": 2,
      "username": "user2",
      "first_name": "Jane",
      "last_name": "Smith",
      "level": 3,
      "gender": "F"
    }
  ],
  "total_count": 2
}
```

### 5. Получить входящие запросы дружбы
**GET** `/api/accounts/friends/requests/pending/`

**Response (200):**
```json
{
  "success": true,
  "pending_requests": [
    {
      "id": 1,
      "from_user": {
        "id": 5,
        "username": "user5",
        "first_name": "Bob",
        "last_name": "Wilson",
        "level": 7,
        "gender": "M"
      },
      "to_user": {
        "id": 1,
        "username": "user1",
        "first_name": "John",
        "last_name": "Doe",
        "level": 5,
        "gender": "M"
      },
      "status": "pending",
      "created_at": "2024-01-01T11:00:00Z",
      "updated_at": "2024-01-01T11:00:00Z"
    }
  ],
  "total_count": 1
}
```

### 6. Получить отправленные запросы дружбы
**GET** `/api/accounts/friends/requests/sent/`

**Response (200):**
```json
{
  "success": true,
  "sent_requests": [
    {
      "id": 2,
      "from_user": {
        "id": 1,
        "username": "user1",
        "first_name": "John",
        "last_name": "Doe",
        "level": 5,
        "gender": "M"
      },
      "to_user": {
        "id": 10,
        "username": "user10",
        "first_name": "Alice",
        "last_name": "Brown",
        "level": 4,
        "gender": "F"
      },
      "status": "pending",
      "created_at": "2024-01-01T10:00:00Z",
      "updated_at": "2024-01-01T10:00:00Z"
    }
  ],
  "total_count": 1
}
```

### 7. Удалить друга
**DELETE** `/api/accounts/friends/<friend_id>/remove/`

**Response (200):**
```json
{
  "success": true,
  "message": "Friend removed successfully"
}
```

## Обработка ошибок

Все endpoints возвращают стандартизированные ответы об ошибках:

```json
{
  "success": false,
  "error": "Описание ошибки"
}
```

### Возможные ошибки:

1. **400 Bad Request:**
   - "Cannot send friend request to yourself"
   - "You are already friends with this user"
   - "Friend request already sent"
   - "This user has already sent you a friend request. Please accept it instead."
   - "You are already friends"

2. **403 Forbidden:**
   - "You are not authorized to accept this request"
   - "You are not authorized to reject this request"

3. **404 Not Found:**
   - "User not found"
   - "Friend request not found or already processed"

## Установка и применение миграций

После реализации необходимо создать и применить миграции:

```bash
python manage.py makemigrations accounts
python manage.py migrate accounts
```

**Примечание:** Если возникает ошибка с модулем `drf_spectacular`, временно уберите его из `INSTALLED_APPS` в `settings.py` для создания миграций, или установите его: `pip install drf-spectacular`

## Логика работы

1. **Отправка запроса:**
   - Пользователь A отправляет запрос пользователю B
   - Создаётся запись `FriendRequest` со статусом `pending`
   - Проверяется, что пользователи не друзья и нет активных запросов

2. **Принятие запроса:**
   - Пользователь B принимает запрос от пользователя A
   - Создаётся запись `Friendship` с user1 и user2 (упорядоченные по ID)
   - Статус `FriendRequest` меняется на `accepted`

3. **Отклонение запроса:**
   - Пользователь B отклоняет запрос от пользователя A
   - Статус `FriendRequest` меняется на `rejected`

4. **Удаление друга:**
   - Удаляется запись `Friendship`
   - Все связанные `FriendRequest` со статусом `accepted` меняются на `cancelled`

## Безопасность

- Все endpoints требуют аутентификации (JWT токен)
- Пользователи могут принимать/отклонять только запросы, адресованные им
- Проверка на попытку добавить самого себя в друзья
- Проверка на дублирование запросов и дружеских отношений



