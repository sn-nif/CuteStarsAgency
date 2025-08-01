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

    # ➕ Include IP and geo details
    if data.get('ip'):
        message += f"\n🛰️ *IP Address:* {data.get('ip')}\n"
    if data.get('ip_city') or data.get('ip_country'):
        message += f"🌐 *Location:* {data.get('ip_city')}, {data.get('ip_region')} ({data.get('ip_country')})\n"
    if data.get('ip_org'):
        message += f"🏢 *ISP/Org:* {data.get('ip_org')}\n"

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
        forwarded = request.headers.get("X-Forwarded-For", request.remote_addr)
        ip_address = forwarded.split(",")[0].strip()

        # Geolocation via ipapi
        geo = {}
        try:
            res = requests.get(f"https://ipapi.co/{ip_address}/json/")
            if res.status_code == 200:
                data = res.json()
                geo = {
                    "ip": ip_address,
                    "ip_country": data.get("country_name"),
                    "ip_city": data.get("city"),
                    "ip_region": data.get("region"),
                    "ip_postal": data.get("postal"),
                    "ip_org": data.get("org")
                }
        except Exception as geo_err:
            print("🌐 IP lookup failed:", geo_err)

        # Upload to Cloudinary
        uploaded_urls = []
        for photo in photos:
            upload_result = cloudinary.uploader.upload(photo, folder="cutestars_applications")
            uploaded_urls.append(upload_result["secure_url"])

        # Save to DB
        applicant_data = {
            "name": name,
            "age": age,
            "email": email,
            "contact": contact,
            "country": country,
            "instagram": instagram,
            "tiktok": tiktok,
            "telegram": telegram,
            "photos": uploaded_urls,
            **geo
        }
        applications_collection.insert_one(applicant_data)

        # ✅ Send Telegram alert
        send_application_to_telegram(applicant_data, uploaded_urls)

        return jsonify({"message": "Application received successfully."}), 200

    except Exception as e:
        print("❌ Error:", str(e))
        return jsonify({"message": f"Server error: {str(e)}"}), 500

@app.route("/delete_applications", methods=["POST"])
def delete_applications():
    if "user" not in session:
        return jsonify({"message": "Unauthorized"}), 401

    data = request.json
    emails = data.get("emails", [])

    if not emails:
        return jsonify({"message": "No emails provided"}), 400

    result = applications_collection.delete_many({ "email": { "$in": emails } })

    return jsonify({ "deleted": result.deleted_count }), 200

if __name__ == "__main__":
    print("✅ Flask server ready on port", PORT)
    app.run(host="0.0.0.0", port=PORT)