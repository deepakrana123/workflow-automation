"""
app/workspace_integrations/integrations.py

WorkspaceIntegrationService — manages the full lifecycle of workspace integrations.

Responsibilities:
  - Validate and create integrations
  - Update integration properties
  - Activate / deactivate
  - Prevent duplicate names within a workspace
"""

from sqlalchemy.orm import Session

from app.workspace_integrations.models import WorkspaceIntegration
from app.workspace_integrations.repository import WorkspaceIntegrationRepository
from app.models.workspace import Workspace
from app.schemas.workspace_integration import WorkspaceIntegrationCreate, WorkspaceIntegrationUpdate
from app.core.logger import logger


class WorkspaceIntegrationService:

    def __init__(
        self,
        db: Session,
        repo: WorkspaceIntegrationRepository | None = None,
    ):
        self.db   = db
        self.repo = repo or WorkspaceIntegrationRepository(db)

    # ── Create ────────────────────────────────────────────────────────────────

    def create(
        self,
        workspace_id: int,
        payload: WorkspaceIntegrationCreate,
    ) -> WorkspaceIntegration:
        self._assert_workspace_exists(workspace_id)
        self._assert_name_unique(workspace_id, payload.name)

        integration = WorkspaceIntegration(
            workspace_id        = workspace_id,
            name                = payload.name,
            provider_type       = payload.provider_type,
            base_url            = payload.base_url,
            authentication_type = payload.authentication_type,
            credentials         = payload.credentials,
            description         = payload.description,
            active              = True,
        )
        result = self.repo.create(integration)

        self.db.commit()

        logger.info(
            "workspace_integration_created",
            extra={"extra_data": {
                "workspace_id":   workspace_id,
                "integration_id": result.id,
                "name":           result.name,
                "provider_type":  result.provider_type,
            }},
        )
        return result

    # ── Read ──────────────────────────────────────────────────────────────────

    def get(self, integration_id: int) -> WorkspaceIntegration:
        integration = self.repo.get_by_id(integration_id)
        if integration is None:
            raise ValueError(f"WorkspaceIntegration {integration_id} not found")
        return integration

    def list_by_workspace(
        self,
        workspace_id: int,
        active_only: bool = False,
    ) -> list[WorkspaceIntegration]:
        self._assert_workspace_exists(workspace_id)
        return self.repo.list_by_workspace(workspace_id, active_only=active_only)

    # ── Update ────────────────────────────────────────────────────────────────

    def update(
        self,
        integration_id: int,
        payload: WorkspaceIntegrationUpdate,
    ) -> WorkspaceIntegration:
        integration = self.get(integration_id)

        if payload.name is not None and payload.name != integration.name:
            self._assert_name_unique(integration.workspace_id, payload.name)
            integration.name = payload.name

        if payload.provider_type is not None:
            integration.provider_type = payload.provider_type

        if payload.base_url is not None:
            integration.base_url = payload.base_url

        if payload.authentication_type is not None:
            integration.authentication_type = payload.authentication_type

        if payload.credentials is not None:
            integration.credentials = payload.credentials

        if payload.description is not None:
            integration.description = payload.description

        result = self.repo.update(integration)

        self.db.commit()

        logger.info(
            "workspace_integration_updated",
            extra={"extra_data": {
                "workspace_id":   integration.workspace_id,
                "integration_id": result.id,
            }},
        )
        return result

    # ── Delete ────────────────────────────────────────────────────────────────

    def delete(self, integration_id: int) -> None:
        integration = self.get(integration_id)
        workspace_id = integration.workspace_id

        self.repo.delete(integration)

        self.db.commit()

        logger.info(
            "workspace_integration_deleted",
            extra={"extra_data": {
                "workspace_id":   workspace_id,
                "integration_id": integration_id,
            }},
        )

    # ── Private helpers ───────────────────────────────────────────────────────

    def _assert_workspace_exists(self, workspace_id: int) -> None:
        exists = (
            self.db.query(Workspace)
            .filter(Workspace.id == workspace_id, Workspace.active.is_(True))
            .first()
        )
        if not exists:
            raise ValueError(f"Workspace {workspace_id} not found or inactive")

    def _assert_name_unique(self, workspace_id: int, name: str) -> None:
        existing = self.repo.get_by_name(workspace_id, name)
        if existing:
            raise ValueError(
                f"A workspace integration named '{name}' already exists "
                f"in workspace {workspace_id}"
            )
