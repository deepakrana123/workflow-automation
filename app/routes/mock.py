"""
app/routes/mock.py

POST /api/mock/{action_name}

Mock HTTP endpoint for all catalog actions that use execution_type="http".

Purpose:
  When WorkspaceIntegration.base_url = "http://localhost:8000/api"
  and execution_template.configuration.endpoint = "/mock/run_cibil_check",
  HttpExecutor calls this route.

  For demo/development the mock returns a realistic response matching the
  action's output_schema. For production the consumer replaces base_url with
  their real endpoint. Nothing else changes.

Response generation:
  1. Look up ActionDefinition by action_name.
  2. Read output_schema — generate a mock response matching its fields.
  3. Return JSON that response_mapping on execution_template can extract.

SLO simulation:
  Configurable via query param ?slo_ms=N — adds artificial latency.
  Default: 0 (no artificial latency in tests).

Error rate simulation:
  Query param ?error_rate=0.05 → 5% chance of returning a 503.
  Default: 0.0.
"""

import random
import time

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.action_definitions import ActionDefinition
from app.core.logger import logger

router = APIRouter(prefix="/mock", tags=["mock"])


@router.post("/{action_name}")
async def mock_action(
    action_name: str,
    request: Request,
    slo_ms: int = 0,
    error_rate: float = 0.0,
    db: Session = Depends(get_db),
):
    """
    Simulate an HTTP action response.

    The body sent by HttpExecutor (rendered from body_template) is echoed
    back in the response under "request_received" for observability.

    response_mapping on the execution_template extracts fields from the
    response body — so the mock must return those fields under the paths
    that response_mapping expects.
    """
    # ── SLO simulation ────────────────────────────────────────────────────────
    if slo_ms > 0:
        time.sleep(slo_ms / 1000)

    # ── Error rate simulation ─────────────────────────────────────────────────
    if error_rate > 0 and random.random() < error_rate:
        logger.info(
            "mock_action_simulated_error",
            extra={"extra_data": {"action_name": action_name, "error_rate": error_rate}},
        )
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=503,
            content={"error": "simulated_service_unavailable", "action": action_name},
        )

    # ── Load action definition ────────────────────────────────────────────────
    action_def = (
        db.query(ActionDefinition)
        .filter(ActionDefinition.name == action_name, ActionDefinition.active.is_(True))
        .first()
    )

    # ── Read incoming body ────────────────────────────────────────────────────
    try:
        body = await request.json()
    except Exception:
        body = {}

    # ── Generate mock response ────────────────────────────────────────────────
    mock_data = _generate_mock_response(action_name, action_def, body)

    logger.info(
        "mock_action_response",
        extra={"extra_data": {
            "action_name":  action_name,
            "slo_ms":       slo_ms,
            "error_rate":   error_rate,
        }},
    )

    return {"data": mock_data, "status": "success", "action": action_name}


# ── Mock response generator ───────────────────────────────────────────────────

def _generate_mock_response(
    action_name: str,
    action_def: ActionDefinition | None,
    body: dict,
) -> dict:
    """
    Generate a mock response dict.

    Strategy:
      1. If action_def has output_schema, generate values for each declared field.
      2. Fall back to action-name-based heuristics for common patterns.
      3. Always return something — never an empty dict.
    """
    if action_def and action_def.output_schema:
        return _mock_from_schema(action_def.output_schema, action_name, body)

    return _mock_by_name(action_name, body)


def _mock_from_schema(schema: dict, action_name: str, body: dict) -> dict:
    """Generate a mock value for each property declared in output_schema."""
    props = schema.get("properties") or {}
    result = {}
    ts = int(time.time())

    for field, spec in props.items():
        ftype = spec.get("type", "string")
        desc  = spec.get("description", "").lower()

        if ftype == "boolean":
            result[field] = True
        elif ftype == "number" or ftype == "integer":
            # Try to produce a domain-relevant number
            if any(k in field for k in ("score", "rating", "rank")):
                result[field] = 700 + (hash(body.get("entity_id", action_name)) % 150)
            elif any(k in field for k in ("amount", "balance", "principal", "emi")):
                result[field] = 10000 + (hash(action_name) % 90000)
            elif any(k in field for k in ("rate", "pct", "percent")):
                result[field] = round(8.5 + (hash(action_name) % 40) / 10, 2)
            elif any(k in field for k in ("days", "months", "tenure")):
                result[field] = 36 + (hash(action_name) % 84)
            elif ftype == "integer":
                result[field] = 1
            else:
                result[field] = 0.0
        elif ftype == "string":
            if any(k in field for k in ("id", "_id", "reference", "number", "ref")):
                result[field] = f"{action_name.upper()[:6]}-{ts}"
            elif any(k in field for k in ("status", "state")):
                result[field] = "SUCCESS"
            elif any(k in field for k in ("date", "_at", "time")):
                result[field] = "2026-08-26T00:00:00Z"
            else:
                result[field] = f"mock_{field}"
        elif ftype == "array":
            result[field] = []
        elif ftype == "object":
            result[field] = {}
        else:
            result[field] = None

    return result


def _mock_by_name(action_name: str, body: dict) -> dict:
    """
    Heuristic mock responses for common action name patterns.
    Used when output_schema is not populated yet.
    """
    ts  = int(time.time())
    eid = body.get("entity_id", "MOCK")

    patterns: dict[str, dict] = {
        "cibil": {"credit_score": 742, "report_id": f"CIB-{ts}", "delinquency_count": 0},
        "bureau": {"score": 720, "report_id": f"BUR-{ts}", "status": "CLEAR"},
        "aml":    {"cleared": True, "risk_flag": None, "screening_id": f"AML-{ts}"},
        "sanction": {"cleared": True, "match": False, "screening_id": f"SANC-{ts}"},
        "kyc":    {"kyc_status": "VERIFIED", "kyc_id": f"KYC-{ts}"},
        "aadhaar": {"verified": True, "name_match": True, "reference": f"UIDAI-{ts}"},
        "pan":    {"verified": True, "name": "MOCK CUSTOMER", "status": "ACTIVE"},
        "neft":   {"processed": True, "utr": f"NEFT{ts}", "settlement": "same_day"},
        "rtgs":   {"processed": True, "utr": f"RTGS{ts}", "settlement": "same_day"},
        "imps":   {"processed": True, "utr": f"IMPS{ts}", "settlement": "instant"},
        "upi":    {"processed": True, "transaction_id": f"UPI{ts}", "status": "SUCCESS"},
        "notify": {"delivered": True, "channel": "SMS", "message_id": f"MSG-{ts}"},
        "send":   {"delivered": True, "reference": f"MSG-{ts}"},
        "disburse": {"disbursed": True, "reference": f"DISB-{ts}", "amount": 500000},
        "verify": {"verified": True, "reference": f"VER-{ts}"},
        "generate": {"document_id": f"DOC-{ts}", "generated": True},
    }

    name_lower = action_name.lower()
    for keyword, response in patterns.items():
        if keyword in name_lower:
            return response

    # Generic fallback
    return {
        "success":   True,
        "reference": f"{action_name.upper()[:8]}-{ts}",
        "action":    action_name,
    }
