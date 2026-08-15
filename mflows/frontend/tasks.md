# MFlows Frontend — Implementation Tasks

## Phase 1: Foundation + Dashboard (Week 1)

### Task 1.1: Project Scaffolding
- [ ] `npm create vite@latest frontend -- --template react-ts`
- [ ] Install: tailwindcss, shadcn/ui, react-router, tanstack-query, axios, recharts, lucide-react, sonner, zod, react-hook-form
- [ ] Configure tailwind.config.ts with banking color palette
- [ ] Configure path aliases (`@/` → `src/`)
- [ ] Set up `.env` with `VITE_API_BASE_URL=http://localhost:8000/api`
- [ ] ESLint + Prettier config

### Task 1.2: API Client Layer
- [ ] Create `src/api/client.ts` — Axios instance with base URL, error interceptor, toast on failure
- [ ] Create typed API modules: `workflows.ts`, `executions.ts`, `dashboard.ts`, `catalog.ts`
- [ ] Create `src/types/` — TypeScript interfaces matching API responses

### Task 1.3: Layout Shell
- [ ] `MainLayout.tsx` — sidebar + header + content area
- [ ] `Sidebar.tsx` — navigation links with icons (Lucide)
- [ ] `Header.tsx` — page title breadcrumb
- [ ] React Router setup with nested routes under MainLayout

### Task 1.4: Dashboard Page
- [ ] KPI cards row (4 cards: workflows, executions, success rate, queue)
- [ ] Execution trend chart (Recharts line chart, 7-day default)
- [ ] Top workflows table (name, execution count)
- [ ] Hook: `useDashboardStats()`, `useExecutionTrend()`
- [ ] Auto-refetch on window focus

---

## Phase 2: Workflows + Generation (Week 2)

### Task 2.1: Workflows List Page
- [ ] DataTable with columns: name, domain, status, created_at
- [ ] Domain filter dropdown
- [ ] Click row → navigate to detail
- [ ] Hook: `useWorkflows(domain?)`

### Task 2.2: Workflow Generate Page
- [ ] Form: user_request (textarea), name (input), domain (select)
- [ ] Submit → `POST /api/workflows/generate`
- [ ] Loading state during LLM processing (can take 10-30s)
- [ ] Success: show DSL + step list + navigate to workflow detail
- [ ] Error: show validation error message

### Task 2.3: Workflow Detail Page
- [ ] Header: name, domain, status, created_at
- [ ] DSL display (code block with syntax highlighting)
- [ ] Parsed steps table (id, action, dependencies)
- [ ] "Execute" button → `POST /api/execute/`
- [ ] Execution history table (recent executions for this workflow)

---

## Phase 3: Execution Monitoring (Week 2-3)

### Task 3.1: Executions List Page
- [ ] DataTable: id, workflow_name, status, started_at, duration, retry_count
- [ ] Status filter tabs: All | Running | Completed | Failed | DLQ
- [ ] Date range filter
- [ ] Pagination (20 per page)
- [ ] StatusBadge component (colored pill)
- [ ] Hook: `useExecutions(filters)`

### Task 3.2: Execution Detail Page
- [ ] Metadata header: status, trace_id, entity_id, duration, attempts
- [ ] Step timeline (vertical list): step_name, status badge, duration, expandable I/O
- [ ] Expand step → show input_payload, output_payload, error
- [ ] Retry history section per step
- [ ] Pause/Resume action buttons (conditional on status)
- [ ] Polling: refetch every 5s while status is RUNNING

### Task 3.3: Status Badge & Timeline Components
- [ ] `StatusBadge.tsx` — maps status string to color/icon
- [ ] `StepTimeline.tsx` — vertical stepper with connectors
- [ ] `RetryHistory.tsx` — collapsible table of retry attempts

---

## Phase 4: Catalog + Search (Week 3)

### Task 4.1: Catalog Page
- [ ] Tab navigation: Triggers | Actions
- [ ] Search input (debounced, 300ms)
- [ ] Filter: workflow_type, active status
- [ ] Paginated table: name, display_name, workflow_type, active
- [ ] Click row → detail drawer (slide-over panel)
- [ ] Detail: description, aliases list, handler_name

### Task 4.2: Semantic Search Page
- [ ] Search input with submit button
- [ ] Split results: trigger matches (left) + action matches (right)
- [ ] Each result: name, display_name, similarity_score bar
- [ ] Hook: `useSemanticSearch(query)`

---

## Phase 5: BRD Ingestion (Week 3-4)

### Task 5.1: Knowledge Ingestion Page
- [ ] File upload zone (drag-and-drop PDF)
- [ ] Upload progress indicator
- [ ] Result display: workflow_name, summary
- [ ] Extracted triggers list
- [ ] Extracted actions list with mapping status (matched ✓ / unmapped ✗)
- [ ] Business rules, actors, external systems (collapsible sections)

---

## Phase 6: Configuration & Integrations (Week 4)

### Task 6.1: Action Configurations Page
- [ ] Select workflow_knowledge from dropdown
- [ ] Table: action_name, execution_type, version, active
- [ ] Edit modal: execution_type selector, dynamic form fields per type
  - Python: handler name input
  - HTTP: method, endpoint, headers, body_template, response_mapping
- [ ] Activate/deactivate toggle

### Task 6.2: Workspace Integrations Page
- [ ] Create integration form: name, provider_type, base_url, auth_type, credentials
- [ ] List table: name, provider, base_url, active
- [ ] Edit modal (same form, pre-filled)
- [ ] Delete with confirmation
- [ ] Credentials fields: password input (masked), show/hide toggle

---

## Phase 7: Analytics + Prompts + Settings (Week 4-5)

### Task 7.1: Analytics Page
- [ ] Date range selector (7d, 30d, 90d, custom)
- [ ] Workflow creation trend (line chart)
- [ ] Execution volume (bar chart)
- [ ] Failure rate (line + threshold)
- [ ] Retry analysis (bar chart)
- [ ] All charts responsive to date range

### Task 7.2: Prompts Page
- [ ] Table: prompt_name, active_version, available_versions
- [ ] Activate button → confirm modal → `POST /activate`
- [ ] Rollback button → confirm modal → `POST /rollback`
- [ ] Stats table: version, total attempts, pass rate, avg latency

### Task 7.3: Traces Page
- [ ] Table: event_type, status, step_name, created_at
- [ ] Filter by execution_id
- [ ] Expand row → full payload JSON viewer
- [ ] Timeline view option (spans as horizontal bars)

### Task 7.4: Settings Page
- [ ] Health check card (DB ✓/✗, Redis ✓/✗, Embedding Model ✓/✗)
- [ ] Runtime info display

---

## Phase 8: Polish (Week 5)

### Task 8.1: Global Polish
- [ ] Loading skeletons on all pages
- [ ] Empty states with illustrations/messages
- [ ] Error boundaries per page section
- [ ] Cmd+K global search (searches workflows + catalog)
- [ ] Breadcrumb navigation
- [ ] Page title management (document.title)
- [ ] Favicon + meta tags

### Task 8.2: Performance
- [ ] Code splitting per route (React.lazy)
- [ ] Prefetch on hover for detail pages
- [ ] Virtualized tables for large datasets (catalog 500+ rows)

---

## What NOT to Build (Out of Scope)

- Authentication/login (add when deploying externally)
- User management
- Mobile responsive design
- Real-time WebSocket updates (polling is sufficient)
- Workflow visual DAG editor (read-only DAG display is enough)
- Multi-workspace switching UI (single workspace for MVP)
