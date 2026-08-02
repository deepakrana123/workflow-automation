# MFlows Frontend — Requirements

## Functional Requirements

### FR-1: Dashboard
- Display KPI cards: total workflows, active executions, success rate, queue depth
- Show execution trend chart (daily success/failure over 7/30 days)
- Show top 5 workflows by execution count
- Auto-refresh every 30 seconds

### FR-2: Workflow Management
- List all workflows with domain filter and search
- Generate new workflow from natural language input
- Display generated DSL and compiled DAG structure
- Show execution history per workflow

### FR-3: Workflow Generation
- Text input accepting banking workflow instructions
- Domain selector (currently "finance" only)
- Workflow name field
- Display compilation result (DSL, steps, dependencies)
- Show validation errors if generation fails

### FR-4: Execution Monitoring
- Paginated table of all executions
- Filter by: status (completed/failed/running/pending/dlq), workflow, date range
- Sort by: created_at, duration, status
- Click to open execution detail

### FR-5: Execution Detail
- Show execution metadata: status, trace_id, entity_id, duration, attempts
- Step timeline showing each action with: status, duration, input/output payloads
- Retry history per step
- Pause button (when RUNNING)
- Resume button (when PAUSED)

### FR-6: Distributed Traces
- List trace events with pagination
- Filter by execution_id, status
- Expand to see payload, event_type, timestamps
- Timeline visualization of spans

### FR-7: Banking Action Catalog
- Tabbed view: Triggers | Actions
- Search across name, display_name, description, aliases
- Filter by workflow_type, active status
- Paginated with configurable page size
- Click to see full detail (description, aliases, handler)

### FR-8: Semantic Search
- Single search input
- Returns scored trigger + action matches
- Display similarity scores and match type

### FR-9: BRD Knowledge Ingestion
- PDF file upload (drag-and-drop + click)
- Show extraction progress/status
- Display extracted: workflow_name, triggers, actions, business_rules, actors
- Show mapping results (matched vs unmapped actions/triggers)

### FR-10: Action Configuration Management
- List configurations by workflow
- Edit: execution_type, handler/endpoint, workspace_integration
- Version history display
- Activate/deactivate toggle
- Validation: required fields per execution_type

### FR-11: Workspace Integrations
- CRUD for integrations (name, provider_type, base_url, auth_type, credentials)
- List by workspace
- Active/inactive toggle
- Credential fields masked by default

### FR-12: Analytics
- Workflow creation trend (line chart)
- Execution volume (bar chart)
- Failure rate (line chart with threshold line)
- Retry distribution (bar chart)
- Date range selector

### FR-13: Prompt Version Management
- List all prompts with active version
- Activate specific version
- Rollback to previous
- Performance stats table (pass rate, avg latency per version)

### FR-14: Settings & Health
- Display system health (DB, Redis, embedding model)
- Show runtime configuration values

---

## Non-Functional Requirements

### NFR-1: Performance
- Initial page load < 2 seconds
- API responses rendered within 200ms of receipt
- No unnecessary re-renders (React Query caching)

### NFR-2: Responsiveness
- Desktop-first (1280px+)
- Usable at 1024px (sidebar collapses)
- Not required for mobile

### NFR-3: Error Handling
- All API errors shown via toast notifications
- Network failures shown with retry button
- Form validation errors shown inline

### NFR-4: Accessibility
- Keyboard navigable
- Proper heading hierarchy
- Sufficient color contrast (WCAG AA)
- ARIA labels on interactive elements

### NFR-5: Developer Experience
- TypeScript strict mode
- ESLint + Prettier configured
- Path aliases (@/ → src/)
- Environment variables for API base URL
