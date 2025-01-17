from pymongo import MongoClient

CONNECTION_STRING = "mongodb://localhost:27017/"
CLIENT = MongoClient(CONNECTION_STRING)

def get_db(dbname: str):
    return CLIENT.get_database(dbname)