# 🚀 BotCraft - AI Assistant Platform

**BotCraft** - это платформа для создания ИИ-ассистентов с поддержкой множественных каналов связи (Telegram, WhatsApp, Instagram).

## ✨ Возможности

- 🔐 **Система авторизации** (Telegram WebApp + Email/Password)
- 🤖 **Управление ИИ-агентами** с базой данных
- 📱 **Мультиканальность** (Telegram, WhatsApp, Instagram)
- 🔧 **Два режима работы**: локальный (polling) и облачный (webhook)
- 🏗️ **Модульная архитектура** с channels
- 🌐 **Современный WebApp** интерфейс
- ☁️ **Готовность к развертыванию** в Google Cloud Run

## 🏗️ Архитектура

```
BotCraft/
├── bot_constructor/          # Основной код приложения
│   ├── app.py               # FastAPI сервер
│   ├── auth.py              # Система авторизации
│   ├── agents.py            # Управление агентами
│   ├── database.py          # База данных
│   ├── channels/            # Интеграции с каналами
│   │   ├── base.py         # Базовый класс канала
│   │   ├── telegram.py     # Telegram интеграция
│   │   ├── whatsapp.py     # WhatsApp интеграция
│   │   └── instagram.py    # Instagram интеграция
│   └── webapp/             # Веб-интерфейс
├── Dockerfile               # Docker образ для Cloud Run
├── requirements.txt         # Python зависимости
├── cloud_run.py            # Точка входа для Cloud Run
└── README.md               # Документация
```

## 🚀 Быстрый старт

### Локальная разработка

1. **Клонируйте репозиторий:**
```bash
git clone https://github.com/AbaiBaurzhan/BotCraft.git
cd BotCraft
```

2. **Создайте виртуальное окружение:**
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# или
.venv\Scripts\activate     # Windows
```

3. **Установите зависимости:**
```bash
pip install -r requirements.txt
```

4. **Настройте переменные окружения:**
```bash
cd bot_constructor
cp touch.env.example touch.env
# Отредактируйте touch.env с вашими токенами
```

5. **Запустите в локальном режиме:**
```bash
python cloud_run.py
```

### Google Cloud Run развертывание

1. **Соберите Docker образ:**
```bash
docker build -t botcraft .
```

2. **Протестируйте локально:**
```bash
docker run -p 8080:8080 -e CLOUD_RUN=true botcraft
```

3. **Разверните в Google Cloud Run:**
```bash
# Установите gcloud CLI
gcloud auth configure-docker

# Соберите и загрузите образ
docker build -t gcr.io/YOUR_PROJECT_ID/botcraft .
docker push gcr.io/YOUR_PROJECT_ID/botcraft

# Разверните сервис
gcloud run deploy botcraft \
  --image gcr.io/YOUR_PROJECT_ID/botcraft \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8080
```

## 🔧 Переменные окружения

### Обязательные переменные

```env
# Telegram Bot Configuration
TELEGRAM_TOKEN=your_telegram_bot_token_here
TELEGRAM_WEBHOOK_MODE=false  # true для Cloud Run, false для локальной разработки

# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here

# WebApp URL (для Cloud Run)
WEBAPP_URL=https://your-cloud-run-url.run.app
```

### Опциональные переменные

```env
# WhatsApp Business API Configuration
WHATSAPP_ACCESS_TOKEN=your_whatsapp_access_token_here
WHATSAPP_PHONE_NUMBER_ID=your_whatsapp_phone_number_id_here
WHATSAPP_VERIFY_TOKEN=your_whatsapp_verify_token_here
WHATSAPP_APP_SECRET=your_whatsapp_app_secret_here

# Instagram Business API Configuration
INSTAGRAM_ACCESS_TOKEN=your_instagram_access_token_here
INSTAGRAM_BUSINESS_ACCOUNT_ID=your_instagram_business_account_id_here
INSTAGRAM_PAGE_ID=your_instagram_page_id_here
INSTAGRAM_VERIFY_TOKEN=your_instagram_verify_token_here

# JWT Secret (измените в продакшн)
JWT_SECRET_KEY=your-secret-key-change-in-production

# Дополнительные настройки
LOG_LEVEL=INFO
ENVIRONMENT=production  # или development
```

## 📱 Режимы работы

### 🏠 Локальный режим (Polling)
- **Использование**: Разработка и тестирование
- **Запуск**: `python cloud_run.py`
- **Порт**: 8000
- **Telegram**: Polling режим
- **Преимущества**: Простая настройка, не требует публичного URL

### ☁️ Облачный режим (Webhook)
- **Использование**: Продакшен в Google Cloud Run
- **Запуск**: Автоматически при развертывании
- **Порт**: 8080 (или переменная PORT)
- **Telegram**: Webhook режим
- **Преимущества**: Масштабируемость, высокая доступность

## 🌐 API Endpoints

### Основные endpoints
- `GET /health` - Статус сервиса
- `GET /healthz` - Health check для Cloud Run
- `GET /` - Главная страница
- `GET /docs` - Swagger документация

### Авторизация
- `POST /api/auth/telegram` - Вход через Telegram
- `POST /api/auth/email` - Вход по email/password
- `POST /api/auth/logout` - Выход

### Управление агентами
- `GET /api/agents` - Список агентов
- `POST /api/agents` - Создание агента
- `GET /api/agents/{id}` - Получение агента
- `PUT /api/agents/{id}` - Обновление агента
- `DELETE /api/agents/{id}` - Удаление агента

### Webhook endpoints
- `GET/POST /webhook/telegram` - Telegram webhook
- `GET/POST /webhook/whatsapp` - WhatsApp webhook
- `GET/POST /webhook/instagram` - Instagram webhook

## 🔐 Настройка Telegram Webhook

После развертывания в Cloud Run:

1. **Получите URL вашего сервиса:**
```bash
gcloud run services describe botcraft --region us-central1 --format="value(status.url)"
```

2. **Настройте webhook:**
```bash
curl -X POST "https://api.telegram.org/botYOUR_BOT_TOKEN/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-service-url.run.app/webhook/telegram",
    "allowed_updates": ["message", "callback_query", "inline_query"]
  }'
```

3. **Проверьте статус:**
```bash
curl "https://api.telegram.org/botYOUR_BOT_TOKEN/getWebhookInfo"
```

## 🧪 Тестирование

### Локальное тестирование
```bash
# Проверка health endpoint
curl http://127.0.0.1:8000/health

# Проверка API документации
open http://127.0.0.1:8000/docs
```

### Cloud Run тестирование
```bash
# Проверка health endpoint
curl https://your-service-url.run.app/healthz

# Проверка API документации
open https://your-service-url.run.app/docs
```

## 📊 Мониторинг

### Google Cloud Run
- **Логи**: Cloud Logging
- **Метрики**: Cloud Monitoring
- **Трассировка**: Cloud Trace

### Локальная разработка
- **Логи**: Консоль терминала
- **Метрики**: FastAPI встроенные метрики

## 🚨 Безопасность

### Рекомендации для продакшена
1. **Измените** `JWT_SECRET_KEY`
2. **Используйте** HTTPS (автоматически в Cloud Run)
3. **Настройте** CORS правильно
4. **Добавьте** rate limiting
5. **Настройте** логирование
6. **Используйте** переменные окружения
7. **Регулярно** обновляйте зависимости

## 🔧 Разработка

### Добавление нового канала
1. Создайте класс в `bot_constructor/channels/`
2. Наследуйтесь от `BaseChannel`
3. Реализуйте все абстрактные методы
4. Добавьте в `ChannelManager`

### Добавление новых полей агента
1. Обновите схему в `database.py`
2. Добавьте поля в `AIAgent` dataclass
3. Обновите API эндпоинты
4. Обновите веб-интерфейс

## 📚 Дополнительные ресурсы

- [FastAPI документация](https://fastapi.tiangolo.com/)
- [Google Cloud Run документация](https://cloud.google.com/run/docs)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [WhatsApp Business API](https://developers.facebook.com/docs/whatsapp)
- [Instagram Graph API](https://developers.facebook.com/docs/instagram-api)

## 🤝 Поддержка

При возникновении проблем:
1. Проверьте логи сервера
2. Убедитесь в правильности токенов
3. Проверьте настройки webhook
4. Убедитесь в доступности Cloud Run сервиса

## 📄 Лицензия

MIT License

---

**BotCraft v2.0** - Платформа для создания ИИ-ассистентов с поддержкой Google Cloud Run.
