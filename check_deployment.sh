#!/bin/bash

# Скрипт для проверки статуса деплоя SelinaAI в Cloud Run
# Использование: ./check_deployment.sh

set -e

echo "🔍 Проверка статуса деплоя SelinaAI..."

# Проверяем, что gcloud настроен
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI не установлен. Установите Google Cloud SDK"
    exit 1
fi

# Проверяем аутентификацию
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "❌ Не аутентифицирован в Google Cloud. Выполните: gcloud auth login"
    exit 1
fi

PROJECT_ID="836619908242"
REGION="europe-central2"
SERVICE_NAME="selinaai-new"

echo "📊 Информация о проекте:"
echo "   • Project ID: $PROJECT_ID"
echo "   • Region: $REGION"
echo "   • Service: $SERVICE_NAME"

# Проверяем статус сервиса
echo ""
echo "🚀 Проверка статуса Cloud Run сервиса..."
if gcloud run services describe $SERVICE_NAME --region $REGION --format="value(status.conditions[0].status)" 2>/dev/null | grep -q "True"; then
    echo "✅ Сервис $SERVICE_NAME активен"
    
    # Получаем URL сервиса
    SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format="value(status.url)")
    echo "🌐 URL сервиса: $SERVICE_URL"
    
    # Проверяем health endpoint
    echo ""
    echo "🧪 Тестирование health endpoint..."
    if curl -f "$SERVICE_URL/healthz" > /dev/null 2>&1; then
        echo "✅ Health check прошел успешно"
        
        # Проверяем основные endpoints
        echo ""
        echo "🔍 Проверка основных endpoints:"
        
        # Главная страница
        if curl -f "$SERVICE_URL/" > /dev/null 2>&1; then
            echo "✅ Главная страница доступна"
        else
            echo "❌ Главная страница недоступна"
        fi
        
        # API документация
        if curl -f "$SERVICE_URL/docs" > /dev/null 2>&1; then
            echo "✅ API документация доступна"
        else
            echo "❌ API документация недоступна"
        fi
        
        # WebApp интерфейс
        if curl -f "$SERVICE_URL/webapp/" > /dev/null 2>&1; then
            echo "✅ WebApp интерфейс доступен"
        else
            echo "❌ WebApp интерфейс недоступен"
        fi
        
        echo ""
        echo "🎉 Сервис готов к работе!"
        echo ""
        echo "📱 Следующие шаги:"
        echo "1. Настройте Telegram webhook:"
        echo "   ./setup_webhook.sh $SERVICE_URL 8334017012:AAGiIJfbJpn5Y18F0eQNrcfwkGXKKdM0eZI"
        echo ""
        echo "2. Откройте веб-интерфейс:"
        echo "   open $SERVICE_URL/webapp/"
        echo ""
        echo "3. Проверьте API документацию:"
        echo "   open $SERVICE_URL/docs"
        
    else
        echo "❌ Health check не прошел. Сервис еще запускается..."
        echo "💡 Подождите несколько минут и попробуйте снова"
    fi
    
else
    echo "❌ Сервис $SERVICE_NAME не найден или не активен"
    echo "💡 Проверьте логи GitHub Actions для диагностики"
fi

echo ""
echo "🔍 Для просмотра логов сервиса выполните:"
echo "   gcloud run services logs read $SERVICE_NAME --region $REGION"
