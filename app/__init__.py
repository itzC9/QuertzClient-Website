from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = "yourtheone"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite"
db = SQLAlchemy(app)

# Removed Discord OAuth configuration and blueprint
# from flask_dance.contrib.discord import make_discord_blueprint
# app.config["DISCORD_OAUTH_CLIENT_ID"] = "1257710925662785596"
# app.config["DISCORD_OAUTH_CLIENT_SECRET"] = "fWxV0t5GMEmGywzg1zp_fDfPuE7gFq_a"
# app.config["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
# discord_bp = make_discord_blueprint(scope=["identify", "email"], redirect_url="/discord_callback")
# app.register_blueprint(discord_bp, url_prefix="/login")

from app import routes