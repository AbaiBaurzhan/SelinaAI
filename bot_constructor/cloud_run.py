#!/usr/bin/env python3
"""
Cloud Run Entry Point for SelinaAI
Автоматически определяет режим работы: локальный (polling) или облачный (webhook)
"""

import os
import asyncio
import uvicorn
import sys
from pathlib import Path
from dotenv import load_dotenv

# Добавляем корневую папку в PYTHONPATH
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

# Загружаем переменные окружения
load_dotenv("bot_constructor/touch.env") or load_dotenv("touch.env")

def is_cloud_environment():
    """Определяем, запущены ли мы в облаке"""
    return (
        os.getenv("K_SERVICE") is not None or  # Google Cloud Run
        os.getenv("PORT") is not None or        # Cloud Run порт
        os.getenv("CLOUD_RUN") == "true"       # Принудительный флаг
    )

def get_server_config():
    """Получаем конфигурацию сервера в зависимости от окружения"""
    if is_cloud_environment():
        print("☁️ Запуск в облачном режиме (webhook)")
        return {
            "host": "0.0.0.0",
            "port": int(os.getenv("PORT", 8080)),
            "webhook_mode": True
        }
    else:
        print("🏠 Запуск в локальном режиме (polling)")
        return {
            "host": "127.0.0.1",
            "port": 8000,
            "webhook_mode": False
        }

async def setup_environment():
    """Настройка окружения в зависимости от режима"""
    config = get_server_config()
    
    if config["webhook_mode"]:
        # В облаке используем webhook режим
        os.environ["TELEGRAM_WEBHOOK_MODE"] = "true"
        print("🔧 Webhook режим активирован")
        
        # Проверяем обязательные переменные для webhook
        required_vars = [
            "TELEGRAM_TOKEN",
            "OPENAI_API_KEY",
            "WEBAPP_URL"
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            print(f"⚠️ Отсутствуют переменные окружения: {', '.join(missing_vars)}")
            print("💡 Установите их в Google Cloud Run")
            return False
        
        print("✅ Все переменные окружения настроены")
        return True
    else:
        # Локально используем polling режим
        os.environ["TELEGRAM_WEBHOOK_MODE"] = "false"
        print("🔧 Polling режим активирован")
        return True

def main():
    """Главная функция запуска"""
    print("🚀 SelinaAI Multi-Channel API")
    print("=" * 40)
    
    # Настраиваем окружение
    if not asyncio.run(setup_environment()):
        print("❌ Не удалось настроить окружение")
        return
    
    # Получаем конфигурацию сервера
    config = get_server_config()
    
    print(f"🌐 Сервер запускается на {config['host']}:{config['port']}")
    print(f"🔧 Режим: {'Webhook' if config['webhook_mode'] else 'Polling'}")
    
    if config["webhook_mode"]:
        print("📱 Webhook endpoints:")
        print(f"   • Telegram: {os.getenv('WEBAPP_URL', 'N/A')}/webhook/telegram")
        print(f"   • WhatsApp: {os.getenv('WEBAPP_URL', 'N/A')}/webhook/whatsapp")
        print(f"   • Instagram: {os.getenv('WEBAPP_URL', 'N/A')}/webhook/instagram")
    else:
        print("📱 Локальные endpoints:")
        print(f"   • API: http://127.0.0.1:8000")
        print(f"   • Docs: http://127.0.0.1:8000/docs")
        print(f"   • WebApp: http://127.0.0.1:8000/webapp")
    
    # Запускаем сервер
    uvicorn.run(
        "bot_constructor.app:app",
        host=config["host"],
        port=config["port"],
        log_level="info"
    )

if __name__ == "__main__":
    main()
