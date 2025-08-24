#!/usr/bin/env python3
"""
SelinaAI Webhook Runner
Запуск системы в webhook режиме для продакшена
"""

import os
import sys
import time
import subprocess
import signal
from pathlib import Path
from dotenv import load_dotenv

def check_env_file():
    """Проверка файла окружения"""
    env_file = Path("touch.env")
    if not env_file.exists():
        print("❌ Файл touch.env не найден!")
        return False
    
    # Загружаем переменные
    load_dotenv("touch.env")
    
    # Проверяем обязательные переменные
    required_vars = [
        "TELEGRAM_TOKEN",
        "OPENAI_API_KEY",
        "WEBAPP_URL"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var) or os.getenv(var).startswith("your_"):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"⚠️ В файле touch.env не заполнены: {', '.join(missing_vars)}")
        return False
    
    # Проверяем webhook режим
    webhook_mode = os.getenv("TELEGRAM_WEBHOOK_MODE", "false").lower() == "true"
    if not webhook_mode:
        print("⚠️ TELEGRAM_WEBHOOK_MODE должен быть true для webhook режима")
        return False
    
    print("✅ Файл окружения проверен")
    print(f"🔧 Webhook режим: {'ВКЛЮЧЕН' if webhook_mode else 'ВЫКЛЮЧЕН'}")
    return True

def start_ngrok():
    """Запуск ngrok для HTTPS"""
    print("🌐 Запуск ngrok...")
    
    try:
        # Проверяем, не запущен ли уже ngrok
        result = subprocess.run(["pgrep", "ngrok"], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ ngrok уже запущен")
            return True
    except:
        pass
    
    try:
        subprocess.Popen(
            ["ngrok", "http", "8000"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        time.sleep(3)
        print("✅ ngrok запущен")
        return True
    except Exception as e:
        print(f"❌ Ошибка запуска ngrok: {e}")
        return False

def get_ngrok_url():
    """Получение публичного URL ngrok"""
    try:
        import requests
        response = requests.get("http://127.0.0.1:4040/api/tunnels")
        data = response.json()
        
        for tunnel in data.get("tunnels", []):
            if tunnel["proto"] == "https":
                return tunnel["public_url"]
        
        return None
    except:
        return None

def update_env_with_ngrok(ngrok_url):
    """Обновление touch.env с ngrok URL"""
    if not ngrok_url:
        return False
    
    try:
        env_file = Path("touch.env")
        content = env_file.read_text()
        
        # Обновляем WEBAPP_URL
        if "WEBAPP_URL=" in content:
            content = content.replace(
                "WEBAPP_URL=https://127.0.0.1:8000",
                f"WEBAPP_URL={ngrok_url}"
            )
        else:
            content += f"\nWEBAPP_URL={ngrok_url}\n"
        
        env_file.write_text(content)
        print(f"✅ Обновлен WEBAPP_URL: {ngrok_url}")
        return True
    except Exception as e:
        print(f"❌ Ошибка обновления touch.env: {e}")
        return False

def setup_webhook():
    """Настройка webhook для Telegram бота"""
    print("🔧 Настройка webhook...")
    
    try:
        result = subprocess.run([sys.executable, "setup_webhook.py"], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Webhook настроен успешно")
            return True
        else:
            print(f"❌ Ошибка настройки webhook: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Ошибка запуска setup_webhook.py: {e}")
        return False

def start_fastapi():
    """Запуск FastAPI сервера"""
    print("🚀 Запуск SelinaAI Webhook API...")
    
    try:
        process = subprocess.Popen([
            sys.executable, "-m", "uvicorn", "app:app",
            "--host", "0.0.0.0", "--port", "8000"  # 0.0.0.0 для webhook
        ])
        
        print("✅ FastAPI сервер запущен на 0.0.0.0:8000")
        return process
    except Exception as e:
        print(f"❌ Ошибка запуска FastAPI: {e}")
        return None

def main():
    """Основная функция"""
    print("🚀 Запуск SelinaAI в Webhook режиме")
    print("=" * 50)
    
    # Проверяем файл окружения
    if not check_env_file():
        return
    
    # Запускаем ngrok
    if not start_ngrok():
        print("❌ Не удалось запустить ngrok")
        return
    
    # Получаем ngrok URL
    ngrok_url = get_ngrok_url()
    if ngrok_url:
        update_env_with_ngrok(ngrok_url)
        print(f"🌐 Публичный URL: {ngrok_url}")
    else:
        print("❌ Не удалось получить ngrok URL")
        return
    
    # Настраиваем webhook
    if not setup_webhook():
        print("❌ Не удалось настроить webhook")
        return
    
    # Запускаем FastAPI
    fastapi_process = start_fastapi()
    if not fastapi_process:
        return
    
    print("\n🎯 Система запущена в webhook режиме!")
    print(f"📱 Локальный сервер: http://127.0.0.1:8000")
    print(f"🌐 Публичный URL: {ngrok_url}")
    print(f"📚 API Docs: {ngrok_url}/docs")
    print(f"🌐 WebApp: {ngrok_url}/webapp")
    print(f"🔗 Webhook endpoint: {ngrok_url}/webhook/telegram")
    
    print("\n🔐 Система авторизации:")
    print("   • Telegram WebApp авторизация")
    print("   • Email/Password авторизация")
    print("   • JWT токены и сессии")
    
    print("\n🤖 Управление агентами:")
    print("   • Создание/редактирование/удаление")
    print("   • Загрузка документов")
    print("   • Настройка интеграций")
    
    print("\n📱 Webhook режим:")
    print("   • Telegram: webhook активен")
    print("   • WhatsApp: готов к настройке")
    print("   • Instagram: готов к настройке")
    
    print("\n⏹️ Нажмите Ctrl+C для остановки...")
    
    try:
        # Ждем завершения процесса
        fastapi_process.wait()
    except KeyboardInterrupt:
        print("\n🛑 Остановка сервера...")
        
        # Останавливаем FastAPI
        if fastapi_process:
            fastapi_process.terminate()
            fastapi_process.wait()
        
        # Останавливаем ngrok
        try:
            subprocess.run(["pkill", "ngrok"], check=False)
            print("✅ ngrok остановлен")
        except:
            pass
        
        print("🛑 SelinaAI остановлен")

if __name__ == "__main__":
    main()
