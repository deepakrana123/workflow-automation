"""
app/execution/executors/http_executor.py

Executes external HTTP endpoints.

The full connection config lives in execution_template.configuration on the
ActionDefinition (or its WorkflowActionMapping snapshot for workspace-scoped
actions). No WorkspaceIntegration table lookup needed.

Expected execution_template shape:
{
  "execution_type": "http",
  "configuration": {
    "base_url":   "https://api.example.com",   ← optional, overrides workspace default
    "method":     "POST",
    "endpoint":   "/receive-loan-application",
    "timeout":    30,
    "headers":    {"X-Api-Key": "secret"},
    "body_template": {
      "entity_id":   "{{entity_id}}",
      "action":      "receive_loan_application",
      "workflow_id": "{{workflow_id}}"
    },
    "response_mapping": {
      "status":    "$.status",
      "reference": "$.reference_id",
      "message":   "$.message"
    }
  }
}

body_template values wrapped in {{}} are interpolated from the step context.
response_mapping maps output keys to dot-path locations in the JSON response.
"""

import re

import requests

from app.execution.executors.base_executor import BaseExecutor
from app.models.action_definitions import ActionDefinition
from app.workflow_execution.schemas.action_result import ActionResult
from app.core.logger import logger

_DEFAULT_TIMEOUT = 30
_DEFAULT_METHOD  = "POST"


class HttpExecutor(BaseExecutor):

    def execute(
        self,
        action_definition: ActionDefinition,
        context: dict,
    ) -> ActionResult:
        template = action_definition.execution_template or {}
        cfg      = template.get("configuration") or {}

        # ── Build URL ─────────────────────────────────────────────────────────
        # base_url resolution order:
        #   1. execution_template.configuration.base_url — only if it is set
        #      AND does not point at localhost (localhost values in the DB are
        #      seed artefacts and must not override the running service URL).
        #   2. DEFAULT_HTTP_BASE_URL env var — set to http://api:8000/api in
        #      Docker, or http://localhost:8000/api for plain local runs.
        from app.core.config import DEFAULT_HTTP_BASE_URL

        _raw = (cfg.get("base_url") or "").rstrip("/")
        _is_localhost = "localhost" in _raw or "127.0.0.1" in _raw
        base_url = (_raw if _raw and not _is_localhost else None) or DEFAULT_HTTP_BASE_URL

        endpoint = cfg.get("endpoint", "").lstrip("/")
        url = f"{base_url}/{endpoint}" if endpoint else base_url

        # ── Build headers ─────────────────────────────────────────────────────
        headers = dict(cfg.get("headers") or {})
        headers.setdefault("Content-Type", "application/json")

        # ── Render body template ──────────────────────────────────────────────
        body_template = cfg.get("body_template") or {}
        body = self._render_template(body_template, context)

        # ── Query params ──────────────────────────────────────────────────────
        query_params = cfg.get("query_params") or {}

        method  = cfg.get("method", _DEFAULT_METHOD).upper()
        timeout = cfg.get("timeout", _DEFAULT_TIMEOUT)

        logger.info(
            "http_executor_request",
            extra={"extra_data": {
                "method":               method,
                "url":                  url,
                "action_definition_id": action_definition.id,
                "action_name":          action_definition.name,
            }},
        )

        # ── Execute request ───────────────────────────────────────────────────
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                params=query_params,
                json=body if body else None,
                timeout=timeout,
            )
        except requests.exceptions.Timeout:
            return ActionResult(
                success=False,
                error=f"http_executor: request timed out after {timeout}s — {url}",
            )
        except requests.exceptions.ConnectionError as e:
            return ActionResult(
                success=False,
                error=f"http_executor: connection error — {url} — {e}",
            )
        except requests.exceptions.RequestException as e:
            return ActionResult(
                success=False,
                error=f"http_executor: request failed — {url} — {e}",
            )

        # ── Evaluate success ──────────────────────────────────────────────────
        success = response.ok

        logger.info(
            "http_executor_response",
            extra={"extra_data": {
                "status_code": response.status_code,
                "url":         url,
                "success":     success,
            }},
        )

        # ── Parse response body ───────────────────────────────────────────────
        try:
            response_body = response.json()
        except Exception:
            response_body = {"raw": response.text}

        # ── Map response to outputs ───────────────────────────────────────────
        response_mapping = cfg.get("response_mapping") or {}
        outputs = self._map_response(response_body, response_mapping)

        if not success:
            return ActionResult(
                success=False,
                error=f"http_executor: HTTP {response.status_code} from {url}",
                outputs=outputs,
            )

        return ActionResult(
            success=True,
            outputs=outputs,
        )

    # ── Private helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _render_template(template: dict, context: dict) -> dict:
        """Interpolate {{variable}} placeholders in template values from context."""
        result = {}
        for key, value in template.items():
            if isinstance(value, str):
                def replacer(match):
                    var = match.group(1).strip()
                    return str(context.get(var, match.group(0)))
                result[key] = re.sub(r"\{\{(.+?)\}\}", replacer, value)
            else:
                result[key] = value
        return result

    @staticmethod
    def _map_response(response_body: dict, mapping: dict) -> dict:
        """Map response JSON fields to output keys using dot-path expressions."""
        if not mapping:
            return response_body

        outputs = {}
        for output_key, source_key in mapping.items():
            path  = source_key.lstrip("$").lstrip(".")
            parts = path.split(".")
            value = response_body
            for part in parts:
                if isinstance(value, dict):
                    value = value.get(part)
                else:
                    value = None
                    break
            outputs[output_key] = value

        return outputs
