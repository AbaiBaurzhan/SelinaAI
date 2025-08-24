# Используем официальный Python образ
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Копируем файл зависимостей
COPY requirements.txt .

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY bot_constructor/ ./bot_constructor/

# Создаем директорию для загрузок
RUN mkdir -p bot_constructor/uploads

# Устанавливаем переменные окружения
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Открываем порт (Cloud Run использует переменную PORT)
EXPOSE 8080

# Запускаем приложение
CMD ["python", "-m", "uvicorn", "bot_constructor.app:app", "--host", "0.0.0.0", "--port", "8080"]
