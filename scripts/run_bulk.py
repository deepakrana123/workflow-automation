"""
scripts/run_bulk.py

Fires 30-40 executions spread across all active workflows.

Usage:
    python scripts/run_bulk.py
    python scripts/run_bulk.py --base-url http://localhost:8000  # default
    python scripts/run_bulk.py --iterations 40
"""

import sys
import os
import time
import random
import argparse
import urllib.request
import urllib.error
import json

BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


def get(path: str):
    url = f"{BASE_URL}{path}"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())


def post(path: str, body: dict):
    url = f"{BASE_URL}{path}"
    data = json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read()), r.status
    except urllib.error.HTTPError as e:
        return json.loads(e.read()), e.code


def main(iterations: int):
    # ── Fetch active workflows ────────────────────────────────────────────────
    workflows = get("/api/workflows")
    if not workflows:
        print("No active workflows found. Exiting.")
        sys.exit(1)

    print(f"Found {len(workflows)} active workflow(s):")
    for w in workflows:
        print(f"  [{w['id']}] {w['name']}")

    # ── Build entity IDs — realistic loan/customer IDs ────────────────────────
    prefixes = ["LOAN", "HL", "CAR", "BIZ", "CUST", "ACC", "CASE"]
    entity_ids = [
        f"{random.choice(prefixes)}-{random.randint(100000, 999999)}"
        for _ in range(iterations)
    ]

    # ── Distribute iterations round-robin across workflows ────────────────────
    print(f"\nFiring {iterations} executions across {len(workflows)} workflow(s)…\n")

    ok = 0
    skipped = 0
    failed = 0

    for i, entity_id in enumerate(entity_ids):
        workflow = workflows[i % len(workflows)]
        wf_id    = workflow["id"]
        wf_name  = workflow["name"][:50]

        body = {"workflow_id": wf_id, "entity_id": entity_id}
        result, status = post("/api/execute/", body)

        if status in (200, 201) and result.get("success"):
            exec_id = result.get("workflow_execution_id", "?")
            print(f"  [{i+1:02d}] ✓  wf={wf_id} entity={entity_id:20s}  exec_id={exec_id}")
            ok += 1
        elif status in (200, 201) and not result.get("success"):
            # duplicate guard fired — already has an active execution
            msg = result.get("message", "")
            print(f"  [{i+1:02d}] ~  wf={wf_id} entity={entity_id:20s}  skipped ({msg})")
            skipped += 1
        else:
            print(f"  [{i+1:02d}] ✗  wf={wf_id} entity={entity_id:20s}  HTTP {status} {result}")
            failed += 1

        # Small pause to avoid hammering Redis with all events at once
        time.sleep(0.15)

    print(f"\n── Summary ──────────────────────────────")
    print(f"  Queued:   {ok}")
    print(f"  Skipped:  {skipped}  (duplicate guard)")
    print(f"  Failed:   {failed}")
    print(f"  Total:    {iterations}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url",   default=os.getenv("API_BASE_URL", "http://localhost:8000"))
    parser.add_argument("--iterations", default=40, type=int)
    args = parser.parse_args()
    BASE_URL = args.base_url
    main(args.iterations)
