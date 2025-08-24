"""
Base Channel Class
Базовый класс для всех каналов связи
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum


class MessageType(Enum):
    """Типы сообщений"""
    TEXT = "text"
    IMAGE = "image"
    DOCUMENT = "document"
    AUDIO = "audio"
    VIDEO = "video"
    LOCATION = "location"
    CONTACT = "contact"


@dataclass
class Message:
    """Унифицированное сообщение"""
    id: str
    channel: str
    user_id: str
    chat_id: str
    message_type: MessageType
    content: str
    metadata: Dict[str, Any]
    timestamp: float


@dataclass
class Response:
    """Унифицированный ответ"""
    chat_id: str
    content: str
    message_type: MessageType = MessageType.TEXT
    metadata: Optional[Dict[str, Any]] = None


class BaseChannel(ABC):
    """Базовый класс для всех каналов связи"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.name = self.__class__.__name__.lower()
        self.is_active = False
    
    @abstractmethod
    async def start(self) -> bool:
        """Запуск канала"""
        pass
    
    @abstractmethod
    async def stop(self) -> bool:
        """Остановка канала"""
        pass
    
    @abstractmethod
    async def send_message(self, response: Response) -> bool:
        """Отправка сообщения"""
        pass
    
    @abstractmethod
    async def process_message(self, message: Message) -> Optional[Response]:
        """Обработка входящего сообщения"""
        pass
    
    @abstractmethod
    async def get_webhook_url(self) -> str:
        """Получение URL для вебхука"""
        pass
    
    @abstractmethod
    async def verify_webhook(self, data: Dict[str, Any]) -> bool:
        """Верификация вебхука"""
        pass
    
    def get_status(self) -> Dict[str, Any]:
        """Получение статуса канала"""
        return {
            "name": self.name,
            "active": self.is_active,
            "config": {k: v for k, v in self.config.items() if "key" not in k.lower()}
        }
    
    async def health_check(self) -> bool:
        """Проверка здоровья канала"""
        return self.is_active
