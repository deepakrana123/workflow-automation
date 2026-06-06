def success_response(
    provider, model, text, latency_ms, score=0.8, cost=0, retries=0, fallback_used=False
):
    return {
        "success": True,
        "provider": provider,
        "model": model,
        "text": text,
        "latency_ms": latency_ms,
        "score": score,
        "cost": cost,
        "retries": retries,
        "fallback_used": fallback_used,
        "error": None,
    }


def fail_response(provider, error, retries=0):
    return {
        "success": False,
        "provider": provider,
        "error": str(error),
        "retries": retries,
    }
