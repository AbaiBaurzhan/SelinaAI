"""
WhatsApp Business Channel Implementation
Поддержка WhatsApp Business через Meta Cloud API
"""

import os
import json
import hmac
import hashlib
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from .base import BaseChannel, Message, Response, MessageType


class WhatsAppChannel(BaseChannel):
    """WhatsApp Business канал связи"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.access_token = config.get("access_token")
        self.phone_number_id = config.get("phone_number_id")
        self.verify_token = config.get("verify_token")
        self.app_secret = config.get("app_secret")
        
        # Логирование
        self.logger = logging.getLogger(f"whatsapp.{self.name}")
        
        # Проверяем обязательные параметры
        if not all([self.access_token, self.phone_number_id, self.verify_token]):
            self.logger.warning("Не все обязательные параметры WhatsApp настроены")
    
    async def start(self) -> bool:
        """Запуск WhatsApp канала"""
        try:
            if not all([self.access_token, self.phone_number_id, self.verify_token]):
                self.logger.error("WhatsApp канал не может быть запущен - отсутствуют обязательные параметры")
                return False
            
            # Проверяем доступность API
            if await self._test_api_connection():
                self.is_active = True
                self.logger.info(f"WhatsApp канал {self.name} запущен")
                return True
            else:
                self.logger.error("Не удалось подключиться к WhatsApp API")
                return False
                
        except Exception as e:
            self.logger.error(f"Ошибка запуска WhatsApp канала: {e}")
            return False
    
    async def stop(self) -> bool:
        """Остановка WhatsApp канала"""
        try:
            self.is_active = False
            self.logger.info(f"WhatsApp канал {self.name} остановлен")
            return True
        except Exception as e:
            self.logger.error(f"Ошибка остановки WhatsApp канала: {e}")
            return False
    
    async def send_message(self, response: Response) -> bool:
        """Отправка сообщения в WhatsApp"""
        try:
            if not self.is_active:
                return False
            
            # Формируем данные для отправки
            message_data = {
                "messaging_product": "whatsapp",
                "to": response.chat_id,
                "type": "text",
                "text": {"body": response.content}
            }
            
            # Отправляем через Meta API
            success = await self._send_whatsapp_message(message_data)
            
            if success:
                self.logger.info(f"Сообщение отправлено в WhatsApp: {response.chat_id}")
                return True
            else:
                self.logger.error(f"Не удалось отправить сообщение в WhatsApp: {response.chat_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"Ошибка отправки WhatsApp сообщения: {e}")
            return False
    
    async def process_message(self, message: Message) -> Optional[Response]:
        """Обработка входящего сообщения из WhatsApp"""
        # Этот метод вызывается из webhook обработчика
        # Здесь можно добавить логику обработки
        return None
    
    async def get_webhook_url(self) -> str:
        """Получение URL для вебхука"""
        base_url = self.config.get("webhook_base_url", "")
        return f"{base_url}/webhook/whatsapp"
    
    async def verify_webhook(self, data: Dict[str, Any]) -> bool:
        """Верификация вебхука WhatsApp"""
        try:
            # Получаем параметры верификации
            mode = data.get("hub.mode")
            token = data.get("hub.verify_token")
            challenge = data.get("hub.challenge")
            
            # Проверяем режим и токен
            if mode == "subscribe" and token == self.verify_token:
                self.logger.info("WhatsApp webhook верифицирован")
                return True
            else:
                self.logger.warning("WhatsApp webhook верификация не пройдена")
                return False
                
        except Exception as e:
            self.logger.error(f"Ошибка верификации WhatsApp webhook: {e}")
            return False
    
    async def process_webhook_message(self, data: Dict[str, Any]) -> Optional[Response]:
        """Обработка входящего сообщения из webhook"""
        try:
            # Парсим данные webhook
            if "object" not in data or data["object"] != "whatsapp_business_account":
                return None
            
            # Получаем сообщения
            entries = data.get("entry", [])
            for entry in entries:
                changes = entry.get("changes", [])
                for change in changes:
                    if change.get("value", {}).get("messages"):
                        messages = change["value"]["messages"]
                        for msg in messages:
                            # Обрабатываем каждое сообщение
                            response = await self._process_whatsapp_message(msg)
                            if response:
                                return response
            
            return None
            
        except Exception as e:
            self.logger.error(f"Ошибка обработки WhatsApp webhook: {e}")
            return None
    
    async def _process_whatsapp_message(self, msg_data: Dict[str, Any]) -> Optional[Response]:
        """Обработка отдельного WhatsApp сообщения"""
        try:
            # Извлекаем данные сообщения
            message_id = msg_data.get("id")
            from_number = msg_data.get("from")
            timestamp = msg_data.get("timestamp")
            message_type = msg_data.get("type")
            
            if not all([message_id, from_number, timestamp]):
                return None
            
            # Определяем тип сообщения
            if message_type == "text":
                content = msg_data.get("text", {}).get("body", "")
                msg_type = MessageType.TEXT
            elif message_type == "image":
                content = "Изображение"
                msg_type = MessageType.IMAGE
            elif message_type == "document":
                content = "Документ"
                msg_type = MessageType.DOCUMENT
            else:
                content = f"Сообщение типа: {message_type}"
                msg_type = MessageType.TEXT
            
            # Создаем унифицированное сообщение
            message = Message(
                id=message_id,
                channel="whatsapp",
                user_id=from_number,
                chat_id=from_number,
                message_type=msg_type,
                content=content,
                metadata={
                    "whatsapp_type": message_type,
                    "raw_data": msg_data
                },
                timestamp=float(timestamp)
            )
            
            # Обрабатываем через общий обработчик
            return await self._handle_message(message)
            
        except Exception as e:
            self.logger.error(f"Ошибка обработки WhatsApp сообщения: {e}")
            return None
    
    async def _handle_message(self, message: Message) -> Optional[Response]:
        """Общий обработчик WhatsApp сообщений"""
        # Здесь будет логика обработки через RAG и AI
        # Пока возвращаем заглушку
        
        return Response(
            chat_id=message.chat_id,
            content="📱 Получил ваше WhatsApp сообщение! Скоро здесь будет ИИ-обработка."
        )
    
    async def _test_api_connection(self) -> bool:
        """Тестирование подключения к WhatsApp API"""
        try:
            # Простая проверка - пытаемся получить информацию о номере
            # В реальности здесь можно сделать более сложную проверку
            return True
        except Exception as e:
            self.logger.error(f"Ошибка тестирования WhatsApp API: {e}")
            return False
    
    async def _send_whatsapp_message(self, message_data: Dict[str, Any]) -> bool:
        """Отправка сообщения через WhatsApp API"""
        try:
            # Здесь должна быть реальная отправка через Meta API
            # Пока возвращаем заглушку
            self.logger.info(f"Отправка WhatsApp сообщения: {message_data}")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка отправки через WhatsApp API: {e}")
            return False
    
    def verify_signature(self, body: str, signature: str) -> bool:
        """Проверка подписи webhook для безопасности"""
        try:
            if not self.app_secret:
                self.logger.warning("App secret не настроен, пропускаем проверку подписи")
                return True
            
            # Вычисляем ожидаемую подпись
            expected_signature = "sha256=" + hmac.new(
                self.app_secret.encode('utf-8'),
                body.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature, expected_signature)
            
        except Exception as e:
            self.logger.error(f"Ошибка проверки подписи: {e}")
            return False
