# Установка и настройка Swagger/OpenAPI документации

## Установка пакета

На сервере выполните:

```bash
cd /opt/activegrad_backend
source venv/bin/activate  # если используете виртуальное окружение
pip install drf-spectacular
```

Или добавьте в `requirements.txt` (если используете):

```
drf-spectacular>=0.27.0
```

## Доступ к документации

После установки и перезапуска сервера, документация будет доступна по адресам:

### 1. Swagger UI (интерактивная документация)
```
http://87.228.97.188/api/docs/
```

### 2. ReDoc (альтернативный интерфейс)
```
http://87.228.97.188/api/redoc/
```

### 3. OpenAPI Schema (JSON/YAML)
```
http://87.228.97.188/api/schema/
```

## Использование

### Swagger UI

1. Откройте `http://87.228.97.188/api/docs/`
2. Нажмите кнопку **"Authorize"** (справа вверху)
3. Введите токен в формате: `Bearer ваш_токен` или просто `ваш_токен`
4. Нажмите **"Authorize"**
5. Теперь вы можете тестировать API прямо в браузере!

### Пример использования токена

1. Получите токен через `/api/login/` или `/api/token/`
2. В Swagger UI нажмите **"Authorize"**
3. В поле введите: `Bearer eyJ0eXAiOiJKV1QiLCJhbGc...` (ваш access токен)
4. Или просто: `eyJ0eXAiOiJKV1QiLCJhbGc...` (без Bearer)

## Что включено

Документация автоматически включает:

- ✅ Все API endpoints
- ✅ Параметры запросов
- ✅ Форматы ответов
- ✅ Примеры запросов и ответов
- ✅ Возможность тестирования API прямо в браузере
- ✅ Описания ошибок

## Перезапуск сервера

После установки пакета:

```bash
sudo systemctl restart gunicorn
```

## Проверка установки

```bash
# Проверьте, что пакет установлен
pip list | grep drf-spectacular

# Проверьте, что URL доступен
curl http://87.228.97.188/api/schema/
```

## Настройка (опционально)

Если нужно изменить настройки, отредактируйте `SPECTACULAR_SETTINGS` в `settings.py`:

```python
SPECTACULAR_SETTINGS = {
    'TITLE': 'ActiveGrad API',
    'DESCRIPTION': 'API документация для ActiveGrad Backend',
    'VERSION': '1.0.0',
    # Другие настройки...
}
```

## Troubleshooting

### Проблема: "ModuleNotFoundError: No module named 'drf_spectacular'"

**Решение:** Установите пакет:
```bash
pip install drf-spectacular
```

### Проблема: 404 на `/api/docs/`

**Решение:** 
1. Проверьте, что `drf_spectacular` в `INSTALLED_APPS`
2. Проверьте, что URL правильно настроен в `urls.py`
3. Перезапустите gunicorn

### Проблема: Endpoints не отображаются

**Решение:**
1. Убедитесь, что используете `APIView` или `ViewSet` из DRF
2. Проверьте, что `DEFAULT_SCHEMA_CLASS` настроен в `REST_FRAMEWORK`

## Дополнительная информация

- Документация drf-spectacular: https://drf-spectacular.readthedocs.io/
- OpenAPI спецификация: https://swagger.io/specification/

