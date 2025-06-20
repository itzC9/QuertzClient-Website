from flask import render_template, redirect, request, session, url_for, jsonify, send_file
from datetime import datetime, timedelta
from app import app, db
from flask_dance.contrib.discord import discord
import subprocess, os
from sqlalchemy import Column, Integer, String, Boolean, DateTime

class User(db.Model):
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True)
    password = Column(String(100))
    coins = Column(Integer, default=0)

class VPS(db.Model):
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    name = Column(String(50))
    running = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, default=lambda: datetime.utcnow() + timedelta(days=3))
    type = Column(String(20), default="python")

def login_required(f):
    from functools import wraps
    @wraps(f)
    def wrapped(*args, **kwargs):
        if 'user_id' not in session:
            return redirect("/auth")
        return f(*args, **kwargs)
    return wrapped

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/auth", methods=["GET", "POST"])
def auth():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session["user_id"] = user.id
            return redirect("/panel")
        else:
            return "Invalid login"
    return render_template("auth.html")

@app.route("/discord_callback")
def discord_callback():
    if not discord.authorized:
        return redirect("/login/discord")
    resp = discord.get("/api/users/@me")
    if not resp.ok:
        return "Failed to fetch Discord user"
    data = resp.json()
    username = data["username"]
    user = User.query.filter_by(username=username).first()
    if not user:
        user = User(username=username, password="", coins=0)
        db.session.add(user)
        db.session.commit()
    session["user_id"] = user.id
    return redirect("/panel")

@app.route("/store")
@login_required
def store():
    return render_template("store.html")

@app.route("/create", methods=["POST"])
@login_required
def create():
    name = request.form["name"]
    bot_type = request.form.get("type", "python")
    user = User.query.get(session["user_id"])
    if user.coins < 120:
        return "Not enough coins"
    vps = VPS(user_id=user.id, name=name, expires_at=datetime.utcnow() + timedelta(days=3), type=bot_type)
    db.session.add(vps)
    user.coins -= 120
    db.session.commit()
    os.makedirs(f"vps/{name}", exist_ok=True)
    return redirect("/panel")

@app.route("/renew/<int:vps_id>")
@login_required
def renew(vps_id):
    user = User.query.get(session["user_id"])
    vps = VPS.query.get(vps_id)
    if user.coins < 70:
        return "Not enough coins to renew"
    vps.expires_at = datetime.utcnow() + timedelta(days=3)
    user.coins -= 70
    db.session.commit()
    return redirect("/panel")

@app.route("/panel")
@login_required
def panel():
    now = datetime.utcnow()
    expired = VPS.query.filter(VPS.expires_at < now).all()
    for v in expired:
        try:
            os.system(f"rm -rf vps/{v.name}")
        except:
            pass
        db.session.delete(v)
        db.session.commit()
    vps_list = VPS.query.filter_by(user_id=session["user_id"]).all()
    return render_template("panel.html", vps_list=vps_list)

@app.route("/run/<int:vps_id>")
@login_required
def run(vps_id):
    vps = VPS.query.get(vps_id)
    vps.running = True
    logfile = f"vps/{vps.name}/output.log"
    if vps.type == "python":
        command = ["python3", f"vps/{vps.name}/main.py"]
    else:
        command = ["node", f"vps/{vps.name}/index.js"]
    with open(logfile, "w") as f:
        subprocess.Popen(command, stdout=f, stderr=subprocess.STDOUT)
    db.session.commit()
    return redirect("/panel")

@app.route("/stop/<int:vps_id>")
@login_required
def stop(vps_id):
    vps = VPS.query.get(vps_id)
    vps.running = False
    db.session.commit()
    return redirect("/panel")

@app.route("/upload/<int:vps_id>", methods=["POST"])
@login_required
def upload(vps_id):
    file = request.files["file"]
    vps = VPS.query.get(vps_id)
    file.save(f"vps/{vps.name}/{file.filename}")
    return redirect("/panel")

@app.route("/logs/<int:vps_id>")
@login_required
def logs(vps_id):
    vps = VPS.query.get(vps_id)
    logfile = f"vps/{vps.name}/output.log"
    if not os.path.exists(logfile):
        return "No logs yet."
    with open(logfile, "r") as f:
        content = f.read()
    return f"<pre>{content}</pre><br><a href='/panel'>Back</a>"

@app.route("/afk")
@login_required
def afk():
    user = User.query.get(session["user_id"])
    user.coins += 3
    db.session.commit()
    return jsonify({"coins": user.coins})