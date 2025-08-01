from flask import Flask, request, render_template, redirect, url_for, session, jsonify
from pymongo import MongoClient
from flask_cors import CORS
from dotenv import load_dotenv
import cloudinary.uploader
import requests
import os

# Load environment variables
load_dotenv()

# Flask setup
app = Flask(__name__)
CORS(app)
app.secret_key = "super-secret-key"

# MongoDB setup
MONGO_URI = os.getenv("MONGODB_URI")
PORT = int(os.getenv("PORT", 10000))
client = MongoClient(MONGO_URI)
db = client["CuteStarsDB"]
applications_collection = db["applications"]

# Cloudinary setup
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

# Telegram notifier
def send_application_to_telegram(data, photo_urls=[]):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    message = f"📥 *New Application Received*\n\n" \
              f"👤 *Name:* {data.get('name')}\n" \
              f"🎂 *Age:* {data.get('age')}\n" \
              f"📧 *Email:* {data.get('email')}\n" \
              f"📱 *Phone:* {data.get('contact')}\n" \
              f"🌍 *Nationality:* {data.get('country')}\n"

    if data.get('instagram'):
        message += f"📸 *Instagram:* {data.get('instagram')}\n"
    if data.get('tiktok'):
        message += f"🎵 *TikTok:* {data.get('tiktok')}\n"
    if data.get('telegram'):
        message += f"📬 *Telegram:* @{data.get('telegram')}\n"

    if photo_urls:
        message += "\n🖼️ *Photos:*\n"
        for i, url in enumerate(photo_urls):
            message += f"🔗 [Photo {i+1}]({url})\n"

    try:
        requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
        )
    except Exception as e:
        print("❌ Telegram notification failed:", str(e))


# Admin credentials
USERNAME = "admin"
PASSWORD = "Stars2025!"

@app.route("/")
def home():
    return "✅ CuteStars backend is running and connected!"

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
    return render_template("applications.html", apps=data)

@app.route("/apply", methods=["POST"])
def apply():
    try:
        name = request.form.get("name")
        age = request.form.get("age")
        email = request.form.get("email")
        contact = request.form.get("contact")
        country = request.form.get("country")
        instagram = request.form.get("instagram")
        tiktok = request.form.get("tiktok")
        telegram = request.form.get("telegram")
        photos = request.files.getlist("photos")

        if not all([name, age, email, contact, country]) or not photos:
            return jsonify({"message": "Missing required fields or photos."}), 400

        # Extract real IP address
        forwarded = request.headers.get("X-For
