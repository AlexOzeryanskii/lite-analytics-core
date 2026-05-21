import os
import json
import sqlite3
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any
from pydantic import BaseModel
from fastapi import FastAPI, Request, status, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

DB_PATH = "analytics.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.execute("PRAGMA synchronous=NORMAL;")

    # 1. Таблица проектов
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS projects
                   (
                       id
                       TEXT
                       PRIMARY
                       KEY,
                       name
                       TEXT
                       NOT
                       NULL,
                       created_at
                       TIMESTAMP
                       DEFAULT
                       CURRENT_TIMESTAMP
                   )
                   """)

    # 2. Таблица событий (Аналитика)
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS events
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       project_id
                       TEXT
                       NOT
                       NULL,
                       session_id
                       TEXT
                       NOT
                       NULL,
                       event_type
                       TEXT
                       NOT
                       NULL,
                       page_url
                       TEXT,
                       referrer
                       TEXT,
                       screen_resolution
                       TEXT,
                       payload
                       TEXT,
                       ip_address
                       TEXT,
                       created_at
                       TIMESTAMP
                       DEFAULT
                       CURRENT_TIMESTAMP
                   )
                   """)

    # 3. Новая таблица: Сборщик Push-подписок (Твоя база контактов)
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS push_subscriptions
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       project_id
                       TEXT
                       NOT
                       NULL,
                       session_id
                       TEXT
                       NOT
                       NULL,
                       subscription_json
                       TEXT
                       NOT
                       NULL,
                       created_at
                       TIMESTAMP
                       DEFAULT
                       CURRENT_TIMESTAMP,
                       UNIQUE
                   (
                       project_id,
                       session_id
                   )
                       )
                   """)

    cursor.execute("SELECT COUNT(*) FROM projects")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO projects (id, name) VALUES ('test_project', 'Мой Тестовый Сайт')")

    conn.commit()
    conn.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="LiteAnalytics & PushFort Core", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class EventModel(BaseModel):
    project_id: str
    session_id: str
    event_type: str
    page_url: Optional[str] = None
    referrer: Optional[str] = None
    screen_resolution: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None


class PushSubscribeModel(BaseModel):
    project_id: str
    session_id: str
    subscription: Dict[str, Any]


# --- API СБОРА АНАЛИТИКИ ---
@app.post("/api/track", status_code=status.HTTP_201_CREATED)
async def track_event(event: EventModel, request: Request):
    ip_address = request.client.host if request.client else "unknown"
    payload_str = json.dumps(event.payload) if event.payload else None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
                       INSERT INTO events (project_id, session_id, event_type, page_url, referrer, screen_resolution,
                                           payload, ip_address)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                       """, (event.project_id, event.session_id, event.event_type, event.page_url, event.referrer,
                             event.screen_resolution, payload_str, ip_address))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Ошибка записи аналитики: {e}")
    return {"status": "ok"}


# --- API СБОРА PUSH-ПОДПИСОК (ПЫЛЕСОС ТОКЕНОВ) ---
@app.post("/api/push/subscribe", status_code=status.HTTP_201_CREATED)
async def subscribe_push(data: PushSubscribeModel):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        # Сохраняем или обновляем токен устройства
        cursor.execute("""
                       INSERT INTO push_subscriptions (project_id, session_id, subscription_json)
                       VALUES (?, ?, ?) ON CONFLICT(project_id, session_id) DO
                       UPDATE SET subscription_json = excluded.subscription_json
                       """, (data.project_id, data.session_id, json.dumps(data.subscription)))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Ошибка сохранения пуш-подписки: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    return {"status": "subscribed"}


# --- API СТАТИСТИКИ ДЛЯ АДМИНКИ ---
@app.get("/api/stats/{project_id}")
async def get_project_stats(project_id: str, days: int = 7):
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM projects WHERE id = ?", (project_id,))
        p_row = cursor.fetchone()
        if not p_row:
            raise HTTPException(status_code=404, detail="Project not found")

        # Считаем пуши
        cursor.execute("SELECT COUNT(*) FROM push_subscriptions WHERE project_id = ?", (project_id,))
        total_pushes = cursor.fetchone()[0]

        stats = {
            "project_name": p_row["name"],
            "total_views": 0,
            "unique_sessions": 0,
            "total_push_subscribers": total_pushes,
            "by_date": [],
            "top_pages": [],
            "top_referrers": []
        }

        cursor.execute(
            "SELECT COUNT(*) as total_views, COUNT(DISTINCT session_id) as unique_sessions FROM events WHERE project_id = ? AND created_at >= datetime('now', ?)",
            (project_id, f"-{days} days"))
        m_row = cursor.fetchone()
        if m_row:
            stats["total_views"] = m_row["total_views"] or 0
            stats["unique_sessions"] = m_row["unique_sessions"] or 0

        cursor.execute(
            "SELECT date(created_at) as event_date, COUNT(*) as views, COUNT(DISTINCT session_id) as uniques FROM events WHERE project_id = ? AND created_at >= datetime('now', ?) GROUP BY event_date ORDER BY event_date ASC",
            (project_id, f"-{days} days"))
        stats["by_date"] = [dict(row) for row in cursor.fetchall()]

        conn.close()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- РАЗДАЧА ФРОНТЕНДА И СЕРВИС-ВОРКЕРА ---
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/service-worker.js")
async def read_service_worker():
    # Отдаем файл из папки static, но так, чтобы он думал, что лежит в корне сайта
    return FileResponse("static/service-worker.js", media_type="application/javascript")


@app.get("/")
async def read_index():
    return FileResponse("static/index.html")

@app.get("/favicon.ico", status_code=status.HTTP_204_NO_CONTENT)
async def favicon():
    return