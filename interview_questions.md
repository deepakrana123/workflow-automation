# FlowOS Backend — Senior Software Engineer Interview Questions

These questions are grounded in the actual architecture and implementation
decisions made during the FlowOS Multi-Tenant Personal Loan Sourcing Platform
build. Every question maps to something that was designed, debated, or
implemented in this codebase.

---

## Section 1 — Multi-Tenant Architecture

**1.**
We modelled Tenant as a bank and Workspace as a product/knowledge domain inside
that bank. What are the tradeoffs of this two-level isolation hierarchy compared
to a single-level tenant model where every bank directly owns all resources?

**2.**
The `workspaces` table has a composite unique constraint `UNIQUE(tenant_id, name)`
instead of a global `UNIQUE(name)`. Explain why. What would break if you kept
the global uniqueness instead?

**3.**
`BRDDocument` carries a denormalised `tenant_id` column even though
`workspace.tenant_id` already implies it. Why was this decision made? What
query patterns does it enable, and what invariant must the application enforce
to keep it correct?

**4.**
When we removed the geographical workspace hierarchy (global / region / zone /
branch), several RBAC and rule-inheritance components depended on
`get_ancestor_chain()`. What is the safest migration strategy for removing a
function that has seven confirmed call sites across different subsystems?

**5.**
The existing `workspaces` table had a `UNIQUE(name)` constraint. We needed to
replace it with `UNIQUE(tenant_id, name)` without losing existing data. Walk
through the exact migration steps in correct order, explaining why each step
must come before the next.

**6.**
We have a `Tenant → Workspace → BRDDocument → DocumentVersion → IngestionAttempt`
ownership chain. A query arrives with a `document_version_id`. What is the
minimum number of joins required to verify that the version belongs to a
specific tenant, and how would you optimise this for a hot path?

---

## Section 2 — Database Design and SQLAlchemy

**7.**
The `BRDDocument` model uses a plain `VARCHAR` column with a `CHECK` constraint
for `ingestion_status` rather than a PostgreSQL native `ENUM` type. What are the
tradeoffs of each approach in a production system using Alembic for migrations?

**8.**
`DocumentVersion` has two separate unique constraints:
- `UNIQUE(document_id, version_number)`
- `UNIQUE(document_id, sha256_hash)`

What is each one protecting against? Could you replace both with a single
constraint? Why or why not?

**9.**
The `IngestionAttempt` model uses `attempt_number` as a monotonically increasing
integer within a version. The service assigns it as `MAX(attempt_number) + 1`.
What is the race condition here, and how would you fix it without introducing
a distributed lock?

**10.**
Explain the difference between `db.flush()` and `db.commit()` in SQLAlchemy.
In the tenant registration flow, we call `db.flush()` after adding the Tenant
but before creating the Workspace. Why is this necessary, and what would happen
if you called `db.commit()` instead at that point?

**11.**
In `WorkflowKnowledge`, we added a nullable `brd_document_id` FK with
`ON DELETE SET NULL`. Why nullable? Why `SET NULL` rather than `CASCADE`?
What does this choice say about the relationship between extraction output
and its source document?

**12.**
The `RoleAssignment` model has `UniqueConstraint("user_id", "workspace_id")`.
`user_id` is nullable (NULL until a real user is assigned). What does PostgreSQL
do with NULL values in a unique constraint? Does this constraint actually prevent
duplicate unassigned role shapes in the same workspace?

**13.**
You need to add a new non-nullable column to a large production table with
millions of rows. Walk through the safest migration strategy that avoids
locking the table for an extended period in PostgreSQL.

---

## Section 3 — API Design and FastAPI

**14.**
The `POST /api/tenants` endpoint must atomically create a Tenant and a default
Workspace. The current implementation commits the Tenant before creating the
Workspace. Describe exactly what failure scenario this creates, and write the
corrected pseudocode showing the correct flush/commit ordering.

**15.**
The document upload endpoint `POST /knowledge-ingestion/upload` accepts
`workspace_id` as a form field. This means any caller can pass any
`workspace_id` without proving they belong to that tenant. What is the
attack surface, and what is the minimum change to close it without implementing
full JWT authentication?

**16.**
The `WorkspaceCreate` schema previously had `level`, `parent_id`, and
`organization_name` fields. After removing the geographical hierarchy, these
were removed from the schema but the database columns still existed during the
migration window. How do you safely manage this schema/DB drift in a live
system where old API clients may still be sending those fields?

**17.**
We return HTTP 409 for both duplicate tenant name and duplicate workspace name
within a tenant. A client receives a 409. What information must the response
body contain to allow the client to distinguish these two cases
programmatically, without exposing internal DB constraint names?

**18.**
The workspace routes file is over 350 lines and handles CRUD, synthesis,
chain detection, merge suggestions, and BRD generation. What criteria would
you use to decide whether to split this into multiple routers, and what are
the tradeoffs of doing so in a FastAPI application?

---

## Section 4 — Document Storage and File Handling

**19.**
The `DocumentRegistrationService` stores PDF bytes via `FileStorageService`
before writing to the database. If the database commit fails after the file
is stored, the service calls `_cleanup_storage()` to delete the file. This
cleanup can also fail. How do you handle this class of problem — where
two non-atomic systems must be kept consistent — in a production system?

**20.**
The storage key format is:
```
{tenant_id}/{workspace_id}/{sha256[:8]}/{uuid4}_{sanitised_filename}
```
Explain the purpose of each component. What would break if you removed the
`uuid4` component and stored files only by their SHA-256 hash?

**21.**
`_validate_file()` checks that the uploaded bytes start with `%PDF`. What is
the actual security guarantee this provides? What attack does it not prevent?
What additional validation would you add before the bytes reach the LLM
extraction pipeline?

**22.**
The `FileStorageService.store()` method uses a workspace-scoped key:
`{workspace_id}/{file_id}_{filename}`. The `DocumentRegistrationService`
overrides this with a tenant-scoped key that also includes the tenant prefix.
Why was the existing `FileStorageService` not modified? What principle does
this reflect?

**23.**
Two concurrent requests upload the same PDF to the same workspace at exactly
the same time. Walk through what happens at each stage: validation, hash check,
storage write, and DB insert. Where does the race condition manifest, and how
does the current implementation handle it?

---

## Section 5 — Extraction Pipeline

**24.**
The `MultiModalDocumentExtractor.extract()` returns a single merged string.
We identified that this loses page-level provenance. We added
`extract_structured()` that returns a 3-tuple without changing `extract()`.
Why did we not simply change the return type of `extract()`? What principle
does keeping `extract()` unchanged reflect?

**25.**
The extraction pipeline runs three threads concurrently:
- Thread A: pypdf body text
- Thread B: VisionProvider (table/image pages)
- Thread C: TextProvider (appendix pages)

Thread B fails. What happens to threads A and C? Does the document fail entirely?
Show the exact code path that handles this.

**26.**
`PageClassifier` classifies pages using local heuristics — no LLM, no rendering.
What are the signals it uses? What is the deliberate limitation of this approach,
and why was it accepted rather than fixed?

**27.**
The `PdfExtractionPipeline._run_extraction()` calls `PageClassifier.classify()`
twice — once to get `total_pages` and once inside `extract_structured()`. This
was noted as acceptable because classification is cheap. What would you change
if the classification became expensive (e.g. if it called an LLM), without
changing the public interface of `PdfExtractionPipeline`?

**28.**
`DocumentExtractionResult.full_text` returns a merged string with `[Page N]`
markers. This was described as a backward-compatibility bridge for the existing
`WorkflowExtractor`. What is the correct long-term design, and what is the
risk of leaving the bridge in place indefinitely?

**29.**
The `AppendixExtractor` sends all appendix pages as a single combined call to
the `TextProvider`. Why all pages in one call rather than one call per page?
What is the failure characteristic — if the TextProvider fails for page 37 of
a 40-page appendix, what happens to pages 35, 36, 38, 39, 40?

**30.**
`PageExtractionOutput` has a `source_metadata` field typed as `dict` rather
than a typed dataclass. What are the tradeoffs of this design? Under what
conditions would you replace it with a typed schema?

---

## Section 6 — Ingestion Lifecycle and State Machines

**31.**
The `VersionStatus` lifecycle is:
```
REGISTERED → PROCESSING → COMPLETED
                        → FAILED → RETRY_PENDING → PROCESSING
COMPLETED → RETRY_PENDING → PROCESSING
```
Draw the complete state machine. Which transitions are valid but not explicitly
guarded by the application code? What would you add to enforce them?

**32.**
`IngestionAttempt` rows are never updated after reaching `COMPLETED` or `FAILED`
— retries create new rows. What is the operational advantage of this design?
What is the storage cost as retry counts grow? How would you manage it?

**33.**
`BRDDocument.ingestion_status` is described as a "denormalised mirror" of
`DocumentVersion.status`. It was kept for backward compatibility rather than
removed. Write the SQL query that would detect rows where these two fields
are inconsistent with each other.

**34.**
The `AttemptErrorCode` class contains constants like `EMPTY_DOCUMENT`,
`LLM_TIMEOUT`, `NO_ACTIONS_EXTRACTED`. These are plain string constants on
a class, not a Python `Enum`. What are the implications of this choice for
exhaustiveness checking, serialisation, and future refactoring?

---

## Section 7 — RBAC and Rule Inheritance

**35.**
The existing `PermissionChecker.can()` calls `get_ancestor_chain()` which reads
`workspace.parent_id` and `workspace.level` — both columns that were commented
out of the ORM model. What happens at runtime when this code executes? Why
does it not raise `AttributeError` immediately at import time?

**36.**
`resolve_effective_rules()` collects `BusinessRuleDefinition` rows from all
ancestor workspaces ordered by chain position. After removing the geographical
hierarchy, this function becomes a simple single-workspace query. What is the
correct migration path for this function that does not break callers?

**37.**
`ROLE_MIN_LEVEL` documents minimum workspace levels for roles like
`global_admin`, `region_manager`. With the geographical hierarchy removed,
this mapping is meaningless but still exists in the codebase. What is the
risk of leaving dead configuration in place, and when is it acceptable to
defer its removal?

**38.**
The `_ACTOR_ROLE_MAP` in `rule_extractor.py` maps actor names to roles that
encode hierarchy levels: `"regional head" → "region_manager"`. With the
hierarchy gone, these role names still exist. What is your strategy for
renaming roles in a live system where role names are stored as strings in
the database?

---

## Section 8 — Engineering Process and Architecture

**39.**
During the investigation phase, we found a "split-brain" state: the SQLAlchemy
`Workspace` model had the hierarchy columns commented out, but the database
schema (via migrations) still had them, and all the RBAC code tried to read them.
How do you detect and prevent this class of drift in a team environment?

**40.**
We discovered that `app/schemas/workspace.py` imports `WORKSPACE_LEVELS` and
`_PARENT_LEVEL` from `app/models/workspace.py` at module load time, and those
names no longer exist. This means the entire FastAPI application fails to start.
How should this class of import-time crash be caught in a CI pipeline before
it reaches production?

**41.**
The investigation identified a typo `qyery` in `WorkflowRepository.search_business_rules()`
that causes a `NameError` at runtime. This method had presumably been in the
codebase for some time without being caught. What testing and static analysis
practices would have caught this before it was found during architecture review?

**42.**
`EmbeddingMapper.map_actions()` previously fetched all `PENDING` and `UNMAPPED`
action rows globally — across all workspaces. In a single-tenant system this
was harmless. In a multi-tenant system it means one tenant's ingestion processes
another tenant's unmapped rows. How should multi-tenancy concerns be validated
during code review for a system undergoing a tenancy migration?

**43.**
We made `get_unmapped_actions(workspace_id=None)` backward compatible by
defaulting to `None` (global query). Is this the right default? Make the
argument for and against keeping the global fallback, and state which you
would choose in a production financial platform.

**44.**
The `PdfExtractionPipeline` always returns a `DocumentExtractionResult` and
never raises. The `DocumentRegistrationService` always raises typed exceptions
(`InvalidFileError`, `WorkspaceTenantMismatchError`, etc.) and never returns
error objects. These are two different error-handling philosophies. When is
each one appropriate, and what is the deciding factor?

**45.**
We built the registration, storage, and extraction layers without yet building
the migration for the new tables (`brd_documents`, `document_versions`,
`ingestion_attempts`). What is the risk of this sequencing, and what must be
true about the new code before it is safe to run in a production environment
that already has the old schema applied?
