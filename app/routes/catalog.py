"""
app/routes/catalog.py

Exposes trigger_definitions and action_definitions tables for the frontend catalog page.
Supports search, workflow_type filter, active filter, and pagination.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.db.session import get_db
from app.models.trigger_definitions import TriggerDefinition
from app.models.action_definitions import ActionDefinition

router = APIRouter(prefix="/catalog", tags=["catalog"])


def _paginate(query, page: int, page_size: int):
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return {
        "data": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": max(1, (total + page_size - 1) // page_size),
    }


def _serialize_trigger(t: TriggerDefinition) -> dict:
    return {
        "id": t.id,
        "name": t.name,
        "display_name": t.display_name,
        "description": t.description,
        "workflow_type": t.workflow_type,
        "aliases": t.aliases or [],
        "active": t.active,
    }


def _serialize_action(a: ActionDefinition) -> dict:
    return {
        "id": a.id,
        "name": a.name,
        "display_name": a.display_name,
        "description": a.description,
        "workflow_type": a.workflow_type,
        "aliases": a.aliases or [],
        "active": a.active,
    }


@router.get("/triggers")
def list_triggers(
    search: str | None = Query(None),
    workflow_type: str | None = Query(None),
    active: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    q = db.query(TriggerDefinition)

    if search:
        term = f"%{search.lower()}%"
        q = q.filter(
            or_(
                TriggerDefinition.name.ilike(term),
                TriggerDefinition.display_name.ilike(term),
                TriggerDefinition.description.ilike(term),
            )
        )
    if workflow_type:
        q = q.filter(TriggerDefinition.workflow_type == workflow_type)
    if active is not None:
        q = q.filter(TriggerDefinition.active == (active.lower() == "true"))

    q = q.order_by(TriggerDefinition.name)
    result = _paginate(q, page, page_size)
    result["data"] = [_serialize_trigger(t) for t in result["data"]]
    return result


@router.get("/triggers/{trigger_id}")
def get_trigger(trigger_id: int, db: Session = Depends(get_db)):
    t = db.query(TriggerDefinition).filter(TriggerDefinition.id == trigger_id).first()
    if not t:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Trigger not found")
    return _serialize_trigger(t)


@router.get("/actions")
def list_actions(
    search: str | None = Query(None),
    workflow_type: str | None = Query(None),
    active: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    q = db.query(ActionDefinition)

    if search:
        term = f"%{search.lower()}%"
        q = q.filter(
            or_(
                ActionDefinition.name.ilike(term),
                ActionDefinition.display_name.ilike(term),
                ActionDefinition.description.ilike(term),
            )
        )
    if workflow_type:
        q = q.filter(ActionDefinition.workflow_type == workflow_type)
    if active is not None:
        q = q.filter(ActionDefinition.active == (active.lower() == "true"))

    q = q.order_by(ActionDefinition.name)
    result = _paginate(q, page, page_size)
    result["data"] = [_serialize_action(a) for a in result["data"]]
    return result


@router.get("/actions/{action_id}")
def get_action(action_id: int, db: Session = Depends(get_db)):
    a = db.query(ActionDefinition).filter(ActionDefinition.id == action_id).first()
    if not a:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Action not found")
    return _serialize_action(a)
