#!/bin/bash

# Скрипт для настройки Telegram webhook после деплоя в Cloud Run
# Использование: ./setup_webhook.sh <SERVICE_URL> <TELEGRAM_TOKEN>

set -e

if [ $# -lt 2 ]; then
    echo "❌ Ошибка: Укажите URL сервиса Cloud Run и Telegram токен"
    echo "Использование: ./setup_webhook.sh <SERVICE_URL> <TELEGRAM_TOKEN>"
    echo "Пример: ./setup_webhook.sh https://selinaai-new-836619908242.europe-central2.run.app 8334017012:AAGiIJfbJpn5Y18F0eQNrcfwkGXKKdM0eZI"
    exit 1
fi

SERVICE_URL=$1
TELEGRAM_TOKEN=$2

echo "🔧 Настройка Telegram webhook для SelinaAI..."
echo "🌐 Сервис: $SERVICE_URL"
echo "🤖 Telegram Bot: @$(curl -s "https://api.telegram.org/bot$TELEGRAM_TOKEN/getMe" | grep -o '"username":"[^"]*"' | cut -d'"' -f4)"

# Проверяем доступность сервиса
echo "🧪 Проверка доступности сервиса..."
if curl -f "$SERVICE_URL/healthz" > /dev/null 2>&1; then
    echo "✅ Сервис доступен"
else
    echo "❌ Сервис недоступен. Проверьте URL и статус деплоя."
    exit 1
fi

# Удаляем старый webhook
echo "🗑️ Удаление старого webhook..."
curl -s -X POST "https://api.telegram.org/bot$TELEGRAM_TOKEN/deleteWebhook" > /dev/null

# Устанавливаем новый webhook
echo "🔗 Установка нового webhook..."
WEBHOOK_URL="$SERVICE_URL/webhook/telegram"
RESPONSE=$(curl -s -X POST "https://api.telegram.org/bot$TELEGRAM_TOKEN/setWebhook" \
    -H "Content-Type: application/json" \
    -d "{
        \"url\": \"$WEBHOOK_URL\",
        \"allowed_updates\": [\"message\", \"callback_query\", \"inline_query\"],
        \"drop_pending_updates\": true
    }")

if echo "$RESPONSE" | grep -q '"ok":true'; then
    echo "✅ Webhook успешно установлен"
    echo "🔗 URL: $WEBHOOK_URL"
else
    echo "❌ Ошибка установки webhook:"
    echo "$RESPONSE"
    exit 1
fi

# Проверяем статус webhook
echo "📊 Проверка статуса webhook..."
WEBHOOK_INFO=$(curl -s "https://api.telegram.org/bot$TELEGRAM_TOKEN/getWebhookInfo")
echo "$WEBHOOK_INFO" | python3 -m json.tool

echo ""
echo "🎉 Настройка webhook завершена!"
echo "📱 Теперь бот будет получать обновления через webhook"
echo "🌐 Сервис доступен по адресу: $SERVICE_URL"
echo "📚 API документация: $SERVICE_URL/docs"
echo "🤖 WebApp интерфейс: $SERVICE_URL/webapp"
