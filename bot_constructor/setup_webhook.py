#!/usr/bin/env python3
"""
Скрипт настройки webhook для Telegram бота
"""

import os
import requests
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv("touch.env")

def setup_telegram_webhook():
    """Настройка webhook для Telegram бота"""
    
    # Получаем токен и URL
    bot_token = os.getenv("TELEGRAM_TOKEN")
    webhook_url = os.getenv("WEBAPP_URL")
    
    if not bot_token:
        print("❌ TELEGRAM_TOKEN не найден в touch.env")
        return False
    
    if not webhook_url:
        print("❌ WEBAPP_URL не найден в touch.env")
        return False
    
    # Формируем webhook URL
    webhook_endpoint = f"{webhook_url}/webhook/telegram"
    
    print(f"🤖 Настройка webhook для бота...")
    print(f"📱 Webhook URL: {webhook_endpoint}")
    
    try:
        # Устанавливаем webhook
        response = requests.post(
            f"https://api.telegram.org/bot{bot_token}/setWebhook",
            json={
                "url": webhook_endpoint,
                "allowed_updates": ["message", "callback_query", "inline_query"]
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("ok"):
                print("✅ Webhook успешно установлен!")
                print(f"📊 Результат: {result}")
                
                # Проверяем текущий webhook
                webhook_info = requests.get(
                    f"https://api.telegram.org/bot{bot_token}/getWebhookInfo"
                )
                
                if webhook_info.status_code == 200:
                    info = webhook_info.json()
                    if info.get("ok"):
                        print(f"📋 Информация о webhook:")
                        print(f"   URL: {info['result'].get('url', 'Не установлен')}")
                        print(f"   Ошибки: {info['result'].get('last_error_message', 'Нет')}")
                        print(f"   Обновления: {info['result'].get('pending_update_count', 0)}")
                
                return True
            else:
                print(f"❌ Ошибка установки webhook: {result}")
                return False
        else:
            print(f"❌ HTTP ошибка: {response.status_code}")
            print(f"📝 Ответ: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при настройке webhook: {e}")
        return False

def remove_telegram_webhook():
    """Удаление webhook для Telegram бота"""
    
    bot_token = os.getenv("TELEGRAM_TOKEN")
    if not bot_token:
        print("❌ TELEGRAM_TOKEN не найден в touch.env")
        return False
    
    try:
        response = requests.post(
            f"https://api.telegram.org/bot{bot_token}/deleteWebhook"
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("ok"):
                print("✅ Webhook успешно удален!")
                return True
            else:
                print(f"❌ Ошибка удаления webhook: {result}")
                return False
        else:
            print(f"❌ HTTP ошибка: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при удалении webhook: {e}")
        return False

def get_webhook_info():
    """Получение информации о текущем webhook"""
    
    bot_token = os.getenv("TELEGRAM_TOKEN")
    if not bot_token:
        print("❌ TELEGRAM_TOKEN не найден в touch.env")
        return False
    
    try:
        response = requests.get(
            f"https://api.telegram.org/bot{bot_token}/getWebhookInfo"
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("ok"):
                info = result["result"]
                print("📋 Информация о webhook:")
                print(f"   URL: {info.get('url', 'Не установлен')}")
                print(f"   Ошибки: {info.get('last_error_message', 'Нет')}")
                print(f"   Обновления: {info.get('pending_update_count', 0)}")
                print(f"   Время ошибки: {info.get('last_error_date', 'Нет')}")
                return True
            else:
                print(f"❌ Ошибка получения информации: {result}")
                return False
        else:
            print(f"❌ HTTP ошибка: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при получении информации: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Настройка Telegram Webhook")
    print("=" * 40)
    
    # Показываем текущую информацию
    print("\n📋 Текущий статус webhook:")
    get_webhook_info()
    
    # Устанавливаем webhook
    print("\n🔧 Установка webhook...")
    if setup_telegram_webhook():
        print("\n✅ Webhook настроен успешно!")
        print("🚀 Теперь бот будет получать обновления через webhook")
    else:
        print("\n❌ Не удалось настроить webhook")
        print("💡 Проверьте:")
        print("   - Правильность TELEGRAM_TOKEN")
        print("   - Доступность WEBAPP_URL")
        print("   - Запущен ли сервер")
