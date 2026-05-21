import hashlib
import secrets

from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.logger import get_logger
from app.models import Project

logger = get_logger(__name__)

security = HTTPBasic(auto_error=False)


def hash_ip(ip: str | None) -> str | None:
    if not ip:
        return None
    return hashlib.sha256(ip.encode("utf-8")).hexdigest()[:32]


def get_client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


def verify_api_key(x_api_key: str | None = Header(default=None, alias="X-API-Key")) -> None:
    settings = get_settings()
    if not settings.api_key:
        if settings.debug:
            return
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="API_KEY is not configured",
        )
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
        )
    if not secrets.compare_digest(x_api_key, settings.api_key):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key",
        )


def verify_dashboard_access(
    request: Request,
    credentials: HTTPBasicCredentials | None = Depends(security),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> None:
    settings = get_settings()

    if x_api_key and settings.api_key and secrets.compare_digest(x_api_key, settings.api_key):
        return

    if credentials and settings.dashboard_password:
        username_ok = secrets.compare_digest(credentials.username, settings.dashboard_username)
        password_ok = secrets.compare_digest(credentials.password, settings.dashboard_password)
        if username_ok and password_ok:
            return

    if settings.debug and not settings.dashboard_password and not settings.api_key:
        return

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
        headers={"WWW-Authenticate": "Basic"},
    )


def get_active_project(db: Session, project_key: str) -> Project:
    project = (
        db.query(Project)
        .filter(Project.project_key == project_key, Project.is_active.is_(True))
        .first()
    )
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project
