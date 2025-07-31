from flask import Flask, request, render_template, redirect, url_for, session
from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

# Flask setup
app = Flask(__name__)
app.secret_key = "super-secret-key"  # Change this to something long and random in production

# MongoDB setup
MONGO_URI = os.getenv("MONGODB_URI")
PORT = int(os.getenv("PORT", 10000))
client = MongoClient(MONGO_URI)
db = client["CuteStarsDB"]
applications_collection = db["applications"]  # Change collection name if needed

# Simple credentials (you can change later)
USERNAME = "admin"
PASSWORD = "Stars2025!"

@app.route("/")
def home():
    return "✅ CuteStars backend is connected to MongoDB!"

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username == USERNAME and password == PASSWORD:
            session["user"] = username
            return redirect(url_for("applications"))
        else:
            return render_template("login.html", error="Invalid credentials")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

@app.route("/applications")
def applications():
    if "user" not in session:
        return redirect(url_for("login"))
    data = list(applications_collection.find({}, {"_id": 0}))
if not data:
    data = [{}]  # avoid template crash when empty
return render_template("applications.html", apps=data)

if __name__ == "__main__":
    print("✅ Connected to MongoDB")
    app.run(host="0.0.0.0", port=PORT)
