from motor.motor_asyncio import AsyncIOMotorClient
import logging

from repository.implementation.mongodb.user_repository import MongoDBUserRepository
from repository.implementation.mongodb.team_repository import MongoDBTeamRepository
from repository.implementation.mongodb.api_key_repository import MongoDBAPIKeyRepository
from repository.implementation.mongodb.image_repository import MongoDBImageRepository
from repository.implementation.mongodb.audit_log_repository import MongoDBauditLogRepository
from repository.interfaces.domains.api_key_repository_interface import IAPIKeyRepository
from repository.interfaces.domains.audit_log_repository_interface import IAuditLogRepository
from repository.interfaces.domains.image_repository_interface import IImageRepository
from repository.interfaces.domains.team_repository_interface import ITeamRepository
from repository.interfaces.domains.user_repository_interface import IUserRepository
from repository.interfaces.repository_interface import IRepository


class MongoDBRepository(IRepository):
    """MongoDB implementation of the main repository interface"""
    
    def __init__(self, uri: str):
        """
        Initialize the MongoDB repository
        
        Args:
            uri: MongoDB connection URI
        """
        self.client = AsyncIOMotorClient(uri)
        self.db = self.client.user_image_db
        self.app_logger = logging.getLogger("app")

        # Create repositories with shared resources
        self.user_repository = MongoDBUserRepository(self.db.users, self.app_logger)
        self.team_repository = MongoDBTeamRepository(self.db.teams, self.app_logger)
        self.api_key_repository = MongoDBAPIKeyRepository(self.db.api_keys, self.app_logger)
        self.image_repository = MongoDBImageRepository(self.db.images, self.app_logger)
        self.audit_log_repository = MongoDBauditLogRepository(self.db.audit_logs, self.app_logger)
    
    async def startup_db_client(self):
        """Initialize database connection and setup indexes"""
        self.app_logger.info("Starting application...")
        
        # Setup indexes for each repository
        await self.user_repository.setup_indexes()
        await self.team_repository.setup_indexes()
        await self.api_key_repository.setup_indexes()
        await self.image_repository.setup_indexes()
        await self.audit_log_repository.setup_indexes()
        
        self.app_logger.info("Database setup completed")
    
    async def shutdown_db_client(self):
        """Close database connection"""
        self.app_logger.info("Shutting down application...")
        self.client.close()
        self.app_logger.info("MongoDB connection closed")

    @property
    def users(self) -> IUserRepository:
        """Get the user repository"""
        return self.user_repository
    
    @property
    def teams(self) -> ITeamRepository:
        """Get the team repository"""
        return self.team_repository
    
    @property
    def api_keys(self) -> IAPIKeyRepository:
        """Get the API key repository"""
        return self.api_key_repository
    
    @property
    def images(self) -> IImageRepository:
        """Get the image repository"""
        return self.image_repository
    
    @property
    def audit_logs(self) -> IAuditLogRepository:
        """Get the audit log repository"""
        return self.audit_log_repository