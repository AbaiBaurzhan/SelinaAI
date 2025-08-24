#!/usr/bin/env python3
"""
Development runner for BotCraft
Запускает FastAPI сервер и Telegram бота
"""
import subprocess
import sys
import time
from pathlib import Path

def main():
    print("🚀 Запуск BotCraft для разработки...")
    
    # Проверяем наличие .env файла
    env_file = Path("touch.env")
    if not env_file.exists():
        print("❌ Файл touch.env не найден!")
        print("Создайте touch.env с вашими ключами:")
        print("TELEGRAM_TOKEN=your_bot_token")
        print("OPENAI_API_KEY=your_openai_key")
        return 1
    
    # Запускаем FastAPI сервер
    print("📡 Запуск FastAPI сервера на http://127.0.0.1:8000")
    api_process = subprocess.Popen([
        sys.executable, "-m", "uvicorn", "app:app", 
        "--host", "127.0.0.1", "--port", "8000", "--reload"
    ])
    
    # Ждем запуска сервера
    time.sleep(3)
    
    # Запускаем Telegram бота
    print("🤖 Запуск Telegram бота...")
    bot_process = subprocess.Popen([sys.executable, "main.py"])
    
    try:
        print("✅ Оба сервиса запущены!")
        print("🌐 WebApp: http://127.0.0.1:8000")
        print("📱 Бот: проверьте /start в Telegram")
        print("\nНажмите Ctrl+C для остановки...")
        
        # Ждем завершения
        api_process.wait()
        bot_process.wait()
        
    except KeyboardInterrupt:
        print("\n🛑 Остановка сервисов...")
        api_process.terminate()
        bot_process.terminate()
        api_process.wait()
        bot_process.wait()
        print("✅ Все сервисы остановлены")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
