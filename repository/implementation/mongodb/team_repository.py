from repository.interfaces.domains.team_repository_interface import ITeamRepository
from models import TeamModel
from typing import List, Optional


class MongoDBTeamRepository(ITeamRepository):
    """MongoDB implementation of the team repository"""
    
    def __init__(self, db, logger=None):
        self.db = db
        self.logger = logger
    
    async def setup_indexes(self):
        """Setup all required indexes for the teams collection"""
        await self.db.create_index("id", unique=True)
        await self.db.create_index("name", unique=True)
    
    async def create_team(self, team) -> TeamModel:
        await self.db.insert_one(team)
        return TeamModel(**team)
    
    async def get_team_by_id(self, team_id: str) -> Optional[TeamModel]:
        team_data = await self.db.find_one({"id": team_id})
        return TeamModel(**team_data) if team_data else None
    
    async def get_team_by_name(self, name: str) -> Optional[TeamModel]:
        team_data = await self.db.find_one({"name": name})
        return TeamModel(**team_data) if team_data else None
    
    async def get_teams(self, skip: int, limit: int) -> List[TeamModel]:
        cursor = self.db.find()
        cursor = cursor.skip(skip)
        cursor = cursor.limit(limit)
        teams_data = await cursor.to_list(limit)
        return [TeamModel(**team) for team in teams_data]
    
    async def delete_team(self, team_id: str) -> None:
        await self.db.delete_one({"id": team_id})