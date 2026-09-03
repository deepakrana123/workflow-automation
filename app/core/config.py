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
