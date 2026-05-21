from fastapi import APIRouter

from app.routes import dashboard, public, push, stats

api_router = APIRouter()
api_router.include_router(public.router)
api_router.include_router(push.router)
api_router.include_router(stats.router)
api_router.include_router(dashboard.router)
