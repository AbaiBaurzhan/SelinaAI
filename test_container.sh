#!/bin/bash

echo "🧪 Тестирование контейнера SelinaAI локально..."

# Собираем образ
echo "🔨 Сборка Docker образа..."
docker build -t selinaai-test .

# Проверяем, что образ создался
if [ $? -ne 0 ]; then
    echo "❌ Ошибка сборки Docker образа"
    exit 1
fi

echo "✅ Образ собран успешно"

# Запускаем контейнер
echo "🚀 Запуск контейнера..."
docker run -d --name selinaai-test-container \
    -p 8080:8080 \
    -e TELEGRAM_TOKEN=test \
    -e OPENAI_API_KEY=test \
    -e WEBAPP_URL=http://localhost:8080 \
    selinaai-test

# Ждем запуска
echo "⏳ Ожидание запуска контейнера..."
sleep 10

# Проверяем health check
echo "🏥 Проверка health check..."
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/healthz)

if [ "$response" = "200" ]; then
    echo "✅ Health check прошел успешно"
else
    echo "❌ Health check не прошел. HTTP код: $response"
fi

# Проверяем логи
echo "📋 Логи контейнера:"
docker logs selinaai-test-container

# Останавливаем и удаляем контейнер
echo "🛑 Остановка тестового контейнера..."
docker stop selinaai-test-container
docker rm selinaai-test-container

echo "🧹 Тестовый контейнер удален"

if [ "$response" = "200" ]; then
    echo "🎉 Тест прошел успешно! Контейнер готов к деплою"
    exit 0
else
    echo "💥 Тест не прошел. Проверьте логи выше"
    exit 1
fi
