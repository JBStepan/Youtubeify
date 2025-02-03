from flask import Flask
import os
import dotenv

from api import api
from views import views

dotenv.load_dotenv()

app = Flask("frontend", static_url_path="/app/static/", static_folder="/app/assets/static")

app.register_blueprint(views)
app.register_blueprint(api)

def run_frontend():
    app.run("0.0.0.0", 8080)