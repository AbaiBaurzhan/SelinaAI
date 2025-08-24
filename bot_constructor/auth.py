"""
Authentication Module for BotCraft
Система авторизации пользователей
"""

import os
import hmac
import hashlib
import secrets
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from urllib.parse import parse_qsl, unquote_plus
from fastapi import HTTPException, Request
from database import db, User


class AuthManager:
    """Менеджер авторизации"""
    
    def __init__(self):
        self.secret_key = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 60 * 24  # 24 часа
    
    def validate_telegram_init_data(self, init_data: str) -> Dict[str, Any]:
        """HMAC‑проверка initData из Telegram Web App"""
        try:
            data = dict(parse_qsl(init_data, keep_blank_values=True))
            if "hash" not in data:
                raise HTTPException(status_code=401, detail="No hash in initData")
            
            received_hash = data.pop("hash")
            
            # Получаем токен бота
            bot_token = os.getenv("TELEGRAM_TOKEN")
            if not bot_token:
                raise HTTPException(status_code=500, detail="Bot token not configured")
            
            # Вычисляем HMAC
            secret = hashlib.sha256(bot_token.encode()).digest()
            check_str = "\n".join(f"{k}={unquote_plus(v)}" for k, v in sorted(data.items()))
            calculated_hash = hmac.new(secret, check_str.encode(), hashlib.sha256).hexdigest()
            
            if not hmac.compare_digest(received_hash, calculated_hash):
                raise HTTPException(status_code=401, detail="Invalid hash")
            
            # Проверяем время (не старше 24 часов)
            auth_date = int(data.get("auth_date", "0") or "0")
            if abs(datetime.now().timestamp() - auth_date) > 60 * 60 * 24:
                raise HTTPException(status_code=401, detail="Expired auth_date")
            
            # Парсим данные пользователя
            user_data = {}
            if "user" in data:
                try:
                    user_data = eval(data["user"])  # Безопасно для Telegram данных
                except:
                    user_data = {}
            
            if "id" not in user_data:
                raise HTTPException(status_code=401, detail="No user.id in initData")
            
            return {
                "telegram_id": user_data["id"],
                "first_name": user_data.get("first_name", ""),
                "last_name": user_data.get("last_name", ""),
                "username": user_data.get("username", ""),
                "language_code": user_data.get("language_code", ""),
                "raw_data": data
            }
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=401, detail=f"Invalid initData: {str(e)}")
    
    def authenticate_telegram_user(self, init_data: str) -> User:
        """Аутентификация пользователя через Telegram"""
        # Валидируем initData
        telegram_data = self.validate_telegram_init_data(init_data)
        telegram_id = telegram_data["telegram_id"]
        
        # Ищем пользователя в базе
        user = db.get_user_by_telegram_id(telegram_id)
        
        if not user:
            # Создаем нового пользователя
            user_id = db.create_user(telegram_id=telegram_id)
            user = db.get_user_by_telegram_id(telegram_id)
        
        return user
    
    def authenticate_email_user(self, email: str, password: str) -> Optional[User]:
        """Аутентификация пользователя по email и паролю"""
        return db.authenticate_user(email, password)
    
    def create_access_token(self, user: User) -> str:
        """Создание JWT токена доступа"""
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode = {
            "sub": str(user.id),
            "telegram_id": user.telegram_id,
            "email": user.email,
            "exp": expire
        }
        
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def verify_access_token(self, token: str) -> Optional[User]:
        """Проверка JWT токена"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id = int(payload.get("sub"))
            
            # Получаем пользователя из базы
            if payload.get("telegram_id"):
                return db.get_user_by_telegram_id(payload["telegram_id"])
            elif payload.get("email"):
                return db.get_user_by_email(payload["email"])
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.JWTError:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        return None
    
    def create_session(self, user: User) -> str:
        """Создание сессии в базе данных"""
        return db.create_session(user.id)
    
    def validate_session(self, session_token: str) -> Optional[User]:
        """Проверка сессии"""
        return db.validate_session(session_token)
    
    def logout(self, session_token: str):
        """Выход пользователя"""
        db.delete_session(session_token)


# Глобальный экземпляр менеджера авторизации
auth_manager = AuthManager()


def get_current_user(request: Request) -> User:
    """Dependency для получения текущего пользователя"""
    # Сначала пробуем через Authorization header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        user = auth_manager.verify_access_token(token)
        if user:
            return user
    
    # Затем пробуем через session cookie
    session_token = request.cookies.get("session_token")
    if session_token:
        user = auth_manager.validate_session(session_token)
        if user:
            return user
    
    # Наконец, пробуем через Telegram initData (для WebApp)
    try:
        body = request.json()
        if body and "initData" in body:
            user = auth_manager.authenticate_telegram_user(body["initData"])
            return user
    except:
        pass
    
    raise HTTPException(status_code=401, detail="Not authenticated")


def get_optional_user(request: Request) -> Optional[User]:
    """Dependency для получения пользователя (опционально)"""
    try:
        return get_current_user(request)
    except HTTPException:
        return None
