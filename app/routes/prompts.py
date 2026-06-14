from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.session import get_db
from app.nlp.prompts.prompt_registry import registry
from app.nlp.prompts.prompt_version_store import version_store
from app.repositories import generation_log_repo

router = APIRouter(prefix="/prompts", tags=["prompts"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class ActivateVersionRequest(BaseModel):
    version: str


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/")
def list_prompts():
    """
    List all prompt names, their available versions, and current active version.
    """
    result = []
    for name in registry.list_prompts():
        result.append({
            "prompt_name": name,
            "available_versions": registry.list_versions(name),
            "active_version": version_store.get_active(name),
            "previous_version": version_store.get_previous(name),
        })
    return result


@router.get("/stats")
def prompt_stats(db: Session = Depends(get_db)):
    """
    Pass rate, avg retries, avg latency grouped by prompt_name + version.
    Use this to compare v1 vs v2 performance before promoting.
    """
    return generation_log_repo.get_stats_by_version(db)


@router.get("/{prompt_name}/state")
def prompt_state(prompt_name: str):
    """Current version state for a specific prompt."""
    try:
        return version_store.get_state(prompt_name)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Prompt '{prompt_name}' not found")


@router.post("/{prompt_name}/activate")
def activate_version(prompt_name: str, body: ActivateVersionRequest):
    """
    Promote a specific version to active.
    Current active becomes the rollback target.
    """
    available = registry.list_versions(prompt_name)
    if not available:
        raise HTTPException(status_code=404, detail=f"Prompt '{prompt_name}' not found")
    if body.version not in available:
        raise HTTPException(
            status_code=400,
            detail=f"Version '{body.version}' not found. Available: {available}",
        )
    version_store.set_active(prompt_name, body.version)
    return {
        "success": True,
        "prompt_name": prompt_name,
        "active_version": body.version,
    }


@router.post("/{prompt_name}/rollback")
def rollback_version(prompt_name: str):
    """
    Roll back to the previous version.
    Raises 400 if no previous version exists.
    """
    available = registry.list_versions(prompt_name)
    if not available:
        raise HTTPException(status_code=404, detail=f"Prompt '{prompt_name}' not found")
    try:
        rolled_back_to = version_store.rollback(prompt_name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {
        "success": True,
        "prompt_name": prompt_name,
        "rolled_back_to": rolled_back_to,
    }


@router.get("/{prompt_name}/failures")
def recent_failures(prompt_name: str, limit: int = 10, db: Session = Depends(get_db)):
    """
    Last N failed generation attempts for a prompt.
    Use to diagnose whether a version is underperforming before manual rollback.
    """
    return generation_log_repo.get_recent_failures(db, prompt_name, limit)
