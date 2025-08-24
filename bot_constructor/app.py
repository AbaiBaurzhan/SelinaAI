# app.py - SelinaAI Multi-Channel API
from __future__ import annotations
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, List

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Form, Depends, Response
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer

# Импортируем новые модули
from database import db, User, AIAgent, Document
from auth import auth_manager, get_current_user, get_optional_user
from agents import get_agent_manager
from channels.manager import ChannelManager
from channels.base import Message, Response as ChannelResponse, MessageType

# ---------- ENV ----------
load_dotenv("touch.env") or load_dotenv()

# Проверяем обязательные переменные
BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("TELEGRAM_TOKEN не найден в окружении")

ROOT = Path(__file__).parent
WEB_DIR = ROOT / "webapp"
UPLOADS_DIR = ROOT / "uploads"
WEB_DIR.mkdir(exist_ok=True)
UPLOADS_DIR.mkdir(exist_ok=True)

# ---------- Конфигурация каналов ----------
CHANNELS_CONFIG = {
    "webhook_base_url": os.getenv("WEBAPP_URL", "https://127.0.0.1:8000"),
    "telegram": {
        "token": os.getenv("TELEGRAM_TOKEN"),
        "webhook_url": os.getenv("WEBAPP_URL", "https://127.0.0.1:8000"),
        "webhook_mode": os.getenv("TELEGRAM_WEBHOOK_MODE", "false").lower() == "true"
    },
    "whatsapp": {
        "access_token": os.getenv("WHATSAPP_ACCESS_TOKEN"),
        "phone_number_id": os.getenv("WHATSAPP_PHONE_NUMBER_ID"),
        "verify_token": os.getenv("WHATSAPP_VERIFY_TOKEN"),
        "app_secret": os.getenv("WHATSAPP_APP_SECRET")
    },
    "instagram": {
        "access_token": os.getenv("INSTAGRAM_ACCESS_TOKEN"),
        "instagram_business_account_id": os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID"),
        "page_id": os.getenv("INSTAGRAM_PAGE_ID"),
        "verify_token": os.getenv("INSTAGRAM_VERIFY_TOKEN")
    }
}

# ---------- App ----------
app = FastAPI(
    title="SelinaAI Multi-Channel API",
    description="Платформа для создания ИИ-ассистентов с поддержкой Telegram, WhatsApp и Instagram",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware, 
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],
)

# Инициализируем менеджер каналов
channel_manager = ChannelManager(CHANNELS_CONFIG)

# Инициализируем менеджер агентов
agent_manager = get_agent_manager(channel_manager)

# ---------- Dependency для получения менеджера агентов ----------
def get_agent_manager_dep() -> Any:
    return agent_manager

# ---------- Базовые эндпоинты ----------
@app.get("/health")
async def health(): 
    return {"ok": True, "service": "SelinaAI Multi-Channel API", "version": "2.0.0"}

@app.get("/healthz")
async def healthz(): 
    """Health check endpoint for Google Cloud Run"""
    return {"status": "healthy", "service": "SelinaAI", "version": "2.0.0"}

@app.get("/")
async def root():
    """Главная страница"""
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>SelinaAI API</title>
        <meta charset="utf-8">
    </head>
    <body>
        <h1>🚀 SelinaAI Multi-Channel API</h1>
        <p>Платформа для создания ИИ-ассистентов</p>
        <p><a href="/docs">📚 API Документация</a></p>
        <p><a href="/webapp">🌐 WebApp Интерфейс</a></p>
    </body>
    </html>
    """)

# ---------- API авторизации ----------
@app.post("/api/auth/telegram")
async def auth_telegram(request: Request):
    """Авторизация через Telegram WebApp"""
    try:
        body = await request.json()
        init_data = body.get("initData")
        
        if not init_data:
            raise HTTPException(status_code=400, detail="initData required")
        
        # Аутентифицируем пользователя
        user = auth_manager.authenticate_telegram_user(init_data)
        
        # Создаем сессию
        session_token = auth_manager.create_session(user)
        
        # Создаем JWT токен
        access_token = auth_manager.create_access_token(user)
        
        return {
            "ok": True,
            "user": {
                "id": user.id,
                "telegram_id": user.telegram_id,
                "email": user.email,
                "created_at": user.created_at.isoformat()
            },
            "session_token": session_token,
            "access_token": access_token
        }
        
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

@app.post("/api/auth/email")
async def auth_email(request: Request):
    """Авторизация по email и паролю"""
    try:
        body = await request.json()
        email = body.get("email")
        password = body.get("password")
        
        if not email or not password:
            raise HTTPException(status_code=400, detail="Email and password required")
        
        # Аутентифицируем пользователя
        user = auth_manager.authenticate_email_user(email, password)
        
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Создаем сессию
        session_token = auth_manager.create_session(user)
        
        # Создаем JWT токен
        access_token = auth_manager.create_access_token(user)
        
        return {
            "ok": True,
            "user": {
                "id": user.id,
                "telegram_id": user.telegram_id,
                "email": user.email,
                "created_at": user.created_at.isoformat()
            },
            "session_token": session_token,
            "access_token": access_token
        }
        
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

@app.post("/api/auth/logout")
async def logout(request: Request):
    """Выход пользователя"""
    try:
        # Получаем токен сессии из cookie
        session_token = request.cookies.get("session_token")
        
        if session_token:
            auth_manager.logout(session_token)
        
        response = JSONResponse({"ok": True, "message": "Logged out successfully"})
        response.delete_cookie("session_token")
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---------- API управления агентами ----------
@app.get("/api/agents")
async def get_agents(user: User = Depends(get_current_user)):
    """Получение всех агентов пользователя"""
    try:
        agents = agent_manager.get_user_agents(user)
        return {
            "ok": True,
            "agents": [
                {
                    "id": agent.id,
                    "name": agent.name,
                    "business_description": agent.business_description,
                    "capabilities": agent.capabilities,
                    "tone": agent.tone,
                    "system_prompt": agent.system_prompt,
                    "integrations": json.loads(agent.integrations) if agent.integrations else {},
                    "created_at": agent.created_at.isoformat(),
                    "is_active": agent.is_active
                }
                for agent in agents
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/agents")
async def create_agent(
    request: Request,
    user: User = Depends(get_current_user),
    agent_manager_dep: Any = Depends(get_agent_manager_dep)
):
    """Создание нового ИИ агента"""
    try:
        body = await request.json()
        name = body.get("name")
        business_description = body.get("business_description")
        capabilities = body.get("capabilities")
        tone = body.get("tone", "дружелюбный")
        
        if not all([name, business_description, capabilities]):
            raise HTTPException(status_code=400, detail="Name, business_description and capabilities required")
        
        # Создаем агента
        agent = agent_manager_dep.create_agent(
            user=user,
            name=name,
            business_description=business_description,
            capabilities=capabilities,
            tone=tone
        )
        
        return {
            "ok": True,
            "agent": {
                "id": agent.id,
                "name": agent.name,
                "business_description": agent.business_description,
                "capabilities": agent.capabilities,
                "tone": agent.tone,
                "created_at": agent.created_at.isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/agents/{agent_id}")
async def get_agent(
    agent_id: int,
    user: User = Depends(get_current_user),
    agent_manager_dep: Any = Depends(get_agent_manager_dep)
):
    """Получение конкретного агента"""
    try:
        agent = agent_manager_dep.get_agent(user, agent_id)
        
        return {
            "ok": True,
            "agent": {
                "id": agent.id,
                "name": agent.name,
                "business_description": agent.business_description,
                "capabilities": agent.capabilities,
                "tone": agent.tone,
                "system_prompt": agent.system_prompt,
                "integrations": agent.integrations,
                "created_at": agent.created_at.isoformat(),
                "is_active": agent.is_active
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/agents/{agent_id}")
async def update_agent(
    agent_id: int,
    request: Request,
    user: User = Depends(get_current_user),
    agent_manager_dep: Any = Depends(get_agent_manager_dep)
):
    """Обновление ИИ агента"""
    try:
        body = await request.json()
        
        # Обновляем агента
        updated_agent = agent_manager_dep.update_agent(user, agent_id, **body)
        
        return {
            "ok": True,
            "agent": {
                "id": updated_agent.id,
                "name": updated_agent.name,
                "business_description": updated_agent.business_description,
                "capabilities": updated_agent.capabilities,
                "tone": updated_agent.tone,
                "system_prompt": updated_agent.system_prompt,
                "integrations": json.loads(updated_agent.integrations) if updated_agent.integrations else {},
                "updated_at": updated_agent.created_at.isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/agents/{agent_id}")
async def delete_agent(
    agent_id: int,
    user: User = Depends(get_current_user),
    agent_manager_dep: Any = Depends(get_agent_manager_dep)
):
    """Удаление ИИ агента"""
    try:
        success = agent_manager_dep.delete_agent(user, agent_id)
        
        if success:
            return {"ok": True, "message": "Agent deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete agent")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---------- API для промптов ----------
@app.post("/api/agents/{agent_id}/generate_prompt")
async def generate_prompt(
    agent_id: int,
    user: User = Depends(get_current_user),
    agent_manager_dep: Any = Depends(get_agent_manager_dep)
):
    """Генерация системного промпта для агента"""
    try:
        # Получаем агента
        agent = agent_manager_dep.get_agent(user, agent_id)
        
        # Генерируем промпт
        prompt = agent_manager_dep.generate_system_prompt(agent)
        
        # Обновляем агента
        updated_agent = agent_manager_dep.update_agent_prompt(user, agent_id, prompt)
        
        return {
            "ok": True,
            "prompt": prompt,
            "agent_id": agent_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---------- API для интеграций ----------
@app.put("/api/agents/{agent_id}/integrations")
async def update_integrations(
    agent_id: int,
    request: Request,
    user: User = Depends(get_current_user),
    agent_manager_dep: Any = Depends(get_agent_manager_dep)
):
    """Обновление интеграций агента"""
    try:
        body = await request.json()
        integrations = body.get("integrations", {})
        
        # Обновляем интеграции
        updated_agent = agent_manager_dep.update_agent_integrations(user, agent_id, integrations)
        
        return {
            "ok": True,
            "integrations": updated_agent.integrations,
            "agent_id": agent_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---------- API для документов ----------
@app.post("/api/agents/{agent_id}/documents")
async def upload_document(
    agent_id: int,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    agent_manager_dep: Any = Depends(get_agent_manager_dep)
):
    """Загрузка документа для агента"""
    try:
        # Загружаем документ
        document = agent_manager_dep.upload_document(user, agent_id, file)
        
        return {
            "ok": True,
            "document": {
                "id": document.id,
                "filename": document.filename,
                "file_type": document.file_type,
                "uploaded_at": document.uploaded_at.isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/agents/{agent_id}/documents")
async def get_agent_documents(
    agent_id: int,
    user: User = Depends(get_current_user),
    agent_manager_dep: Any = Depends(get_agent_manager_dep)
):
    """Получение документов агента"""
    try:
        documents = agent_manager_dep.get_agent_documents(user, agent_id)
        
        return {
            "ok": True,
            "documents": [
                {
                    "id": doc.id,
                    "filename": doc.filename,
                    "file_type": doc.file_type,
                    "uploaded_at": doc.uploaded_at.isoformat(),
                    "is_processed": doc.is_processed
                }
                for doc in documents
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---------- API для тестирования каналов ----------
@app.get("/api/agents/{agent_id}/test_channels")
async def test_agent_channels(
    agent_id: int,
    user: User = Depends(get_current_user),
    agent_manager_dep: Any = Depends(get_agent_manager_dep)
):
    """Тестирование каналов агента"""
    try:
        results = agent_manager_dep.test_agent_channels(user, agent_id)
        return {"ok": True, **results}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---------- API для каналов ----------
@app.get("/channels/status")
async def get_channels_status():
    """Получение статуса всех каналов"""
    return {
        "ok": True,
        "channels": channel_manager.get_all_channels_status(),
        "active_channels": channel_manager.get_active_channels()
    }

@app.post("/channels/start")
async def start_channels():
    """Запуск всех каналов"""
    success = await channel_manager.start_all_channels()
    return {
        "ok": success,
        "message": "Каналы запущены" if success else "Ошибка запуска каналов"
    }

@app.post("/channels/stop")
async def stop_channels():
    """Остановка всех каналов"""
    success = await channel_manager.stop_all_channels()
    return {
        "ok": success,
        "message": "Каналы остановлены" if success else "Ошибка остановки каналов"
    }

# ---------- Webhook эндпоинты для каналов ----------
@app.get("/webhook/telegram")
async def telegram_webhook_verify(request: Request):
    """Верификация webhook Telegram"""
    params = dict(request.query_params)
    if await channel_manager.verify_webhook("telegram", params):
        return JSONResponse(content=params.get("hub.challenge", ""))
    else:
        raise HTTPException(status_code=400, detail="Webhook verification failed")

@app.post("/webhook/telegram")
async def telegram_webhook(request: Request):
    """Обработка webhook Telegram"""
    try:
        data = await request.json()
        response = await channel_manager.process_message("telegram", data)
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/webhook/whatsapp")
async def whatsapp_webhook_verify(request: Request):
    """Верификация webhook WhatsApp"""
    params = dict(request.query_params)
    if await channel_manager.verify_webhook("whatsapp", params):
        return JSONResponse(content=params.get("hub.challenge", ""))
    else:
        raise HTTPException(status_code=400, detail="Webhook verification failed")

@app.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request):
    """Обработка webhook WhatsApp"""
    try:
        data = await request.json()
        response = await channel_manager.process_message("whatsapp", data)
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/webhook/instagram")
async def instagram_webhook_verify(request: Request):
    """Верификация webhook Instagram"""
    params = dict(request.query_params)
    if await channel_manager.verify_webhook("instagram", params):
        return JSONResponse(content=params.get("hub.challenge", ""))
    else:
        raise HTTPException(status_code=400, detail="Webhook verification failed")

@app.post("/webhook/instagram")
async def instagram_webhook(request: Request):
    """Обработка webhook Instagram"""
    try:
        data = await request.json()
        response = await channel_manager.process_message("instagram", data)
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---------- API для отправки сообщений ----------
@app.post("/api/send_message")
async def send_message(request: Request):
    """Отправка сообщения в конкретный канал"""
    try:
        data = await request.json()
        channel = data.get("channel")
        chat_id = data.get("chat_id")
        content = data.get("content")
        
        if not all([channel, chat_id, content]):
            raise HTTPException(status_code=400, detail="Missing required fields")
        
        response = ChannelResponse(
            chat_id=chat_id,
            content=content,
            message_type=MessageType.TEXT
        )
        
        success = await channel_manager.send_message(channel, response)
        return {"ok": success, "channel": channel}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/send_message_all")
async def send_message_all_channels(request: Request):
    """Отправка сообщения во все активные каналы"""
    try:
        data = await request.json()
        chat_id = data.get("chat_id")
        content = data.get("content")
        
        if not all([chat_id, content]):
            raise HTTPException(status_code=400, detail="Missing required fields")
        
        response = ChannelResponse(
            chat_id=chat_id,
            content=content,
            message_type=MessageType.TEXT
        )
        
        results = await channel_manager.send_message_all_channels(response)
        return {"ok": True, "results": results}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---------- Статика (WebApp) ----------
app.mount("/webapp", StaticFiles(directory=str(WEB_DIR), html=True), name="webapp")

# ---------- Startup и Shutdown события ----------
@app.on_event("startup")
async def startup_event():
    """Запуск при старте FastAPI"""
    try:
        # Запускаем все каналы
        await channel_manager.start_all_channels()
        print("🚀 SelinaAI Multi-Channel API v2.0 запущен")
        print("📱 Поддержка: Telegram, WhatsApp, Instagram")
        print("🔐 Система авторизации: активна")
        print("🤖 Управление агентами: готово")
    except Exception as e:
        print(f"❌ Ошибка запуска каналов: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Остановка при завершении FastAPI"""
    try:
        # Останавливаем все каналы
        await channel_manager.stop_all_channels()
        print("🛑 SelinaAI Multi-Channel API остановлен")
    except Exception as e:
        print(f"❌ Ошибка остановки каналов: {e}")
