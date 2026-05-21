import json
from datetime import datetime, timezone

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.config import get_settings
from app.logger import get_logger
from app.models import Project, PushSubscription
from app.schemas import PushSendResult

logger = get_logger(__name__)


def subscribe_push(
    db: Session,
    project: Project,
    *,
    endpoint: str,
    p256dh: str,
    auth: str,
    user_agent: str | None = None,
    ip_hash: str | None = None,
) -> PushSubscription:
    subscription = db.query(PushSubscription).filter(PushSubscription.endpoint == endpoint).first()

    if subscription:
        subscription.project_id = project.id
        subscription.p256dh = p256dh
        subscription.auth = auth
        subscription.user_agent = user_agent
        subscription.ip_hash = ip_hash
        subscription.is_active = True
        subscription.fail_count = 0
        subscription.last_error = None
        subscription.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    else:
        subscription = PushSubscription(
            project_id=project.id,
            endpoint=endpoint,
            p256dh=p256dh,
            auth=auth,
            user_agent=user_agent,
            ip_hash=ip_hash,
            is_active=True,
            fail_count=0,
        )
        db.add(subscription)

    try:
        db.commit()
        db.refresh(subscription)
    except SQLAlchemyError as exc:
        db.rollback()
        logger.error("Failed to save push subscription for project %s: %s", project.project_key, exc)
        raise
    return subscription


def _webpush_available() -> bool:
    settings = get_settings()
    if not settings.vapid_private_key or not settings.vapid_public_key:
        return False
    try:
        import pywebpush  # noqa: F401
    except ImportError:
        return False
    return True


def send_push_to_project(
    db: Session,
    project: Project,
    *,
    title: str,
    body: str,
    url: str | None = None,
) -> PushSendResult:
    settings = get_settings()

    if not _webpush_available():
        raise RuntimeError(
            "Web push is not configured. Install pywebpush and set VAPID_PUBLIC_KEY / VAPID_PRIVATE_KEY."
        )

    from pywebpush import WebPushException, webpush

    subscriptions = (
        db.query(PushSubscription)
        .filter(
            PushSubscription.project_id == project.id,
            PushSubscription.is_active.is_(True),
        )
        .all()
    )

    payload = json.dumps({"title": title, "body": body, "url": url or "/"})
    sent = 0
    failed = 0
    deactivated = 0
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    for sub in subscriptions:
        try:
            webpush(
                subscription_info={
                    "endpoint": sub.endpoint,
                    "keys": {"p256dh": sub.p256dh, "auth": sub.auth},
                },
                data=payload,
                vapid_private_key=settings.vapid_private_key,
                vapid_claims={"sub": settings.vapid_claims_sub},
            )
            sub.last_success_at = now
            sub.last_error = None
            sub.fail_count = 0
            sent += 1
        except WebPushException as exc:
            failed += 1
            sub.fail_count += 1
            sub.last_error = str(exc)[:1000]
            if sub.fail_count >= settings.push_max_fail_count:
                sub.is_active = False
                deactivated += 1
            logger.error("Push failed for subscription %s: %s", sub.id, exc)
        except Exception as exc:
            failed += 1
            sub.fail_count += 1
            sub.last_error = str(exc)[:1000]
            if sub.fail_count >= settings.push_max_fail_count:
                sub.is_active = False
                deactivated += 1
            logger.error("Push error for subscription %s: %s", sub.id, exc)

        sub.updated_at = now

    try:
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        logger.error("Failed to commit push send results for project %s: %s", project.project_key, exc)
        raise
    return PushSendResult(ok=True, sent=sent, failed=failed, deactivated=deactivated)
