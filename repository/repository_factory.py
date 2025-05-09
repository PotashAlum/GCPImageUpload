from repository.implementation.mongodb_repository import MongoDBRepository

def create_mongo_db_repository(uri: str) -> MongoDBRepository:
    """
    Create a MongoDB repository instance
    
    Args:
        uri: MongoDB connection URI
        
    Returns:
        A MongoDB repository instance
    """
    return MongoDBRepository(uri)