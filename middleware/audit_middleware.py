from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime
import uuid
import json
import logging

from dependencies import repository

# Get the audit logger
audit_logger = logging.getLogger("audit")

class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = datetime.now()
        
        # Extract relevant request information
        method = request.method
        path = request.url.path
        ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        api_key = request.headers.get("x-api-key", None)
        
        response = await call_next(request)
        
        # Get user ID from API key if possible
        if api_key:
            api_key_doc = await repository.get_api_key_by_key(api_key)
        user_id = api_key_doc.user_id if api_key_doc else None
        
        # Create audit log entry
        log_entry = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
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
        await repository.create_audit_log(log_entry)
        
        return response