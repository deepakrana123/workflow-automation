import requests
import os
import time
import json
from app.config.retry_wrapper import with_retry
from app.llm.contracts import fail_response
from app.llm.repair import repair_json
from app.llm.validator import score_response
from app.core.logger import logger

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL = os.getenv("GEMINI_MODEL")
url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={API_KEY}"

# Part 5 — configurable timeout, default tight for repair path
GEMINI_TIMEOUT_SECONDS = int(os.getenv("GEMINI_TIMEOUT_SECONDS", "5"))


def try_call_gemini_rest(prompt: str):

    def __call():
        start = time.time()
        try:
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            response = requests.post(url=url, json=payload, timeout=GEMINI_TIMEOUT_SECONDS)
            if response.status_code != 200:
                error_body = response.text[:300]
                # Surface API key errors explicitly for provider health tracking
                if response.status_code in (401, 403) or "api key" in error_body.lower():
                    error_msg = f"API_KEY_INVALID: {error_body}"
                else:
                    error_msg = error_body
                logger.warning(
                    "gemini_http_error",
                    extra={
                        "extra_data": {
                            "status_code": response.status_code,
                            "response_body": error_body,
                        }
                    },
                )
                return fail_response("gemini", error_msg)
            data = response.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"]

            # ✅ scoring — parse the JSON text and score it semantically
            clean_text = text.replace("```json", "").replace("```", "").strip()
            parsed = repair_json(clean_text)
            score = score_response(parsed["data"]) if parsed["success"] else 0.5

            latency = int((time.time() - start) * 1000)
            logger.info(
                "gemini_call_success",
                extra={"extra_data": {"latency_ms": latency, "score": score}},
            )
            return {
                "success": True,
                "provider": "gemini",
                "model": "gemini-flash-latest",
                "text": text,
                "latency_ms": latency,
                "score": score,
                "cost": 0,
            }
        except requests.Timeout:
            logger.warning("gemini_timeout")
            return {"success": False, "provider": "gemini", "error": "timeout"}
        except Exception as e:
            logger.error(
                "gemini_unexpected_error",
                extra={"extra_data": {"error": str(e)}},
            )
            return {"success": False, "provider": "gemini", "error": str(e)}

    return with_retry(__call, retries=2)
