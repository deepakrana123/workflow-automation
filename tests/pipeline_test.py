"""
tests/pipeline_test.py

Full generation pipeline test for workspaces 2, 34, 5.
Tests: workspace info, mapped actions, catalog matching, workflow generation,
       unmapped actions, chains, business rules, execution.
Produces a structured report.
"""

import json
import time
import requests

BASE = "http://localhost:8000/api"
WORKSPACE_IDS = [2, 34, 5]
DOMAIN = "finance"

# Generation requests — one per workspace
GENERATION_REQUESTS = {
    2:  "Generate a loan origination workflow starting from application receipt through KYC, credit assessment, and disbursement",
    34: "Generate a collections workflow for overdue accounts starting from early warning signal through recovery agent assignment",
    5:  "Generate an account opening workflow starting from KYC verification through account creation and welcome notification",
}

results = {}

def step(label):
    print(f"\n{'='*60}")
    print(f"  {label}")
    print('='*60)

def ok(msg): print(f"  ✓  {msg}")
def fail(msg): print(f"  ✗  {msg}")
def info(msg): print(f"  ·  {msg}")


def test_workspace(ws_id):
    r = {}
    print(f"\n{'#'*70}")
    print(f"  WORKSPACE {ws_id}")
    print(f"{'#'*70}")

    # ── 1. Workspace info ─────────────────────────────────────────────────────
    step(f"1. Workspace info [{ws_id}]")
    try:
        res = requests.get(f"{BASE}/workspaces/{ws_id}", timeout=10)
        if res.status_code == 200:
            ws = res.json()
            ok(f"name={ws.get('name')} level={ws.get('level')} active={ws.get('active')}")
            r["workspace"] = ws
        else:
            fail(f"GET /workspaces/{ws_id} → {res.status_code}: {res.text[:200]}")
            r["workspace_error"] = res.text[:200]
    except Exception as e:
        fail(f"Connection error: {e}")
        r["workspace_error"] = str(e)
        return r

    # ── 2. Overview ───────────────────────────────────────────────────────────
    step(f"2. Workspace overview [{ws_id}]")
    try:
        res = requests.get(f"{BASE}/workspaces/{ws_id}/overview", timeout=10)
        if res.status_code == 200:
            ov = res.json()
            ok(f"brd_count={ov.get('brd_count')} action_count={ov.get('action_count')} "
               f"trigger_count={ov.get('trigger_count')} rule_count={ov.get('business_rule_count')}")
            r["overview"] = ov
        else:
            fail(f"GET /workspaces/{ws_id}/overview → {res.status_code}: {res.text[:200]}")
            r["overview_error"] = res.text[:200]
    except Exception as e:
        fail(f"Exception: {e}")
        r["overview_error"] = str(e)

    # ── 3. Actions ────────────────────────────────────────────────────────────
    step(f"3. Workspace actions [{ws_id}]")
    try:
        res = requests.get(f"{BASE}/workspaces/{ws_id}/actions", timeout=10)
        if res.status_code == 200:
            acts = res.json()
            mapped = acts.get("mapped_actions", [])
            unresolved = acts.get("unresolved_actions", [])
            ok(f"mapped={len(mapped)} unresolved={len(unresolved)}")
            if mapped:
                sample = [a.get("canonical_name") or a.get("name") for a in mapped[:5]]
                info(f"Sample: {sample}")
            r["actions"] = {"mapped": len(mapped), "unresolved": len(unresolved)}
        else:
            fail(f"GET /workspaces/{ws_id}/actions → {res.status_code}: {res.text[:200]}")
            r["actions_error"] = res.text[:200]
    except Exception as e:
        fail(f"Exception: {e}")
        r["actions_error"] = str(e)

    # ── 4. Unmapped actions ───────────────────────────────────────────────────
    step(f"4. Unmapped actions [{ws_id}]")
    try:
        res = requests.get(f"{BASE}/workspaces/{ws_id}/unmapped-actions", timeout=10)
        if res.status_code == 200:
            data = res.json()
            unmapped = data.get("unmapped_actions", [])
            ok(f"unmapped={len(unmapped)}")
            for u in unmapped[:3]:
                info(f"  '{u.get('extract_name')}' from {u.get('source_document')}")
            r["unmapped"] = len(unmapped)
        else:
            fail(f"GET /workspaces/{ws_id}/unmapped-actions → {res.status_code}: {res.text[:200]}")
            r["unmapped_error"] = res.text[:200]
    except Exception as e:
        fail(f"Exception: {e}")
        r["unmapped_error"] = str(e)

    # ── 5. Business rules ─────────────────────────────────────────────────────
    step(f"5. Business rules [{ws_id}]")
    try:
        res = requests.get(f"{BASE}/workspaces/{ws_id}/business-rules", timeout=10)
        if res.status_code == 200:
            data = res.json()
            rules = data.get("business_rules", [])
            ok(f"rules={len(rules)}")
            for rule in rules[:3]:
                info(f"  [{rule.get('source_document','')}] {rule.get('rule','')[:80]}")
            r["business_rules"] = len(rules)
        else:
            fail(f"GET /workspaces/{ws_id}/business-rules → {res.status_code}: {res.text[:200]}")
            r["business_rules_error"] = res.text[:200]
    except Exception as e:
        fail(f"Exception: {e}")
        r["business_rules_error"] = str(e)

    # ── 6. Workflow generation ─────────────────────────────────────────────────
    step(f"6. Workflow generation [{ws_id}]")
    user_request = GENERATION_REQUESTS.get(ws_id,
        "Generate a basic loan processing workflow with KYC and approval steps")
    payload = {
        "name":          f"test_workflow_ws{ws_id}_{int(time.time())}",
        "user_request":  user_request,
        "domain":        DOMAIN,
        "selected_action_ids": [],
    }
    info(f"Request: '{user_request[:80]}...'")
    try:
        t0 = time.time()
        res = requests.post(
            f"{BASE}/workspaces/{ws_id}/generate",
            json=payload,
            timeout=120,
        )
        elapsed = round(time.time() - t0, 2)

        if res.status_code == 200:
            wf = res.json()
            wf_id = wf.get("workflow_id")
            steps = (wf.get("parsed_rule_json") or {}).get("steps", [])
            ok(f"Generated workflow_id={wf_id} steps={len(steps)} time={elapsed}s")
            for s in steps:
                info(f"  Step {s.get('id')}: {s.get('action')} depends_on={s.get('depends_on')}")
            r["generation"] = {
                "status":      "success",
                "workflow_id": wf_id,
                "step_count":  len(steps),
                "elapsed_s":   elapsed,
                "steps":       [{"id": s.get("id"), "action": s.get("action")} for s in steps],
            }

            # ── 7. Dispatch execution ─────────────────────────────────────────
            step(f"7. Execute workflow [{ws_id}] wf_id={wf_id}")
            exec_payload = {"workflow_id": wf_id, "entity_id": f"TEST-ENTITY-WS{ws_id}"}
            try:
                er = requests.post(f"{BASE}/execute/", json=exec_payload, timeout=15)
                if er.status_code == 200:
                    ed = er.json()
                    if ed.get("success"):
                        ok(f"Queued — run_id={ed.get('workflow_run_id')} exec_id={ed.get('workflow_execution_id')}")
                        r["execution"] = {"status": "queued", **ed}
                        # Wait briefly and check execution status
                        time.sleep(3)
                        exec_id = ed.get("workflow_execution_id")
                        if exec_id:
                            sr = requests.get(f"{BASE}/executions/{exec_id}", timeout=10)
                            if sr.status_code == 200:
                                st = sr.json()
                                info(f"Status after 3s: {st.get('status')}")
                                r["execution"]["status_after_3s"] = st.get("status")
                                r["execution"]["steps"] = [
                                    {"name": s.get("step_name"), "status": s.get("status")}
                                    for s in (st.get("steps") or [])
                                ]
                    else:
                        fail(f"Dispatch failed: {ed.get('message')}")
                        r["execution"] = {"status": "failed", "message": ed.get("message")}
                else:
                    fail(f"POST /execute → {er.status_code}: {er.text[:200]}")
                    r["execution"] = {"status": "error", "http": er.status_code, "body": er.text[:200]}
            except Exception as ee:
                fail(f"Execution exception: {ee}")
                r["execution"] = {"status": "exception", "error": str(ee)}

        else:
            fail(f"POST /generate → {res.status_code}: {res.text[:300]}")
            r["generation"] = {
                "status":    "failed",
                "http":      res.status_code,
                "error":     res.text[:300],
                "elapsed_s": elapsed,
            }
    except requests.exceptions.Timeout:
        fail(f"Generation timed out after 120s")
        r["generation"] = {"status": "timeout", "elapsed_s": 120}
    except Exception as e:
        fail(f"Exception during generation: {e}")
        r["generation"] = {"status": "exception", "error": str(e)}

    # ── 8. Existing workflows ─────────────────────────────────────────────────
    step(f"8. Existing workflows [{ws_id}]")
    try:
        res = requests.get(f"{BASE}/workflows/?workspace_id={ws_id}", timeout=10)
        if res.status_code == 200:
            wfs = res.json()
            ok(f"total_workflows={len(wfs)}")
            for w in wfs[:3]:
                steps_n = len((w.get("parsed_rule_json") or {}).get("steps", []))
                info(f"  #{w.get('id')} '{w.get('name')}' steps={steps_n} status={w.get('status')}")
            r["existing_workflows"] = len(wfs)
        else:
            fail(f"GET /workflows/?workspace_id={ws_id} → {res.status_code}: {res.text[:200]}")
            r["existing_workflows_error"] = res.text[:200]
    except Exception as e:
        fail(f"Exception: {e}")
        r["existing_workflows_error"] = str(e)

    # ── 9. Chains ─────────────────────────────────────────────────────────────
    step(f"9. Workflow chains [{ws_id}]")
    try:
        res = requests.get(f"{BASE}/workspaces/{ws_id}/chains", timeout=10)
        if res.status_code == 200:
            chains = res.json()
            ok(f"chains={len(chains)}")
            for c in chains[:3]:
                info(f"  {c.get('source_action')} → {c.get('target_trigger')} "
                     f"({c.get('match_type')} {c.get('confidence')} {c.get('status')})")
            r["chains"] = len(chains)
        else:
            fail(f"GET /workspaces/{ws_id}/chains → {res.status_code}: {res.text[:200]}")
            r["chains_error"] = res.text[:200]
    except Exception as e:
        fail(f"Exception: {e}")
        r["chains_error"] = str(e)

    # ── 10. Diagnostics ────────────────────────────────────────────────────────
    step(f"10. Mapping diagnostics [{ws_id}]")
    try:
        res = requests.get(f"{BASE}/workspaces/{ws_id}/diagnostics", timeout=10)
        if res.status_code == 200:
            diag = res.json()
            totals = diag.get("totals", {})
            ok(f"extracted={totals.get('extracted_actions')} "
               f"mapped={totals.get('mapped')} "
               f"unmapped={totals.get('unmapped')} "
               f"retrieval_miss={totals.get('retrieval_miss')}")
            r["diagnostics"] = totals
        else:
            fail(f"GET /workspaces/{ws_id}/diagnostics → {res.status_code}: {res.text[:200]}")
            r["diagnostics_error"] = res.text[:200]
    except Exception as e:
        fail(f"Exception: {e}")
        r["diagnostics_error"] = str(e)

    return r


# ── Health check ───────────────────────────────────────────────────────────────
step("HEALTH CHECK")
try:
    h = requests.get(f"{BASE}/health/", timeout=10)
    if h.status_code == 200:
        hd = h.json()
        ok(f"API up — db={hd.get('db_ok')} redis={hd.get('redis_ok')}")
        if not hd.get("redis_ok"):
            fail("Redis is DOWN — execution queue will not work (consumer cannot dequeue)")
    else:
        fail(f"Health check failed: {h.status_code}")
except Exception as e:
    fail(f"API not reachable: {e}")
    print("\nServer is not ready yet. Exiting.")
    exit(1)

# ── Run tests ──────────────────────────────────────────────────────────────────
for ws_id in WORKSPACE_IDS:
    results[ws_id] = test_workspace(ws_id)

# ── Final report ───────────────────────────────────────────────────────────────
print(f"\n\n{'='*70}")
print("  FINAL REPORT")
print(f"{'='*70}\n")

vulnerabilities = []
for ws_id, r in results.items():
    print(f"Workspace {ws_id}:")

    gen = r.get("generation", {})
    if gen.get("status") == "success":
        print(f"  Generation:  ✓  workflow_id={gen.get('workflow_id')} "
              f"steps={gen.get('step_count')} time={gen.get('elapsed_s')}s")
    else:
        print(f"  Generation:  ✗  status={gen.get('status')} error={gen.get('error','')[:80]}")
        vulnerabilities.append(f"WS{ws_id}: Generation failed — {gen.get('status')}: {gen.get('error','')[:80]}")

    exe = r.get("execution", {})
    if exe.get("status") in ("queued", "success"):
        print(f"  Execution:   ✓  status_after_3s={exe.get('status_after_3s','unknown')}")
        after = exe.get("status_after_3s", "")
        if after not in ("COMPLETED", "RUNNING", "PENDING", ""):
            vulnerabilities.append(f"WS{ws_id}: Execution status '{after}' unexpected")
    elif exe:
        print(f"  Execution:   ✗  {exe.get('status')} {exe.get('error','')[:60]}")
        if exe.get("status") == "failed" and "already has an active execution" in (exe.get("message") or ""):
            pass  # Expected — duplicate guard
        else:
            vulnerabilities.append(f"WS{ws_id}: Execution failed — {exe.get('status')}: {exe.get('error','')[:60]}")

    unmapped = r.get("unmapped", 0)
    if unmapped and unmapped > 0:
        print(f"  Unmapped:    ⚠  {unmapped} actions need manual resolution")
        vulnerabilities.append(f"WS{ws_id}: {unmapped} unmapped actions — reduce retrieval threshold or resolve manually")

    diag = r.get("diagnostics", {})
    miss = diag.get("retrieval_miss", 0)
    if miss and miss > 3:
        vulnerabilities.append(f"WS{ws_id}: {miss} retrieval misses — catalog coverage gap")

    redis_issue = r.get("execution", {}).get("status") == "queued" and \
                  r.get("execution", {}).get("status_after_3s") in (None, "PENDING")
    if redis_issue:
        vulnerabilities.append(f"WS{ws_id}: Execution PENDING after 3s — Redis consumer may not be running")

    print(f"  BRDs:        {r.get('overview',{}).get('brd_count','?')}")
    print(f"  Mapped:      {r.get('actions',{}).get('mapped','?')}")
    print(f"  Rules:       {r.get('business_rules','?')}")
    print(f"  Chains:      {r.get('chains','?')}")
    print()

print(f"\n{'─'*70}")
print("VULNERABILITIES AND ISSUES FOUND:")
print(f"{'─'*70}")
if vulnerabilities:
    for i, v in enumerate(vulnerabilities, 1):
        print(f"  {i}. {v}")
else:
    print("  None found.")

# Redis warning always
print("\nNOTE: Redis is not running locally — workflow execution queue is unavailable.")
print("      The execute endpoint queues to Redis but the consumer cannot dequeue.")
print("      All generation tests are unaffected. Execution status will remain PENDING.")

with open("tests/pipeline_report.json", "w") as f:
    json.dump({"workspaces": results, "vulnerabilities": vulnerabilities}, f, indent=2, default=str)
print("\nFull report saved: tests/pipeline_report.json")
