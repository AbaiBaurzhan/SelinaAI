"""
Channel Manager
Менеджер для управления всеми каналами связи
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from .base import BaseChannel, Message, Response
from .telegram import TelegramChannel
from .whatsapp import WhatsAppChannel
from .instagram import InstagramChannel


class ChannelManager:
    """Менеджер каналов связи"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.channels: Dict[str, BaseChannel] = {}
        self.logger = logging.getLogger("channel_manager")
        
        # Инициализируем каналы
        self._initialize_channels()
    
    def _initialize_channels(self):
        """Инициализация всех каналов"""
        try:
            # Telegram канал
            if "telegram" in self.config:
                telegram_config = self.config["telegram"].copy()
                telegram_config["webhook_base_url"] = self.config.get("webhook_base_url", "")
                self.channels["telegram"] = TelegramChannel(telegram_config)
                self.logger.info("Telegram канал инициализирован")
            
            # WhatsApp канал
            if "whatsapp" in self.config:
                whatsapp_config = self.config["whatsapp"].copy()
                whatsapp_config["webhook_base_url"] = self.config.get("webhook_base_url", "")
                self.channels["whatsapp"] = WhatsAppChannel(whatsapp_config)
                self.logger.info("WhatsApp канал инициализирован")
            
            # Instagram канал
            if "instagram" in self.config:
                instagram_config = self.config["instagram"].copy()
                instagram_config["webhook_base_url"] = self.config.get("webhook_base_url", "")
                self.channels["instagram"] = InstagramChannel(instagram_config)
                self.logger.info("Instagram канал инициализирован")
            
            self.logger.info(f"Инициализировано каналов: {len(self.channels)}")
            
        except Exception as e:
            self.logger.error(f"Ошибка инициализации каналов: {e}")
    
    async def start_all_channels(self) -> bool:
        """Запуск всех каналов"""
        try:
            results = []
            for name, channel in self.channels.items():
                self.logger.info(f"Запуск канала: {name}")
                result = await channel.start()
                results.append(result)
                if result:
                    self.logger.info(f"✅ Канал {name} запущен")
                else:
                    self.logger.error(f"❌ Канал {name} не запущен")
            
            # Возвращаем True если хотя бы один канал запущен
            return any(results)
            
        except Exception as e:
            self.logger.error(f"Ошибка запуска каналов: {e}")
            return False
    
    async def stop_all_channels(self) -> bool:
        """Остановка всех каналов"""
        try:
            results = []
            for name, channel in self.channels.items():
                self.logger.info(f"Остановка канала: {name}")
                result = await channel.stop()
                results.append(result)
                if result:
                    self.logger.info(f"✅ Канал {name} остановлен")
                else:
                    self.logger.warning(f"⚠️ Канал {name} не остановлен")
            
            return all(results)
            
        except Exception as e:
            self.logger.error(f"Ошибка остановки каналов: {e}")
            return False
    
    async def send_message(self, channel_name: str, response: Response) -> bool:
        """Отправка сообщения в конкретный канал"""
        try:
            if channel_name not in self.channels:
                self.logger.error(f"Канал {channel_name} не найден")
                return False
            
            channel = self.channels[channel_name]
            if not channel.is_active:
                self.logger.warning(f"Канал {channel_name} не активен")
                return False
            
            return await channel.send_message(response)
            
        except Exception as e:
            self.logger.error(f"Ошибка отправки сообщения в канал {channel_name}: {e}")
            return False
    
    async def send_message_all_channels(self, response: Response) -> Dict[str, bool]:
        """Отправка сообщения во все активные каналы"""
        try:
            results = {}
            for name, channel in self.channels.items():
                if channel.is_active:
                    self.logger.info(f"Отправка сообщения в канал: {name}")
                    result = await channel.send_message(response)
                    results[name] = result
                else:
                    self.logger.info(f"Пропуск неактивного канала: {name}")
                    results[name] = False
            
            return results
            
        except Exception as e:
            self.logger.error(f"Ошибка отправки сообщения во все каналы: {e}")
            return {name: False for name in self.channels.keys()}
    
    async def process_message(self, channel_name: str, message: Message) -> Optional[Response]:
        """Обработка входящего сообщения из конкретного канала"""
        try:
            if channel_name not in self.channels:
                self.logger.error(f"Канал {channel_name} не найден")
                return None
            
            channel = self.channels[channel_name]
            return await channel.process_message(message)
            
        except Exception as e:
            self.logger.error(f"Ошибка обработки сообщения из канала {channel_name}: {e}")
            return None
    
    def get_channel_status(self, channel_name: str) -> Optional[Dict[str, Any]]:
        """Получение статуса конкретного канала"""
        try:
            if channel_name not in self.channels:
                return None
            
            return self.channels[channel_name].get_status()
            
        except Exception as e:
            self.logger.error(f"Ошибка получения статуса канала {channel_name}: {e}")
            return None
    
    def get_all_channels_status(self) -> Dict[str, Dict[str, Any]]:
        """Получение статуса всех каналов"""
        try:
            return {
                name: channel.get_status() 
                for name, channel in self.channels.items()
            }
        except Exception as e:
            self.logger.error(f"Ошибка получения статуса всех каналов: {e}")
            return {}
    
    def get_active_channels(self) -> List[str]:
        """Получение списка активных каналов"""
        try:
            return [
                name for name, channel in self.channels.items() 
                if channel.is_active
            ]
        except Exception as e:
            self.logger.error(f"Ошибка получения активных каналов: {e}")
            return []
    
    def get_channel_webhook_url(self, channel_name: str) -> Optional[str]:
        """Получение webhook URL для конкретного канала"""
        try:
            if channel_name not in self.channels:
                return None
            
            channel = self.channels[channel_name]
            return asyncio.run(channel.get_webhook_url())
            
        except Exception as e:
            self.logger.error(f"Ошибка получения webhook URL для канала {channel_name}: {e}")
            return None
    
    async def verify_webhook(self, channel_name: str, data: Dict[str, Any]) -> bool:
        """Верификация webhook для конкретного канала"""
        try:
            if channel_name not in self.channels:
                self.logger.error(f"Канал {channel_name} не найден")
                return False
            
            channel = self.channels[channel_name]
            return await channel.verify_webhook(data)
            
        except Exception as e:
            self.logger.error(f"Ошибка верификации webhook для канала {channel_name}: {e}")
            return False
    
    async def health_check_all(self) -> Dict[str, bool]:
        """Проверка здоровья всех каналов"""
        try:
            results = {}
            for name, channel in self.channels.items():
                try:
                    result = await channel.health_check()
                    results[name] = result
                except Exception as e:
                    self.logger.error(f"Ошибка проверки здоровья канала {name}: {e}")
                    results[name] = False
            
            return results
            
        except Exception as e:
            self.logger.error(f"Ошибка проверки здоровья всех каналов: {e}")
            return {name: False for name in self.channels.keys()}
    
    def get_channel_config(self, channel_name: str) -> Optional[Dict[str, Any]]:
        """Получение конфигурации конкретного канала"""
        try:
            if channel_name not in self.channels:
                return None
            
            channel = self.channels[channel_name]
            return channel.config
            
        except Exception as e:
            self.logger.error(f"Ошибка получения конфигурации канала {channel_name}: {e}")
            return None
    
    def update_channel_config(self, channel_name: str, new_config: Dict[str, Any]) -> bool:
        """Обновление конфигурации канала"""
        try:
            if channel_name not in self.channels:
                self.logger.error(f"Канал {channel_name} не найден")
                return False
            
            # Останавливаем канал
            channel = self.channels[channel_name]
            asyncio.run(channel.stop())
            
            # Обновляем конфигурацию
            channel.config.update(new_config)
            
            # Перезапускаем канал
            success = asyncio.run(channel.start())
            
            if success:
                self.logger.info(f"Конфигурация канала {channel_name} обновлена")
            else:
                self.logger.error(f"Не удалось перезапустить канал {channel_name}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Ошибка обновления конфигурации канала {channel_name}: {e}")
            return False
