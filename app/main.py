from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
load_dotenv()

from app.routes.workflows import router as workflow_router
from app.routes.execute import router as execute_router
from app.routes.health import router as health_router
from app.routes.prompts import router as prompts_router
from app.routes.catalog import router as catalog_router
from app.routes.executions import router as executions_router
from app.routes.traces import router as traces_router
from app.routes.dashboard import router as dashboard_router
from app.routes.analytics import router as analytics_router
from app.routes.search import router as search_router
from app.routes.settings import router as settings_router
from app.routes.knowledge_ingestion import router as knowledge_ingestion_router
from app.routes.workspace_integrations import router as workspace_integrations_router
from app.routes.human_tasks import router as human_tasks_router
from app.routes.workspaces import router as workspaces_router
from app.routes.capabilities import router as capabilities_router
from app.routes.rbac import router as rbac_router
from app.routes.runtime import router as runtime_router
from app.routes.mock import router as mock_router
from app.core import startup as startup_module



@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ───────────────────────────────────────────────────────────────
    results = startup_module.run_startup_checks()
    startup_module._startup_results = results
    yield
    # ── Shutdown (nothing needed) ─────────────────────────────────────────────


app = FastAPI(
    title="MFlows AI",
    version="2.0.0",
    description="AI workflow automation engine — natural language to executable DAG",
    lifespan=lifespan,
)

# CORS — allow the Vite dev server and deployed frontend to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(workflow_router, prefix="/api")
app.include_router(execute_router, prefix="/api")
app.include_router(health_router, prefix="/api")
app.include_router(prompts_router, prefix="/api")
app.include_router(catalog_router, prefix="/api")
app.include_router(executions_router, prefix="/api")
app.include_router(traces_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")
app.include_router(analytics_router, prefix="/api")
app.include_router(search_router, prefix="/api")
app.include_router(settings_router, prefix="/api")
app.include_router(knowledge_ingestion_router, prefix="/api")
app.include_router(workspace_integrations_router, prefix="/api")
app.include_router(human_tasks_router, prefix="/api")
app.include_router(workspaces_router, prefix="/api")
app.include_router(capabilities_router, prefix="/api")
app.include_router(rbac_router, prefix="/api")
app.include_router(runtime_router, prefix="/api")
app.include_router(mock_router,    prefix="/api")


@app.get("/")
def root():
    return {"status": "ok", "service": "mflows"}
