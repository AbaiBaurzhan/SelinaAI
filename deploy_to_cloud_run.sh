#!/bin/bash

# Скрипт развертывания SelinaAI в Google Cloud Run
# Использование: ./deploy_to_cloud_run.sh [PROJECT_ID] [REGION] [SERVICE_NAME]

set -e

# Параметры по умолчанию
PROJECT_ID=${1:-"your-project-id"}
REGION=${2:-"us-central1"}
SERVICE_NAME=${3:-"botcraft"}

echo "🚀 Развертывание SelinaAI в Google Cloud Run"
echo "=============================================="
echo "Project ID: $PROJECT_ID"
echo "Region: $REGION"
echo "Service Name: $SERVICE_NAME"
echo ""

# Проверяем, что gcloud установлен
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI не установлен"
    echo "💡 Установите: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Проверяем аутентификацию
echo "🔐 Проверка аутентификации..."
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "❌ Не аутентифицированы в gcloud"
    echo "💡 Выполните: gcloud auth login"
    exit 1
fi

# Устанавливаем проект
echo "📋 Установка проекта..."
gcloud config set project $PROJECT_ID

# Настраиваем Docker для работы с Google Container Registry
echo "🐳 Настройка Docker..."
gcloud auth configure-docker

# Собираем Docker образ
echo "🔨 Сборка Docker образа..."
docker build -t gcr.io/$PROJECT_ID/$SERVICE_NAME .

# Загружаем образ в Google Container Registry
echo "📤 Загрузка образа в GCR..."
docker push gcr.io/$PROJECT_ID/$SERVICE_NAME

# Развертываем сервис в Cloud Run
echo "🚀 Развертывание сервиса..."
gcloud run deploy $SERVICE_NAME \
    --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --port 8080 \
    --memory 1Gi \
    --cpu 1 \
    --max-instances 10 \
    --timeout 300 \
    --concurrency 80

# Получаем URL сервиса
echo "🔗 Получение URL сервиса..."
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format="value(status.url)")

echo ""
echo "✅ Развертывание завершено!"
echo "🌐 URL сервиса: $SERVICE_URL"
echo "📚 API Docs: $SERVICE_URL/docs"
echo "🌐 WebApp: $SERVICE_URL/webapp"
echo "🔗 Health check: $SERVICE_URL/healthz"
echo ""

echo "🔧 Следующие шаги:"
echo "1. Установите переменные окружения в Cloud Run:"
echo "   gcloud run services update $SERVICE_NAME --region $REGION --set-env-vars TELEGRAM_TOKEN=your_token,OPENAI_API_KEY=your_key,WEBAPP_URL=$SERVICE_URL"
echo ""
echo "2. Настройте webhook для Telegram бота:"
echo "   curl -X POST \"https://api.telegram.org/botYOUR_BOT_TOKEN/setWebhook\" \\"
echo "     -H \"Content-Type: application/json\" \\"
echo "     -d '{\"url\": \"$SERVICE_URL/webhook/telegram\"}'"
echo ""
echo "3. Проверьте статус webhook:"
echo "   curl \"https://api.telegram.org/botYOUR_BOT_TOKEN/getWebhookInfo\""
echo ""
echo "🎉 SelinaAI готов к использованию в облаке!"
