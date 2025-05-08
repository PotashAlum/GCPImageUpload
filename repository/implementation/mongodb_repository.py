from motor.motor_asyncio import AsyncIOMotorClient
import logging

from repository.repository_interface import IRepository
from models import APIKeyModel, UserModel, TeamModel, AuditLogModel, ImageModel


class MongoDBRepository(IRepository):
    def __init__(self, uri):
        # Database connection
        self.client = AsyncIOMotorClient(uri)
        self.db = self.client.user_image_db
        self.users_collection = self.db.users
        self.teams_collection = self.db.teams
        self.api_keys_collection = self.db.api_keys
        self.images_collection = self.db.images
        self.audit_logs_collection = self.db.audit_logs

        self.app_logger = logging.getLogger("app")

    async def startup_db_client(self):
        self.app_logger.info("Starting application...")
        
        # Create indexes
        await self.users_collection.create_index("id", unique=True)
        await self.teams_collection.create_index("id", unique=True)
        await self.api_keys_collection.create_index("id", unique=True)
        await self.api_keys_collection.create_index("key", unique=True)
        
        # Add index for images collection
        await self.images_collection.create_index("id", unique=True)
        
        # Add compound indexes for frequent queries
        await self.images_collection.create_index([("user_id", 1), ("created_at", -1)])
        await self.images_collection.create_index([("team_id", 1), ("created_at", -1)])
        await self.users_collection.create_index("team_id")
        await self.api_keys_collection.create_index("user_id")
        
        # Add TTL index for audit logs to automatically expire old logs
        await self.audit_logs_collection.create_index("timestamp", expireAfterSeconds=7776000)  # 90 days
        
        self.app_logger.info("Database setup completed")
    
    async def shutdown_db_client(self):
        self.app_logger.info("Shutting down application...")
        self.client.close()
        self.app_logger.info("MongoDB connection closed")

    async def create_api_key(self, api_key):
        await self.api_keys_collection.insert_one(api_key)
        return APIKeyModel(**api_key)
    
    async def get_api_key_by_id(self, api_key_id):
        api_key_data = await self.api_keys_collection.find_one({"id": api_key_id})
        return APIKeyModel(**api_key_data) if api_key_data else None
    
    async def get_api_key_by_key(self, api_key):
        api_key_data = await self.api_keys_collection.find_one({"key": api_key})
        return APIKeyModel(**api_key_data) if api_key_data else None
    
    async def list_api_keys(self, skip = 0, limit = 10):
        api_keys_data = await self.api_keys_collection.find().skip(skip).limit(limit).to_list(limit)
        return [APIKeyModel(**api_key) for api_key in api_keys_data]

    async def delete_api_key(self, api_key_id):
        await self.api_keys_collection.delete_one({"id": api_key_id})

    async def create_user(self, user):
        await self.users_collection.insert_one(user)
        return user

    async def get_user_by_id(self, user_id):
        user_data = await self.users_collection.find_one({"id": user_id})
        return UserModel(**user_data) if user_data else None
    
    async def get_user_by_username(self, username):
        user_data = await self.users_collection.find_one({"username": username})
        return UserModel(**user_data) if user_data else None
    
    async def get_user_by_email(self, email):
        user_data = await self.users_collection.find_one({"email": email})
        return UserModel(**user_data) if user_data else None
    
    async def delete_user(self, user_id):
        await self.users_collection.delete_one({"email": user_id})
        
    async def get_users(self, skip, limit):
        users_data = await self.users_collection.find().skip(skip).limit(limit).to_list(limit)
        return [UserModel(**user) for user in users_data]
    
    async def create_team(self, team):
        await self.teams_collection.insert_one(team)
        return team

    async def get_team_by_id(self, team_id):
        team_data = await self.teams_collection.find_one({"id": team_id})
        return TeamModel(**team_data) if team_data else None
    
    async def get_team_by_name(self, name):
        team_data = await self.teams_collection.find_one({"name": name})
        return TeamModel(**team_data) if team_data else None
    
    async def delete_team(self, team_id):
        await self.teams_collection.delete_one({"id": team_id})
    
    async def get_teams(self, skip, limit):
        teams_data = await self.teams_collection.find().skip(skip).limit(limit).to_list(limit)
        return [TeamModel(**team) for team in teams_data]

    async def create_image(self, image):
        await self.images_collection.insert_one(image)
        return image

    async def get_image_by_id(self, image_id):
        image_data = await self.images_collection.find_one({"id": image_id})
        return ImageModel(**image_data) if image_data else None
    
    async def delete_image(self, image_id):
        await self.images_collection.delete_one({"image_id": image_id})
    
    async def delete_images_by_team_id(self, team_id):
        await self.images_collection.delete_many({"team_id": team_id})
    
    async def create_audit_log(self, log_data):
        log_instance = AuditLogModel(**log_data)
        await self.audit_logs_collection.insert_one(log_data)
        return log_instance
    
    async def get_users_by_team_id(self, team_id, skip = 0, limit = 10):
        users_data = await self.users_collection.find({"team_id": team_id}).skip(skip).limit(limit).to_list(limit)
        return [UserModel(**user) for user in users_data]
    
    async def get_users_count_by_team_id(self, team_id):
        count = await self.users_collection.count_documents({"team_id": team_id})
        return count
    
    async def get_api_keys_by_user_id(self, user_id, skip = 0, limit = 10):
        api_keys_data = await self.api_keys_collection.find({"user_id": user_id}).skip(skip).limit(limit).to_list(limit)
        return [APIKeyModel(**api_key) for api_key in api_keys_data]
    
    async def delete_user_api_keys(self, user_id):
        await self.api_keys_collection.delete_many({"user_id": user_id})
    
    async def get_images_by_team_id(self, team_id, skip = 0, limit = 10):
        images_data = await self.images_collection.find({"team_id": team_id}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
        return [ImageModel(**image) for image in images_data]
    
    async def get_images_by_user_id(self, user_id, skip = 0, limit = 10):
        images_data = await self.images_collection.find({"user_id": user_id}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
        return [ImageModel(**image) for image in images_data]
    
    async def get_audit_logs(self, query, skip = 0, limit = 10):
        audit_logs_data = await self.audit_logs_collection.find(query).sort("timestamp", -1).skip(skip).limit(limit).to_list(limit)
        return [AuditLogModel(**log) for log in audit_logs_data]