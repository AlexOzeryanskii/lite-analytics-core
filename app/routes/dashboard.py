from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_active_project, verify_dashboard_access
from app.services import analytics_service

router = APIRouter(tags=["dashboard"])

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get(
    "/dashboard/{project_key}",
    response_class=HTMLResponse,
    dependencies=[Depends(verify_dashboard_access)],
)
def dashboard(
    request: Request,
    project_key: str,
    db: Session = Depends(get_db),
):
    project = get_active_project(db, project_key)
    stats = analytics_service.get_project_stats(db, project)
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={"stats": stats},
    )
