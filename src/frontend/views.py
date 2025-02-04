from flask import Blueprint, jsonify, render_template, redirect
from .auth import auth
import data

views = Blueprint("views", __name__, template_folder="/app/assets/templates/")
config = data.get_db("config")

@views.get("/")
@auth.login_required
def index():
    return "Hi mom!"

@views.get("/setup")
def setup():
    if config["settings"].find_one({ "admin_user": True}):
        return redirect("/", 302)
    return render_template("setup.html")