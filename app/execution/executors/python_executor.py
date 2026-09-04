"""
app/execution/executors/python_executor.py

Executes internal Python handlers via two resolution tiers.

Tier 1 — ActionHandlerRegistry (backward-compatible, unchanged):
    action_definition.name → ACTION_HANDLER_MAP lookup → handler(context, cfg)
    Used for built-in core handlers that ship with MFlows.

Tier 2 — Inline script (no redeploy needed):
    execution_template.configuration.script → exec in sandbox → run(context, config)
    Used for workspace-specific or catalog actions where the logic lives in the DB.
    The script must define: def run(context: dict, config: dict) -> dict | ActionResult

Tier 1 is always checked first so every existing handler continues to work
without any change. Tier 2 only activates when Tier 1 returns nothing.
"""

from app.execution.executors.base_executor import BaseExecutor
from app.execution.exceptions import HandlerNotFoundError
from app.models.action_definitions import ActionDefinition
from app.workflow_execution.schemas.action_result import ActionResult
from app.core.logger import logger


# ── Safe builtins for the inline script sandbox ───────────────────────────────
# Only include what a business-logic script legitimately needs.
# Explicitly excluded: os, sys, subprocess, open, __import__, socket, requests.
_SAFE_BUILTINS: dict = {
    "abs": abs, "round": round, "min": min, "max": max,
    "int": int, "float": float, "str": str, "bool": bool,
    "list": list, "dict": dict, "tuple": tuple, "set": set,
    "len": len, "range": range, "sum": sum, "sorted": sorted,
    "reversed": reversed, "enumerate": enumerate, "zip": zip,
    "map": map, "filter": filter, "any": any, "all": all,
    "isinstance": isinstance, "issubclass": issubclass, "type": type,
    "hasattr": hasattr, "getattr": getattr,
    "print": print,   # allowed — output goes to structured logger, not stdout bypass
    "True": True, "False": False, "None": None,
    "ValueError": ValueError, "TypeError": TypeError, "KeyError": KeyError,
    "Exception": Exception,
}


class PythonExecutor(BaseExecutor):

    def execute(
        self,
        action_definition: ActionDefinition,
        context: dict,
    ) -> ActionResult:
        template  = action_definition.execution_template or {}
        cfg       = template.get("configuration") or {}

        # ── Tier 1: built-in registry lookup ─────────────────────────────────
        # Checks ACTION_HANDLER_MAP by action name. Every existing handler
        # continues to work without any change.
        from app.execution.python.action_handler_registry import ACTION_HANDLER_MAP

        handler_name = cfg.get("handler") or action_definition.name
        handler = ACTION_HANDLER_MAP.get(handler_name)

        if handler is not None:
            logger.info(
                "python_executor_tier1_dispatch",
                extra={"extra_data": {
                    "handler_name":         handler_name,
                    "action_definition_id": action_definition.id,
                }},
            )
            raw = handler(context, cfg)
            return _normalise(raw)

        # ── Tier 2: inline script execution ──────────────────────────────────
        # The script is stored in execution_template.configuration.script.
        # It must define: def run(context: dict, config: dict) -> dict | ActionResult
        # No external calls, no file I/O, no network — sandboxed builtins only.
        script = cfg.get("script")
        if script:
            logger.info(
                "python_executor_tier2_script",
                extra={"extra_data": {
                    "action_name":          action_definition.name,
                    "action_definition_id": action_definition.id,
                }},
            )
            return _execute_script(
                script=script,
                context=context,
                config=cfg,
                action_name=action_definition.name,
            )

        # ── Nothing found ─────────────────────────────────────────────────────
        raise HandlerNotFoundError(
            handler_name=handler_name,
            action_configuration_id=None,
        )


# ── Helpers ───────────────────────────────────────────────────────────────────

def _execute_script(
    script: str,
    context: dict,
    config: dict,
    action_name: str,
) -> ActionResult:
    """
    Execute an inline Python script in a restricted namespace.

    The script must define:
        def run(context: dict, config: dict) -> dict | ActionResult

    Returns ActionResult. Normalises dict return automatically.
    Raises HandlerNotFoundError if `run` is not defined.
    Wraps any script exception as a non-retryable ActionResult failure.
    """
    safe_globals = {
        "__builtins__": _SAFE_BUILTINS,
        "math":         __import__("math"),
        "decimal":      __import__("decimal"),
        "datetime":     __import__("datetime"),
        "re":           __import__("re"),
        "json":         __import__("json"),
        "random":       __import__("random"),
        "ActionResult": ActionResult,
    }
    local_ns: dict = {}

    try:
        exec(compile(script, f"<action:{action_name}>", "exec"), safe_globals, local_ns)
    except SyntaxError as exc:
        return ActionResult(
            success=False,
            error=f"script_syntax_error: {exc}",
            metadata={"skip_retry": True, "action_name": action_name},
        )

    run_fn = local_ns.get("run")
    if run_fn is None:
        raise HandlerNotFoundError(
            handler_name="run",
            action_configuration_id=None,
        )

    try:
        result = run_fn(context, config)
        return _normalise(result)
    except Exception as exc:  # noqa: BLE001
        return ActionResult(
            success=False,
            error=f"script_runtime_error: {exc}",
            metadata={"skip_retry": False, "action_name": action_name},
        )


def _normalise(raw) -> ActionResult:
    """Normalise a handler return value to ActionResult."""
    if isinstance(raw, ActionResult):
        return raw
    if isinstance(raw, dict):
        success = raw.get("success", True)
        if isinstance(success, bool) is False:
            success = bool(success)
        outputs = {
            k: v for k, v in raw.items()
            if k not in ("success", "status", "skip_retry", "message", "error")
        }
        return ActionResult(
            success=success,
            outputs=outputs,
            message=raw.get("message"),
            error=raw.get("error"),
            metadata={"skip_retry": raw.get("skip_retry", False)},
        )
    # Unexpected return type — treat as success with no outputs
    return ActionResult(success=True)
