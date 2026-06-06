from app.execution.conditions import is_rule_matched
from app.core.logger import logger


def get_matching_workflows(workflows, payload, event):
    matched = []
    for workflow in workflows:
        rule = workflow.parsed_rule_json
        if is_rule_matched(rule, event, payload):
            matched.append(workflow)
        else:
            logger.debug(
                "workflow_not_matched",
                extra={
                    "extra_data": {
                        "workflow_id": workflow.id,
                        "event_type": event["event_type"],
                    }
                },
            )

    return matched
