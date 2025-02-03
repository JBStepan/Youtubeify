from flask import Blueprint, send_from_directory

api = Blueprint("api", __name__, url_prefix="/api")
