"""
TODO (Person 1): build out alerts CRUD following the exact pattern in devices.py
(list / get / create / update / delete, RBAC via require_role(...)).
Model to use: app.models.Alert
Schemas to add in app/schemas/__init__.py: matching *Create, *Update, *Out classes.
"""

from fastapi import APIRouter, Depends
from app.deps import get_current_user

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("")
def list_alerts(_user=Depends(get_current_user)):
    # TODO: replace with a real DB query once the schema for this resource is added
    return {"detail": "Not implemented yet - see TODO in app/routers/alerts.py"}
