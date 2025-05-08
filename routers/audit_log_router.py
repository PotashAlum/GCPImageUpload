from fastapi import APIRouter
from typing import List, Optional
from datetime import datetime

from models import AuditLogModel
from dependencies import repository

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
    # Build query
    query = {}
    
    if user_id:
        query["user_id"] = user_id
    
    if resource_type:
        query["resource_type"] = resource_type
    
    if action:
        query["action"] = action
    
    if status:
        query["status"] = status
    
    date_query = {}
    if from_date:
        date_query["$gte"] = from_date
    
    if to_date:
        date_query["$lte"] = to_date
    
    if date_query:
        query["timestamp"] = date_query
       
    # Get logs
    logs = await repository.get_audit_logs(query, skip, limit)
    return logs
