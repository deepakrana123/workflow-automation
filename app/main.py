from fastapi import FastAPI
from dotenv import load_dotenv

load_dotenv()

from app.routes.workflows import router as workflow_router
from app.routes.execute import router as execute_router
from app.routes.health import router as health_router
from app.routes.prompts import router as prompts_router

app = FastAPI(
    title="MFlows AI",
    version="2.0.0",
    description="AI workflow automation engine — natural language to executable DAG",
)

app.include_router(workflow_router, prefix="/api")
app.include_router(execute_router, prefix="/api")
app.include_router(health_router, prefix="/api")
app.include_router(prompts_router, prefix="/api")


@app.get("/")
def health():
    return {"status": "ok", "service": "mflows"}
