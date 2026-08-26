"""
app/models/role_assignment.py

Maps a user to a role within a specific workspace.

Key design choices:
  - user_id starts NULL: the platform creates role SHAPES from BRD actors.
    A human admin maps actual user IDs to those shapes later (HR integration
    or admin UI). RBAC is structurally ready the moment BRDs are ingested.
  - One role per user per workspace (unique constraint).
  - source_rule_id links back to the BusinessRuleDefinition that caused this
    role shape to be extracted — provides full provenance.

Role catalogue (static, not DB-configurable):
  global_admin   — global workspace only, all permissions
  region_manager — region workspace, most permissions
  zone_manager   — zone workspace
  branch_manager — branch workspace, can publish and resolve
  branch_officer — branch workspace, read + resolve human tasks
  auditor        — any level, read-only + audit:read
  read_only      — any level, read-only
"""

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.sql import func

from app.db.base import Base


# ── Valid roles (static catalogue) ───────────────────────────────────────────

VALID_ROLES = frozenset({
    "global_admin",
    "region_manager",
    "zone_manager",
    "branch_manager",
    "branch_officer",
    "auditor",
    "read_only",
})

# Minimum workspace level required to hold each role
ROLE_MIN_LEVEL: dict[str, str] = {
    "global_admin":   "global",
    "region_manager": "region",
    "zone_manager":   "zone",
    "branch_manager": "branch",
    "branch_officer": "branch",
    "auditor":        "global",   # auditor is valid at any level
    "read_only":      "global",   # read_only is valid at any level
}

# Permissions granted by each role
ROLE_PERMISSIONS: dict[str, frozenset[str]] = {
    "global_admin": frozenset({
        "workflow:read", "workflow:create", "workflow:publish", "workflow:delete",
        "rule:read", "rule:create", "rule:override",
        "humantask:read", "humantask:resolve", "humantask:escalate",
        "audit:read",
        "admin:manage_roles",
        "capability:read",
    }),
    "region_manager": frozenset({
        "workflow:read", "workflow:create", "workflow:publish", "workflow:delete",
        "rule:read", "rule:create", "rule:override",
        "humantask:read", "humantask:resolve", "humantask:escalate",
        "audit:read",
        "capability:read",
    }),
    "zone_manager": frozenset({
        "workflow:read", "workflow:create", "workflow:publish",
        "rule:read", "rule:create", "rule:override",
        "humantask:read", "humantask:resolve", "humantask:escalate",
        "audit:read",
        "capability:read",
    }),
    "branch_manager": frozenset({
        "workflow:read", "workflow:create", "workflow:publish",
        "rule:read", "rule:create", "rule:override",
        "humantask:read", "humantask:resolve", "humantask:escalate",
        "capability:read",
    }),
    "branch_officer": frozenset({
        "workflow:read",
        "rule:read",
        "humantask:read", "humantask:resolve",
        "capability:read",
    }),
    "auditor": frozenset({
        "workflow:read",
        "rule:read",
        "humantask:read",
        "audit:read",
        "capability:read",
    }),
    "read_only": frozenset({
        "workflow:read",
        "rule:read",
        "capability:read",
    }),
}


def get_permissions_for_role(role: str) -> frozenset[str]:
    """Return the permission set for a role. Empty set for unknown roles."""
    return ROLE_PERMISSIONS.get(role, frozenset())


class RoleAssignment(Base):
    __tablename__ = "role_assignments"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "workspace_id",
            name="uq_role_assignment_user_workspace",
        ),
    )

    id = Column(Integer, primary_key=True)

    # NULL until a real user is mapped to this role shape by admin/HR.
    user_id = Column(String(255), nullable=True, index=True)

    # One of VALID_ROLES
    role = Column(String(50), nullable=False, index=True)

    workspace_id = Column(
        Integer,
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Which structured rule triggered extraction of this role shape (nullable)
    source_rule_id = Column(
        Integer,
        ForeignKey("business_rule_definitions.id", ondelete="SET NULL"),
        nullable=True,
    )

    active = Column(Boolean, nullable=False, default=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
