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
