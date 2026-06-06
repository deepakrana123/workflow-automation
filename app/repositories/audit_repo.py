from app.models.audit_log import AuditLog
from app.core.logger import logger


def create(
    db, workflow_id, action, status, event_type, request_payload, response_payload
):
    try:
        log = AuditLog(
            workflow_id=workflow_id,
            action=action,
            status=status,
            event_type=event_type,
            request_payload=request_payload,
            response_payload=response_payload,
        )
        db.add(log)
        db.commit()  # ✅ persist immediately

        logger.debug(
            "audit_log_written",
            extra={
                "extra_data": {
                    "workflow_id": workflow_id,
                    "action": action,
                    "status": status,
                    "event_type": event_type,
                }
            },
        )
    except Exception as e:
        db.rollback()  # ✅ prevent session corruption
        logger.error(
            "audit_log_failed",
            extra={"extra_data": {"error": str(e)}},
        )
