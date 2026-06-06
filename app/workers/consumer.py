import json
from app.core.redis_client import redis_client
from app.db.session import SessionLocal
from app.core.logger import logger
from concurrent.futures import ThreadPoolExecutor
from app.execution.runtime_processor import runtime_processor

QUEUE = "workflow_events"
MAX_WORKERS = 5


def handle_event(payload: dict):
    db = SessionLocal()
    try:
        workflow_execution_id = payload.get("workflow_execution_id")
        if not workflow_execution_id:
            logger.error(
                "consumer_missing_workflow_execution_id",
                extra={"extra_data": {"payload": payload}},
            )
            return

        runtime_processor(db=db, workflow_execution_id=workflow_execution_id)

    except Exception as e:
        logger.error(
            "consumer_worker_error",
            extra={"extra_data": {"error": str(e), "payload": payload}},
        )
    finally:
        db.close()


def worker():
    executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)
    logger.info("consumer_worker_started")
    while True:
        item = redis_client.brpop(QUEUE, timeout=5)
        if not item:
            continue
        _, event_data = item
        payload = json.loads(event_data)
        executor.submit(handle_event, payload)


if __name__ == "__main__":
    print("Worker started...", flush=True)
    worker()
