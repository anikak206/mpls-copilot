"""
TODO (Person 1): build out incidents CRUD following the exact pattern in devices.py
(list / get / create / update / delete, RBAC via require_role(...)).
Model to use: app.models.Incident
Schemas to add in app/schemas/__init__.py: matching *Create, *Update, *Out classes.
"""

from fastapi import APIRouter, Depends
from app.deps import get_current_user

router = APIRouter(prefix="/incidents", tags=["incidents"])


@router.get("")
def list_incidents(_user=Depends(get_current_user)):
    # TODO: replace with a real DB query once the schema for this resource is added
    return {"detail": "Not implemented yet - see TODO in app/routers/incidents.py"}
