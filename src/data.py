from pymongo import MongoClient
import os
import dotenv

dotenv.load_dotenv()

CONNECTION_STRING = os.getenv("MONGODB_CONNECTION").strip('"') # Doing this is the stupidist thing ever
CLIENT = MongoClient(CONNECTION_STRING)

def get_db(dbname: str):
    return CLIENT.get_database(dbname)