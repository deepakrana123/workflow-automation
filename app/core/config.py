import os

MAX_RETRIES = 5
BASE_DELAY_SECONDS = 30
PROCESSING_TIMEOUT_SECONDS = 60

# Maximum wall-clock seconds allowed for the entire generation pipeline
# (all LLM attempts combined). Free tier default: 30s — enough for 2 Gemini
# calls with breathing room. Drop to 5–10s when using a paid fast model.
GENERATION_BUDGET_SECONDS: float = float(
    os.getenv("GENERATION_BUDGET_SECONDS", "30")
)

# Default base URL for HTTP actions whose execution_template carries no
# base_url.  Resolution order in HttpExecutor:
#   1. execution_template.configuration.base_url  (action-specific override)
#   2. http://localhost:8000/api                  (local dev / mock server)
#   3. DEFAULT_HTTP_BASE_URL from env             (staging / production)
DEFAULT_HTTP_BASE_URL: str = os.getenv(
    "DEFAULT_HTTP_BASE_URL",
    "http://localhost:8000/api",
)

# ── Vision (multimodal table/diagram) extraction ─────────────────────────────
# Tunables for the grouped, rate-limit-aware Vision extraction path
# (app/knowledge_ingestions/table_image_extractor.py).
#
# VISION_MAX_CONCURRENCY:
#   Number of INDEPENDENT extraction groups processed in parallel. Pages within
#   a continuation group are always sequential regardless of this value.
#   Default 1 (fully sequential) — start conservative to avoid provider 429s;
#   raise deliberately after observing rate-limit behaviour.
VISION_MAX_CONCURRENCY: int = int(os.getenv("VISION_MAX_CONCURRENCY", "1"))

# Retry count per page. Preserves the previous 3-attempt semantics by default.
VISION_MAX_RETRIES: int = int(os.getenv("VISION_MAX_RETRIES", "3"))

# Exponential backoff for retryable Vision errors (used when the provider does
# not supply a Retry-After). Wait ≈ min(base * 2**attempt, max) + jitter.
VISION_BACKOFF_BASE_SECONDS: float = float(
    os.getenv("VISION_BACKOFF_BASE_SECONDS", "2.0")
)
VISION_BACKOFF_MAX_SECONDS: float = float(
    os.getenv("VISION_BACKOFF_MAX_SECONDS", "30.0")
)
VISION_BACKOFF_JITTER_SECONDS: float = float(
    os.getenv("VISION_BACKOFF_JITTER_SECONDS", "1.0")
)

# Pause between sequential page calls within a group (gentle pacing vs 429).
VISION_INTER_PAGE_DELAY_SECONDS: float = float(
    os.getenv("VISION_INTER_PAGE_DELAY_SECONDS", "2.0")
)


# ── BRD ingestion — workflow extraction model ────────────────────────────────
# Stage 2 of BRD ingestion (app/knowledge_ingestions/worfklow_extractors.py,
# WorkflowExtractor.extract) prefers Gemini, then falls back to OpenRouter.
#
# The shared OpenRouter provider default (OPENROUTER_MODEL, "openai/gpt-4o-mini")
# is too weak for large, dense BRDs — it under-extracts and is non-deterministic
# (observed 5–7 actions vs 48 on the same input). This dedicated var lets BRD
# ingestion use a capable model for the OpenRouter fallback WITHOUT changing the
# shared OPENROUTER_MODEL (which the NL workflow-generation pipeline relies on).
#
# Default is a genuinely FREE ($0/$0) finance-tuned model that extracted the
# full BRD well in benchmarking. Override via env if the free landscape changes.
# Scope: BRD ingestion ONLY. The workflow generation pipeline is unaffected.
BRD_EXTRACTION_OPENROUTER_MODEL: str = os.getenv(
    "BRD_EXTRACTION_OPENROUTER_MODEL",
    "inclusionai/ling-3.0-flash-fin:free",
)
