#!/usr/bin/env python3
"""
Финальный тест BotCraft
Проверяет все компоненты перед запуском
"""
import sys
import os
from pathlib import Path

def test_environment():
    """Тестирует переменные окружения"""
    print("🔧 Проверяю переменные окружения...")
    
    from dotenv import load_dotenv
    load_dotenv("touch.env")
    
    required_vars = ["TELEGRAM_TOKEN", "OPENAI_API_KEY", "WEBAPP_URL"]
    for var in required_vars:
        value = os.getenv(var)
        if value and value != f"your_{var.lower()}_here":
            print(f"✅ {var}: OK")
        else:
            print(f"❌ {var}: MISSING")
            return False
    return True

def test_database():
    """Тестирует базу данных"""
    print("\n🗄️  Проверяю базу данных...")
    
    try:
        from app import db
        con = db()
        cur = con.cursor()
        
        # Проверяем таблицы
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cur.fetchall()]
        expected_tables = ['owners', 'documents', 'chunks', 'catalog_items']
        
        for table in expected_tables:
            if table in tables:
                print(f"✅ Таблица {table}: OK")
            else:
                print(f"❌ Таблица {table}: MISSING")
                return False
        
        # Проверяем целостность
        cur.execute("PRAGMA integrity_check")
        result = cur.fetchone()
        if result and result[0] == "ok":
            print("✅ Целостность БД: OK")
        else:
            print("❌ Целостность БД: ERROR")
            return False
        
        con.close()
        return True
        
    except Exception as e:
        print(f"❌ Ошибка БД: {e}")
        return False

def test_rag_system():
    """Тестирует RAG систему"""
    print("\n🤖 Проверяю RAG систему...")
    
    try:
        from rag import db_init_rag, upload_doc, retrieve_top_k
        db_init_rag()
        print("✅ RAG БД: OK")
        print("✅ RAG функции: OK")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка RAG: {e}")
        return False

def test_fastapi():
    """Тестирует FastAPI приложение"""
    print("\n🌐 Проверяю FastAPI...")
    
    try:
        from app import app
        
        # Проверяем маршруты
        routes = [route.path for route in app.routes]
        expected_routes = ['/health', '/api/verify', '/api/save_basics']
        
        for route in expected_routes:
            if route in routes:
                print(f"✅ Маршрут {route}: OK")
            else:
                print(f"❌ Маршрут {route}: MISSING")
                return False
        
        print("✅ FastAPI приложение: OK")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка FastAPI: {e}")
        return False

def test_telegram_bot():
    """Тестирует Telegram бота"""
    print("\n📱 Проверяю Telegram бота...")
    
    try:
        from main import start_cmd, panel_cmd, ask_cmd, main
        
        # Проверяем функции
        functions = [start_cmd, panel_cmd, ask_cmd]
        for func in functions:
            if callable(func):
                print(f"✅ Функция {func.__name__}: OK")
            else:
                print(f"❌ Функция {func.__name__}: ERROR")
                return False
        
        print("✅ Telegram бот: OK")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка Telegram бота: {e}")
        return False

def test_webapp():
    """Тестирует WebApp"""
    print("\n📱 Проверяю WebApp...")
    
    try:
        webapp_path = Path("webapp/index.html")
        if webapp_path.exists():
            content = webapp_path.read_text(encoding='utf-8')
            if len(content) > 1000:
                print("✅ WebApp HTML: OK")
                return True
            else:
                print("❌ WebApp HTML: слишком короткий")
                return False
        else:
            print("❌ WebApp HTML: файл не найден")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка WebApp: {e}")
        return False

def main():
    print("🚀 ФИНАЛЬНЫЙ ТЕСТ BOTCRAFT\n")
    print("=" * 50)
    
    tests = [
        ("Переменные окружения", test_environment),
        ("База данных", test_database),
        ("RAG система", test_rag_system),
        ("FastAPI", test_fastapi),
        ("Telegram бот", test_telegram_bot),
        ("WebApp", test_webapp),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Критическая ошибка в {test_name}: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("📊 РЕЗУЛЬТАТЫ ТЕСТОВ:")
    
    all_passed = True
    for test_name, result in results:
        status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
        print(f"{test_name}: {status}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 50)
    
    if all_passed:
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
        print("🚀 Проект готов к запуску!")
        print("\nДля запуска используйте:")
        print("source venv/bin/activate")
        print("python run_dev.py")
        return 0
    else:
        print("❌ ЕСТЬ ПРОБЛЕМЫ!")
        print("🔧 Исправьте их перед запуском")
        return 1

if __name__ == "__main__":
    sys.exit(main())
