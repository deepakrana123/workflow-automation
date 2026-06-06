from app.core.config import MAX_RETRIES, BASE_DELAY_SECONDS


def should_retry(attempts: int) -> bool:
    return attempts <= MAX_RETRIES


def calculate_delay(attempts: int) -> int:
    return BASE_DELAY_SECONDS * (2 ** (attempts - 1))
