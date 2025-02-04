from flask import Blueprint, send_from_directory, request, redirect, flash
import data
from werkzeug.security import generate_password_hash
from .auth import auth

api = Blueprint("api", __name__, url_prefix="/api")

config = data.get_db("config")

@api.post("/admin/create")
def create_admin():
    username = request.form["username"]
    password = request.form["password"]

    if config["users"].insert_one({ "username": username, "password": generate_password_hash(password=password) }):
        config["settings"].insert_one({ "admin_user": True })
        return redirect("/", 302)
    else:
        flash("Something has gone wrong!")
        return redirect("/setup", 305)
