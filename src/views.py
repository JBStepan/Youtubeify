from flask import Blueprint

views = Blueprint("views", __name__, template_folder="/app/assets/templates/")

@views.get("/")
def index():
    return "<h1>Hello</h1>"