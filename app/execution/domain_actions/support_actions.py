"""
Customer Support Domain Actions

Covers: ticket lifecycle, SLA management, agent assignment,
customer communication, satisfaction surveys, refunds.
"""

import time
from app.core.logger import logger
from app.workflow_execution.schemas.action_result import ActionResult


def create_support_ticket(payload: dict, config: dict) -> ActionResult:
    """Create a new support ticket in the ticketing system."""
    priority = config.get("priority", "medium")
    category = config.get("category", "general")
    logger.info("support_ticket_created", extra={"extra_data": {
        "entity_id": payload.get("entity_id"),
        "priority": priority,
        "category": category,
    }})
    return ActionResult(success=True, outputs={
        "ticket_id": f"TK-{int(time.time())}",
        "priority": priority,
        "category": category,
    })


def assign_support_agent(payload: dict, config: dict) -> ActionResult:
    """Assign ticket to an available support agent based on skill/load."""
    skill = config.get("required_skill", "general")
    agent_id = config.get("agent_id", "AGENT_AUTO")
    logger.info("support_agent_assigned", extra={"extra_data": {
        "entity_id": payload.get("entity_id"),
        "agent_id": agent_id,
        "skill": skill,
    }})
    return ActionResult(success=True, outputs={
        "agent_id": agent_id,
        "assigned_skill": skill,
    })


def escalate_to_tier2(payload: dict, config: dict) -> ActionResult:
    """Escalate ticket to Tier-2 support team."""
    reason = config.get("reason", "unresolved_after_sla")
    logger.info("support_escalated_tier2", extra={"extra_data": {
        "entity_id": payload.get("entity_id"),
        "reason": reason,
    }})
    return ActionResult(success=True, outputs={
        "escalated_to": "tier2",
        "reason": reason,
    })


def send_sla_breach_alert(payload: dict, config: dict) -> ActionResult:
    """Alert manager when SLA is about to be or has been breached."""
    sla_hours = config.get("sla_hours", 24)
    channel = config.get("channel", "email")
    logger.warning("sla_breach_alert_sent", extra={"extra_data": {
        "entity_id": payload.get("entity_id"),
        "sla_hours": sla_hours,
        "channel": channel,
    }})
    return ActionResult(success=True, outputs={
        "alert_type": "sla_breach",
        "sla_hours": sla_hours,
        "channel": channel,
    })


def send_customer_update(payload: dict, config: dict) -> ActionResult:
    """Send status update to customer via preferred channel."""
    channel = config.get("channel", "email")
    template = config.get("template", "ticket_update")
    logger.info("customer_update_sent", extra={"extra_data": {
        "entity_id": payload.get("entity_id"),
        "channel": channel,
        "template": template,
    }})
    return ActionResult(success=True, outputs={
        "channel": channel,
        "template": template,
    })


def resolve_ticket(payload: dict, config: dict) -> ActionResult:
    """Mark ticket as resolved and trigger satisfaction survey."""
    resolution_code = config.get("resolution_code", "solved")
    logger.info("ticket_resolved", extra={"extra_data": {
        "entity_id": payload.get("entity_id"),
        "resolution_code": resolution_code,
    }})
    return ActionResult(success=True, outputs={
        "resolution_code": resolution_code,
        "survey_triggered": True,
    })


def send_satisfaction_survey(payload: dict, config: dict) -> ActionResult:
    """Send CSAT/NPS survey after ticket resolution."""
    survey_type = config.get("survey_type", "csat")
    delay_hours = config.get("delay_hours", 2)
    logger.info("satisfaction_survey_sent", extra={"extra_data": {
        "entity_id": payload.get("entity_id"),
        "survey_type": survey_type,
        "delay_hours": delay_hours,
    }})
    return ActionResult(success=True, outputs={
        "survey_type": survey_type,
        "delay_hours": delay_hours,
    })


def process_refund(payload: dict, config: dict) -> ActionResult:
    """Initiate refund process for customer complaint."""
    amount = config.get("refund_amount", 0)
    method = config.get("refund_method", "original_payment")
    logger.info("refund_processed", extra={"extra_data": {
        "entity_id": payload.get("entity_id"),
        "amount": amount,
        "method": method,
    }})
    return ActionResult(success=True, outputs={
        "refund_amount": amount,
        "refund_method": method,
        "refund_id": f"REF-{int(time.time())}",
    })


def flag_repeat_complaint(payload: dict, config: dict) -> ActionResult:
    """Flag customer as repeat complainer for priority handling."""
    threshold = config.get("complaint_threshold", 3)
    logger.warning("repeat_complaint_flagged", extra={"extra_data": {
        "entity_id": payload.get("entity_id"),
        "threshold": threshold,
    }})
    return ActionResult(success=True, outputs={
        "flagged": True,
        "complaint_threshold": threshold,
    })


def close_ticket_no_response(payload: dict, config: dict) -> ActionResult:
    """Auto-close ticket when customer hasn't responded within SLA window."""
    wait_days = config.get("wait_days", 7)
    logger.info("ticket_closed_no_response", extra={"extra_data": {
        "entity_id": payload.get("entity_id"),
        "wait_days": wait_days,
    }})
    return ActionResult(success=True, outputs={
        "close_reason": "no_customer_response",
        "wait_days": wait_days,
    })
