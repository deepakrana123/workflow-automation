# Folder Structure

```
mflows/
├── app/
│   ├── main.py                          # FastAPI app + lifespan + router registration
│   │
│   ├── core/                            # Cross-cutting infrastructure
│   │   ├── config.py                    # Retry/timeout constants
│   │   ├── domains.py                   # Allowed banking domains
│   │   ├── logger.py                    # Structured logging setup
│   │   ├── redis_client.py              # Redis connection singleton
│   │   ├── setting.py                   # OCR path configuration
│   │   ├── startup.py                   # Health checks at boot
│   │   ├── text_similarity.py           # Text scoring utility
│   │   └── tracing.py                   # Trace ID/span ID generation
│   │
│   ├── db/                              # Database infrastructure
│   │   ├── base.py                      # SQLAlchemy declarative base
│   │   └── session.py                   # SessionLocal + engine
│   │
│   ├── models/                          # SQLAlchemy ORM models
│   │   ├── workflow.py                  # Workflow (compiled DAG)
│   │   ├── workflow_execution.py        # Runtime execution state
│   │   ├── workflow_run.py              # Execution run grouping
│   │   ├── execution_step.py           # Per-step state
│   │   ├── action_definitions.py        # Banking action catalog
│   │   ├── trigger_definitions.py       # Banking trigger catalog
│   │   ├── action_configurations_model.py # Per-workflow action config
│   │   ├── workflow_knowledge.py        # BRD extraction result
│   │   ├── trace_event.py              # Distributed trace events
│   │   ├── step_retry_history.py       # Retry audit trail
│   │   ├── audit_log.py                # General audit log
│   │   └── generation_log.py           # LLM generation metrics
│   │
│   ├── routes/                          # API layer (FastAPI routers)
│   │   ├── workflows.py                # Generate + list workflows
│   │   ├── execute.py                  # Dispatch/pause/resume
│   │   ├── executions.py              # Execution history
│   │   ├── catalog.py                  # Browse action/trigger catalog
│   │   ├── search.py                   # Semantic search
│   │   ├── traces.py                   # Trace viewer
│   │   ├── dashboard.py               # KPI dashboard
│   │   ├── analytics.py               # Time-series charts
│   │   ├── prompts.py                  # Prompt version management
│   │   ├── knowledge_ingestion.py      # BRD upload
│   │   ├── workspace_integrations.py   # Integration CRUD
│   │   ├── action_configurations.py    # Action config CRUD
│   │   ├── health.py                   # Health/readiness
│   │   └── settings.py                 # Runtime settings
│   │
│   ├── services/                        # Application service layer
│   │   ├── nl_workflow_service.py       # NL → compile → save orchestrator
│   │   ├── workflow_dispatch_service.py # Queue workflow for execution
│   │   └── trace_service.py            # Trace event writer
│   │
│   ├── repositories/                    # Data access layer
│   │   ├── workflow.py                  # Workflow CRUD
│   │   ├── workflows_run_repo.py       # WorkflowRun CRUD
│   │   ├── action_configuration_repository.py
│   │   ├── generation_log_repo.py      # LLM metrics (fire-and-forget)
│   │   ├── audit_repo.py              # Audit log (fire-and-forget)
│   │   ├── step_retry_history_repo.py  # Retry history
│   │   └── entity_repo.py             # Entity payload (stub)
│   │
│   ├── execution/                       # Workflow execution engine
│   │   ├── runtime_processor.py         # Main orchestration entry point
│   │   ├── constants.py                 # Redis queue names
│   │   ├── state_manager.py            # Low-level step status mutations
│   │   ├── retry_handler.py            # Retry vs DLQ decision
│   │   ├── retry_policy.py            # Retry rules (max, delay)
│   │   ├── retry.py                    # Redis retry queue operations
│   │   ├── dispatcher.py              # Action dispatch map
│   │   ├── actions.py                  # Core action handlers
│   │   ├── chaos_actions.py           # Chaos engineering handlers
│   │   ├── runtime/
│   │   │   ├── constants.py            # State machine constants
│   │   │   ├── dag_executor.py         # DAG traversal loop
│   │   │   ├── dag_scheduler.py        # Ready step calculation
│   │   │   ├── step_executor.py        # Single step execution
│   │   │   ├── parallel_step_executor.py # Threaded parallel execution
│   │   │   ├── retry_executor.py       # Re-execute retried steps
│   │   │   ├── config_resolver.py      # ActionConfiguration lookup
│   │   │   ├── workflow_execution_service.py # Workflow state transitions
│   │   │   ├── step_execution_service.py    # Step state transitions
│   │   │   ├── workflow_finalizer.py   # Determine final workflow status
│   │   │   └── execution_state_manager.py   # Transition validation
│   │   ├── executors/
│   │   │   ├── registry.py            # ExecutorRegistry
│   │   │   ├── base_executor.py       # Abstract base
│   │   │   ├── python_executor.py     # Internal handler dispatch
│   │   │   ├── http_executor.py       # External HTTP calls
│   │   │   └── constants.py           # ExecutionType enum
│   │   ├── domain_actions/
│   │   │   ├── loan_actions.py        # Loan origination/servicing
│   │   │   ├── home_loan_actions.py   # Home loan specific
│   │   │   ├── car_loan_actions.py    # Vehicle loan specific
│   │   │   ├── support_actions.py     # (legacy)
│   │   │   └── health_actions.py      # (legacy)
│   │   └── python/
│   │       └── action_handler_registry.py # ACTION_HANDLER_MAP
│   │
│   ├── nlp/                             # NL processing (LLM integration)
│   │   ├── services/
│   │   │   └── nl_workflow_service.py   # NLP pipeline with retry/fallback
│   │   ├── catalog/
│   │   │   ├── matcher.py             # Keyword + semantic catalog matching
│   │   │   ├── trigger_repository.py   # TriggerDefinition data access
│   │   │   └── action_repository.py    # ActionDefinition data access
│   │   ├── suitability/
│   │   │   └── suitability_agent.py    # Pre-LLM guardrail
│   │   ├── llm_manager/
│   │   │   ├── llm_manager.py         # Multi-provider LLM orchestrator
│   │   │   └── providers/
│   │   │       └── gemini_rest.py     # Gemini API client
│   │   ├── parsers/
│   │   │   └── rule_parser.py         # DSL text → ParseNodes
│   │   ├── ast/
│   │   │   ├── builder.py            # ParseNodes → WorkflowAST
│   │   │   └── validator.py          # Cycle detection, dep validation
│   │   └── complier/
│   │       └── workflow_complier.py   # AST → compiled JSON
│   │
│   ├── prompting/                       # Unified prompt management
│   │   ├── __init__.py                 # Public API exports
│   │   ├── prompt_manager.py           # THE public API
│   │   ├── prompt_registry.py          # Template locator + PromptKey enum
│   │   ├── prompt_renderer.py          # Template interpolation
│   │   ├── prompt_context.py           # Generic variable container
│   │   ├── prompt_version_store.py     # Active version + auto-rollback
│   │   ├── prompt_version.py           # PromptVersion dataclass
│   │   ├── versioned_registry.py       # File-based version scanner
│   │   ├── token_estimator.py          # Heuristic token counting
│   │   └── versions/
│   │       └── workflow_generation/
│   │           └── v1.txt             # Active generation prompt
│   │
│   ├── prompts/                         # Prompt template files (.md)
│   │   ├── extractor.md               # BRD extraction prompt
│   │   ├── repair.md                  # Workflow repair prompt
│   │   ├── validator.md               # (reserved)
│   │   └── dsl.md                     # (reserved)
│   │
│   ├── knowledge_ingestions/            # BRD document processing
│   │   ├── service.py                  # Ingestion pipeline orchestrator
│   │   ├── extractor.py               # PDF text extraction
│   │   ├── worfklow_extractors.py     # LLM-based extraction
│   │   ├── workflow_repository.py      # Knowledge persistence + search
│   │   ├── embedding_mapper.py        # Catalog matching via embeddings
│   │   ├── schemas.py                 # Pydantic models
│   │   └── exceptions.py             # Domain exceptions
│   │
│   ├── retrieval/                       # Multi-strategy retrieval pipeline
│   │   ├── pipeline.py                # Orchestrator
│   │   ├── vector_retriever.py        # pgvector cosine search
│   │   ├── keyword_retriever.py       # BM25/alias matching
│   │   ├── postgress_retriever.py     # PostgreSQL full-text search
│   │   ├── reciprocal_rank_fusion.py  # RRF fusion
│   │   ├── cross_encoder.py          # Re-ranking
│   │   ├── decision_engine.py        # Confidence thresholding
│   │   └── models.py                  # RankedCandidate dataclass
│   │
│   ├── semantic/                        # Embedding infrastructure
│   │   ├── embedding_service.py        # Model loading + encoding
│   │   ├── semantic_catalog_retriever.py # High-level semantic search
│   │   ├── semantic_repository.py      # Raw SQL vector queries
│   │   └── vector_repository.py       # Embedding update operations
│   │
│   ├── workflow/                        # Workflow compilation + persistence
│   │   ├── workflow_compiler_service.py # DSL → AST → compiled
│   │   ├── workflow_persistence_service.py # Save to DB
│   │   ├── workflow_generator.py       # LLM call wrapper
│   │   ├── workflow_validator.py       # Structure validation
│   │   ├── workflow_schema_validator.py # Schema validation
│   │   ├── workflow_repair_service.py  # Repair prompt builder
│   │   └── workflow_response_parser.py # JSON extraction from LLM output
│   │
│   ├── action_configuration/           # Action config management
│   │   ├── management_service.py       # CRUD + versioning
│   │   └── action_configuration_service.py # Default seeding
│   │
│   ├── workspace_integrations/         # External system connections
│   │   ├── models.py                  # SQLAlchemy model
│   │   ├── repository.py             # Data access
│   │   └── integrations.py           # Service layer
│   │
│   ├── evaluation/                     # Retrieval evaluation framework
│   │   ├── evaluator.py              # Compare extracted vs expected
│   │   ├── metrics.py                # Accuracy, MRR, similarity
│   │   └── models.py                 # EvaluationReport dataclass
│   │
│   ├── dsl/                            # DSL generation
│   │   └── dsl_generator.py          # Workflow JSON → DSL text
│   │
│   └── workers/                        # Background workers
│       ├── consumer.py                # Main event consumer
│       ├── retry_worker.py           # Retry processor
│       └── reaper_worker.py          # Timeout recovery
│
├── alembic/                            # Database migrations
│   ├── env.py
│   └── versions/
│
├── scripts/                            # Development utilities
│   ├── seed_banking_catalog.py        # Seed 500+ banking actions
│   ├── banking_catalog_data.py        # Catalog data definitions
│   ├── seed_banking_catalog.sql       # Generated SQL
│   ├── backfill_embeddings.py         # Generate vector embeddings
│   └── test_semantic_*.py            # Integration test scripts
│
├── docs/                               # Documentation
├── docker-compose.yml                  # Container orchestration
├── Dockerfile                         # Application image
├── requirements.txt                   # Python dependencies
├── alembic.ini                        # Migration config
└── .env                               # Environment variables
```
