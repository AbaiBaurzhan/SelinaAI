#!/usr/bin/env python3
"""
SelinaAI Multi-Channel API Runner with Authentication
Запуск обновленной системы с авторизацией
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
        print("📝 Создайте файл touch.env с необходимыми переменными")
        return False
    
    # Загружаем переменные
    load_dotenv("touch.env")
    
    # Проверяем обязательные переменные
    required_vars = [
        "TELEGRAM_TOKEN",
        "OPENAI_API_KEY"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var) or os.getenv(var).startswith("your_"):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"⚠️ В файле touch.env не заполнены: {', '.join(missing_vars)}")
        print("📝 Заполните все обязательные переменные окружения")
        return False
    
    print("✅ Файл окружения проверен")
    return True

def start_ngrok():
    """Запуск ngrok для HTTPS"""
    print("🌐 Запуск ngrok...")
    
    # Проверяем, не запущен ли уже ngrok
    try:
        result = subprocess.run(["pgrep", "ngrok"], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ ngrok уже запущен")
            return True
    except:
        pass
    
    # Запускаем ngrok
    try:
        subprocess.Popen(
            ["ngrok", "http", "8000"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        time.sleep(3)  # Ждем запуска
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

def start_fastapi():
    """Запуск FastAPI сервера"""
    print("🚀 Запуск SelinaAI Multi-Channel API...")
    
    try:
        # Запускаем uvicorn
        process = subprocess.Popen([
            sys.executable, "-m", "uvicorn", "app:app",
            "--host", "127.0.0.1", "--port", "8000", "--reload"
        ])
        
        print("✅ FastAPI сервер запущен на http://127.0.0.1:8000")
        return process
    except Exception as e:
        print(f"❌ Ошибка запуска FastAPI: {e}")
        return None

def main():
    """Основная функция"""
    print("🚀 Запуск SelinaAI Multi-Channel API с авторизацией")
    print("=" * 60)
    
    # Проверяем файл окружения
    if not check_env_file():
        return
    
    # Запускаем ngrok
    if not start_ngrok():
        print("⚠️ ngrok не запущен, но продолжаем...")
    
    # Получаем ngrok URL
    ngrok_url = get_ngrok_url()
    if ngrok_url:
        update_env_with_ngrok(ngrok_url)
        print(f"🌐 Публичный URL: {ngrok_url}")
    else:
        print("⚠️ ngrok URL не получен")
    
    # Запускаем FastAPI
    fastapi_process = start_fastapi()
    if not fastapi_process:
        return
    
    print("\n🎯 Доступные URL:")
    print(f"   📱 Локальный: http://127.0.0.1:8000")
    if ngrok_url:
        print(f"   🌐 Публичный: {ngrok_url}")
    print(f"   📚 API Docs: http://127.0.0.1:8000/docs")
    print(f"   🌐 WebApp: http://127.0.0.1:8000/webapp")
    
    print("\n🔐 Система авторизации:")
    print("   • Telegram WebApp авторизация")
    print("   • Email/Password авторизация")
    print("   • JWT токены и сессии")
    
    print("\n🤖 Управление агентами:")
    print("   • Создание/редактирование/удаление")
    print("   • Загрузка документов")
    print("   • Настройка интеграций")
    
    print("\n📱 Поддерживаемые каналы:")
    print("   • Telegram (polling/webhook)")
    print("   • WhatsApp Business API")
    print("   • Instagram Direct Messages")
    
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
