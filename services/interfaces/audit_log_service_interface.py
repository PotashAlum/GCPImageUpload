from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime
from models import AuditLogModel

class IAuditLogService(ABC):
    """
    Interface for audit log service operations.
    Defines the contract that any audit log service implementation must follow.
    """
    
    @abstractmethod
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
        """
        Retrieve audit logs with optional filtering criteria
        
        Args:
            skip: Number of records to skip for pagination
            limit: Maximum number of records to return
            user_id: Filter by user ID
            resource_type: Filter by resource type
            action: Filter by action
            status: Filter by status
            from_date: Filter by timestamp (from)
            to_date: Filter by timestamp (to)
            
        Returns:
            List of audit log records
        """
        pass