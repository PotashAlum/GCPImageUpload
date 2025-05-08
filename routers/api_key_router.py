import logging
from typing import List
from fastapi import APIRouter
from models import APIKeyModel
from dependencies import api_key_management_service

logger = logging.getLogger("app")
router = APIRouter(prefix="/api-keys", tags=["API Keys"])

@router.post("/", response_model=APIKeyModel, status_code=201)
async def create_api_key(name, role, user_id, team_id):
    return await api_key_management_service.create_api_key(name, role, user_id, team_id)

@router.get("/", response_model=List[APIKeyModel], status_code=200)
async def list_api_keys():
    return await api_key_management_service.list_api_keys()

@router.get("/{api_key_id}", response_model=APIKeyModel, status_code=200)
async def get_api_key_by_id(api_key_id):
    return await api_key_management_service.get_api_key_by_id(api_key_id)

@router.get("/{api_key_id}", status_code=200)
async def delete_api_key(api_key_id):
    await api_key_management_service.delete_api_key(api_key_id)