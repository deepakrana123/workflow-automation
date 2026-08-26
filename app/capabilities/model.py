"""
app/capabilities/model.py

CapabilityView — a projection that surfaces an ActionDefinition as an
executable platform capability with its permission requirements resolved.

This is NOT a database table. It is assembled on demand from:
  - ActionDefinition        (catalog)
  - BusinessRuleDefinition  (required roles / permissions per workspace)
  - Workflow                (which published workflows contain this action)

The capability layer is what search/chat resolves to BEFORE RBAC filtering.
After retrieval returns RankedCandidate[], the CapabilityService wraps each
ActionDefinition in a CapabilityView and filters by user permissions.

Separation of concerns:
  Retrieval  → "What capabilities might match this query?"
  Capability → "What are the access requirements for each candidate?"
  RBAC       → "Can this user use this capability?"
  Execution  → "Can the capability execute under current rules?"
"""

from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class CapabilityView:
    """A resolved capability ready for permission checking and execution.

    Fields:
        action_id:           ActionDefinition.id
        name:                ActionDefinition.name  (e.g. "approve_loan")
        display_name:        ActionDefinition.display_name
        description:         ActionDefinition.description
        aliases:             ActionDefinition.aliases
        workflow_type:       ActionDefinition.workflow_type  (e.g. "finance")
        required_roles:      Roles extracted from BusinessRuleDefinition rows
                             for this action in the target workspace.
        required_permissions: Permissions implied by required_roles.
        input_schema:        ActionDefinition.input_schema
        output_schema:       ActionDefinition.output_schema
        linked_workflow_ids: IDs of published workflows containing this action.
        active:              ActionDefinition.active
    """

    action_id: int
    name: str
    display_name: str
    description: str | None
    aliases: list[str]
    workflow_type: str
    required_roles: list[str]
    required_permissions: list[str]
    input_schema: dict | None
    output_schema: dict | None
    linked_workflow_ids: list[int]
    active: bool

    def to_dict(self) -> dict:
        return {
            "action_id":            self.action_id,
            "name":                 self.name,
            "display_name":         self.display_name,
            "description":          self.description,
            "aliases":              self.aliases,
            "workflow_type":        self.workflow_type,
            "required_roles":       self.required_roles,
            "required_permissions": self.required_permissions,
            "input_schema":         self.input_schema,
            "output_schema":        self.output_schema,
            "linked_workflow_ids":  self.linked_workflow_ids,
            "active":               self.active,
        }
