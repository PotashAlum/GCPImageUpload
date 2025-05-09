from fastapi import APIRouter
from typing import List, Optional
from datetime import datetime

from models import AuditLogModel
from dependencies import audit_log_service

router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])

@router.get("/", response_model=List[AuditLogModel])
async def list_audit_logs(
    skip: int = 0,
    limit: int = 50,
    user_id: Optional[str] = None,
    resource_type: Optional[str] = None,
    action: Optional[str] = None,
    status: Optional[str] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
):
    return await audit_log_service.list_audit_logs(
        skip=skip,
        limit=limit,
        user_id=user_id,
        resource_type=resource_type,
        action=action,
        status=status,
        from_date=from_date,
        to_date=to_date
    )