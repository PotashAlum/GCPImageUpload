async def verify_team_access(self, user_id: str, team_id: str) -> None:
    """
    Verify that a user has access to a specific team.
    
    Args:
        user_id: The ID of the user
        team_id: The ID of the team
        
    Raises:
        HTTPException: When the user doesn't have access to the team
    """
    pass