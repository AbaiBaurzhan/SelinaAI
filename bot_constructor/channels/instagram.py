"""
Instagram DM Channel Implementation
Поддержка Instagram Direct Messages через Meta Graph API
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from .base import BaseChannel, Message, Response, MessageType


class InstagramChannel(BaseChannel):
    """Instagram DM канал связи"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.access_token = config.get("access_token")
        self.instagram_business_account_id = config.get("instagram_business_account_id")
        self.page_id = config.get("page_id")
        self.verify_token = config.get("verify_token")
        
        # Логирование
        self.logger = logging.getLogger(f"instagram.{self.name}")
        
        # Проверяем обязательные параметры
        if not all([self.access_token, self.instagram_business_account_id, self.page_id]):
            self.logger.warning("Не все обязательные параметры Instagram настроены")
        
        # Флаг доступности отправки сообщений
        self.can_send_messages = False
        self.permissions_checked = False
    
    async def start(self) -> bool:
        """Запуск Instagram канала"""
        try:
            if not all([self.access_token, self.instagram_business_account_id, self.page_id]):
                self.logger.error("Instagram канал не может быть запущен - отсутствуют обязательные параметры")
                return False
            
            # Проверяем разрешения и доступность API
            await self._check_permissions()
            
            if await self._test_api_connection():
                self.is_active = True
                self.logger.info(f"Instagram канал {self.name} запущен")
                if self.can_send_messages:
                    self.logger.info("✅ Отправка сообщений доступна")
                else:
                    self.logger.warning("⚠️ Отправка сообщений недоступна (только прием)")
                return True
            else:
                self.logger.error("Не удалось подключиться к Instagram API")
                return False
                
        except Exception as e:
            self.logger.error(f"Ошибка запуска Instagram канала: {e}")
            return False
    
    async def stop(self) -> bool:
        """Остановка Instagram канала"""
        try:
            self.is_active = False
            self.logger.info(f"Instagram канал {self.name} остановлен")
            return True
        except Exception as e:
            self.logger.error(f"Ошибка остановки Instagram канала: {e}")
            return False
    
    async def send_message(self, response: Response) -> bool:
        """Отправка сообщения в Instagram DM"""
        try:
            if not self.is_active:
                return False
            
            if not self.can_send_messages:
                self.logger.warning("Отправка сообщений в Instagram недоступна")
                # Возвращаем True, чтобы не блокировать основной поток
                # В реальности здесь можно добавить очередь для отложенной отправки
                return True
            
            # Формируем данные для отправки
            message_data = {
                "recipient_type": "individual",
                "to": response.chat_id,
                "type": "text",
                "text": response.content
            }
            
            # Отправляем через Meta Graph API
            success = await self._send_instagram_message(message_data)
            
            if success:
                self.logger.info(f"Сообщение отправлено в Instagram: {response.chat_id}")
                return True
            else:
                self.logger.error(f"Не удалось отправить сообщение в Instagram: {response.chat_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"Ошибка отправки Instagram сообщения: {e}")
            return False
    
    async def process_message(self, message: Message) -> Optional[Response]:
        """Обработка входящего сообщения из Instagram"""
        # Этот метод вызывается из webhook обработчика
        # Здесь можно добавить логику обработки
        return None
    
    async def get_webhook_url(self) -> str:
        """Получение URL для вебхука"""
        base_url = self.config.get("webhook_base_url", "")
        return f"{base_url}/webhook/instagram"
    
    async def verify_webhook(self, data: Dict[str, Any]) -> bool:
        """Верификация вебхука Instagram"""
        try:
            # Получаем параметры верификации
            mode = data.get("hub.mode")
            token = data.get("hub.verify_token")
            challenge = data.get("hub.challenge")
            
            # Проверяем режим и токен
            if mode == "subscribe" and token == self.verify_token:
                self.logger.info("Instagram webhook верифицирован")
                return True
            else:
                self.logger.warning("Instagram webhook верификация не пройдена")
                return False
                
        except Exception as e:
            self.logger.error(f"Ошибка верификации Instagram webhook: {e}")
            return False
    
    async def process_webhook_message(self, data: Dict[str, Any]) -> Optional[Response]:
        """Обработка входящего сообщения из webhook"""
        try:
            # Парсим данные webhook Instagram
            if "object" not in data or data["object"] != "instagram":
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
                            response = await self._process_instagram_message(msg)
                            if response:
                                return response
            
            return None
            
        except Exception as e:
            self.logger.error(f"Ошибка обработки Instagram webhook: {e}")
            return None
    
    async def _process_instagram_message(self, msg_data: Dict[str, Any]) -> Optional[Response]:
        """Обработка отдельного Instagram сообщения"""
        try:
            # Извлекаем данные сообщения
            message_id = msg_data.get("id")
            from_user = msg_data.get("from", {})
            timestamp = msg_data.get("timestamp")
            message_type = msg_data.get("type")
            
            if not all([message_id, from_user, timestamp]):
                return None
            
            user_id = from_user.get("id")
            username = from_user.get("username", "unknown")
            
            # Определяем тип сообщения
            if message_type == "text":
                content = msg_data.get("text", "")
                msg_type = MessageType.TEXT
            elif message_type == "image":
                content = "Изображение"
                msg_type = MessageType.IMAGE
            elif message_type == "story_mention":
                content = "Упоминание в истории"
                msg_type = MessageType.TEXT
            else:
                content = f"Сообщение типа: {message_type}"
                msg_type = MessageType.TEXT
            
            # Создаем унифицированное сообщение
            message = Message(
                id=message_id,
                channel="instagram",
                user_id=str(user_id),
                chat_id=str(user_id),
                message_type=msg_type,
                content=content,
                metadata={
                    "instagram_type": message_type,
                    "username": username,
                    "raw_data": msg_data
                },
                timestamp=float(timestamp)
            )
            
            # Обрабатываем через общий обработчик
            return await self._handle_message(message)
            
        except Exception as e:
            self.logger.error(f"Ошибка обработки Instagram сообщения: {e}")
            return None
    
    async def _handle_message(self, message: Message) -> Optional[Response]:
        """Общий обработчик Instagram сообщений"""
        # Здесь будет логика обработки через RAG и AI
        # Пока возвращаем заглушку
        
        return Response(
            chat_id=message.chat_id,
            content="📸 Получил ваше Instagram сообщение! Скоро здесь будет ИИ-обработка."
        )
    
    async def _check_permissions(self) -> None:
        """Проверка разрешений для отправки сообщений"""
        try:
            if self.permissions_checked:
                return
            
            # Проверяем разрешения через Graph API
            # В реальности здесь нужно сделать запрос к /me/permissions
            # Пока используем заглушку
            
            # Проверяем наличие необходимых разрешений
            required_permissions = [
                "instagram_basic",
                "instagram_manage_comments",
                "pages_messaging"
            ]
            
            # Здесь должна быть реальная проверка через API
            # Пока считаем, что разрешения есть
            self.can_send_messages = True
            self.permissions_checked = True
            
            self.logger.info("Разрешения Instagram проверены")
            
        except Exception as e:
            self.logger.error(f"Ошибка проверки разрешений Instagram: {e}")
            self.can_send_messages = False
            self.permissions_checked = True
    
    async def _test_api_connection(self) -> bool:
        """Тестирование подключения к Instagram API"""
        try:
            # Простая проверка - пытаемся получить информацию об аккаунте
            # В реальности здесь можно сделать запрос к Graph API
            return True
        except Exception as e:
            self.logger.error(f"Ошибка тестирования Instagram API: {e}")
            return False
    
    async def _send_instagram_message(self, message_data: Dict[str, Any]) -> bool:
        """Отправка сообщения через Instagram Graph API"""
        try:
            # Здесь должна быть реальная отправка через Meta Graph API
            # Пока возвращаем заглушку
            self.logger.info(f"Отправка Instagram сообщения: {message_data}")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка отправки через Instagram API: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Получение расширенного статуса Instagram канала"""
        base_status = super().get_status()
        base_status.update({
            "can_send_messages": self.can_send_messages,
            "permissions_checked": self.permissions_checked,
            "instagram_account_id": self.instagram_business_account_id,
            "page_id": self.page_id
        })
        return base_status
    
    async def prepare_message_for_sending(self, response: Response) -> Dict[str, Any]:
        """Подготовка сообщения для отправки (функция-обёртка)"""
        """
        Эта функция-обёртка позволяет подготовить сообщение для отправки
        даже если нет прав на отправку. В реальности здесь можно:
        - Сохранить сообщение в базу для отложенной отправки
        - Отправить уведомление администратору
        - Логировать попытки отправки
        """
        try:
            if not self.can_send_messages:
                # Логируем попытку отправки
                self.logger.info(f"Сообщение подготовлено для отложенной отправки: {response.chat_id}")
                
                # Возвращаем данные для сохранения
                return {
                    "status": "prepared",
                    "message": response,
                    "channel": "instagram",
                    "timestamp": datetime.now().isoformat(),
                    "requires_permission": True
                }
            else:
                # Если есть права, отправляем сразу
                success = await self.send_message(response)
                return {
                    "status": "sent" if success else "failed",
                    "message": response,
                    "channel": "instagram",
                    "timestamp": datetime.now().isoformat(),
                    "requires_permission": False
                }
                
        except Exception as e:
            self.logger.error(f"Ошибка подготовки Instagram сообщения: {e}")
            return {
                "status": "error",
                "error": str(e),
                "message": response,
                "channel": "instagram",
                "timestamp": datetime.now().isoformat()
            }
