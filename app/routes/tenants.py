"""
app/routes/tenants.py

Tenant management endpoints.

A Tenant represents a bank.  These endpoints let platform admins register
banks and inspect their workspaces.

Endpoints:
  POST   /tenants              — register a new bank
  GET    /tenants              — list all tenants
  GET    /tenants/{id}         — get a single tenant
  PATCH  /tenants/{id}/deactivate  — soft-delete a tenant
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.tenant import Tenant
from app.schemas.tenant import TenantCreate, TenantResponse

router = APIRouter(prefix="/tenants", tags=["tenants"])


# ── Create ────────────────────────────────────────────────────────────────────

@router.post("", response_model=TenantResponse, status_code=201)
def create_tenant(body: TenantCreate, db: Session = Depends(get_db)):
    """Register a new bank (tenant) on the platform.

    Both `name` and `slug` must be unique across all tenants.
    """
    tenant = Tenant(
        name=body.name,
        slug=body.slug,
        display_name=body.display_name,
        active=True,
    )
    db.add(tenant)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=(
                f"A tenant with name '{body.name}' or slug '{body.slug}' "
                "already exists."
            ),
        )
    db.refresh(tenant)
    return tenant


# ── List ──────────────────────────────────────────────────────────────────────

@router.get("", response_model=list[TenantResponse])
def list_tenants(active_only: bool = True, db: Session = Depends(get_db)):
    """List all registered tenants.

    Pass ?active_only=false to include deactivated tenants.
    """
    query = db.query(Tenant)
    if active_only:
        query = query.filter(Tenant.active.is_(True))
    return query.order_by(Tenant.id.asc()).all()


# ── Get ───────────────────────────────────────────────────────────────────────

@router.get("/{tenant_id}", response_model=TenantResponse)
def get_tenant(tenant_id: int, db: Session = Depends(get_db)):
    """Get a single tenant by ID."""
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if tenant is None:
        raise HTTPException(status_code=404, detail="Tenant not found.")
    return tenant


# ── Deactivate ────────────────────────────────────────────────────────────────

@router.patch("/{tenant_id}/deactivate", response_model=TenantResponse)
def deactivate_tenant(tenant_id: int, db: Session = Depends(get_db)):
    """Soft-delete a tenant.

    Sets active=False.  All tenant data (workspaces, BRDs, workflows) is
    retained — nothing is deleted from the database.
    """
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if tenant is None:
        raise HTTPException(status_code=404, detail="Tenant not found.")
    if not tenant.active:
        raise HTTPException(status_code=409, detail="Tenant is already inactive.")
    tenant.active = False
    db.commit()
    db.refresh(tenant)
    return tenant
