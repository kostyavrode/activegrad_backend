# Инструкция по перезапуску Django + Gunicorn + Nginx

## Проблема

После изменений в коде Django нужно перезапустить gunicorn, чтобы изменения вступили в силу.

## Шаги для перезапуска

### 1. Найти процесс gunicorn

```bash
# Найти процесс gunicorn
ps aux | grep gunicorn

# Или найти по порту
sudo lsof -i :8000
```

### 2. Перезапустить gunicorn

**Вариант A: Если gunicorn запущен как systemd service**

```bash
# Проверить статус
sudo systemctl status gunicorn

# Перезапустить
sudo systemctl restart gunicorn

# Или перезагрузить (более мягкий способ)
sudo systemctl reload gunicorn
```

**Вариант B: Если gunicorn запущен вручную**

```bash
# Найти PID процесса
ps aux | grep gunicorn

# Отправить сигнал HUP для перезагрузки (не убивает процесс)
kill -HUP <PID>

# Или убить и запустить заново
pkill gunicorn
# Затем запустите снова (команда зависит от вашей настройки)
```

**Вариант C: Если используется supervisor**

```bash
sudo supervisorctl restart gunicorn
```

### 3. Перезагрузить nginx

```bash
# Проверить конфигурацию nginx
sudo nginx -t

# Если конфигурация правильная, перезагрузить
sudo systemctl reload nginx

# Или
sudo service nginx reload
```

### 4. Проверить, что всё работает

```bash
# Проверить статус gunicorn
sudo systemctl status gunicorn

# Проверить статус nginx
sudo systemctl status nginx

# Проверить, что gunicorn слушает порт 8000
sudo netstat -tlnp | grep 8000
# или
sudo ss -tlnp | grep 8000
```

## Типичная команда запуска gunicorn

Если вы запускаете gunicorn вручную, команда обычно выглядит так:

```bash
cd /opt/activegrad_backend
source venv/bin/activate  # если используете виртуальное окружение
gunicorn myproject.wsgi:application \
    --bind 127.0.0.1:8000 \
    --workers 3 \
    --timeout 120 \
    --access-logfile /var/log/gunicorn/access.log \
    --error-logfile /var/log/gunicorn/error.log \
    --daemon
```

## Проверка логов

Если что-то не работает, проверьте логи:

```bash
# Логи gunicorn
sudo tail -f /var/log/gunicorn/error.log
# или где у вас хранятся логи

# Логи nginx
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log

# Логи Django (если настроены)
tail -f /opt/activegrad_backend/logs/django.log
```

## Быстрая проверка после перезапуска

```bash
# Проверить тестовый endpoint
curl -X GET http://87.228.97.188/api/landmarks/test/ \
  -H "Authorization: Bearer ВАШ_ТОКЕН"

# Если тестовый endpoint работает, проверьте save endpoint
curl -X POST http://87.228.97.188/api/landmarks/save/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ВАШ_ТОКЕН" \
  -d '{"player_id": 1, "external_ids": ["Q12345"]}'
```

## Если проблема сохраняется

1. **Проверьте, что код загружен на сервер:**
   ```bash
   cd /opt/activegrad_backend
   ls -la landmarks/views.py
   cat landmarks/urls.py
   ```

2. **Проверьте, что приложение в INSTALLED_APPS:**
   ```bash
   python manage.py shell
   >>> from django.conf import settings
   >>> 'landmarks' in settings.INSTALLED_APPS
   True
   ```

3. **Проверьте URL через Django:**
   ```bash
   python manage.py shell
   >>> from django.urls import reverse
   >>> reverse('save-player-landmarks')
   '/api/landmarks/save/'
   ```

4. **Проверьте, что миграции применены:**
   ```bash
   python manage.py showmigrations landmarks
   ```

## Рекомендация: Использовать systemd service для gunicorn

Создайте файл `/etc/systemd/system/gunicorn.service`:

```ini
[Unit]
Description=gunicorn daemon
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/activegrad_backend
ExecStart=/opt/activegrad_backend/venv/bin/gunicorn \
    --access-logfile - \
    --workers 3 \
    --bind 127.0.0.1:8000 \
    myproject.wsgi:application

[Install]
WantedBy=multi-user.target
```

Затем:
```bash
sudo systemctl daemon-reload
sudo systemctl enable gunicorn
sudo systemctl start gunicorn
```

После этого перезапуск будет простым:
```bash
sudo systemctl restart gunicorn
```

