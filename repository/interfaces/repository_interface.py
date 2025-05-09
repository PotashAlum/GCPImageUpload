from abc import ABC, abstractmethod

from repository.interfaces.domains.user_repository_interface import IUserRepository
from repository.interfaces.domains.team_repository_interface import ITeamRepository
from repository.interfaces.domains.api_key_repository_interface import IAPIKeyRepository
from repository.interfaces.domains.image_repository_interface import IImageRepository
from repository.interfaces.domains.audit_log_repository_interface import IAuditLogRepository


class IRepository(ABC):
    """
    Interface for data repository operations.
    Acts as a facade for the individual domain repositories.
    """
    
    @abstractmethod
    async def startup_db_client(self) -> None:
        """Initialize the database connection"""
        pass
    
    @abstractmethod
    async def shutdown_db_client(self) -> None:
        """Close the database connection"""
        pass
    
    @property
    @abstractmethod
    def users(self) -> IUserRepository:
        """Get the user repository"""
        pass
    
    @property
    @abstractmethod
    def teams(self) -> ITeamRepository:
        """Get the team repository"""
        pass
    
    @property
    @abstractmethod
    def api_keys(self) -> IAPIKeyRepository:
        """Get the API key repository"""
        pass
    
    @property
    @abstractmethod
    def images(self) -> IImageRepository:
        """Get the image repository"""
        pass
    
    @property
    @abstractmethod
    def audit_logs(self) -> IAuditLogRepository:
        """Get the audit log repository"""
        pass