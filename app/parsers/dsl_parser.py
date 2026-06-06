"""
PART 1 — DSL Grammar Parser

Supported format:
    @1: payment_due -> validate_payment
    @2 @depends(@1): payment_due -> send_email
    @3 @depends(@1,@2): payment_due -> close_case

Rules:
    - left side of -> is trigger
    - right side of -> is action
    - @depends(...) is optional
    - whitespace tolerant
    - lines starting with # are comments
    - empty lines ignored
    - ambiguous syntax (no ->) fails immediately
"""

import re
from app.core.logger import logger

# Strict step line pattern:
# @<id> [optional @depends(@id,...)] : <trigger> -> <action>
_STEP_PATTERN = re.compile(
    r"^@(?P<step_id>\w+)"                          # @1 or @step_name
    r"(?:\s+@depends\((?P<depends>[^)]*)\))?"       # optional @depends(@1,@2)
    r"\s*:\s*"                                      # colon separator
    r"(?P<trigger>\w+)"                             # trigger word
    r"\s*->\s*"                                     # arrow (required)
    r"(?P<action>\w+)"                              # action word
    r"\s*$"
)

_DEPENDS_SPLIT = re.compile(r"[\s,]+")


def _is_repairable(line: str) -> bool:
    """
    Determine if a malformed line is structurally repairable by LLM.
    Repairable = has some structure but is malformed (broken indentation,
    corrupted depends syntax, incomplete formatting).
    NOT repairable = missing arrow (ambiguous grammar), missing step id,
    semantic failures.
    """
    has_step_id = line.strip().startswith("@")
    has_arrow = "->" in line
    has_colon = ":" in line

    # Has step id and colon but no arrow — ambiguous, not repairable
    if has_step_id and has_colon and not has_arrow:
        return False

    # Has arrow but no step id — structural issue, repairable
    if has_arrow and not has_step_id:
        return True

    # Has step id and arrow but malformed depends — repairable
    if has_step_id and has_arrow and "@depends" in line:
        return True

    # Completely unrecognized line with some content — repairable
    if has_step_id and not has_colon:
        return True

    return False


def parse_dsl(text: str) -> dict:
    """
    Parse DSL text into a list of step definitions.

    Returns:
        {
            "success": bool,
            "steps": [...],
            "errors": [...],
            "repairable": bool   # True = LLM repair may help
        }
    """
    logger.info("parser_started", extra={"extra_data": {"input_length": len(text)}})

    steps = []
    errors = []
    repairable_lines = []

    lines = text.strip().splitlines()

    for raw_line in lines:
        line = raw_line.strip()

        # Skip empty lines and comments
        if not line or line.startswith("#"):
            continue

        match = _STEP_PATTERN.match(line)

        if not match:
            # Check if this line is repairable or a hard fail
            if _is_repairable(line):
                repairable_lines.append(line)
                errors.append(f"malformed_line: {line!r}")
            else:
                # Ambiguous syntax — hard fail, no LLM repair
                errors.append(f"invalid_syntax_no_arrow: {line!r}")
                logger.warning(
                    "parser_validation_failed",
                    extra={"extra_data": {"reason": "invalid_syntax_no_arrow", "line": line}},
                )
                return {
                    "success": False,
                    "steps": [],
                    "errors": errors,
                    "repairable": False,
                }
            continue

        step_id = match.group("step_id")
        trigger = match.group("trigger").lower()
        action = match.group("action").lower()
        depends_raw = match.group("depends") or ""

        depends_on = []
        if depends_raw.strip():
            depends_on = [
                d.lstrip("@").strip()
                for d in _DEPENDS_SPLIT.split(depends_raw.strip())
                if d.strip()
            ]

        steps.append({
            "id": step_id,
            "trigger": trigger,
            "action": action,
            "depends_on": depends_on,
        })

    # If we had repairable lines but also got some valid steps,
    # the whole input is considered repairable
    if errors:
        is_repairable = len(repairable_lines) > 0
        logger.warning(
            "parser_validation_failed",
            extra={"extra_data": {"errors": errors, "repairable": is_repairable}},
        )
        return {
            "success": False,
            "steps": steps,
            "errors": errors,
            "repairable": is_repairable,
        }

    logger.info(
        "parser_validation_passed",
        extra={"extra_data": {"step_count": len(steps)}},
    )

    return {
        "success": True,
        "steps": steps,
        "errors": [],
        "repairable": False,
    }
