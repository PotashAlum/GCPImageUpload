from repository.implementation.mongodb_repository import MongoDBRepository

def create_mongo_db_repository(uri):
    return MongoDBRepository(uri)