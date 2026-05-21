from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_active_project, get_client_ip, hash_ip, verify_api_key
from app.logger import get_logger
from app.schemas import OkResponse, PushSendRequest, PushSendResult, PushSubscribeRequest
from app.security.rate_limit import enforce_push_subscribe_rate_limit
from app.services import push_service

router = APIRouter(tags=["push"])
logger = get_logger(__name__)


@router.post("/api/push/subscribe", response_model=OkResponse)
def push_subscribe(
    body: PushSubscribeRequest,
    request: Request,
    db: Session = Depends(get_db),
    _: None = Depends(enforce_push_subscribe_rate_limit),
) -> OkResponse:
    project = get_active_project(db, body.project_key)
    push_service.subscribe_push(
        db,
        project,
        endpoint=body.endpoint,
        p256dh=body.keys.p256dh,
        auth=body.keys.auth,
        user_agent=request.headers.get("user-agent"),
        ip_hash=hash_ip(get_client_ip(request)),
    )
    logger.info("Push subscription saved for project %s", project.project_key)
    return OkResponse()


@router.post(
    "/api/push/send/{project_key}",
    response_model=PushSendResult,
    dependencies=[Depends(verify_api_key)],
)
def push_send(
    project_key: str,
    body: PushSendRequest,
    db: Session = Depends(get_db),
) -> PushSendResult:
    project = get_active_project(db, project_key)
    try:
        return push_service.send_push_to_project(
            db,
            project,
            title=body.title,
            body=body.body,
            url=body.url,
        )
    except RuntimeError as exc:
        logger.error("Push send unavailable for %s: %s", project_key, exc)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
