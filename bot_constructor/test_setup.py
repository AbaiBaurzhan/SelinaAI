#!/usr/bin/env python3
"""
Тест настройки BotCraft
Проверяет импорты и базовую функциональность
"""
import sys
from pathlib import Path

def test_imports():
    """Тестирует импорт всех модулей"""
    print("🧪 Тестирую импорты...")
    
    try:
        import fastapi
        print("✅ FastAPI импортирован")
    except ImportError as e:
        print(f"❌ FastAPI: {e}")
        return False
    
    try:
        import telegram
        print("✅ python-telegram-bot импортирован")
    except ImportError as e:
        print(f"❌ python-telegram-bot: {e}")
        return False
    
    try:
        import openai
        print("✅ OpenAI импортирован")
    except ImportError as e:
        print(f"❌ OpenAI: {e}")
        return False
    
    try:
        import fitz
        print("✅ PyMuPDF импортирован")
    except ImportError as e:
        print(f"❌ PyMuPDF: {e}")
        return False
    
    try:
        import docx
        print("✅ python-docx импортирован")
    except ImportError as e:
        print(f"❌ python-docx: {e}")
        return False
    
    try:
        import openpyxl
        print("✅ openpyxl импортирован")
    except ImportError as e:
        print(f"❌ openpyxl: {e}")
        return False
    
    try:
        import numpy
        print("✅ NumPy импортирован")
    except ImportError as e:
        print(f"❌ NumPy: {e}")
        return False
    
    return True

def test_local_modules():
    """Тестирует импорт локальных модулей"""
    print("\n🧪 Тестирую локальные модули...")
    
    try:
        from app import app
        print("✅ app.py импортирован")
    except Exception as e:
        print(f"❌ app.py: {e}")
        return False
    
    try:
        from main import main
        print("✅ main.py импортирован")
    except Exception as e:
        print(f"❌ main.py: {e}")
        return False
    
    try:
        from rag import db_init_rag
        print("✅ rag.py импортирован")
    except Exception as e:
        print(f"❌ rag.py: {e}")
        return False
    
    return True

def test_env_file():
    """Проверяет наличие конфигурационного файла"""
    print("\n🧪 Проверяю конфигурацию...")
    
    env_file = Path("touch.env")
    if not env_file.exists():
        print("❌ Файл touch.env не найден!")
        print("Создайте touch.env с вашими ключами:")
        print("TELEGRAM_TOKEN=your_bot_token")
        print("OPENAI_API_KEY=your_openai_key")
        return False
    
    print("✅ touch.env найден")
    
    # Проверяем содержимое
    content = env_file.read_text()
    if "your_telegram_bot_token_here" in content:
        print("⚠️  Замените placeholder'ы в touch.env на реальные ключи")
        return False
    
    print("✅ Ключи настроены")
    return True

def main():
    print("🚀 Тест настройки BotCraft\n")
    
    success = True
    
    if not test_imports():
        success = False
    
    if not test_local_modules():
        success = False
    
    if not test_env_file():
        success = False
    
    print("\n" + "="*50)
    if success:
        print("🎉 Все тесты пройдены! Проект готов к запуску.")
        print("\nДля запуска используйте:")
        print("python run_dev.py")
    else:
        print("❌ Есть проблемы с настройкой. Исправьте их перед запуском.")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
