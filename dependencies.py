import os

from repository import create_mongo_db_repository
from services.service_factory import (
    create_api_key_management_service,
    create_api_key_authentication_service,
    create_audit_log_service,
    create_image_service,
    create_team_service,
    create_user_service,
    create_gcp_storage_service,
    create_authorization_service
)

from utils import initialize_app_logger
from utils import initialize_audit_logger

from google.cloud import storage

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "user-images-bucket")
ROOT_API_KEY = os.getenv("ROOT_API_KEY", "root-admin-key")

initialize_app_logger()
initialize_audit_logger()

repository = create_mongo_db_repository(MONGODB_URI)

# GCS client
storage_client = storage.Client()
bucket = storage_client.bucket(GCS_BUCKET_NAME)

storage_service = create_gcp_storage_service(bucket, GCS_BUCKET_NAME)
api_key_management_service = create_api_key_management_service(repository)
api_key_authentication_service = create_api_key_authentication_service(repository, ROOT_API_KEY)
audit_log_service = create_audit_log_service(repository)
image_service = create_image_service(repository, storage_service)
team_service = create_team_service(repository, storage_service)
user_service = create_user_service(repository)
authorization_service = create_authorization_service(repository)
