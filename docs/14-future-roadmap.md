# Future Roadmap

## Near-Term (Banking Platform Hardening)

### Multi-Tenant Workspace Isolation
- Enforce workspace_id filtering on all queries
- Role-based access control (Maker/Checker pattern for banking)
- Workspace-level action catalog customization

### Enhanced Action Execution Types
- **MCP (Model Context Protocol)** — AI agent actions
- **Kafka** — Event-driven banking message bus integration
- **SOAP** — Legacy core banking system connectivity
- **gRPC** — High-performance internal service calls

### Workflow Approval Gates
- Human-in-the-loop approval steps for high-value operations
- Dual authorization (4-eyes principle) for sensitive banking actions
- SLA tracking for pending approvals

### Advanced Retry Policies
- Per-action retry configuration (some actions should never retry)
- Circuit breaker pattern for failing external integrations
- Retry with modified payload (e.g., fallback to alternate payment channel)

## Mid-Term (Banking Intelligence)

### Workflow Analytics & Optimization
- Step-level latency percentiles
- Bottleneck detection across workflow executions
- SLA breach prediction based on historical execution patterns

### Regulatory Reporting Automation
- Auto-generate RBI returns from workflow execution data
- Compliance audit trail exports (FATCA, AML reports)
- Basel III risk-weighted asset calculation workflows

### Dynamic Action Catalog
- Bank-specific action definitions (not just platform defaults)
- Action versioning with canary deployment
- A/B testing between action implementations

### LLM Improvements
- Fine-tuned model for banking workflow generation
- Multi-turn conversation for workflow refinement
- Workflow explanation in natural language

## Long-Term (Platform Evolution)

### Event-Driven Architecture
- Replace Redis polling with proper event sourcing
- CQRS for workflow execution reads vs writes
- Real-time execution streaming to frontend

### Distributed Execution
- Multi-region workflow execution for DR
- Priority-based execution queues (urgent vs batch)
- Resource-aware scheduling (CPU/memory limits per action)

### Banking Ecosystem Integration
- NPCI (UPI, NACH, BBPS) direct connectivity
- SWIFT message automation
- Core banking adapter framework (Finacle, Flexcube, T24)
- Credit bureau real-time pull integration

### Observability
- OpenTelemetry integration (replace custom tracing)
- Grafana dashboard auto-provisioning
- PagerDuty/OpsGenie alerting on DLQ threshold breach
