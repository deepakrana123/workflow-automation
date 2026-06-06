from app.parsers.dsl_parser import parse_dsl
from app.parsers.dag_validator import validate_dag
from app.parsers.cache import cache_store
from app.llm.service import repair_dsl_with_llm
from app.metrics.parser_metrics import parser_metrics
from app.core.logger import logger


def _hard_fail(errors: list) -> dict:
    """Strict hard fail response — never mixes success with errors."""
    return {
        "success": False,
        "steps": [],
        "validation": {
            "is_valid": False,
            "errors": errors,
        },
    }


def _success(steps: list, source: str) -> dict:
    """Strict success response."""
    return {
        "success": True,
        "steps": steps,
        "source": source,
        "validation": {
            "is_valid": True,
            "errors": [],
        },
    }


def parse_dag_workflow(text: str) -> dict:
    """
    Main entry point for DAG workflow parsing.
    Deterministic parser first, LLM repair only if structurally repairable.
    """
    parser_metrics.total_requests += 1

    logger.info(
        "parser_started",
        extra={"extra_data": {"input_length": len(text)}},
    )

    # Check cache
    if text in cache_store:
        parser_metrics.cache_hits += 1
        return cache_store[text]

    # Step 1 — deterministic DSL parse
    parse_result = parse_dsl(text)

    if not parse_result["success"]:
        repairable = parse_result.get("repairable", False)

        if not repairable:
            # Hard fail — ambiguous syntax, missing arrow, unsupported grammar
            # LLM repair must NOT be triggered
            parser_metrics.failures += 1
            logger.warning(
                "llm_repair_skipped",
                extra={
                    "extra_data": {
                        "reason": "not_repairable",
                        "errors": parse_result["errors"],
                    }
                },
            )
            result = _hard_fail(parse_result["errors"])
            cache_store[text] = result
            return result

        # Step 2 — attempt LLM repair (structural issues only)
        logger.info(
            "llm_repair_started",
            extra={"extra_data": {"errors": parse_result["errors"]}},
        )

        repair_result = repair_dsl_with_llm(text)

        if not repair_result["success"]:
            parser_metrics.failures += 1
            parser_metrics.fallback_used += 1
            logger.warning(
                "llm_repair_failed",
                extra={"extra_data": {"error": repair_result.get("error")}},
            )
            result = _hard_fail(parse_result["errors"] + ["llm_repair_failed"])
            cache_store[text] = result
            return result

        # Re-parse the repaired text
        repaired_text = repair_result.get("repaired_text", "")
        parse_result = parse_dsl(repaired_text)

        if not parse_result["success"]:
            parser_metrics.failures += 1
            logger.warning(
                "llm_repair_failed",
                extra={"extra_data": {"reason": "repaired_text_still_invalid"}},
            )
            result = _hard_fail(
                parse_result["errors"] + ["llm_repair_produced_invalid_dsl"]
            )
            cache_store[text] = result
            return result

        parser_metrics.llm_hits += 1
        source = "llm_repair"
    else:
        source = "deterministic"

    steps = parse_result["steps"]
    validation = validate_dag(steps)

    if not validation["is_valid"]:
        parser_metrics.failures += 1
        logger.warning(
            "parser_validation_failed",
            extra={"extra_data": {"errors": validation["errors"]}},
        )
        # Hard fail — do NOT attempt LLM repair for semantic validation failures
        result = _hard_fail(validation["errors"])
        cache_store[text] = result
        return result

    # Step 4 — success
    parser_metrics.regex_hits += 1
    logger.info(
        "parser_completed",
        extra={
            "extra_data": {
                "step_count": len(steps),
                "source": source,
            }
        },
    )

    result = _success(steps, source)
    cache_store[text] = result
    return result
