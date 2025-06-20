from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(name, static_folder="static", template_folder="templates")
app.secret_key = "your-secret-key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite"
db = SQLAlchemy(app)

from flask_dance.contrib.discord import make_discord_blueprint
app.config["DISCORD_OAUTH_CLIENT_ID"] = "YOUR_CLIENT_ID"
app.config["DISCORD_OAUTH_CLIENT_SECRET"] = "YOUR_CLIENT_SECRET"
app.config["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
discord_bp = make_discord_blueprint(scope=["identify", "email"], redirect_url="/discord_callback")
app.register_blueprint(discord_bp, url_prefix="/login")

from app import routes