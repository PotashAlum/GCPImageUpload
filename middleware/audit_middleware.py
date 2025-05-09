from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime
import uuid
import json
import logging

from models.api_key_model import APIKeyModel
from models.audit_log_model import AuditLogModel
from services.interfaces.audit_log_service_interface import IAuditLogService

# Get the audit logger
audit_logger = logging.getLogger("audit")

class AuditMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, audit_log_service: IAuditLogService):
        super().__init__(app)
        self.audit_log_service = audit_log_service

    async def dispatch(self, request: Request, call_next):
        start_time = datetime.now()
        
        # Extract relevant request information
        method = request.method
        path = request.url.path
        ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        response = await call_next(request)
        
        # Get user ID from API key if possible
        user_id = team_id = None
        if request.state.api_key_info:
            user_id, team_id = request.state.api_key_info.user_id, request.state.api_key_info.team_id
        
        # Create audit log entry
        log_entry: AuditLogModel = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "team_id": team_id,
            "action": method,
            "resource_type": path.split("/")[1] if len(path.split("/")) > 1 else "root",
            "resource_id": path.split("/")[2] if len(path.split("/")) > 2 else None,
            "status": "success" if response.status_code < 400 else "failure",
            "status_code": response.status_code,
            "ip_address": ip,
            "user_agent": user_agent,
            "details": {
                "path": path,
                "duration_ms": (datetime.now() - start_time).total_seconds() * 1000
            },
            "timestamp": datetime.now()
        }
        
        # Log to file
        audit_logger.info(json.dumps(log_entry, indent=4, sort_keys=True, default=str))
        
        # Store in database
        await self.audit_log_service.create_audit_log(log_entry)
        
        return response