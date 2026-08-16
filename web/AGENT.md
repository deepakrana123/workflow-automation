# AGENT.md — MFlows Web (Frontend) Engineering Reference

> Reference for engineers working on the MFlows web client.
> Covers the stack, how it runs, project structure, the data layer, and — most
> importantly — how each screen maps onto the backend pipelines.
>
> **Precedence:** where this document and the code disagree, the code is
> authoritative. Backend behavior is documented in the root `AGENT.md`; this
> file only describes the frontend and the contract it consumes.

---

## What this app is

A single-page React admin console for MFlows — the banking workflow engine. It is
a **thin client**: no business logic lives here. Every meaningful operation
(workflow generation, BRD ingestion, synthesis, execution, catalog search) is a
call to the FastAPI backend. The frontend's job is to render backend state and
submit user intent.

The console exposes the whole platform surface: dashboard, workspaces, workflows,
executions, human tasks, catalog, BRD ingestion, traces, analytics, prompts,
integrations, action configurations, and health.

---

## Tech stack

| Layer | Technology |
|-------|-----------|
| Framework | React 18 + TypeScript |
| Build/dev | Vite 5 (`@vitejs/plugin-react`) |
| Routing | react-router-dom v6 |
| State / data | Redux Toolkit + RTK Query (`@reduxjs/toolkit`, `react-redux`) |
| Styling | Tailwind CSS 3 (utility classes + a few component classes in `index.css`) |
| Icons | lucide-react |
| Charts | recharts |
| Utils | clsx (conditional classNames) |

No component library — UI primitives are hand-rolled under `src/components/shared/`.

---

## Running locally

```bash
cd mflows/web
npm install
npm run dev        # Vite dev server on http://localhost:5173
```

- **API proxy:** `vite.config.ts` proxies `/api` → `http://localhost:8000`
  (`changeOrigin: true`). So the backend must be running on port 8000. In
  RTK Query, `baseUrl` is `/api`, meaning every request is relative and the
  proxy forwards it in dev.
- **Path alias:** `@` → `./src` (configured in `vite.config.ts` and used
  throughout as `@/store/api`, `@/components/...`, `@/config/forms`).

Build:

```bash
npm run build      # tsc typecheck + vite build
npm run preview    # serve the production build
```

> The backend CORS config already allows `http://localhost:5173`, so a direct
> (non-proxied) origin also works if needed.

---

## Project structure

```
mflows/web/src/
├── main.tsx              # entry: Provider (store) + BrowserRouter + App
├── App.tsx               # all routes, wrapped in <Layout />
├── index.css             # Tailwind layers + shared component classes (card, input, btn-brand, tabs-pill, skeleton…)
├── store/
│   ├── api.ts            # RTK Query api — THE single source of backend calls
│   └── index.ts          # configureStore, RootState/AppDispatch types
├── components/
│   ├── Layout.tsx        # sidebar nav + top bar + <Outlet/>
│   ├── KPICard.tsx, StatusBadge.tsx
│   └── shared/           # reusable primitives (see below)
├── config/
│   └── forms.ts          # declarative form field definitions
├── types/
│   └── form.ts           # FormField / DropdownItem types
└── pages/                # one file per route (see routing table)
```

---

## Composition & entry

`main.tsx` mounts the tree in this order:

```
React.StrictMode
  └─ Provider (Redux store)
       └─ BrowserRouter
            └─ App  →  Routes  →  Layout  →  <Outlet/> (the active page)
```

`store/index.ts` wires a single reducer + middleware — the RTK Query `api`
slice. There is **no other Redux state**; all app state is either server state
(RTK Query cache) or local component state (`useState`).

---

## Routing

Defined in `App.tsx`. Every route renders inside `<Layout />` (persistent
sidebar + top bar). Sidebar entries live in the `nav` array in
`components/Layout.tsx`.

| Path | Page | Purpose |
|------|------|---------|
| `/` | `Dashboard` | KPIs, trends, domain distribution |
| `/workspaces` | `Workspaces` | List + create workspaces |
| `/workspaces/:id` | `WorkspaceDetail` | Workspace tabs: Overview / Documents / Business Rules / Actions / Triggers; deterministic synthesize + link to Build with AI |
| `/workspaces/:id/build` | `WorkspaceBuildWorkflow` | Workspace-scoped AI generation: context + instruction + "+ Add Action" global picker + review |
| `/workflows` | `Workflows` | List workflows (filter by domain) |
| `/workflows/generate` | `WorkflowGenerate` | NL → workflow (global generation) |
| `/workflows/:id` | `WorkflowDetail` | DSL / AST / compiled / provenance |
| `/executions` | `Executions` | Paginated execution list |
| `/executions/:id` | `ExecutionDetail` | Execution + step detail |
| `/human-tasks` | `HumanTasks` | Approve/reject waiting tasks |
| `/catalog` | `Catalog` | Browse/search global triggers & actions |
| `/knowledge` | `KnowledgeIngestion` | Upload BRD (PDF) |
| `/traces` | `Traces` | Distributed traces |
| `/analytics` | `Analytics` | Volume/failure/retry charts |
| `/prompts` | `Prompts` | Prompt versions, stats, activate/rollback |
| `/integrations` | `Integrations` | Workspace HTTP integrations |
| `/configurations` | `Configurations` | Per-action execution configs |
| `/settings` | `Settings` | System/provider health |

> Note: the sidebar labels the health route as "Health" but the path is
> `/settings` (`Settings.tsx`).

---

## Data layer — RTK Query (`store/api.ts`)

This is the most important file in the frontend. It is the **only** place that
knows backend URLs. All components consume auto-generated hooks from it.

- **`baseUrl: "/api"`** — every endpoint path is relative to `/api` and proxied
  to the backend in dev.
- **Tag-based caching/invalidation** via `tagTypes`
  (`Workflows`, `Executions`, `Catalog`, `Dashboard`, `Traces`, `Prompts`,
  `Integrations`, `Configurations`, `HumanTasks`, `Settings`, `Health`,
  `Workspaces`). Queries `providesTags`; mutations `invalidatesTags` to trigger
  refetch (e.g. `generateWorkflow` invalidates `Workflows`).
- **Hook naming:** `useGetXQuery` for reads, `useXMutation` for writes. All are
  re-exported at the bottom of `api.ts`.

### Endpoint groups (each maps to a backend router under `/api`)

| Group | Example hooks | Backend router |
|-------|---------------|----------------|
| Dashboard | `useGetDashboardStatsQuery`, `useGetExecutionTrendQuery` | `/dashboard` |
| Workflows | `useGetWorkflowsQuery`, `useGetWorkflowQuery`, `useGenerateWorkflowMutation`, `useGetWorkflow{Dsl,Ast,Compiled,Provenance}Query` | `/workflows` |
| Execute | `useExecuteWorkflowMutation`, `usePause/ResumeExecutionMutation` | `/execute` |
| Executions | `useGetExecutionsQuery`, `useGetExecutionQuery` | `/executions` |
| Human Tasks | `useGetHumanTasksQuery`, `useDecideHumanTaskMutation` | `/human-tasks` |
| Catalog | `useGetTriggersQuery`, `useGetActionsQuery`, `useSemanticSearchMutation` | `/catalog`, `/search` |
| Knowledge | `useUploadBRDMutation` (FormData) | `/knowledge-ingestion` |
| Traces | `useGetTracesQuery`, `useGetTraceQuery` | `/traces` |
| Prompts | `useGetPromptsQuery`, `useActivate/RollbackPromptMutation` | `/prompts` |
| Workspaces | `useGetWorkspacesQuery`, `useGetWorkspaceQuery`, `useCreateWorkspaceMutation`, `useGetWorkspaceSynthesisQuery`, `useSynthesizeWorkspaceWorkflowMutation` | `/workspaces` |
| Workspace context | `useGetWorkspaceOverviewQuery`, `useGetWorkspaceDocumentsQuery`, `useGetWorkspaceBusinessRulesQuery`, `useGetWorkspaceActionsQuery` | `/workspaces/{id}/{overview,documents,business-rules,actions}` |
| Workspace AI generate | `useGenerateWorkspaceWorkflowMutation` | `POST /workspaces/{id}/generate` |
| Integrations | `useGetIntegrationsQuery`, `useCreate/Update/DeleteIntegrationMutation` | `/workspaces/{id}/integrations`, `/workspace-integrations` |
| Configurations | `useGetConfigurationsQuery`, `useUpdate/Activate/DeactivateConfigurationMutation` | `/action-configurations` |
| Analytics | `useGetExecutionVolumeQuery`, … | `/analytics` |
| Settings/Health | `useGetSettingsQuery`, `useGetProviderHealthQuery`, `useResetProviderMutation` | `/settings`, `/health` |

> Response types are largely `any` today — the backend is the source of truth
> for shapes. When adding endpoints, prefer adding a real TS type for the
> payload you rely on.

---

## How the UI maps to the backend pipelines

The frontend reflects the two backend ingestion paths and one execution engine.

### 1. Workspace (the banking project boundary — primary context)
- **List/create:** `Workspaces.tsx` → `useGetWorkspacesQuery` / `useCreateWorkspaceMutation`
  (`GET/POST /api/workspaces`).
- **Detail tabs:** `WorkspaceDetail.tsx` renders Overview / Documents / Business
  Rules / Actions / Triggers from the read-only context endpoints
  (`/overview`, `/documents`, `/business-rules`, `/actions`). Overview shows
  headline counts, the deterministic synthesize form, review flags (including
  `rule_conflict`), and a card linking to **Build with AI**.
- **Two build paths, deliberately distinct:**
  - **Synthesize from BRDs** (deterministic, no LLM) —
    `useSynthesizeWorkspaceWorkflowMutation` (`POST /api/workspaces/{id}/synthesize`).
  - **Build with AI** (workspace-scoped LLM) — `WorkspaceBuildWorkflow.tsx` →
    `useGenerateWorkspaceWorkflowMutation` (`POST /api/workspaces/{id}/generate`).
    Shows workspace context + business rules + a global-catalog "+ Add Action"
    picker (reuses `useGetActionsQuery` search) and passes chosen actions as
    `selected_action_ids`. Surfaces cross-BRD conflicts before generating.

### 2. BRD ingestion (Path 2)
- `KnowledgeIngestion.tsx` → `useUploadBRDMutation` posts a `FormData` file to
  `POST /api/knowledge-ingestion/upload`. The backend extracts (PyPDF/OCR),
  LLM-extracts structured knowledge, saves it under a workspace, and maps
  extracted actions/triggers to the catalog via embeddings.

### 3. NL → workflow (Path 1)
- `WorkflowGenerate.tsx` → `useGenerateWorkflowMutation`
  (`POST /api/workflows/generate` with `{user_request, name, domain}`). Renders
  the returned DSL, compiled steps, and the deterministic explanation
  (`result.explanation`). **This screen is currently workspace-agnostic** (it
  hardcodes `domain: "finance"` and sends no workspace).

### 4. Catalog (the global action/trigger library)
- `Catalog.tsx` → `useGetActionsQuery` / `useGetTriggersQuery` support
  `search`/pagination (`GET /api/catalog/actions?search=…`). This is the
  discoverable global library — reuse it wherever an explicit action picker is
  needed.

### 5. Execution + review
- Execute via `useExecuteWorkflowMutation` (`POST /api/execute/`).
- Monitor via `Executions.tsx` / `ExecutionDetail.tsx`, `Traces.tsx`.
- Human approvals via `HumanTasks.tsx` (`decideHumanTask` → approve/reject),
  which unblocks a `WAITING` step in the resumable DAG.

---

## Shared UI primitives (`components/shared/`)

Hand-rolled, Tailwind-styled building blocks. Prefer these over new one-offs:

`Badge`, `Button`, `DatePicker`, `Dropdown`, `EmptyState`, `FormRenderer`,
`Input`, `Modal`, `Select`, `Skeleton`, `Tabs`, `Textarea`, `Toggle`, `Tooltip`.

- **`Tabs`** — generic, controlled: `value`, `onChange`, `tabs: {label,value}[]`.
  Uses the `tabs-pill` / `tab-pill-*` classes from `index.css`.
- **`FormRenderer`** — renders a form from a `FormField[]` definition (see below).

Layout/utility classes such as `card`, `input`, `btn-brand`, `skeleton`,
`text-2xs`, `animate-in`, `text-brand-*`, `text-danger`, `text-success` are
defined in `index.css` / Tailwind config. Reuse them for visual consistency.

---

## Declarative forms

Forms are data-driven, not hand-written per field.

- **`types/form.ts`** — `FormField { name, label, type, placeholder?, required?,
  options?, rows?, colSpan?, validation? }`. Types: `text | number | email |
  password | select | textarea | date | toggle`.
- **`config/forms.ts`** — reusable field sets + defaults:
  `INTEGRATION_FIELDS`/`_DEFAULTS`, `CONFIGURATION_EDIT_FIELDS`,
  `WORKFLOW_GENERATE_FIELDS`/`_DEFAULTS`.
- **`components/shared/FormRenderer.tsx`** — consumes `fields`, controlled
  `values`, `onChange`, `onSubmit`, `submitLabel`, `columns`.

To add a form: define fields in `config/forms.ts`, hold state with `useState`,
render `<FormRenderer/>`, submit through an RTK Query mutation hook.

---

## Conventions

- **Data fetching:** always through RTK Query hooks from `@/store/api`. Never
  `fetch()`/`axios` directly in a component.
- **New backend call:** add the endpoint in `store/api.ts` (with `providesTags`/
  `invalidatesTags`), export the hook, then consume it. Keep URLs out of pages.
- **Local UI state:** `useState` in the page. No global store beyond RTK Query.
- **Loading/empty:** use `Skeleton`/`skeleton` class while `data` is undefined;
  use `EmptyState` for empty lists.
- **Errors:** backend errors surface as `(error as any)?.data?.detail`. Render a
  small red `card` (see `WorkflowGenerate`/`Workspaces` for the pattern).
- **Imports:** use the `@/` alias, not deep relative paths.
- **Styling:** Tailwind utilities + the shared classes in `index.css`. Match the
  existing compact, muted aesthetic (small text, `card` containers, `brand`
  accent).
- **Icons:** lucide-react, size 12–18 to match surrounding UI.

---

## Known frontend gaps / notes

- Most RTK Query response types are `any` — tighten as needed.
- `WorkflowGenerate` (the standalone `/workflows/generate` page) is intentionally
  global/workspace-agnostic (hardcoded `finance`). Workspace-scoped generation
  now lives at `/workspaces/:id/build` (`WorkspaceBuildWorkflow`).
- `WorkspaceDetail` tabs implemented: Overview, Documents, Business Rules,
  Actions, Triggers. "Workflows / Executions / Generated Files" tabs are not yet
  added (workflows now carry `workspace_id`, so a Workflows tab is a small
  follow-up; generated files are not yet linked to a workspace).
- The sidebar "Health" item routes to `/settings`.
