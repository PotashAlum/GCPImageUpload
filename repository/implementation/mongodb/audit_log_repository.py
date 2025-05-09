from repository.interfaces.domains.audit_log_repository_interface import IAuditLogRepository
from models import AuditLogModel
from typing import List, Dict, Any


class MongoDBauditLogRepository(IAuditLogRepository):
    """MongoDB implementation of the audit log repository"""
    
    def __init__(self, db, logger=None):
        self.db = db
        self.logger = logger
    
    async def setup_indexes(self):
        """Setup all required indexes for the audit logs collection"""
        # TTL index to automatically expire old logs after 90 days
        await self.db.create_index("timestamp", expireAfterSeconds=7776000)
    
    async def create_audit_log(self, log_data: Dict[str, Any]) -> AuditLogModel:
        log_instance = AuditLogModel(**log_data)
        await self.db.insert_one(log_data)
        return log_instance
    
    async def get_audit_logs(self, query: dict, skip: int = 0, limit: int = 10) -> List[AuditLogModel]:
        audit_logs_data = await self.audit_logs_collection.find(query).sort("timestamp", -1).skip(skip).limit(limit).to_list(limit)
        return [AuditLogModel(**log) for log in audit_logs_data]