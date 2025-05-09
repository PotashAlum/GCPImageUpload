from abc import ABC, abstractmethod
from typing import List, Optional
from models import TeamModel

class ITeamRepository(ABC):
    @abstractmethod
    async def create_team(self, team) -> TeamModel:
        pass
    
    @abstractmethod
    async def get_team_by_id(self, team_id: str) -> Optional[TeamModel]:
        pass
    
    @abstractmethod
    async def get_team_by_name(self, name: str) -> Optional[TeamModel]:
        pass
    
    @abstractmethod
    async def get_teams(self, skip: int, limit: int) -> List[TeamModel]:
        pass
    
    @abstractmethod
    async def delete_team(self, team_id: str) -> None:
        pass