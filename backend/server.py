from flask import Flask, request, render_template, redirect, url_for, session, jsonify
from pymongo import MongoClient
from flask_cors import CORS
from dotenv import load_dotenv
import cloudinary.uploader
import requests
import os
import bcrypt
from bson import ObjectId
import pycountry
import traceback


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
users_collection = db["admin_users"]

# Cloudinary setup
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

# Telegram notifier
import mimetypes
import uuid
import json
def country_to_flag(country_name):
    try:
        country = pycountry.countries.get(name=country_name)
        if not country:
            country = pycountry.countries.search_fuzzy(country_name)[0]
        code = country.alpha_2
        return ''.join(chr(127397 + ord(c)) for c in code.upper())
    except:
        return ''

def send_application_to_telegram(data, photo_files=[]):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    # Step 1: Send applicant message
    flag = country_to_flag(data.get('country', ''))
    message = f"📥 *New Application Received*\n\n"
    message += f"👩🏻 *Name:* {data.get('name')}\n"
    message += f"🎂 *Age:* {data.get('age')}\n"
    message += f"📧 *Email:* {data.get('email')}\n"
    message += f"📱 *Phone:* +{data.get('contact')}\n"
    message += f"🌍 *Nationality:* {flag} {data.get('country')}\n"

    if data.get('instagram'):
        message += f"📸 *Instagram:* {data.get('instagram')}\n"
    if data.get('tiktok'):
        message += f"🎵 *TikTok:* {data.get('tiktok')}\n"
    if data.get('telegram'):
        message += f"📬 *Telegram:* @{data.get('telegram')}\n"
    if data.get('ip'):
        message += f"\n🛰️ *IP Address:* {data.get('ip')}\n"
    if data.get('ip_city') or data.get('ip_country'):
        message += f"🌐 *Location:* {data.get('ip_city')}, {data.get('ip_region')} ({data.get('ip_country')})\n"
    if data.get('ip_org'):
        message += f"🏢 *ISP/Org:* {data.get('ip_org')}\n"

    try:
        requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
        )
    except Exception as e:
        print("❌ Failed to send message:", str(e))

    # Step 2: Send media group
    if not photo_files:
        return

    media = []
    files = {}

    for i, photo in enumerate(photo_files):
        field_id = f"file_{uuid.uuid4().hex}"
        mime_type, _ = mimetypes.guess_type(photo)
        try:
            # Download image from Cloudinary URL into a stream
            img_data = requests.get(photo).content
            files[field_id] = (f"photo{i + 1}.jpg", img_data, mime_type or "image/jpeg")
            media.append({
                "type": "photo",
                "media": f"attach://{field_id}"
            })
        except Exception as e:
            print(f"❌ Failed to process image {photo}: {e}")

    try:
        requests.post(
            f"https://api.telegram.org/bot{token}/sendMediaGroup",
            data={
                "chat_id": chat_id,
                "media": json.dumps(media)
            },
            files=files
        )
    except Exception as e:
        print("❌ Failed to send media group:", str(e))

@app.route("/")
def home():
    return "✅ CuteStars backend is running and connected!"


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = users_collection.find_one({"username": username})
        if user and bcrypt.checkpw(password.encode("utf-8"), user["password_hash"]):
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

    raw_data = list(applications_collection.find({}, {"_id": 0}))

    def country_to_flag(country_name):
        import pycountry
        try:
            country = pycountry.countries.get(name=country_name)
            if not country:
                country = pycountry.countries.search_fuzzy(country_name)[0]
            code = country.alpha_2
            return ''.join(chr(127397 + ord(c)) for c in code.upper())
        except:
            return ''

        for app in raw_data:
            try:
                app["country_flag"] = country_to_flag(app.get("country", ""))
            except Exception as e:
                print("⚠️ Error generating flag for country:", app.get("country", ""))
                traceback.print_exc()
                app["country_flag"] = ""



    return render_template("applications.html", apps=raw_data)



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

        # 🛠️ Fix: Declare geo before use
        geo = {}

        # Optional client-side geo fields
        client_ip = request.form.get("ip")
        client_city = request.form.get("geoCity")
        client_country = request.form.get("geoCountry")
        client_region = request.form.get("geoRegion")

        if client_ip:
            geo["ip"] = client_ip
        if client_city:
            geo["ip_city"] = client_city
        if client_country:
            geo["ip_country"] = client_country
        if client_region:
            geo["ip_region"] = client_region

        if not all([name, age, email, contact, country]) or not photos:
            return jsonify({"message": "Missing required fields or photos."}), 400

        # Improved client IP detection behind proxy/CDN (e.g. Cloudflare)
        ip_address = request.headers.get("CF-Connecting-IP") or \
                     request.headers.get("X-Forwarded-For", request.remote_addr).split(",")[0].strip()

        try:
            res = requests.get(f"https://ipapi.co/{ip_address}/json/")
            if res.status_code == 200:
                data = res.json()
                geo.setdefault("ip", ip_address)
                geo.setdefault("ip_country", data.get("country_name"))
                geo.setdefault("ip_city", data.get("city"))
                geo.setdefault("ip_region", data.get("region"))
                geo["ip_postal"] = data.get("postal")
                geo["ip_org"] = data.get("org")
        except Exception as geo_err:
            print("🌐 IP lookup failed:", geo_err)

        uploaded_urls = []
        for photo in photos:
            upload_result = cloudinary.uploader.upload(photo, folder="cutestars_applications")
            uploaded_urls.append(upload_result["secure_url"])

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

# ✅ Settings API — Admin + Users
@app.route("/api/add-user", methods=["POST"])
def add_user():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    telegram = data.get("telegram")
    permissions = data.get("permissions", [])

    print("➡️ Add User Request:", data)

    if not username or not password:
        return jsonify({"error": "Missing username or password"}), 400

    if users_collection.find_one({"username": username}):
        return jsonify({"error": "User already exists"}), 400

    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

    users_collection.insert_one({
        "username": username,
        "password_hash": password_hash,
        "telegram": telegram,
        "permissions": permissions
    })

    return jsonify({"status": "User added"})


@app.route("/api/update-admin", methods=["POST"])
def update_admin():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Missing fields"}), 400

    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

    users_collection.update_one(
        {"username": "admin"},
        {"$set": {"username": username, "password_hash": password_hash}},
        upsert=True
    )

    return jsonify({"status": "Admin updated"})

@app.route("/send_to_admin", methods=["POST"])
def send_to_admin():
    data = request.get_json()
    emails = data.get("emails", [])
    tg_id = data.get("telegram_id")

    print("📨 SEND TO ADMIN TRIGGERED")
    print("Emails:", emails)
    print("Telegram ID:", tg_id)

    if not emails or not tg_id:
        return jsonify({"status": "error", "message": "Missing data"}), 400

    apps = list(applications_collection.find({"email": {"$in": emails}}))

    for app in apps:
        message = f\"\"\"\n📥 *Application Details*\n\n👩🏻 *Name:* {app.get('name')}\n🎂 *Age:* {app.get('age')}\n📧 *Email:* {app.get('email')}\n📱 *Phone:* +{app.get('contact')}\n🌍 *Nationality:* {app.get('country')}\n📸 *Instagram:* {app.get('instagram', '—')}\n🎵 *TikTok:* {app.get('tiktok', '—')}\n📬 *Telegram:* @{app.get('telegram', '')}\n🛰️ *City:* {app.get('ip_city', '—')}\n🌐 *Region:* {app.get('ip_region', '—')}\n🏳️ *Country:* {app.get('ip_country', '—')}\n\"\"\"\n
        print(f\"\\n➡️ Sending message to {tg_id} for {app.get('email')}\")\n
        try:\n
            msg_res = requests.post(\n
                f\"https://api.telegram.org/bot{os.getenv('TELEGRAM_BOT_TOKEN')}/sendMessage\",\n
                json={\"chat_id\": tg_id, \"text\": message, \"parse_mode\": \"Markdown\"}\n
            )\n
            print(\"✅ Text sent\", msg_res.status_code, msg_res.text)\n
        except Exception as e:\n
            print(\"❌ Telegram message failed:\", e)\n

        for url in app.get(\"photos\", []):\n
            try:\n
                photo_res = requests.post(\n
                    f\"https://api.telegram.org/bot{os.getenv('TELEGRAM_BOT_TOKEN')}/sendPhoto\",\n
                    json={\"chat_id\": tg_id, \"photo\": url}\n
                )\n
                print(\"✅ Photo sent:\", photo_res.status_code, photo_res.text)\n
            except Exception as e:\n
                print(\"❌ Telegram photo failed:\", e)

    return jsonify({\"status\": \"ok\"})

@app.route("/api/users", methods=["GET"])
def get_users():
    result = users_collection.find()
    user_list = []
    for user in result:
        user_list.append({
            "id": str(user["_id"]),
            "username": user["username"],
            "telegram": user.get("telegram", ""),
            "permissions": user.get("permissions", [])
        })
    return jsonify(user_list)

@app.route("/api/edit-user/<user_id>", methods=["PUT"])
def edit_user(user_id):
    data = request.get_json()
    update_fields = {}

    if "username" in data:
        update_fields["username"] = data["username"]

    if "password" in data and data["password"]:
        update_fields["password_hash"] = bcrypt.hashpw(
            data["password"].encode("utf-8"), bcrypt.gensalt()
        )

    if "telegram" in data:
        update_fields["telegram"] = data["telegram"]

    if "permissions" in data:
        update_fields["permissions"] = data["permissions"]

    users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": update_fields}
    )

    return jsonify({"status": "User updated"})


@app.route("/api/delete-user/<user_id>", methods=["DELETE"])
def delete_user(user_id):
    users_collection.delete_one({"_id": ObjectId(user_id)})
    return jsonify({"status": "User deleted"})
@app.route("/create-admin")
def create_admin_user():
    import bcrypt
    username = "admin"
    password = "Stars2025!"
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    
    if users_collection.find_one({"username": username}):
        return "⚠️ Admin already exists"

    users_collection.insert_one({
        "username": username,
        "password_hash": hashed,
        "permissions": ["view", "edit", "delete"]
    })
    return "✅ Admin created"

if __name__ == "__main__":
    print("✅ Flask server ready on port", PORT)
    app.run(host="0.0.0.0", port=PORT)
