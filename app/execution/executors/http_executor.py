"""
app/execution/executors/http_executor.py

Executes external HTTP endpoints via WorkspaceIntegration.

Flow:
    ActionConfiguration
        ↓  workspace_integration_id
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

import json
import re

import requests

from app.execution.executors.base_executor import BaseExecutor
from app.models.action_configurations_model import ActionConfiguration
from app.workflow_execution.schemas.action_result import ActionResult
from app.core.logger import logger


# Default timeout used when not specified in ActionConfiguration.configuration
_DEFAULT_TIMEOUT = 30


class HttpExecutor(BaseExecutor):

    def execute(
        self,
        configuration: ActionConfiguration,
        context: dict,
    ) -> ActionResult:
        cfg = configuration.configuration or {}

        # ── Load WorkspaceIntegration ─────────────────────────────────────────
        if configuration.workspace_integration_id is None:
            return ActionResult(
                success=False,
                error="http_executor: no workspace_integration_id on ActionConfiguration",
                metadata={"skip_retry": True},
            )

        integration = configuration.workspace_integration

        if integration is None:
            return ActionResult(
                success=False,
                error=(
                    f"http_executor: WorkspaceIntegration "
                    f"{configuration.workspace_integration_id} not loaded"
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
                "action_configuration_id": configuration.id,
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
        success = response.ok   # True for 2xx

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
        """Build Authorization header from WorkspaceIntegration credentials."""
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

        # oauth2 — token expected to already be in credentials["access_token"]
        if auth_type == "oauth2":
            token = creds.get("access_token", "")
            return {"Authorization": f"Bearer {token}"}

        return {}

    @staticmethod
    def _render_template(template: dict, context: dict) -> dict:
        """
        Replace {{variable}} placeholders in template values with context values.
        Non-string values are passed through unchanged.
        """
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
        """
        Extract fields from response_body using simple key mapping.
        mapping = {"output_key": "response_key"} or {"output_key": "$.nested.key"}
        Only top-level keys supported for now; JSONPath-style is a future extension.
        """
        if not mapping:
            return response_body

        outputs = {}
        for output_key, source_key in mapping.items():
            # Strip leading $. for basic path support
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
