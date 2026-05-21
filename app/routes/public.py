from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_active_project, get_client_ip, hash_ip
from app.logger import get_logger
from app.schemas import HealthResponse, OkResponse, TrackRequest
from app.security.rate_limit import enforce_track_rate_limit
from app.services import analytics_service
from app.services.bot_detector import is_bot
from app.version import APP_VERSION

router = APIRouter(tags=["public"])
logger = get_logger(__name__)


@router.get("/health", response_model=HealthResponse)
def health(db: Session = Depends(get_db)) -> HealthResponse:
    database = "ok"
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:
        database = "error"
        logger.error("Database health check failed: %s", exc)

    return HealthResponse(
        status="ok" if database == "ok" else "degraded",
        database=database,
        version=APP_VERSION,
        time=datetime.now(timezone.utc).isoformat(),
    )


@router.post("/api/track", response_model=OkResponse)
def track(
    body: TrackRequest,
    request: Request,
    db: Session = Depends(get_db),
    _: None = Depends(enforce_track_rate_limit),
) -> OkResponse:
    user_agent = request.headers.get("user-agent")
    if is_bot(user_agent):
        logger.warning("Bot request ignored: %s", user_agent)
        return OkResponse(ok=True, ignored="bot")

    project = get_active_project(db, body.project_key)
    analytics_service.track_event(
        db,
        project,
        event_type=body.event_type,
        path=body.path,
        title=body.title,
        referrer=body.referrer,
        user_agent=user_agent,
        ip_hash=hash_ip(get_client_ip(request)),
        session_id=body.session_id,
        visitor_id=body.visitor_id,
        screen_width=body.screen_width,
        screen_height=body.screen_height,
        language=body.language,
        timezone=body.timezone,
        payload=body.payload,
    )
    return OkResponse()
