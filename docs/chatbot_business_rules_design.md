# Chatbot Design — "Chat with your Business Rules" (RBAC-scoped, workspace-aware, single-tenant)

> Status: design / proposal. Grounded in the existing mflows architecture. Nothing here
> changes production yet — it documents *how* to build the chatbot on top of what already exists.

## 1. What it is
A conversational interface over a workspace's extracted **business rules** (and the wider
BRD knowledge), so a banker can ask things like:

- "What's the max LTV for a used-car loan?"
- "Who approves a deviation above ₹5 lakh?"
- "Why was applicant X rejected?"
- "Which rules conflict on approval limits?"

Answers are **grounded** in that workspace's rules only, **cited** back to the source BRD +
clause, **RBAC-filtered** to what the user is allowed to see, and **audited**.

## 2. Why it's mostly assembly, not new invention
Every ingredient already exists in mflows:

| Need | Existing component |
|------|--------------------|
| Rules as structured data | `WorkflowBusinessRule` (`rule`, `condition`, `outcome`, `responsible_role`, `threshold`), per `WorkflowKnowledge`, per `workspace_id` |
| Aggregated/deduped view | `WorkspaceSynthesisService.for_workspace` (+ `detect_rule_conflicts`) |
| Retrieval stack | `RetrievalPipeline` (vector + BM25 + Postgres FTS + cross-encoder) over pgvector |
| LLM | `LLMManager` (Gemini → OpenRouter waterfall) |
| Org structure | `Workspace` hierarchy: global → region → zone → branch |
| Role signals | `responsible_role` on rules, `allowed_roles` on human tasks, `CapabilityService` RBAC on actions, `RuleExtractionService` role shapes |
| Audit | `trace_service` pattern |

The chatbot is a new **read** surface (and later a guarded **act** surface) over this data.

## 3. Scoping model
- **Single-tenant** = the deployment is one bank; `DATABASE_URL` *is* the tenant boundary. No
  cross-tenant mixing. (If multi-tenant is needed later, add `tenant_id` above `workspace_id`.)
- **Per-workspace "persona"** = the chat's retrieval filter + system prompt are scoped to one
  workspace, so it answers as *that branch's* policy expert.
- **Hierarchy inheritance** = a branch chat sees branch rules **plus** inherited region/global
  rules, and can show which level a rule came from (and where a branch overrides).

## 4. RBAC — who can ask what / do what
Two layers:
1. **Read scope** — filter retrieved rules by the user's role: intersect the user's RBAC roles
   with each rule's `responsible_role` (+ workspace membership). A Sales Executive sees sourcing
   rules; a Compliance Officer sees AML/compliance rules. Reuse the `CapabilityService` RBAC
   pattern that already does this for actions.
2. **Act scope** (only if the chat can trigger actions/workflows) — gate each action by
   `allowed_roles`/`responsible_actors`; route write / `is_state_changing` actions through the
   human-approval path (`HumanExecutor`).

## 5. Core flow ("chat with policy" = RBAC-scoped RAG)
```
user question
   │
   ▼
resolve user roles + workspace (+ parent chain for inheritance)
   │
   ▼
retrieve candidate rules  (RetrievalPipeline, filtered by workspace + RBAC + role)
   │
   ▼
LLM answer  (LLMManager)  grounded ONLY in retrieved rules, with citations
   │                        (source_document + clause + hierarchy level)
   ▼
audit the turn  (who asked / rules retrieved / answer / any action)  → trace_service
```
- **Grounding** prevents hallucinated policy (critical for banking).
- **Citations** give explainability (regulator-friendly).
- **Conflict awareness**: surface `detect_rule_conflicts` results conversationally.

## 6. Capability ladder (pick how far to go)
1. **Q&A** over rules — grounded + cited. *(start here)*
2. **Explain / trace** — "why was applicant X rejected?" → join the rule to the execution trace
   (`ExecutionStep` / `trace_service`).
3. **Author / edit rules via chat** — propose changes, gated by RBAC + approval, versioned.
4. **Agentic** — chat → generate/trigger a workflow from rules (ties into `nl_workflow_service`),
   RBAC- and approval-gated.

## 7. Suggested API surface (new router, additive)
```
POST /api/workspaces/{id}/chat            # ask a question (RBAC + workspace scoped)
  body: { question, user_roles?, thread_id? }
  resp: { answer, citations:[{rule, source_document, clause, level}], conflicts?, thread_id }

GET  /api/workspaces/{id}/chat/threads    # history (audited)
```
Internally reuses `WorkspaceSynthesisService`, `RetrievalPipeline`, `LLMManager`, RBAC, `trace_service`.

## 8. Governance (the differentiator)
Log every turn — who asked, which rules were retrieved, what was answered/acted — via the
`trace_service`/audit pattern. Combined with RBAC read-scoping, a user cannot extract policy
outside their authority, and every answer is auditable. This is **governed conversational policy
access** — a real selling point for regulated banks.

## 9. Build phases
1. **Index** workspace rules for retrieval (embed rule text + condition/outcome/threshold; keep
   `source_document`, `clause`, hierarchy level as metadata).
2. **Retrieve + ground + cite** (Q&A) — the MVP.
3. **RBAC read-scoping** — filter by role.
4. **Audit** every turn.
5. **Explain/trace**, then **author**, then **agentic** — incrementally.

## 10. Non-goals / guardrails
- No cross-workspace or cross-tenant data leakage (enforced by scoping filters).
- No ungrounded answers (always cite; if no rule supports it, say so).
- Write/act only through approval + RBAC.
