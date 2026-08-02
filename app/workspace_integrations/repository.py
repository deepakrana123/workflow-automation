"""
app/workspace_integrations/repository.py

Database operations for WorkspaceIntegration.
All methods operate within the provided SQLAlchemy session.
"""

from sqlalchemy.orm import Session

from app.workspace_integrations.models import WorkspaceIntegration


class WorkspaceIntegrationRepository:

    def __init__(self, db: Session):
        self.db = db

    # ── Write ─────────────────────────────────────────────────────────────────

    def create(self, integration: WorkspaceIntegration) -> WorkspaceIntegration:
        self.db.add(integration)
        self.db.flush()
        self.db.refresh(integration)
        return integration

    def update(self, integration: WorkspaceIntegration) -> WorkspaceIntegration:
        self.db.flush()
        self.db.refresh(integration)
        return integration

    def deactivate(self, integration: WorkspaceIntegration) -> WorkspaceIntegration:
        integration.active = False
        self.db.flush()
        self.db.refresh(integration)
        return integration

    def delete(self, integration: WorkspaceIntegration) -> None:
        self.db.delete(integration)
        self.db.flush()

    # ── Read ──────────────────────────────────────────────────────────────────

    def get_by_id(self, integration_id: int) -> WorkspaceIntegration | None:
        return (
            self.db.query(WorkspaceIntegration)
            .filter(WorkspaceIntegration.id == integration_id)
            .first()
        )

    def get_by_name(
        self, workspace_id: int, name: str
    ) -> WorkspaceIntegration | None:
        return (
            self.db.query(WorkspaceIntegration)
            .filter(
                WorkspaceIntegration.workspace_id == workspace_id,
                WorkspaceIntegration.name == name,
            )
            .first()
        )

    def list_by_workspace(
        self,
        workspace_id: int,
        active_only: bool = False,
    ) -> list[WorkspaceIntegration]:
        q = self.db.query(WorkspaceIntegration).filter(
            WorkspaceIntegration.workspace_id == workspace_id
        )
        if active_only:
            q = q.filter(WorkspaceIntegration.active.is_(True))
        return q.order_by(WorkspaceIntegration.created_at.desc()).all()
