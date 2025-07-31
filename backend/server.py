from flask import Flask, request, render_template, redirect, url_for, session, jsonify, send_from_directory
from pymongo import MongoClient
from werkzeug.utils import secure_filename
from flask_cors import CORS
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Flask setup
app = Flask(__name__)
CORS(app)
app.secret_key = "super-secret-key"  # Replace in production

# MongoDB setup
MONGO_URI = os.getenv("MONGODB_URI")
PORT = int(os.getenv("PORT", 10000))
client = MongoClient(MONGO_URI)
db = client["CuteStarsDB"]
applications_collection = db["applications"]

# Upload config
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10MB per file

# Credentials
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
        data = [{}]
    return render_template("applications.html", apps=data)

@app.route("/apply", methods=["POST"])
def apply():
    try:
        name = request.form.get("name")
        age = request.form.get("age")
        email = request.form.get("email")
        contact = request.form.get("contact")
        instagram = request.form.get("instagram")
        tiktok = request.form.get("tiktok")
        twitter = request.form.get("twitter")
        photos = request.files.getlist("photos")

        if not all([name, age, email, contact]) or len(photos) == 0:
            return jsonify({"message": "Missing required fields or photos."}), 400

        saved_files = []
        for photo in photos:
            filename = secure_filename(photo.filename)
            path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            photo.save(path)
            saved_files.append(filename)

        applications_collection.insert_one({
            "name": name,
            "age": age,
            "email": email,
            "contact": contact,
            "instagram": instagram,
            "tiktok": tiktok,
            "twitter": twitter,
            "photos": saved_files
        })

        return jsonify({"message": "Application received successfully."}), 200

    except Exception as e:
        return jsonify({"message": f"Server error: {str(e)}"}), 500

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

if __name__ == "__main__":
    print("✅ Connected to MongoDB")
    app.run(host="0.0.0.0", port=PORT)