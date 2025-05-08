from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional

from models import APIKeyModel, UserModel, TeamModel, AuditLogModel, ImageModel


class IRepository(ABC):
    """
    Interface for data repository operations.
    Defines the contract that any repository implementation must follow.
    """
    
    @abstractmethod
    async def startup_db_client(self) -> None:
        pass
    
    @abstractmethod
    async def shutdown_db_client(self) -> None:
        pass
    
    @abstractmethod
    async def create_api_key(self, api_key: APIKeyModel) -> APIKeyModel:
        pass
    
    @abstractmethod
    async def get_api_key_by_id(self, api_key_id: str) -> Optional[APIKeyModel]:
        pass

    @abstractmethod
    async def get_api_key_by_key(self, api_key: str) -> Optional[APIKeyModel]:
        pass
    
    @abstractmethod
    async def list_api_keys(self, skip: int, limit: int) -> List[APIKeyModel]:
        pass
    
    @abstractmethod
    async def delete_api_key(self, api_key_id: str) -> None:
        pass

    @abstractmethod
    async def delete_user_api_keys(self, user_id: str) -> None:
        pass
    
    @abstractmethod
    async def create_user(self, user: UserModel) -> Optional[UserModel]:
        pass

    @abstractmethod
    async def get_user_by_id(self, user_id: str) -> Optional[UserModel]:
        pass

    @abstractmethod
    async def get_user_by_username(self, username: str) -> Optional[UserModel]:
        pass
    
    @abstractmethod
    async def get_user_by_email(self, email: str) -> Optional[UserModel]:
        pass

    @abstractmethod
    async def delete_user(self, user_id: str) -> None:
        pass
    
    @abstractmethod
    async def create_team(self, team: TeamModel) -> Optional[TeamModel]:
        pass
    
    @abstractmethod
    async def get_team_by_id(self, team_id: str) -> Optional[TeamModel]:
        pass

    @abstractmethod
    async def get_team_by_name(self, name: str) -> Optional[TeamModel]:
        pass

    @abstractmethod
    async def delete_team(self, team_id: str) -> None:
        pass
    
    @abstractmethod
    async def get_teams(self, skip: int, limit: int) -> List[TeamModel]:
        pass

    @abstractmethod
    async def create_image(self, image: ImageModel) -> ImageModel:
        pass
    
    @abstractmethod
    async def get_image_by_id(self, image_id: str) -> Optional[ImageModel]:
        pass

    @abstractmethod
    async def delete_image(self, image_id: str) -> None:
        pass

    @abstractmethod
    async def delete_images_by_team_id(self, team_id: str) -> None:
        pass
    
    @abstractmethod
    async def create_audit_log(self, log_data: Dict[str, Any]) -> AuditLogModel:
        pass
    
    @abstractmethod
    async def get_users_by_team_id(self, team_id: str, skip: int, limit: int) -> List[UserModel]:
        pass

    @abstractmethod
    async def get_users(self, skip: int, limit: int) -> List[UserModel]:
        pass

    @abstractmethod
    async def get_users_count_by_team_id(self, team_id: str) -> int:
        pass
    
    @abstractmethod
    async def get_api_keys_by_user_id(self, user_id: str, skip: int, limit: int) -> List[APIKeyModel]:
        pass
    
    @abstractmethod
    async def get_images_by_team_id(self, team_id: str, skip: int, limit: int) -> List[ImageModel]:
        pass
    
    @abstractmethod
    async def get_images_by_user_id(self, user_id: str, skip: int, limit: int) -> List[ImageModel]:
        pass

    @abstractmethod
    async def get_audit_logs(self, query: dict, skip: int, limit: int) -> List[AuditLogModel]:
        pass