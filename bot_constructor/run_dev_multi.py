#!/usr/bin/env python3
"""
SelinaAI Multi-Channel Development Runner
Запуск всех компонентов для разработки
"""

import os
import sys
import asyncio
import subprocess
import signal
import time
from pathlib import Path

def check_env_file():
    """Проверка наличия файла конфигурации"""
    env_file = Path("touch.env")
    if not env_file.exists():
        print("❌ Файл touch.env не найден!")
        print("📝 Создайте файл touch.env на основе touch.env.example")
        return False
    
    # Проверяем обязательные переменные
    with open(env_file, 'r') as f:
        content = f.read()
        required_vars = ["TELEGRAM_TOKEN", "OPENAI_API_KEY"]
        missing_vars = [var for var in required_vars if var not in content or "your_" in content]
        
        if missing_vars:
            print(f"⚠️ В файле touch.env не заполнены: {', '.join(missing_vars)}")
            print("📝 Заполните все обязательные переменные окружения")
            return False
    
    print("✅ Файл touch.env найден и настроен")
    return True

def start_fastapi():
    """Запуск FastAPI сервера"""
    print("📡 Запуск FastAPI сервера на http://127.0.0.1:8000")
    
    # Запускаем FastAPI с поддержкой новой архитектуры
    cmd = [
        sys.executable, "-m", "uvicorn", 
        "app:app", 
        "--host", "127.0.0.1", 
        "--port", "8000", 
        "--reload"
    ]
    
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        
        # Ждем немного для запуска
        time.sleep(3)
        
        if process.poll() is None:
            print("✅ FastAPI сервер запущен")
            return process
        else:
            print("❌ Ошибка запуска FastAPI сервера")
            return None
            
    except Exception as e:
        print(f"❌ Ошибка запуска FastAPI: {e}")
        return None

def start_ngrok():
    """Запуск ngrok туннеля"""
    print("🌐 Запуск ngrok туннеля...")
    
    try:
        # Проверяем, запущен ли уже ngrok
        result = subprocess.run(["pgrep", "-f", "ngrok"], capture_output=True)
        if result.returncode == 0:
            print("✅ ngrok уже запущен")
            return None
        
        # Запускаем ngrok
        process = subprocess.Popen(
            ["ngrok", "http", "8000"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        time.sleep(3)
        
        if process.poll() is None:
            print("✅ ngrok туннель запущен")
            return process
        else:
            print("❌ Ошибка запуска ngrok")
            return None
            
    except FileNotFoundError:
        print("⚠️ ngrok не установлен. Установите: brew install ngrok")
        return None
    except Exception as e:
        print(f"❌ Ошибка запуска ngrok: {e}")
        return None

def get_ngrok_url():
    """Получение URL ngrok туннеля"""
    try:
        import requests
        response = requests.get("http://localhost:4040/api/tunnels", timeout=5)
        if response.status_code == 200:
            data = response.json()
            tunnels = data.get("tunnels", [])
            if tunnels:
                return tunnels[0]["public_url"]
    except:
        pass
    return None

def update_env_with_ngrok(ngrok_url):
    """Обновление .env файла с ngrok URL"""
    if not ngrok_url:
        return
    
    env_file = Path("touch.env")
    if env_file.exists():
        content = env_file.read_text()
        
        # Обновляем WEBAPP_URL
        if "WEBAPP_URL=" in content:
            content = content.replace(
                "WEBAPP_URL=https://127.0.0.1:8000",
                f"WEBAPP_URL={ngrok_url}"
            )
            content = content.replace(
                "WEBAPP_URL=http://127.0.0.1:8000",
                f"WEBAPP_URL={ngrok_url}"
            )
            
            # Если WEBAPP_URL не найден, добавляем
            if "WEBAPP_URL=" not in content:
                content += f"\nWEBAPP_URL={ngrok_url}\n"
        
        env_file.write_text(content)
        print(f"✅ Обновлен WEBAPP_URL: {ngrok_url}")

def main():
    """Основная функция запуска"""
    print("🚀 Запуск SelinaAI Multi-Channel для разработки...")
    print("=" * 50)
    
    # Проверяем файл конфигурации
    if not check_env_file():
        return
    
    # Запускаем ngrok
    ngrok_process = start_ngrok()
    
    # Ждем и получаем URL
    if ngrok_process:
        time.sleep(5)
        ngrok_url = get_ngrok_url()
        if ngrok_url:
            print(f"🌐 Ngrok URL: {ngrok_url}")
            update_env_with_ngrok(ngrok_url)
        else:
            print("⚠️ Не удалось получить ngrok URL")
    
    # Запускаем FastAPI
    fastapi_process = start_fastapi()
    if not fastapi_process:
        print("❌ Не удалось запустить FastAPI сервер")
        if ngrok_process:
            ngrok_process.terminate()
        return
    
    print("\n✅ Все сервисы запущены!")
    print("🌐 WebApp: http://127.0.0.1:8000")
    if ngrok_url:
        print(f"🌐 HTTPS: {ngrok_url}")
    print("📱 Каналы: проверьте /channels/status")
    print("\nНажмите Ctrl+C для остановки...")
    
    try:
        # Ждем завершения
        fastapi_process.wait()
    except KeyboardInterrupt:
        print("\n🛑 Остановка сервисов...")
        
        # Останавливаем процессы
        if fastapi_process:
            fastapi_process.terminate()
            fastapi_process.wait()
        
        if ngrok_process:
            ngrok_process.terminate()
            ngrok_process.wait()
        
        print("✅ Все сервисы остановлены")

if __name__ == "__main__":
    main()
