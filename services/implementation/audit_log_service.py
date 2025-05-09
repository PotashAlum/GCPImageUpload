import logging
from typing import List, Optional
from datetime import datetime

from models import AuditLogModel
from repository import IRepository
from services.interfaces.audit_log_service_interface import IAuditLogService

class AuditLogService(IAuditLogService):
    def __init__(self, repository: IRepository):
        self.logger = logging.getLogger("app")
        self.repository = repository
        
    async def create_audit_log(self, audit_log):
        await self.repository.audit_logs.create_audit_log(audit_log)
        return audit_log
    
    async def list_audit_logs(
        self,
        skip: int = 0,
        limit: int = 50,
        user_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        action: Optional[str] = None,
        status: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
    ) -> List[AuditLogModel]:
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
        logs = await self.repository.audit_logs.get_audit_logs(query, skip, limit)
        return logs