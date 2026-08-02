# MFlows Frontend — Design Document

## Overview

A banking operations dashboard for MFlows — the AI-powered Banking Workflow Platform. The frontend provides workflow creation, execution monitoring, catalog management, BRD ingestion, and observability for banking operations teams.

---

## Tech Stack

| Layer | Choice | Why |
|-------|--------|-----|
| Framework | React 18 + Vite | Fast builds, HMR, production-ready |
| Language | TypeScript | Type safety across API contracts |
| Routing | React Router v6 | File-based-like routing, nested layouts |
| State | TanStack Query (React Query) | Server state caching, auto-refetch, optimistic updates |
| UI Library | shadcn/ui + Tailwind CSS | Composable components, banking-professional look |
| Charts | Recharts | Lightweight, React-native charting |
| Forms | React Hook Form + Zod | Validation, minimal re-renders |
| HTTP Client | Axios | Interceptors, typed responses |
| Table | TanStack Table | Sorting, pagination, filtering |
| Toast/Notifications | Sonner | Minimal, accessible |
| Icons | Lucide React | Consistent icon set |

---

## Pages to Build

### 1. Dashboard (`/`)
- KPI cards: total workflows, active executions, success rate, queue depth, retry count
- Execution trend chart (7/30 days)
- Top workflows by execution count
- Recent failures list
- **API**: `GET /api/dashboard/stats`, `GET /api/dashboard/execution-trend`, `GET /api/dashboard/workflow-usage`

### 2. Workflows (`/workflows`)
- List all workflows with domain filter
- Generate new workflow via NL input (modal/drawer)
- View workflow details (DSL, parsed_rule_json, execution history)
- **API**: `GET /api/workflows`, `POST /api/workflows/generate`, `GET /api/workflows/:id`

### 3. Workflow Builder (`/workflows/generate`)
- Text input for natural language banking instruction
- Domain selector (finance)
- Name field
- Live preview of generated DAG (step visualization)
- Success/error feedback
- **API**: `POST /api/workflows/generate`

### 4. Executions (`/executions`)
- Table: all workflow executions with status, duration, retry count
- Filters: status, workflow, date range
- Pagination
- Click → execution detail
- **API**: `GET /api/executions`

### 5. Execution Detail (`/executions/:id`)
- Workflow execution metadata (status, trace_id, duration)
- Step timeline (vertical): each step with status, duration, input/output
- Retry history per step
- Pause/Resume controls
- **API**: `GET /api/executions/:id`, `POST /api/execute/:id/pause`, `POST /api/execute/:id/resume`

### 6. Traces (`/traces`)
- Distributed trace viewer (LangSmith-style)
- Filter by execution_id, status
- Expandable trace events with payload inspection
- **API**: `GET /api/traces`, `GET /api/traces/:trace_id`

### 7. Catalog (`/catalog`)
- Tabbed view: Triggers | Actions
- Search, filter by workflow_type, active status
- Pagination
- Detail drawer with aliases, description
- **API**: `GET /api/catalog/triggers`, `GET /api/catalog/actions`, `GET /api/catalog/triggers/:id`, `GET /api/catalog/actions/:id`

### 8. Semantic Search (`/catalog/search`)
- Search input with live results
- Shows matched triggers + actions with similarity scores
- **API**: `POST /api/search/semantic`

### 9. Knowledge Ingestion (`/knowledge`)
- PDF upload dropzone
- Extraction result display (triggers, actions, business rules, actors)
- Mapping status (matched vs unmapped)
- **API**: `POST /api/knowledge-ingestion/upload`

### 10. Action Configurations (`/configurations`)
- List by workflow_knowledge
- Edit configuration (execution_type, handler/endpoint details)
- Version history
- Activate/deactivate
- **API**: `GET /api/action-configurations`, `PUT /api/action-configurations/:id`, `PATCH /api/action-configurations/:id/activate`

### 11. Workspace Integrations (`/integrations`)
- CRUD for external system connections
- Provider type, auth type, base URL
- Test connection button (future)
- **API**: Full CRUD on `/api/workspaces/:id/integrations`

### 12. Analytics (`/analytics`)
- Workflow creation trend
- Execution volume
- Failure rate over time
- Retry analysis
- Trigger/action frequency
- **API**: `GET /api/analytics/*`

### 13. Prompts (`/prompts`)
- List prompt versions
- Activate/rollback
- Performance stats (pass rate, latency by version)
- **API**: `GET /api/prompts`, `POST /api/prompts/:name/activate`, `POST /api/prompts/:name/rollback`, `GET /api/prompts/stats`

### 14. Settings (`/settings`)
- Runtime configuration view
- System health status
- **API**: `GET /api/settings`, `GET /api/health/ready`

---

## Folder Structure

```
frontend/
├── index.html
├── vite.config.ts
├── tsconfig.json
├── tailwind.config.ts
├── package.json
├── .env
│
├── src/
│   ├── main.tsx                    # App entry
│   ├── App.tsx                     # Router + Layout
│   │
│   ├── api/                        # API client layer
│   │   ├── client.ts              # Axios instance + interceptors
│   │   ├── workflows.ts           # Workflow API calls
│   │   ├── executions.ts          # Execution API calls
│   │   ├── catalog.ts             # Catalog API calls
│   │   ├── analytics.ts           # Analytics API calls
│   │   ├── ingestion.ts           # Knowledge ingestion API
│   │   ├── configurations.ts     # Action config API
│   │   ├── integrations.ts       # Workspace integration API
│   │   ├── prompts.ts            # Prompt version API
│   │   ├── traces.ts             # Trace API
│   │   └── search.ts             # Semantic search API
│   │
│   ├── hooks/                      # React Query hooks
│   │   ├── useWorkflows.ts
│   │   ├── useExecutions.ts
│   │   ├── useCatalog.ts
│   │   ├── useAnalytics.ts
│   │   ├── useTraces.ts
│   │   └── ...
│   │
│   ├── pages/                      # Route pages
│   │   ├── Dashboard.tsx
│   │   ├── Workflows.tsx
│   │   ├── WorkflowGenerate.tsx
│   │   ├── WorkflowDetail.tsx
│   │   ├── Executions.tsx
│   │   ├── ExecutionDetail.tsx
│   │   ├── Traces.tsx
│   │   ├── Catalog.tsx
│   │   ├── KnowledgeIngestion.tsx
│   │   ├── Configurations.tsx
│   │   ├── Integrations.tsx
│   │   ├── Analytics.tsx
│   │   ├── Prompts.tsx
│   │   └── Settings.tsx
│   │
│   ├── components/                 # Reusable UI
│   │   ├── layout/
│   │   │   ├── Sidebar.tsx
│   │   │   ├── Header.tsx
│   │   │   └── MainLayout.tsx
│   │   ├── workflow/
│   │   │   ├── WorkflowCard.tsx
│   │   │   ├── DAGVisualization.tsx
│   │   │   └── GenerateForm.tsx
│   │   ├── execution/
│   │   │   ├── StepTimeline.tsx
│   │   │   ├── StatusBadge.tsx
│   │   │   └── RetryHistory.tsx
│   │   ├── catalog/
│   │   │   ├── TriggerCard.tsx
│   │   │   ├── ActionCard.tsx
│   │   │   └── SearchResults.tsx
│   │   ├── charts/
│   │   │   ├── ExecutionTrend.tsx
│   │   │   ├── FailureRate.tsx
│   │   │   └── KPICard.tsx
│   │   └── common/
│   │       ├── DataTable.tsx
│   │       ├── EmptyState.tsx
│   │       ├── LoadingSpinner.tsx
│   │       ├── Pagination.tsx
│   │       └── FileUpload.tsx
│   │
│   ├── types/                      # TypeScript interfaces
│   │   ├── workflow.ts
│   │   ├── execution.ts
│   │   ├── catalog.ts
│   │   ├── trace.ts
│   │   ├── configuration.ts
│   │   └── api.ts
│   │
│   ├── lib/                        # Utilities
│   │   ├── utils.ts               # cn(), formatDate, etc.
│   │   ├── constants.ts           # Status colors, labels
│   │   └── formatters.ts         # Duration, timestamps
│   │
│   └── styles/
│       └── globals.css            # Tailwind base + custom
│
└── public/
    └── favicon.ico
```

---

## API Integration Map

| Page | Endpoint | Method | Purpose |
|------|----------|--------|---------|
| Dashboard | `/api/dashboard/stats` | GET | KPI cards |
| Dashboard | `/api/dashboard/execution-trend` | GET | Chart data |
| Workflows | `/api/workflows` | GET | List |
| Workflows | `/api/workflows/generate` | POST | Create via NL |
| Executions | `/api/executions` | GET | Paginated list |
| Executions | `/api/executions/:id` | GET | Detail + steps |
| Execute | `/api/execute/` | POST | Dispatch |
| Execute | `/api/execute/:id/pause` | POST | Pause |
| Execute | `/api/execute/:id/resume` | POST | Resume |
| Catalog | `/api/catalog/triggers` | GET | Trigger list |
| Catalog | `/api/catalog/actions` | GET | Action list |
| Search | `/api/search/semantic` | POST | Semantic search |
| Ingestion | `/api/knowledge-ingestion/upload` | POST | PDF upload |
| Configs | `/api/action-configurations/:id` | PUT | Update config |
| Integrations | `/api/workspaces/:id/integrations` | CRUD | Full lifecycle |
| Traces | `/api/traces` | GET | Trace list |
| Analytics | `/api/analytics/*` | GET | Charts data |
| Prompts | `/api/prompts` | GET | Version list |
| Settings | `/api/health/ready` | GET | Health check |

---

## UX Design Principles

1. **Banking-professional aesthetic** — clean, data-dense, no playful colors. Neutral palette with status-driven accents (green=success, red=failure, amber=retry).
2. **Real-time feel** — React Query auto-refetch on focus, polling on execution pages (5s interval while active).
3. **Dense information display** — tables over cards for lists, inline expandable rows, minimal page navigation.
4. **Keyboard-first** — cmd+k for search, shortcuts for common actions.
5. **Error context** — always show the step/checkpoint where something failed, not just "execution failed".

---

## Build Order (Recommended)

| Phase | Pages | Reason |
|-------|-------|--------|
| 1 | Dashboard + Layout + Executions | Core observability — see if system is working |
| 2 | Workflows + Generate | Core creation — use the NL pipeline |
| 3 | Catalog + Search | Explore what's available |
| 4 | Execution Detail + Traces | Deep debugging |
| 5 | Knowledge Ingestion | BRD upload flow |
| 6 | Configurations + Integrations | Admin setup |
| 7 | Analytics + Prompts + Settings | Polish |

---

## What the Backend Already Provides

Every API endpoint the frontend needs **already exists and is tested**:
- 14 route modules registered in `app/main.py`
- All return JSON
- Pagination built into list endpoints
- CORS configured for `localhost:5173` (Vite default)
- FastAPI auto-generates OpenAPI spec at `/docs`

No backend changes needed to start frontend development.
