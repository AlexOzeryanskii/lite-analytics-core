import json
from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.logger import get_logger
from app.models import Event, Project, PushSubscription
from app.schemas import ProjectStats, RecentEvent, TopItem

logger = get_logger(__name__)


def track_event(
    db: Session,
    project: Project,
    *,
    event_type: str,
    path: str,
    title: str | None = None,
    referrer: str | None = None,
    user_agent: str | None = None,
    ip_hash: str | None = None,
    session_id: str | None = None,
    visitor_id: str | None = None,
    screen_width: int | None = None,
    screen_height: int | None = None,
    language: str | None = None,
    timezone: str | None = None,
    payload: dict | None = None,
) -> Event:
    event = Event(
        project_id=project.id,
        event_type=event_type,
        path=path,
        title=title,
        referrer=referrer,
        user_agent=user_agent,
        ip_hash=ip_hash,
        session_id=session_id,
        visitor_id=visitor_id,
        screen_width=screen_width,
        screen_height=screen_height,
        language=language,
        timezone=timezone,
        payload_json=json.dumps(payload) if payload else None,
    )
    db.add(event)
    try:
        db.commit()
        db.refresh(event)
    except SQLAlchemyError as exc:
        db.rollback()
        logger.error("Failed to store event for project %s: %s", project.project_key, exc)
        raise
    return event


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def get_project_stats(db: Session, project: Project) -> ProjectStats:
    now = _utc_now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=7)

    base = db.query(Event).filter(Event.project_id == project.id)

    total_events = base.count()
    unique_visitors = (
        db.query(func.count(func.distinct(Event.visitor_id)))
        .filter(Event.project_id == project.id, Event.visitor_id.isnot(None))
        .scalar()
        or 0
    )
    events_today = base.filter(Event.created_at >= today_start).count()
    events_last_7_days = base.filter(Event.created_at >= week_start).count()

    top_paths = [
        TopItem(value=row.path, count=row.count)
        for row in (
            db.query(Event.path, func.count(Event.id).label("count"))
            .filter(Event.project_id == project.id)
            .group_by(Event.path)
            .order_by(func.count(Event.id).desc())
            .limit(10)
            .all()
        )
    ]

    top_referrers = [
        TopItem(value=row.referrer or "(direct)", count=row.count)
        for row in (
            db.query(Event.referrer, func.count(Event.id).label("count"))
            .filter(Event.project_id == project.id, Event.referrer.isnot(None), Event.referrer != "")
            .group_by(Event.referrer)
            .order_by(func.count(Event.id).desc())
            .limit(10)
            .all()
        )
    ]

    events_by_type = [
        TopItem(value=row.event_type, count=row.count)
        for row in (
            db.query(Event.event_type, func.count(Event.id).label("count"))
            .filter(Event.project_id == project.id)
            .group_by(Event.event_type)
            .order_by(func.count(Event.id).desc())
            .all()
        )
    ]

    recent_rows = (
        db.query(Event)
        .filter(Event.project_id == project.id)
        .order_by(Event.created_at.desc())
        .limit(20)
        .all()
    )
    recent_events = [
        RecentEvent(
            id=e.id,
            event_type=e.event_type,
            path=e.path,
            title=e.title,
            referrer=e.referrer,
            visitor_id=e.visitor_id,
            session_id=e.session_id,
            created_at=e.created_at,
        )
        for e in recent_rows
    ]

    active_push = (
        db.query(PushSubscription)
        .filter(
            PushSubscription.project_id == project.id,
            PushSubscription.is_active.is_(True),
        )
        .count()
    )

    return ProjectStats(
        project_key=project.project_key,
        project_name=project.name,
        total_events=total_events,
        unique_visitors=unique_visitors,
        events_today=events_today,
        events_last_7_days=events_last_7_days,
        active_push_subscriptions=active_push,
        top_paths=top_paths,
        top_referrers=top_referrers,
        events_by_type=events_by_type,
        recent_events=recent_events,
    )
