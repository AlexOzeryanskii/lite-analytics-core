from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_active_project, verify_api_key
from app.schemas import ProjectStats
from app.services import analytics_service

router = APIRouter(tags=["stats"])


@router.get(
    "/api/stats/{project_key}",
    response_model=ProjectStats,
    dependencies=[Depends(verify_api_key)],
)
def project_stats(project_key: str, db: Session = Depends(get_db)) -> ProjectStats:
    project = get_active_project(db, project_key)
    return analytics_service.get_project_stats(db, project)
