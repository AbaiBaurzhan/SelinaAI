"""
AI Agents Management Module for BotCraft
Управление ИИ агентами пользователей
"""

import json
import time
from typing import List, Optional, Dict, Any
from fastapi import HTTPException, Request, UploadFile, File, Form
from database import db, User, AIAgent, Document
from auth import get_current_user, get_optional_user
from channels.manager import ChannelManager
from pathlib import Path


class AgentManager:
    """Менеджер ИИ агентов"""
    
    def __init__(self, channel_manager: ChannelManager):
        self.channel_manager = channel_manager
    
    def create_agent(self, user: User, name: str, business_description: str, 
                    capabilities: str, tone: str = "дружелюбный") -> AIAgent:
        """Создание нового ИИ агента"""
        # Проверяем лимиты (максимум 5 агентов на пользователя)
        user_agents = db.get_user_agents(user.id)
        if len(user_agents) >= 5:
            raise HTTPException(status_code=400, detail="Maximum 5 agents allowed per user")
        
        # Создаем агента
        agent_id = db.create_ai_agent(
            user_id=user.id,
            name=name,
            business_description=business_description,
            capabilities=capabilities,
            tone=tone
        )
        
        # Получаем созданного агента
        agent = db.get_agent_by_id(agent_id, user.id)
        if not agent:
            raise HTTPException(status_code=500, detail="Failed to create agent")
        
        return agent
    
    def update_agent(self, user: User, agent_id: int, **kwargs) -> AIAgent:
        """Обновление ИИ агента"""
        # Проверяем, что агент принадлежит пользователю
        agent = db.get_agent_by_id(agent_id, user.id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Обновляем агента
        success = db.update_ai_agent(agent_id, **kwargs)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update agent")
        
        # Получаем обновленного агента
        updated_agent = db.get_agent_by_id(agent_id, user.id)
        return updated_agent
    
    def delete_agent(self, user: User, agent_id: int) -> bool:
        """Удаление ИИ агента"""
        # Проверяем, что агент принадлежит пользователю
        agent = db.get_agent_by_id(agent_id, user.id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Помечаем как неактивный (мягкое удаление)
        success = db.update_ai_agent(agent_id, is_active=False)
        return success
    
    def get_user_agents(self, user: User) -> List[AIAgent]:
        """Получение всех агентов пользователя"""
        return db.get_user_agents(user.id)
    
    def get_agent(self, user: User, agent_id: int) -> AIAgent:
        """Получение конкретного агента"""
        agent = db.get_agent_by_id(agent_id, user.id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        return agent
    
    def generate_system_prompt(self, agent: AIAgent) -> str:
        """Генерация системного промпта на основе настроек агента"""
        prompt = (
            f"Ты — ИИ-ассистент для бизнеса: {agent.business_description}. "
            f"Тон общения: {agent.tone}. "
            f"Основные задачи: {agent.capabilities}. "
            "Отвечай кратко, структурированно, уточняй детали, предлагай товары/услуги. "
            "Если чего-то не знаешь — вежливо уточни у клиента и предложи связаться с оператором."
        )
        return prompt
    
    def update_agent_prompt(self, user: User, agent_id: int, prompt: str) -> AIAgent:
        """Обновление системного промпта агента"""
        return self.update_agent(user, agent_id, system_prompt=prompt)
    
    def update_agent_integrations(self, user: User, agent_id: int, 
                                integrations: Dict[str, Any]) -> AIAgent:
        """Обновление интеграций агента"""
        # Валидируем интеграции
        valid_integrations = {}
        
        if "telegram" in integrations:
            telegram_config = integrations["telegram"]
            if telegram_config.get("enabled"):
                if not telegram_config.get("token"):
                    raise HTTPException(status_code=400, detail="Telegram token required when enabled")
                valid_integrations["telegram"] = telegram_config
        
        if "whatsapp" in integrations:
            whatsapp_config = integrations["whatsapp"]
            if whatsapp_config.get("enabled"):
                required_fields = ["access_token", "phone_number_id", "verify_token"]
                for field in required_fields:
                    if not whatsapp_config.get(field):
                        raise HTTPException(status_code=400, detail=f"WhatsApp {field} required when enabled")
                valid_integrations["whatsapp"] = whatsapp_config
        
        if "instagram" in integrations:
            instagram_config = integrations["instagram"]
            if instagram_config.get("enabled"):
                required_fields = ["access_token", "business_account_id", "page_id", "verify_token"]
                for field in required_fields:
                    if not instagram_config.get(field):
                        raise HTTPException(status_code=400, detail=f"Instagram {field} required when enabled")
                valid_integrations["instagram"] = instagram_config
        
        # Сохраняем интеграции
        integrations_json = json.dumps(valid_integrations)
        return self.update_agent(user, agent_id, integrations_json=integrations_json)
    
    def upload_document(self, user: User, agent_id: int, file: UploadFile) -> Document:
        """Загрузка документа для агента"""
        # Проверяем, что агент принадлежит пользователю
        agent = db.get_agent_by_id(agent_id, user.id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Проверяем тип файла
        allowed_types = ["pdf", "docx", "xlsx", "jpg", "jpeg", "png"]
        file_extension = file.filename.split(".")[-1].lower()
        
        if file_extension not in allowed_types:
            raise HTTPException(
                status_code=400, 
                detail=f"File type not allowed. Allowed: {', '.join(allowed_types)}"
            )
        
        # Генерируем уникальное имя файла
        timestamp = int(time.time())
        safe_filename = f"u{user.id}_a{agent_id}_{timestamp}_{file.filename}"
        
        # Сохраняем файл
        upload_dir = Path("uploads")
        upload_dir.mkdir(exist_ok=True)
        
        file_path = upload_dir / safe_filename
        with open(file_path, "wb") as f:
            content = file.file.read()
            f.write(content)
        
        # Добавляем запись в базу
        document_id = db.add_document(
            agent_id=agent_id,
            filename=file.filename,
            file_path=str(file_path),
            file_type=file_extension
        )
        
        # Получаем созданный документ
        documents = db.get_agent_documents(agent_id)
        for doc in documents:
            if doc.id == document_id:
                return doc
        
        raise HTTPException(status_code=500, detail="Failed to create document record")
    
    def get_agent_documents(self, user: User, agent_id: int) -> List[Document]:
        """Получение документов агента"""
        # Проверяем, что агент принадлежит пользователю
        agent = db.get_agent_by_id(agent_id, user.id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        return db.get_agent_documents(agent_id)
    
    def delete_document(self, user: User, document_id: int) -> bool:
        """Удаление документа"""
        # Получаем документ и проверяем права
        documents = db.get_agent_documents(user.id)
        document = None
        
        for doc in documents:
            if doc.id == document_id:
                document = doc
                break
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Удаляем файл
        try:
            Path(document.file_path).unlink(missing_ok=True)
        except:
            pass  # Игнорируем ошибки удаления файла
        
        # Удаляем запись из базы
        return db.delete_document(document_id)
    
    def test_agent_channels(self, user: User, agent_id: int) -> Dict[str, Any]:
        """Тестирование каналов агента"""
        agent = db.get_agent_by_id(agent_id, user.id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Получаем статус каналов
        channels_status = self.channel_manager.get_all_channels_status()
        
        # Проверяем интеграции агента
        agent_integrations = {}
        if agent.integrations:
            try:
                agent_integrations = json.loads(agent.integrations)
            except:
                agent_integrations = {}
        
        test_results = {}
        
        for channel_name, channel_status in channels_status.items():
            if channel_name in agent_integrations and agent_integrations[channel_name].get("enabled"):
                test_results[channel_name] = {
                    "status": "enabled",
                    "channel_active": channel_status["active"],
                    "config": agent_integrations[channel_name]
                }
            else:
                test_results[channel_name] = {
                    "status": "disabled",
                    "channel_active": channel_status["active"]
                }
        
        return {
            "agent_id": agent_id,
            "agent_name": agent.name,
            "channels_status": test_results,
            "overall_status": "active" if any(
                result["status"] == "enabled" and result["channel_active"] 
                for result in test_results.values()
            ) else "inactive"
        }


# Глобальный экземпляр менеджера агентов
agent_manager = None


def get_agent_manager(channel_manager: ChannelManager) -> AgentManager:
    """Получение менеджера агентов"""
    global agent_manager
    if agent_manager is None:
        agent_manager = AgentManager(channel_manager)
    return agent_manager
