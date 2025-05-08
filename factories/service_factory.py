from repository import IRepository
from services.implementation.api_key_authentication_service import APIKeyAuthenticationService
from services.implementation.api_key_management_service import APIKeyManagementService
from services.interfaces.api_key_authentication_interface import IAPIKeyAuthenticationService
from services.interfaces.api_key_management_interface import IAPIKeyManagementService

def create_api_key_management_service(repository: IRepository) -> IAPIKeyManagementService:
    return APIKeyManagementService(repository)

def create_api_key_authentication_service(repository: IRepository, root_key: str) -> IAPIKeyAuthenticationService:
    return APIKeyAuthenticationService(root_key, repository)