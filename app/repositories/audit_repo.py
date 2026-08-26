from app.models.audit_log import AuditLog
from app.core.logger import logger


def create(
    db,
    workflow_id,
    action,
    status,
    event_type,
    request_payload,
    response_payload,
    user_id=None,
    workspace_id=None,
):
    try:
        log = AuditLog(
            workflow_id=workflow_id,
            action=action,
            status=status,
            event_type=event_type,
            request_payload=request_payload,
            response_payload=response_payload,
            user_id=user_id,
            workspace_id=workspace_id,
        )
        db.add(log)
        db.commit()

        logger.debug(
            "audit_log_written",
            extra={
                "extra_data": {
                    "workflow_id":  workflow_id,
                    "action":       action,
                    "status":       status,
                    "event_type":   event_type,
                    "user_id":      user_id,
                    "workspace_id": workspace_id,
                }
            },
        )
    except Exception as e:
        db.rollback()
        logger.error(
            "audit_log_failed",
            extra={"extra_data": {"error": str(e)}},
        )
