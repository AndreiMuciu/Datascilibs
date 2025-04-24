from pymongo import MongoClient


def get_db():
    mongo_uri = 'mongodb://localhost:27017/'
    db_name = 'datasci'
    client = MongoClient(mongo_uri)
    db = client[db_name]
    return db
