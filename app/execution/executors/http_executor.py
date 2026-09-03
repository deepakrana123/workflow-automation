"""
app/execution/executors/http_executor.py

Executes external HTTP endpoints via WorkspaceIntegration.

Flow:
    ActionDefinition.execution_template
        ↓  workspace_integration_id (from template or future WorkflowActionMapping override)
    WorkspaceIntegration  (base_url, authentication_type, credentials)
        ↓
    Build full URL  (base_url + configuration["endpoint"])
        ↓
    Apply auth headers
        ↓
    HTTP request  (method, headers, body_template rendered with context)
        ↓
    Map response via response_mapping  →  ActionResult
"""

import re

import requests

from app.execution.executors.base_executor import BaseExecutor
from app.models.action_definitions import ActionDefinition
from app.workflow_execution.schemas.action_result import ActionResult
from app.core.logger import logger


# Default timeout used when not specified in execution_template
_DEFAULT_TIMEOUT = 30


class HttpExecutor(BaseExecutor):

    def execute(
        self,
        action_definition: ActionDefinition,
        context: dict,
    ) -> ActionResult:
        template = action_definition.execution_template or {}
        cfg = template.get("configuration") or {}

        # workspace_integration is expected to be eager-loaded or accessible
        # via action_definition. For now resolve from context if passed.
        integration = context.get("_workspace_integration")

        if integration is None:
            return ActionResult(
                success=False,
                error=(
                    f"http_executor: no workspace_integration available "
                    f"for action '{action_definition.name}'"
                ),
                metadata={"skip_retry": True},
            )

        # ── Build URL ─────────────────────────────────────────────────────────
        endpoint = cfg.get("endpoint", "")
        url = integration.base_url.rstrip("/") + "/" + endpoint.lstrip("/")

        # ── Build headers ─────────────────────────────────────────────────────
        headers = dict(cfg.get("headers", {}))
        headers = {**headers, **self._auth_headers(integration)}

        # ── Render body template ──────────────────────────────────────────────
        body_template = cfg.get("body_template", {})
        body = self._render_template(body_template, context)

        # ── Query params ──────────────────────────────────────────────────────
        query_params = cfg.get("query_params", {})

        method  = cfg.get("method", "POST").upper()
        timeout = cfg.get("timeout", _DEFAULT_TIMEOUT)

        logger.info(
            "http_executor_request",
            extra={"extra_data": {
                "method": method,
                "url": url,
                "action_definition_id": action_definition.id,
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
                "url": url,
                "success": success,
            }},
        )

        # ── Parse response body ───────────────────────────────────────────────
        try:
            response_body = response.json()
        except Exception:
            response_body = {"raw": response.text}

        # ── Map response to outputs ───────────────────────────────────────────
        response_mapping = cfg.get("response_mapping", {})
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
    def _auth_headers(integration) -> dict:
        auth_type = integration.authentication_type
        creds     = integration.credentials or {}

        if auth_type == "bearer":
            token = creds.get("token", "")
            return {"Authorization": f"Bearer {token}"}

        if auth_type == "api_key":
            header = creds.get("header", "X-API-Key")
            key    = creds.get("key", "")
            return {header: key}

        if auth_type == "basic":
            import base64
            user     = creds.get("username", "")
            password = creds.get("password", "")
            encoded  = base64.b64encode(f"{user}:{password}".encode()).decode()
            return {"Authorization": f"Basic {encoded}"}

        if auth_type == "oauth2":
            token = creds.get("access_token", "")
            return {"Authorization": f"Bearer {token}"}

        return {}

    @staticmethod
    def _render_template(template: dict, context: dict) -> dict:
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
        if not mapping:
            return response_body

        outputs = {}
        for output_key, source_key in mapping.items():
            path = source_key.lstrip("$").lstrip(".")
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
