from werkzeug.security import check_password_hash
from flask_httpauth import HTTPBasicAuth
import data

auth = HTTPBasicAuth()
config = data.get_db("config")

@auth.verify_password
def verify_password(username, password):
    if config["users"].find_one({ "username": username}) and \
        check_password_hash(config["users"].find_one({ "username": username })["password"], password):
            return username
    return None