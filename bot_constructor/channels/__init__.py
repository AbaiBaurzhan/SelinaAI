"""
SelinaAI Channels Module
Поддержка Telegram, WhatsApp Business и Instagram DM
"""

from .base import BaseChannel
from .telegram import TelegramChannel
from .whatsapp import WhatsAppChannel
from .instagram import InstagramChannel

__all__ = [
    'BaseChannel',
    'TelegramChannel', 
    'WhatsAppChannel',
    'InstagramChannel'
]
