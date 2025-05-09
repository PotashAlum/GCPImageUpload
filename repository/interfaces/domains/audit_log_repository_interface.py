from abc import ABC, abstractmethod
from typing import List, Dict, Any
from models import AuditLogModel

class IAuditLogRepository(ABC):
    @abstractmethod
    async def create_audit_log(self, log_data: Dict[str, Any]) -> AuditLogModel:
        pass
    
    @abstractmethod
    async def get_audit_logs(self, query: dict, skip: int = 0, limit: int = 10) -> List[AuditLogModel]:
        pass