# app.py
from __future__ import annotations
import os, hmac, hashlib, time, json, sqlite3
from pathlib import Path
from typing import Dict, Any, Optional
from urllib.parse import parse_qsl, unquote_plus

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Form
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware

# ---------- ENV ----------
load_dotenv("touch.env") or load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("TELEGRAM_TOKEN не найден в окружении")
ROOT = Path(__file__).parent
DB_PATH = ROOT / "state.db"
WEB_DIR = ROOT / "webapp"
UPLOADS_DIR = ROOT / "uploads"
WEB_DIR.mkdir(exist_ok=True)
UPLOADS_DIR.mkdir(exist_ok=True)

# ---------- App ----------
app = FastAPI(title="SynapserAI WebApp API")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

@app.get("/health")
async def health(): return {"ok": True}

def db():
    con = sqlite3.connect(DB_PATH)
    con.execute("""
        CREATE TABLE IF NOT EXISTS owners(
            user_id INTEGER PRIMARY KEY,
            business TEXT DEFAULT '',
            abilities TEXT DEFAULT '',
            tone TEXT DEFAULT 'дружелюбный',
            prompt TEXT DEFAULT '',
            integrations_json TEXT DEFAULT '{}',
            created_at INTEGER DEFAULT (strftime('%s','now'))
        )""")
    con.commit()
    return con

def validate_init_data(init_data: str) -> Dict[str, Any]:
    """HMAC‑проверка initData из Telegram Web App."""
    data = dict(parse_qsl(init_data, keep_blank_values=True))
    if "hash" not in data: raise HTTPException(401, "No hash")
    received_hash = data.pop("hash")

    secret = hashlib.sha256(BOT_TOKEN.encode()).digest()
    check_str = "\n".join(f"{k}={unquote_plus(v)}" for k, v in sorted(data.items()))
    calc = hmac.new(secret, check_str.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(received_hash, calc):
        raise HTTPException(401, "Bad hash")

    # необязательная защита по времени
    auth_date = int(data.get("auth_date", "0") or "0")
    if abs(time.time() - auth_date) > 60 * 60 * 24:
        raise HTTPException(401, "Expired auth_date")

    user = json.loads(data.get("user", "{}"))
    if "id" not in user: raise HTTPException(401, "No user.id")
    return user

# ---------- API: шаги мастера ----------
@app.post("/api/verify")
async def api_verify(request: Request):
    body = await request.json()
    user = validate_init_data(body.get("initData") or "")
    # авто‑создание записи
    with db() as con:
        con.execute(
            "INSERT OR IGNORE INTO owners(user_id) VALUES(?)", (user["id"],)
        ); con.commit()
    return {"ok": True, "user": {"id": user["id"], "first_name": user.get("first_name","")}}

@app.post("/api/save_basics")
async def api_save_basics(request: Request):
    p = await request.json()
    user = validate_init_data(p.get("initData") or "")
    business  = (p.get("business") or "").strip()
    abilities = (p.get("abilities") or "").strip()
    with db() as con:
        con.execute("UPDATE owners SET business=?, abilities=? WHERE user_id=?",
                    (business, abilities, user["id"]))
        con.commit()
    return {"ok": True}

@app.post("/api/save_tone")
async def api_save_tone(request: Request):
    p = await request.json()
    user = validate_init_data(p.get("initData") or "")
    tone = (p.get("tone") or "дружелюбный").strip()
    with db() as con:
        con.execute("UPDATE owners SET tone=? WHERE user_id=?", (tone, user["id"]))
        con.commit()
    return {"ok": True}

@app.post("/api/generate_prompt")
async def api_generate_prompt(request: Request):
    p = await request.json()
    user = validate_init_data(p.get("initData") or "")
    with db() as con:
        row = con.execute("SELECT business, abilities, tone FROM owners WHERE user_id=?",
                          (user["id"],)).fetchone()
    business, abilities, tone = row or ("", "", "дружелюбный")
    prompt = (
        f"Ты — ИИ-ассистент для бизнеса: {business}. "
        f"Тон общения: {tone}. "
        f"Основные задачи: {abilities}. "
        "Отвечай кратко, структурированно, уточняй детали, предлагай товары/услуги. "
        "Если чего-то не знаешь — вежливо уточни у клиента и предложи связаться с оператором."
    )
    with db() as con:
        con.execute("UPDATE owners SET prompt=? WHERE user_id=?", (prompt, user["id"]))
        con.commit()
    return {"ok": True, "prompt": prompt}

@app.get("/api/load_all")
async def api_load_all(initData: str):
    user = validate_init_data(initData)
    with db() as con:
        row = con.execute(
            "SELECT business, abilities, tone, prompt, integrations_json "
            "FROM owners WHERE user_id=?", (user["id"],)
        ).fetchone()
    if not row:
        return {"ok": True, "business":"", "abilities":"", "tone":"дружелюбный",
                "prompt":"", "integrations": {}}
    business, abilities, tone, prompt, integrations_json = row
    return {"ok": True, "business": business, "abilities": abilities, "tone": tone,
            "prompt": prompt, "integrations": json.loads(integrations_json or "{}")}

@app.post("/api/save_integrations")
async def api_save_integrations(request: Request):
    p = await request.json()
    user = validate_init_data(p.get("initData") or "")
    # сохраняем как есть (шифрование/хранилище секретов — на следующих этапах)
    integrations = p.get("integrations") or {}
    with db() as con:
        con.execute("UPDATE owners SET integrations_json=? WHERE user_id=?",
                    (json.dumps(integrations), user["id"]))
        con.commit()
    return {"ok": True}

@app.post("/api/upload_file")
async def api_upload_file(initData: str = Form(...), file: UploadFile = File(...)):
    user = validate_init_data(initData)
    name = f"u{user['id']}_{int(time.time())}_{file.filename}"
    (UPLOADS_DIR / name).write_bytes(await file.read())
    # Индексацию в RAG подключишь позже
    return {"ok": True, "saved_as": name}

# ---------- статика (WebApp) ----------
# ВАЖНО: монтируем в самом конце, чтобы /api/* не перехватывалось
app.mount("/", StaticFiles(directory=str(WEB_DIR), html=True), name="web")
