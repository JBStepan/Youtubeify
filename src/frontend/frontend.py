from flask import Flask
import os
import dotenv
from werkzeug.middleware.proxy_fix import ProxyFix

from .api import api
from .views import views

dotenv.load_dotenv()

app = Flask("frontend", static_url_path="/app/static/", static_folder="/app/assets/static")

if os.getenv("BEHIND_PROXY", "false").lower() == "true":
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_host=1)

app.register_blueprint(views)
app.register_blueprint(api)
