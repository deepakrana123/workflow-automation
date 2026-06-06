import json
from app.llm.llmManager import LLMManager
from app.llm.validator import validate_workflow_json
from app.llm.repair import repair_json
from app.llm.prompt_loader import build_prompt
from app.core.logger import logger

manager = LLMManager()


def clean_json(text: str):
    return text.replace("```json", "").replace("```", "").strip()


def parse_workflow_with_llm(raw_text: str):
    result = manager.call(raw_text)
    if not result["success"]:
        logger.error(
            "llm_all_providers_failed",
            extra={"extra_data": {"errors": result.get("errors")}},
        )
        return result

    raw_output = result["text"]
    logger.debug(
        "llm_raw_output", extra={"extra_data": {"output_preview": raw_output[:100]}}
    )
    try:
        parsed = json.loads(clean_json(raw_output))
    except Exception as e:
        logger.warning(
            "llm_json_parse_failed_attempting_repair",
            extra={"extra_data": {"error": str(e)}},
        )
        repaired = repair_json(raw_output)
        if not repaired["success"]:
            logger.error("llm_json_repair_failed")
            return {"success": False, "error": "invalid json"}
        parsed = repaired["data"]
        logger.info("llm_json_repaired_successfully")
    valid = validate_workflow_json(parsed)
    if not valid["is_valid"]:
        logger.error(
            "llm_validation_failed",
            extra={"extra_data": {"errors": valid["errors"]}},
        )
        return {"success": False, "error": valid["errors"]}

    logger.info(
        "llm_parse_success",
        extra={
            "extra_data": {
                "provider": result["provider"],
                "score": result.get("score", 0),
            }
        },
    )
    return {
        "success": True,
        "source": result["provider"],
        "score": result.get("score", 0),
        "data": parsed,
        "provider": result["provider"],
    }


def repair_dsl_with_llm(raw_dsl: str) -> dict:
    """
    PART 3 — LLM DSL repair.
    Only called for structurally malformed DSL (broken indentation,
    corrupted depends syntax, incomplete formatting).
    NOT called for semantic failures (missing action, invalid trigger).

    Returns:
        { "success": True, "repaired_text": "..." }
        { "success": False, "error": "..." }
    """
    logger.info(
        "llm_repair_started",
        extra={"extra_data": {"input_length": len(raw_dsl)}},
    )

    repair_prompt = build_prompt("repair_v1.txt", {"model_output": raw_dsl})
    result = manager.call(repair_prompt)

    if not result["success"]:
        logger.warning(
            "llm_repair_failed",
            extra={"extra_data": {"error": result.get("error")}},
        )
        return {"success": False, "error": result.get("error", "all providers failed")}

    repaired_text = result.get("text", "").strip()

    if not repaired_text:
        logger.warning("llm_repair_failed", extra={"extra_data": {"reason": "empty_response"}})
        return {"success": False, "error": "llm_returned_empty_repair"}

    logger.info(
        "llm_repair_started",  # reuse key — indicates repair completed
        extra={"extra_data": {"repaired_length": len(repaired_text)}},
    )

    return {"success": True, "repaired_text": repaired_text}
