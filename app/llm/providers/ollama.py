import requests
import time
import os
from app.llm.contracts import success_response, fail_response
from app.config.retry_wrapper import with_retry
from app.core.logger import logger
from app.llm.repair import repair_json
from app.llm.validator import score_response

OLLAMA_URL = "http://host.docker.internal:11434/api/generate"
OLLAMA_TIMEOUT_SECONDS = int(os.getenv("OLLAMA_TIMEOUT_SECONDS", "5"))


def try_call_ollama(prompt: str):
    def __call():
        start = time.time()
        try:
            res = requests.post(
                OLLAMA_URL,
                json={"model": "qwen2.5:7b", "prompt": prompt, "stream": False},
                timeout=OLLAMA_TIMEOUT_SECONDS,
            )
            if res.status_code != 200:
                logger.warning(
                    "ollama_http_error",
                    extra={"extra_data": {"status_code": res.status_code}},
                )
                return fail_response("ollama", f"http_{res.status_code}")

            data = res.json()
            raw_text = data.get("response", "").strip()
            if not raw_text:
                logger.warning("ollama_empty_response")
                return fail_response("ollama", "empty_response")
            parsed = repair_json(raw_text)
            if not parsed["success"]:
                return fail_response("ollama", "invalid_json")

            structured = parsed["data"]

            score = score_response(structured)

            latency = int((time.time() - start) * 1000)
            logger.info(
                "ollama_call_success",
                extra={"extra_data": {"latency_ms": latency, "score": score}},
            )
            return success_response(
                provider="ollama",
                model="qwen2.5:7b",
                text=data["response"],
                latency_ms=latency,
                score=score,
                cost=0,
            )
        except requests.Timeout:
            logger.warning("ollama_timeout")
            return fail_response("ollama", "timeout")
        except Exception as e:
            logger.error(
                "ollama_unexpected_error",
                extra={"extra_data": {"error": str(e)}},
            )
            return fail_response("ollama", str(e))

    return with_retry(__call, retries=1)
