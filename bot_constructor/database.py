"""
Database Module for SelinaAI
Управление базой данных, пользователями и ИИ агентами
"""

import sqlite3
import json
import hashlib
import secrets
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass


@dataclass
class User:
    """Модель пользователя"""
    id: int
    telegram_id: Optional[int]
    email: Optional[str]
    created_at: datetime
    is_active: bool


@dataclass
class AIAgent:
    """Модель ИИ агента"""
    id: int
    user_id: int
    name: str
    business_description: str
    capabilities: str
    tone: str
    system_prompt: Optional[str]
    integrations: Optional[str]  # JSON строка
    created_at: datetime
    is_active: bool


@dataclass
class Document:
    """Модель документа"""
    id: int
    agent_id: int
    filename: str
    file_path: str
    file_type: str
    uploaded_at: datetime
    is_processed: bool


class Database:
    """Класс для работы с базой данных"""
    
    def __init__(self, db_path: str = "botcraft.db"):
        self.db_path = Path(db_path)
        self.init_database()
    
    def init_database(self):
        """Инициализация базы данных"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER UNIQUE,
                    email TEXT UNIQUE,
                    password_hash TEXT,
                    salt TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS ai_agents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    business_description TEXT,
                    capabilities TEXT,
                    tone TEXT DEFAULT 'дружелюбный',
                    system_prompt TEXT,
                    integrations_json TEXT DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id INTEGER NOT NULL,
                    filename TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_processed BOOLEAN DEFAULT FALSE,
                    FOREIGN KEY (agent_id) REFERENCES ai_agents (id)
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    session_token TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            # Индексы для оптимизации
            conn.execute("CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_agents_user_id ON ai_agents(user_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_documents_agent_id ON documents(agent_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(session_token)")
            
            conn.commit()
    
    def create_user(self, telegram_id: Optional[int] = None, email: Optional[str] = None, password: Optional[str] = None) -> int:
        """Создание нового пользователя"""
        with sqlite3.connect(self.db_path) as conn:
            password_hash = None
            salt = None
            
            if password:
                salt = secrets.token_hex(16)
                password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
            
            cursor = conn.execute("""
                INSERT INTO users (telegram_id, email, password_hash, salt)
                VALUES (?, ?, ?, ?)
            """, (telegram_id, email, password_hash, salt))
            
            conn.commit()
            return cursor.lastrowid
    
    def get_user_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Получение пользователя по Telegram ID"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("""
                SELECT * FROM users WHERE telegram_id = ? AND is_active = TRUE
            """, (telegram_id,)).fetchone()
            
            if row:
                return User(
                    id=row['id'],
                    telegram_id=row['telegram_id'],
                    email=row['email'],
                    created_at=datetime.fromisoformat(row['created_at']),
                    is_active=bool(row['is_active'])
                )
            return None
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Получение пользователя по email"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("""
                SELECT * FROM users WHERE email = ? AND is_active = TRUE
            """, (email,)).fetchone()
            
            if row:
                return User(
                    id=row['id'],
                    telegram_id=row['telegram_id'],
                    email=row['email'],
                    created_at=datetime.fromisoformat(row['created_at']),
                    is_active=bool(row['is_active'])
                )
            return None
    
    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Аутентификация пользователя по email и паролю"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("""
                SELECT * FROM users WHERE email = ? AND is_active = TRUE
            """, (email,)).fetchone()
            
            if row and row['password_hash'] and row['salt']:
                # Проверяем пароль
                password_hash = hashlib.sha256((password + row['salt']).encode()).hexdigest()
                if password_hash == row['password_hash']:
                    return User(
                        id=row['id'],
                        telegram_id=row['telegram_id'],
                        email=row['email'],
                        created_at=datetime.fromisoformat(row['created_at']),
                        is_active=bool(row['is_active'])
                    )
            return None
    
    def create_session(self, user_id: int, expires_hours: int = 24) -> str:
        """Создание сессии для пользователя"""
        with sqlite3.connect(self.db_path) as conn:
            session_token = secrets.token_urlsafe(32)
            expires_at = datetime.now().timestamp() + (expires_hours * 3600)
            
            conn.execute("""
                INSERT INTO sessions (user_id, session_token, expires_at)
                VALUES (?, ?, ?)
            """, (user_id, session_token, expires_at))
            
            conn.commit()
            return session_token
    
    def validate_session(self, session_token: str) -> Optional[User]:
        """Проверка валидности сессии"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("""
                SELECT u.* FROM users u
                JOIN sessions s ON u.id = s.user_id
                WHERE s.session_token = ? AND s.expires_at > ? AND u.is_active = TRUE
            """, (session_token, datetime.now().timestamp())).fetchone()
            
            if row:
                return User(
                    id=row['id'],
                    telegram_id=row['telegram_id'],
                    email=row['email'],
                    created_at=datetime.fromisoformat(row['created_at']),
                    is_active=bool(row['is_active'])
                )
            return None
    
    def delete_session(self, session_token: str):
        """Удаление сессии"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM sessions WHERE session_token = ?", (session_token,))
            conn.commit()
    
    def create_ai_agent(self, user_id: int, name: str, business_description: str, 
                        capabilities: str, tone: str = "дружелюбный") -> int:
        """Создание нового ИИ агента"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO ai_agents (user_id, name, business_description, capabilities, tone)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, name, business_description, capabilities, tone))
            
            conn.commit()
            return cursor.lastrowid
    
    def update_ai_agent(self, agent_id: int, **kwargs) -> bool:
        """Обновление ИИ агента"""
        allowed_fields = {
            'name', 'business_description', 'capabilities', 'tone', 
            'system_prompt', 'integrations_json', 'is_active'
        }
        
        update_fields = {k: v for k, v in kwargs.items() if k in allowed_fields}
        
        if not update_fields:
            return False
        
        with sqlite3.connect(self.db_path) as conn:
            set_clause = ", ".join([f"{k} = ?" for k in update_fields.keys()])
            values = list(update_fields.values()) + [agent_id]
            
            conn.execute(f"UPDATE ai_agents SET {set_clause} WHERE id = ?", values)
            conn.commit()
            return True
    
    def get_user_agents(self, user_id: int) -> List[AIAgent]:
        """Получение всех агентов пользователя"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT * FROM ai_agents 
                WHERE user_id = ? AND is_active = TRUE
                ORDER BY created_at DESC
            """, (user_id,)).fetchall()
            
            agents = []
            for row in rows:
                agents.append(AIAgent(
                    id=row['id'],
                    user_id=row['user_id'],
                    name=row['name'],
                    business_description=row['business_description'],
                    capabilities=row['capabilities'],
                    tone=row['tone'],
                    system_prompt=row['system_prompt'],
                    integrations=json.loads(row['integrations_json'] or '{}'),
                    created_at=datetime.fromisoformat(row['created_at']),
                    is_active=bool(row['is_active'])
                ))
            
            return agents
    
    def get_agent_by_id(self, agent_id: int, user_id: int) -> Optional[AIAgent]:
        """Получение агента по ID (с проверкой владельца)"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("""
                SELECT * FROM ai_agents 
                WHERE id = ? AND user_id = ? AND is_active = TRUE
            """, (agent_id, user_id)).fetchone()
            
            if row:
                return AIAgent(
                    id=row['id'],
                    user_id=row['user_id'],
                    name=row['name'],
                    business_description=row['business_description'],
                    capabilities=row['capabilities'],
                    tone=row['tone'],
                    system_prompt=row['system_prompt'],
                    integrations=json.loads(row['integrations_json'] or '{}'),
                    created_at=datetime.fromisoformat(row['created_at']),
                    is_active=bool(row['is_active'])
                )
            return None
    
    def add_document(self, agent_id: int, filename: str, file_path: str, file_type: str) -> int:
        """Добавление документа к агенту"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO documents (agent_id, filename, file_path, file_type)
                VALUES (?, ?, ?, ?)
            """, (agent_id, filename, file_path, file_type))
            
            conn.commit()
            return cursor.lastrowid
    
    def get_agent_documents(self, agent_id: int) -> List[Document]:
        """Получение всех документов агента"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT * FROM documents 
                WHERE agent_id = ? 
                ORDER BY uploaded_at DESC
            """, (agent_id,)).fetchall()
            
            documents = []
            for row in rows:
                documents.append(Document(
                    id=row['id'],
                    agent_id=row['agent_id'],
                    filename=row['filename'],
                    file_path=row['file_path'],
                    file_type=row['file_type'],
                    uploaded_at=datetime.fromisoformat(row['uploaded_at']),
                    is_processed=bool(row['is_processed'])
                ))
            
            return documents
    
    def mark_document_processed(self, document_id: int):
        """Отметить документ как обработанный"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("UPDATE documents SET is_processed = TRUE WHERE id = ?", (document_id,))
            conn.commit()
    
    def delete_document(self, document_id: int) -> bool:
        """Удаление документа"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM documents WHERE id = ?", (document_id,))
            conn.commit()
            return True


# Глобальный экземпляр базы данных
db = Database()
