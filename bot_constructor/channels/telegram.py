"""
Telegram Channel Implementation
Поддержка Telegram бота с polling (dev) и webhook (prod)
"""

import os
import asyncio
import logging
from typing import Dict, Any, Optional
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from telegram.error import TelegramError

from .base import BaseChannel, Message, Response, MessageType


class TelegramChannel(BaseChannel):
    """Telegram канал связи"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.bot = None
        self.app = None
        self.webhook_url = config.get("webhook_url", "")
        self.is_webhook_mode = config.get("webhook_mode", False)
        
        # Обработчики сообщений
        self.message_handlers = []
        self.command_handlers = []
        
        # Логирование
        self.logger = logging.getLogger(f"telegram.{self.name}")
    
    async def start(self) -> bool:
        """Запуск Telegram канала"""
        try:
            token = self.config.get("token")
            if not token:
                self.logger.error("Telegram token не найден")
                return False
            
            self.bot = Bot(token=token)
            self.app = Application.builder().token(token).build()
            
            # Регистрация обработчиков
            self._register_handlers()
            
            if self.is_webhook_mode and self.webhook_url:
                # Webhook режим для продакшена
                await self._setup_webhook()
            else:
                # Polling режим для разработки
                await self._setup_polling()
            
            self.is_active = True
            self.logger.info(f"Telegram канал {self.name} запущен")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка запуска Telegram канала: {e}")
            return False
    
    async def stop(self) -> bool:
        """Остановка Telegram канала"""
        try:
            if self.app:
                await self.app.stop()
                await self.app.shutdown()
            
            if self.is_webhook_mode and self.webhook_url:
                await self.bot.delete_webhook()
            
            self.is_active = False
            self.logger.info(f"Telegram канал {self.name} остановлен")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка остановки Telegram канала: {e}")
            return False
    
    async def send_message(self, response: Response) -> bool:
        """Отправка сообщения в Telegram"""
        try:
            if not self.bot or not self.is_active:
                return False
            
            if response.message_type == MessageType.TEXT:
                await self.bot.send_message(
                    chat_id=response.chat_id,
                    text=response.content,
                    parse_mode='HTML'
                )
            elif response.message_type == MessageType.IMAGE:
                # Отправка изображения (если есть URL или file_id)
                if response.metadata and "image_url" in response.metadata:
                    await self.bot.send_photo(
                        chat_id=response.chat_id,
                        photo=response.metadata["image_url"],
                        caption=response.content
                    )
            
            return True
            
        except TelegramError as e:
            self.logger.error(f"Ошибка отправки сообщения: {e}")
            return False
    
    async def process_message(self, message: Message) -> Optional[Response]:
        """Обработка входящего сообщения из Telegram"""
        # Этот метод вызывается из обработчиков Telegram
        # Здесь можно добавить логику обработки
        return None
    
    async def get_webhook_url(self) -> str:
        """Получение URL для вебхука"""
        return f"{self.webhook_url}/webhook/telegram"
    
    async def verify_webhook(self, data: Dict[str, Any]) -> bool:
        """Верификация вебхука Telegram"""
        # Telegram не требует специальной верификации для webhook
        return True
    
    def _register_handlers(self):
        """Регистрация обработчиков команд и сообщений"""
        
        # Обработчик команды /start
        async def start_command(update: Update, context):
            chat_id = update.effective_chat.id
            user_id = update.effective_user.id
            
            # Создаем унифицированное сообщение
            message = Message(
                id=str(update.message.message_id),
                channel="telegram",
                user_id=str(user_id),
                chat_id=str(chat_id),
                message_type=MessageType.TEXT,
                content="/start",
                metadata={"username": update.effective_user.username},
                timestamp=update.message.date.timestamp()
            )
            
            # Обрабатываем через общий обработчик
            response = await self._handle_message(message)
            if response:
                await self.send_message(response)
        
        # Обработчик команды /panel
        async def panel_command(update: Update, context):
            chat_id = update.effective_chat.id
            
            # Создаем кнопку для открытия WebApp
            webapp_url = self.config.get("webapp_url", "")
            if webapp_url:
                keyboard = [
                    [InlineKeyboardButton(
                        "⚙️ Настройки ассистента", 
                        web_app={"url": webapp_url}
                    )]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await self.bot.send_message(
                    chat_id=chat_id,
                    text="🎯 Панель управления ассистентом",
                    reply_markup=reply_markup
                )
            else:
                await self.bot.send_message(
                    chat_id=chat_id,
                    text="🔗 WebApp недоступен. Проверьте настройки."
                )
        
        # Обработчик текстовых сообщений
        async def text_message(update: Update, context):
            chat_id = update.effective_chat.id
            user_id = update.effective_user.id
            
            message = Message(
                id=str(update.message.message_id),
                channel="telegram",
                user_id=str(user_id),
                chat_id=str(chat_id),
                message_type=MessageType.TEXT,
                content=update.message.text,
                metadata={"username": update.effective_user.username},
                timestamp=update.message.date.timestamp()
            )
            
            # Обрабатываем через общий обработчик
            response = await self._handle_message(message)
            if response:
                await self.send_message(response)
        
        # Обработчик изображений
        async def image_message(update: Update, context):
            chat_id = update.effective_chat.id
            user_id = update.effective_user.id
            
            # Получаем информацию об изображении
            photo = update.message.photo[-1]  # Берем самое большое изображение
            file_id = photo.file_id
            
            message = Message(
                id=str(update.message.message_id),
                channel="telegram",
                user_id=str(user_id),
                chat_id=str(chat_id),
                message_type=MessageType.IMAGE,
                content="",  # Текст подписи, если есть
                metadata={
                    "file_id": file_id,
                    "file_size": photo.file_size,
                    "width": photo.width,
                    "height": photo.height
                },
                timestamp=update.message.date.timestamp()
            )
            
            # Обрабатываем через общий обработчик
            response = await self._handle_message(message)
            if response:
                await self.send_message(response)
        
        # Регистрируем обработчики
        self.app.add_handler(CommandHandler("start", start_command))
        self.app.add_handler(CommandHandler("panel", panel_command))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_message))
        self.app.add_handler(MessageHandler(filters.PHOTO, image_message))
    
    async def _handle_message(self, message: Message) -> Optional[Response]:
        """Общий обработчик сообщений"""
        # Здесь будет логика обработки через RAG и AI
        # Пока возвращаем заглушку
        
        if message.content == "/start":
            return Response(
                chat_id=message.chat_id,
                content="🤖 Добро пожаловать в BotCraft!\n\n"
                       "Я ваш ИИ-ассистент. Отправьте /panel для настройки "
                       "или просто напишите мне сообщение."
            )
        
        # Для обычных сообщений - заглушка
        return Response(
            chat_id=message.chat_id,
            content="📝 Получил ваше сообщение! Скоро здесь будет ИИ-обработка."
        )
    
    async def _setup_webhook(self):
        """Настройка webhook для продакшена"""
        webhook_url = await self.get_webhook_url()
        await self.bot.set_webhook(url=webhook_url)
        self.logger.info(f"Webhook установлен: {webhook_url}")
    
    async def _setup_polling(self):
        """Настройка polling для разработки"""
        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling()
        self.logger.info("Polling режим запущен")
    
    def add_message_handler(self, handler):
        """Добавление обработчика сообщений"""
        self.message_handlers.append(handler)
    
    def add_command_handler(self, handler):
        """Добавление обработчика команд"""
        self.command_handlers.append(handler)
