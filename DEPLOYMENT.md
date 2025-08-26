# 🚀 Деплой SelinaAI в Google Cloud Run

## 📋 **Предварительные требования**

1. **Google Cloud Project** с включенными API:
   - Cloud Run API
   - Container Registry API
   - Cloud Build API

2. **Service Account** с правами:
   - Cloud Run Admin
   - Storage Admin
   - Service Account User

3. **GitHub Secrets** настроены:
   - `GCP_SA_KEY` - JSON ключ service account

## 🔧 **Подготовка к деплою**

### 1. **Проверка конфигурации**
```bash
# Убедитесь, что все файлы готовы
ls -la Dockerfile.cloud
ls -la .github/workflows/main.yml
ls -la bot_constructor/touch.env.production
```

### 2. **Локальное тестирование**
```bash
# Тестируем контейнер локально
./test_container.sh

# Тестируем приложение
cd bot_constructor
python cloud_run.py
```

## 🚀 **Автоматический деплой через GitHub Actions**

### 1. **Запуск деплоя**
```bash
# Просто запушите изменения в main ветку
git add .
git commit -m "Prepare for Cloud Run deployment"
git push origin main
```

### 2. **Мониторинг деплоя**
- Перейдите в GitHub → Actions
- Следите за выполнением job "deploy"
- Дождитесь успешного завершения

### 3. **Получение URL сервиса**
После успешного деплоя в логах будет:
```
🌐 Сервис доступен по адресу: https://selinaai-new-836619908242.europe-central2.run.app
📱 Telegram Webhook: https://selinaai-new-836619908242.europe-central2.run.app/webhook/telegram
📊 Health Check: https://selinaai-new-836619908242.europe-central2.run.app/healthz
```

## 🔗 **Настройка Telegram Webhook**

### 1. **Автоматическая настройка**
```bash
# Используйте скрипт для настройки webhook
./setup_webhook.sh https://selinaai-new-836619908242.europe-central2.run.app
```

### 2. **Ручная настройка**
```bash
# Установка webhook
curl -X POST "https://api.telegram.org/bot8334017012:AAGiIJfbJpn5Y18F0eQNrcfwkGXKKdM0eZI/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://selinaai-new-836619908242.europe-central2.run.app/webhook/telegram",
    "allowed_updates": ["message", "callback_query", "inline_query"]
  }'

# Проверка статуса
curl "https://api.telegram.org/bot8334017012:AAGiIJfbJpn5Y18F0eQNrcfwkGXKKdM0eZI/getWebhookInfo"
```

## 🧪 **Тестирование после деплоя**

### 1. **Health Check**
```bash
curl https://selinaai-new-836619908242.europe-central2.run.app/healthz
```

### 2. **API Endpoints**
```bash
# Главная страница
curl https://selinaai-new-836619908242.europe-central2.run.app/

# API документация
open https://selinaai-new-836619908242.europe-central2.run.app/docs

# WebApp интерфейс
open https://selinaai-new-836619908242.europe-central2.run.app/webapp
```

### 3. **Telegram Bot**
- Напишите `/start` в Telegram боту
- Проверьте, что бот отвечает

## 🔍 **Устранение неполадок**

### 1. **Сервис не запускается**
```bash
# Проверьте логи в Google Cloud Console
gcloud run services logs read selinaai-new --region europe-central2

# Проверьте переменные окружения
gcloud run services describe selinaai-new --region europe-central2
```

### 2. **Webhook не работает**
```bash
# Проверьте статус webhook
curl "https://api.telegram.org/bot8334017012:AAGiIJfbJpn5Y18F0eQNrcfwkGXKKdM0eZI/getWebhookInfo"

# Переустановите webhook
./setup_webhook.sh https://selinaai-new-836619908242.europe-central2.run.app
```

### 3. **Ошибки в GitHub Actions**
- Проверьте логи в GitHub Actions
- Убедитесь, что `GCP_SA_KEY` настроен правильно
- Проверьте права service account

## 📊 **Мониторинг и логи**

### 1. **Google Cloud Console**
- Cloud Run → selinaai-new → Logs
- Cloud Run → selinaai-new → Metrics

### 2. **GitHub Actions**
- Actions → Deploy to Cloud Run → deploy

### 3. **Локальные логи**
```bash
# Если запускаете локально
tail -f bot_constructor/server.log
```

## 🔄 **Обновление сервиса**

### 1. **Автоматическое обновление**
- Просто запушите изменения в main ветку
- GitHub Actions автоматически развернет новую версию

### 2. **Ручное обновление**
```bash
# Сборка и загрузка образа
docker build -f Dockerfile.cloud -t gcr.io/836619908242/selinaai:latest .
docker push gcr.io/836619908242/selinaai:latest

# Развертывание
gcloud run deploy selinaai-new \
  --image gcr.io/836619908242/selinaai:latest \
  --region europe-central2
```

## 🎯 **Готово!**

После успешного деплоя у вас будет:
- ✅ Работающий API в Google Cloud Run
- ✅ Telegram бот с webhook
- ✅ Автоматические обновления через GitHub
- ✅ Масштабируемость и высокая доступность

**SelinaAI готов к продакшену!** 🚀
