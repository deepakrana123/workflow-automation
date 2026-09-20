# Build Guide — Business-Rules Chatbot (implementation steps)

> Companion to `docs/chatbot_business_rules_design.md` (the design/rationale). This is the
> concrete, additive build plan. New router + service only — no existing logic rewritten.

## 0. Verdict
Buildable as a new **read** surface over existing data. Reuses `WorkflowBusinessRule`,
`WorkspaceSynthesisService`, `RetrievalPipeline`, `LLMManager`, RBAC, `trace_service`.

## 1. Components to add (additive)
1. `app/routes/chat.py` — new router (mounted under `/api`).
2. `app/services/chat_service.py` — `ChatService` orchestrating retrieve → ground → cite → audit.
3. (Optional) `ChatThread` / `ChatMessage` models + migration for conversation history/audit.
4. (Optional) a rules index/embedding step so retrieval is semantic (else keyword/FTS on rules).

## 2. Endpoints
```
POST /api/workspaces/{id}/chat
  body: { question: str, user_roles?: [str], thread_id?: str }
  resp: {
    answer: str,
    citations: [{ rule, source_document, clause, hierarchy_level }],
    conflicts?: [...],           // from detect_rule_conflicts
    thread_id: str
  }
GET  /api/workspaces/{id}/chat/threads        # audited history (optional)
```

## 3. ChatService flow (per question)
1. **Resolve scope** — workspace_id (+ parent chain for hierarchy inheritance) and the caller's roles.
2. **Retrieve rules** — pull candidate `WorkflowBusinessRule` rows for the workspace(+inherited),
   ranked by relevance to the question. Options:
   - reuse `RetrievalPipeline` (embed rules once; vector+BM25+FTS), or
   - simpler v1: Postgres FTS / keyword over `rule` + `condition` + `outcome`.
3. **RBAC filter** — keep only rules the caller may see: intersect caller roles with each rule's
   `responsible_role` (+ workspace membership). Reuse the `CapabilityService` RBAC pattern.
4. **Ground + answer** — `LLMManager` answers using ONLY the retrieved rules; instruct it to cite
   each claim (`source_document` + `clause` + hierarchy level) and to say "not specified" if no
   rule supports the answer (no hallucinated policy).
5. **Conflicts** — optionally surface `detect_rule_conflicts` output for the topic.
6. **Audit** — log the turn (user, roles, question, retrieved rule ids, answer, thread) via the
   `trace_service` pattern.

## 4. Data reuse map
| Need | Source |
|---|---|
| Rules | `WorkflowBusinessRule` (rule/condition/outcome/responsible_role/threshold, workspace_id) |
| Aggregated/deduped + conflicts | `WorkspaceSynthesisService.for_workspace`, `detect_rule_conflicts` |
| Retrieval | `RetrievalPipeline` (or FTS v1) |
| LLM | `LLMManager` |
| Roles/RBAC | rule `responsible_role`, `CapabilityService` RBAC pattern, `RuleExtractionService` |
| Hierarchy | `Workspace` parent chain (branch→zone→region→global) |
| Audit | `trace_service` |

## 5. Scoping guarantees
- **Single-tenant** = deployment = one bank (`DATABASE_URL`). No cross-tenant data.
- **Per-workspace** retrieval filter + system prompt → answers as that branch's policy expert.
- **Hierarchy inheritance** → branch sees branch + inherited region/global rules, labeled by level.

## 6. Capability ladder
1. **Q&A** (grounded + cited) — MVP.
2. **Explain/trace** — join answer to execution trace (`ExecutionStep`/`trace_service`).
3. **Author/edit rules via chat** — RBAC + approval + versioning.
4. **Agentic** — chat → generate/trigger a workflow (`nl_workflow_service`), RBAC/approval-gated.

## 7. Phases
1. Router + ChatService + FTS retrieval + grounded/cited answer (no history).
2. RBAC read-scoping by role.
3. Audit every turn (+ optional thread history tables).
4. Semantic retrieval (embed rules), conflict surfacing.
5. Explain/trace, then author, then agentic.

## 8. Guardrails / non-goals
- No cross-workspace/tenant leakage (scoping filters enforce it).
- Always cite; never answer beyond retrieved rules.
- Any write/act only via approval + RBAC.

## 9. Files touched (summary)
- **New:** `app/routes/chat.py`, `app/services/chat_service.py`, (optional) chat history models + migration.
- **Wiring:** mount the chat router in `app/main.py`. No changes to ingestion/execution/workflow logic.
