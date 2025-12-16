# Инструкция по обновлению API квестов на хосте

## Обзор изменений

Обновлена система квестов согласно новым требованиям:
- Добавлены обязательные поля: `type`, `reward_type`, `reward_amount`
- Добавлены новые endpoints: `/api/quests/<quest_id>/complete/` и `/api/quests/progress/`
- Обновлена модель Quest с валидацией
- Добавлена модель QuestProgress для отслеживания прогресса

---

## Шаги для обновления на хосте

### 1. Подключитесь к серверу

```bash
ssh ваш_пользователь@87.228.97.188
```

### 2. Перейдите в директорию проекта

```bash
cd /opt/activegrad_backend
```

### 3. Активируйте виртуальное окружение

```bash
source venv/bin/activate
```

**Важно:** После активации вы должны увидеть `(venv)` в начале строки терминала:
```bash
(venv) kiberkostya@zahra:/opt/activegrad_backend$
```

Если виртуальное окружение не активировано, Django не будет найден!

### 4. Обновите код проекта

**Вариант A: Если используете Git**

```bash
# Сохраните текущее состояние (опционально, для отката)
git stash

# Получите последние изменения
git pull origin main
# или
git pull origin master
```

**Вариант B: Если загружаете файлы вручную**

Загрузите обновленные файлы:
- `quests/models.py`
- `quests/serializers.py`
- `quests/views.py`
- `quests/urls.py`
- `quests/admin.py`

### 5. Установите зависимости (если нужно)

```bash
pip install -r requirements.txt
```

### 6. Создайте миграции для quests

```bash
python manage.py makemigrations quests
```

Вы должны увидеть что-то вроде:
```
Migrations for 'quests':
  quests/migrations/0002_quest_type_quest_reward_type_quest_reward_amount_quest_item_id_quest_is_active_quest_created_at_quest_updated_at_questprogress.py
    - Add field type to quest
    - Add field reward_type to quest
    - Add field reward_amount to quest
    - Add field item_id to quest
    - Add field is_active to quest
    - Add field created_at to quest
    - Add field updated_at to quest
    - Create model QuestProgress
```

### 7. Примените миграции

**⚠️ ВАЖНО: Если у вас уже есть квесты в базе данных, нужно будет указать значение для поля `type`**

**Вариант A: Если у вас НЕТ существующих квестов в БД**

```bash
python manage.py migrate quests
```

**Вариант B: Если у вас ЕСТЬ существующие квесты**

Django попросит указать значение по умолчанию для поля `type`. Выберите один из вариантов:

1. Временно указать значение по умолчанию (например, 'mark_sights')
2. Выйти и заполнить данные вручную

Рекомендуется:
```bash
# Сначала создайте миграцию с default значением
# Отредактируйте файл миграции, если нужно, или используйте:
python manage.py migrate quests
# Когда спросит, введите: 1 (или выберите 'mark_sights')
```

После миграции **обязательно обновите существующие квесты** через админ-панель, указав правильные значения для `type`.

### 8. Примените все миграции (если есть другие)

```bash
python manage.py migrate
```

### 9. Соберите статические файлы (если нужно)

```bash
python manage.py collectstatic --noinput
```

### 10. Проверьте статус миграций

```bash
python manage.py showmigrations quests
```

Должно быть:
```
quests
 [X] 0001_initial
 [X] 0002_... (новая миграция)
```

### 11. Перезапустите Gunicorn

**Вариант A: Если gunicorn запущен как systemd service**

```bash
sudo systemctl restart gunicorn
```

**Вариант B: Если gunicorn запущен вручную**

```bash
# Найти PID процесса
ps aux | grep gunicorn

# Отправить сигнал HUP для перезагрузки
kill -HUP <PID>

# Или перезапустить полностью
pkill gunicorn
# Затем запустите снова (команда зависит от вашей настройки)
```

**Вариант C: Если используется supervisor**

```bash
sudo supervisorctl restart gunicorn
```

### 12. Перезагрузите Nginx (опционально, но рекомендуется)

```bash
# Проверить конфигурацию
sudo nginx -t

# Перезагрузить
sudo systemctl reload nginx
```

### 13. Проверьте, что всё работает

**Проверка статуса сервисов:**

```bash
# Проверить статус gunicorn
sudo systemctl status gunicorn

# Проверить статус nginx
sudo systemctl status nginx
```

**Проверка API:**

```bash
# Проверить endpoint ежедневных квестов
curl -X GET http://87.228.97.188/api/quests/daily/ \
  -H "Authorization: Bearer ВАШ_ACCESS_ТОКЕН"

# Должен вернуться JSON с квестами, у каждого есть поле "type"
```

**Ожидаемый ответ:**
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
    }
  ]
}
```

---

## Важные замечания

### ⚠️ Обновление существующих квестов

Если у вас уже есть квесты в базе данных, **обязательно**:

1. Зайдите в админ-панель Django: `http://87.228.97.188/admin/`
2. Перейдите в раздел "Квесты" (Quests)
3. Для каждого квеста укажите:
   - **`type`** - один из: `mark_sights`, `steps`, `collect_coins`, `level_up`
   - **`reward_type`** - `coins`, `experience` или `item`
   - **`reward_amount`** - количество награды
4. Сохраните изменения

### ⚠️ Создание новых квестов

При создании новых квестов через админ-панель:
- Поле `type` **ОБЯЗАТЕЛЬНО** и не может быть пустым
- Поле `count` должно быть > 0
- Поле `reward_amount` должно быть >= 0
- Если `reward_type = 'item'`, то `item_id` обязателен

### ✅ Проверка валидности квестов

После обновления проверьте, что все квесты имеют поле `type`:

```bash
python manage.py shell
```

```python
from quests.models import Quest

# Проверить квесты без type
invalid_quests = Quest.objects.filter(type__isnull=True) | Quest.objects.filter(type='')
print(f"Квестов без type: {invalid_quests.count()}")

# Показать все квесты
for quest in Quest.objects.all():
    print(f"ID: {quest.id}, Type: {quest.type}, Title: {quest.title}")
```

---

## Откат изменений (если что-то пошло не так)

Если нужно откатить изменения:

```bash
# Откатить миграцию
python manage.py migrate quests 0001_initial

# Или откатить все миграции quests
python manage.py migrate quests zero

# Восстановить старый код из Git
git checkout HEAD~1 quests/
```

---

## Проверка логов при проблемах

Если что-то не работает, проверьте логи:

```bash
# Логи gunicorn
sudo tail -f /var/log/gunicorn/error.log

# Логи nginx
sudo tail -f /var/log/nginx/error.log

# Логи Django (если настроены)
tail -f /opt/activegrad_backend/logs/django.log
```

---

## Быстрая команда для обновления (если всё идёт по плану)

```bash
cd /opt/activegrad_backend && \
source venv/bin/activate && \
python manage.py makemigrations quests && \
python manage.py migrate quests && \
sudo systemctl restart gunicorn && \
echo "Обновление завершено!"
```

---

## Контрольный список

- [ ] Код обновлен на сервере
- [ ] Миграции созданы (`makemigrations`)
- [ ] Миграции применены (`migrate`)
- [ ] Существующие квесты обновлены (поле `type` заполнено)
- [ ] Gunicorn перезапущен
- [ ] Nginx перезагружен
- [ ] API протестирован
- [ ] Все квесты имеют поле `type`

---

**Дата создания:** 2024  
**Версия:** 1.0

