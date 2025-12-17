# Инструкция по обновлению API для промокодов квестов

## Шаги для обновления на сервере

### 1. Подключитесь к серверу

```bash
ssh ваш_пользователь@87.228.97.188
```

### 2. Перейдите в директорию проекта

```bash
cd /opt/activegrad_backend
# или где у вас находится проект
```

### 3. Загрузите изменения кода

**Если используете Git:**
```bash
git pull origin main
# или
git pull origin master
```

**Если загружаете файлы вручную:**
- Загрузите обновленные файлы:
  - `quests/models.py`
  - `quests/views.py`
  - `quests/serializers.py`
  - `quests/admin.py`
  - `quests/urls.py`

### 4. Активируйте виртуальное окружение (если используется)

```bash
source venv/bin/activate
```

### 5. Создайте миграции (если еще не созданы)

```bash
python manage.py makemigrations quests
```

Вы должны увидеть что-то вроде:
```
Migrations for 'quests':
  quests/migrations/0002_quest_promo_code_quest_image_url_and_more.py
    - Add field promo_code to quest
    - Add field image_url to quest
    - Create model QuestPromoCode
```

### 6. Примените миграции

```bash
python manage.py migrate quests
```

Или примените все миграции:
```bash
python manage.py migrate
```

### 7. Перезапустите Gunicorn

**Если gunicorn запущен как systemd service:**
```bash
sudo systemctl restart gunicorn
```

**Если gunicorn запущен вручную:**
```bash
# Найти процесс
ps aux | grep gunicorn

# Отправить сигнал HUP для перезагрузки
kill -HUP <PID>

# Или перезапустить через supervisor
sudo supervisorctl restart gunicorn
```

### 8. Перезагрузите Nginx (опционально, но рекомендуется)

```bash
sudo systemctl reload nginx
```

### 9. Проверьте, что всё работает

**Проверьте статус сервисов:**
```bash
sudo systemctl status gunicorn
sudo systemctl status nginx
```

**Проверьте новый endpoint:**
```bash
curl -X GET http://87.228.97.188/api/quests/promo-codes/ \
  -H "Authorization: Bearer ВАШ_ТОКЕН"
```

Должен вернуться ответ:
```json
{
  "success": true,
  "promo_codes": [],
  "total_count": 0
}
```

**Проверьте, что новые поля доступны в админке:**
- Откройте http://87.228.97.188/admin/quests/quest/
- Убедитесь, что в форме редактирования квеста есть поля:
  - `promo_code`
  - `image_url`

## Быстрая проверка после обновления

```bash
# 1. Проверить миграции
python manage.py showmigrations quests

# 2. Проверить структуру таблиц
python manage.py shell
```

В shell выполните:
```python
from quests.models import Quest, QuestPromoCode
# Проверить, что новые поля есть
print(Quest._meta.get_field('promo_code'))
print(Quest._meta.get_field('image_url'))
print(QuestPromoCode._meta.get_all_field_names())
```

## Если что-то пошло не так

### Проблема: Миграции не применяются

```bash
# Проверьте логи
python manage.py migrate quests --verbosity 2

# Если ошибка с базой данных, проверьте подключение
python manage.py dbshell
```

### Проблема: Gunicorn не перезапускается

```bash
# Проверьте логи
sudo journalctl -u gunicorn -n 50

# Или логи из файла
sudo tail -f /var/log/gunicorn/error.log
```

### Проблема: Endpoint не работает

```bash
# Проверьте URL
python manage.py shell
>>> from django.urls import reverse
>>> reverse('quest-promo-codes')
'/api/quests/promo-codes/'

# Проверьте, что view импортируется
>>> from quests.views import QuestPromoCodesView
```

## Резюме команд (для копирования)

```bash
# Полная последовательность команд
cd /opt/activegrad_backend
source venv/bin/activate  # если используется venv
git pull  # если используете git
python manage.py makemigrations quests
python manage.py migrate quests
sudo systemctl restart gunicorn
sudo systemctl reload nginx
```

## После обновления

1. **В админке Django** добавьте промокоды и картинки к существующим квестам:
   - Откройте квест в админке
   - Заполните поле `promo_code` (например, "QUEST2025")
   - Заполните поле `image_url` (URL картинки)
   - Сохраните

2. **Проверьте работу:**
   - Завершите квест через API
   - Проверьте, что промокод сохранился: `GET /api/quests/promo-codes/`
   - Убедитесь, что в ответе есть информация о квесте (название, описание, картинка)

