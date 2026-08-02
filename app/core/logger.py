import logging
import json


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            "level":     record.levelname,
            "message":   record.getMessage(),
            "timestamp": self.formatTime(record),
        }
        if hasattr(record, "extra_data"):
            log_record.update(record.extra_data)
        return json.dumps(log_record)


logger = logging.getLogger("workflow")

# Prevent duplicate emission when a root handler is also configured
logger.propagate = False

handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())

# Only add handler once — guard against module being imported multiple times
if not logger.handlers:
    logger.addHandler(handler)

logger.setLevel(logging.INFO)
