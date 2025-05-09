from repository import IRepository
from services.implementation.api_key_authentication_service import APIKeyAuthenticationService
from services.implementation.api_key_management_service import APIKeyManagementService
from services.implementation.audit_log_service import AuditLogService
from services.implementation.image_service import ImageService
from services.implementation.team_service import TeamService
from services.implementation.user_service import UserService

from services.interfaces.api_key_authentication_interface import IAPIKeyAuthenticationService
from services.interfaces.api_key_management_interface import IAPIKeyManagementService
from services.interfaces.audit_log_service_interface import IAuditLogService
from services.interfaces.image_service_interface import IImageService
from services.interfaces.team_service_interface import ITeamService
from services.interfaces.user_service_interface import IUserService

def create_api_key_management_service(repository: IRepository) -> IAPIKeyManagementService:
    return APIKeyManagementService(repository)

def create_api_key_authentication_service(repository: IRepository, root_key: str) -> IAPIKeyAuthenticationService:
    return APIKeyAuthenticationService(root_key, repository)

def create_audit_log_service(repository: IRepository) -> IAuditLogService:
    return AuditLogService(repository)

def create_image_service(repository: IRepository, bucket, bucket_name: str) -> IImageService:
    return ImageService(repository, bucket, bucket_name)

def create_team_service(repository: IRepository, bucket) -> ITeamService:
    return TeamService(repository, bucket)

def create_user_service(repository: IRepository) -> IUserService:
    return UserService(repository)