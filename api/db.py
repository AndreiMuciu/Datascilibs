from pymongo import MongoClient


def get_db():
    mongo_uri = 'mongodb://localhost:27017/'
    db_name = 'datasci'
    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5e3, connectTimeoutMS=5e3)
    db = client[db_name]
    return db
