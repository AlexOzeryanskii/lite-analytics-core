#!/usr/bin/env python3
"""Create a new analytics project in the database."""

import argparse
import sys

from app.db import SessionLocal, init_db
from app.logger import get_logger, setup_logging
from app.models import Project

logger = get_logger(__name__)


def main() -> int:
    setup_logging()

    parser = argparse.ArgumentParser(description="Create a Lite Analytics project")
    parser.add_argument("--name", required=True, help="Project display name")
    parser.add_argument("--domain", default=None, help="Primary domain, e.g. example.com")
    parser.add_argument("--key", required=True, help="Public project key used in tracker.js")
    args = parser.parse_args()

    init_db()
    db = SessionLocal()

    try:
        existing = db.query(Project).filter(Project.project_key == args.key).first()
        if existing:
            logger.warning("Project with key '%s' already exists (id=%s)", args.key, existing.id)
            return 1

        project = Project(
            project_key=args.key,
            name=args.name,
            domain=args.domain,
            is_active=True,
        )
        db.add(project)
        db.commit()
        db.refresh(project)

        logger.info(
            "Project created: id=%s key=%s name=%s domain=%s",
            project.id,
            project.project_key,
            project.name,
            project.domain,
        )
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
