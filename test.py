"""
MFlows — Chaos Test Suite
Hits POST /api/workflows/generate with 80+ payloads.

Categories:
  A. Happy path         — clean NL inputs, all domains (20 cases)
  B. Phrasing variants  — synonyms, typos, unusual word order (15 cases)
  C. Multi-action       — 2-4 actions, sequential dependencies (10 cases)
  D. Edge cases         — empty, single word, very long, special chars (10 cases)
  E. Bad domain         — invalid / missing domain (5 cases)
  F. Unsupported intent — unknown triggers/actions (10 cases)
  G. Boundary inputs    — minimal valid, unicode, numbers in text (10 cases)

Run:
    python test.py                  — run all categories
    python test.py --category A     — run one category
    python test.py --stop-on-fail   — stop at first failure

Requirements:
    pip install requests
    API must be running: docker-compose up --build
"""

import sys
import json
import time
import argparse
import requests
from dataclasses import dataclass, field
from typing import Optional

BASE_URL = "http://localhost:8000/api"
GENERATE_URL = f"{BASE_URL}/workflows/generate"
TIMEOUT = 60  # seconds per request


# ─────────────────────────────────────────────────────────────────────────────
# Test case definition
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class TestCase:
    id: str
    category: str
    description: str
    payload: dict
    expect_success: bool = True
    expected_error_contains: Optional[str] = None




# ─────────────────────────────────────────────────────────────────────────────
# Result tracking
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class TestResult:
    case: TestCase
    passed: bool
    status_code: int
    latency_ms: int
    response: dict
    failure_reason: str = ""


# ─────────────────────────────────────────────────────────────────────────────
# Runner
# ─────────────────────────────────────────────────────────────────────────────

def run_case(case: TestCase) -> TestResult:
    start = time.time()
    try:
        resp = requests.post(
            GENERATE_URL,
            json=case.payload,
            timeout=TIMEOUT,
        )
        latency_ms = int((time.time() - start) * 1000)
        try:
            body = resp.json()
        except Exception:
            body = {"raw": resp.text[:300]}

        http_success = resp.status_code < 400

        if case.expect_success:
            passed = (
                http_success
                and isinstance(body, dict)
                and body.get("workflow_id") is not None
            )
            failure_reason = "" if passed else (
                f"Expected workflow_id, got {resp.status_code}: "
                f"{json.dumps(body)[:200]}"
            )
        else:
            # Expect failure — 4xx or contains expected error
            passed = not http_success
            if passed and case.expected_error_contains:
                detail = str(body.get("detail", "")).lower()
                passed = case.expected_error_contains.lower() in detail
                if not passed:
                    failure_reason = (
                        f"Expected error containing '{case.expected_error_contains}', "
                        f"got: {detail[:120]}"
                    )
            else:
                failure_reason = (
                    "" if passed
                    else f"Expected failure but got {resp.status_code}: {json.dumps(body)[:200]}"
                )

        return TestResult(
            case=case,
            passed=passed,
            status_code=resp.status_code,
            latency_ms=latency_ms,
            response=body,
            failure_reason=failure_reason,
        )

    except requests.ConnectionError:
        latency_ms = int((time.time() - start) * 1000)
        return TestResult(
            case=case,
            passed=False,
            status_code=0,
            latency_ms=latency_ms,
            response={},
            failure_reason="CONNECTION_REFUSED — is the API running?",
        )
    except requests.Timeout:
        latency_ms = int((time.time() - start) * 1000)
        return TestResult(
            case=case,
            passed=False,
            status_code=0,
            latency_ms=latency_ms,
            response={},
            failure_reason=f"TIMEOUT after {TIMEOUT}s",
        )
    except Exception as e:
        latency_ms = int((time.time() - start) * 1000)
        return TestResult(
            case=case,
            passed=False,
            status_code=0,
            latency_ms=latency_ms,
            response={},
            failure_reason=f"EXCEPTION: {str(e)[:200]}",
        )


def print_result(r: TestResult, verbose: bool = False) -> None:
    icon = "✅" if r.passed else "❌"
    print(
        f"{icon} [{r.case.id}] {r.case.description:<55} "
        f"{r.status_code}  {r.latency_ms}ms"
    )
    if not r.passed:
        print(f"      → {r.failure_reason}")
        if verbose and r.response:
            print(f"      → Response: {json.dumps(r.response)[:300]}")


def print_summary(results: list[TestResult]) -> None:
    total = len(results)
    passed = sum(1 for r in results if r.passed)
    failed = total - passed
    avg_latency = int(sum(r.latency_ms for r in results) / total) if total else 0

    print("\n" + "=" * 80)
    print(f"TOTAL: {total}   ✅ PASSED: {passed}   ❌ FAILED: {failed}")
    print(f"AVG LATENCY: {avg_latency}ms")
    print("=" * 80)

    # Category breakdown
    categories: dict[str, list[TestResult]] = {}
    for r in results:
        categories.setdefault(r.case.category, []).append(r)

    print("\nBy Category:")
    for cat, cat_results in sorted(categories.items()):
        cat_pass = sum(1 for r in cat_results if r.passed)
        print(
            f"  {cat}: {cat_pass}/{len(cat_results)} passed  "
            f"({'%.0f' % (cat_pass / len(cat_results) * 100)}%)"
        )

    if failed:
        print("\nFailed Cases:")
        for r in results:
            if not r.passed:
                print(f"  ❌ [{r.case.id}] {r.case.description}")
                print(f"       {r.failure_reason}")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="MFlows chaos test suite")
    parser.add_argument(
        "--category",
        choices=["A", "B", "C", "D", "E", "F", "G"],
        help="Run only a specific category",
    )
    parser.add_argument(
        "--stop-on-fail",
        action="store_true",
        help="Stop at first failure",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print response bodies on failure",
    )
    parser.add_argument(
        "--id",
        help="Run a single test case by ID (e.g. A01)",
    )
    args = parser.parse_args()

    # Select cases
    if args.id:
        cases = [c for c in ALL_CASES if c.id == args.id.upper()]
        if not cases:
            print(f"No test case found with id '{args.id}'")
            sys.exit(1)
    elif args.category:
        cases = CATEGORIES[args.category]
    else:
        cases = ALL_CASES

    print(f"\nMFlows Chaos Test Suite — {len(cases)} cases → {GENERATE_URL}")
    print("=" * 80)

    results = []
    for case in cases:
        result = run_case(case)
        results.append(result)
        print_result(result, verbose=args.verbose)

        if args.stop_on_fail and not result.passed:
            print("\n[--stop-on-fail] Stopping at first failure.")
            break

    print_summary(results)

    # Exit code — non-zero if any failures
    failed = sum(1 for r in results if not r.passed)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
