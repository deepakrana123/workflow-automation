# Re-export from the canonical model location to avoid duplicate table definitions.
from app.models.workspace_integration import WorkspaceIntegration  # noqa: F401

__all__ = ["WorkspaceIntegration"]
