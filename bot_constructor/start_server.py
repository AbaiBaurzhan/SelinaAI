#!/usr/bin/env python3
"""
Простой скрипт запуска SelinaAI сервера
"""

import uvicorn
import os
import sys

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("🚀 Запуск SelinaAI Multi-Channel API...")
    print("📱 Поддержка: Telegram, WhatsApp, Instagram")
    print("🔐 Система авторизации: активна")
    print("🤖 Управление агентами: готово")
    print("🌐 Сервер запускается на http://127.0.0.1:8000")
    print("📚 API Docs: http://127.0.0.1:8000/docs")
    print("🌐 WebApp: http://127.0.0.1:8000/webapp")
    print("⏹️ Нажмите Ctrl+C для остановки...")
    
    uvicorn.run(
        "app:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )
