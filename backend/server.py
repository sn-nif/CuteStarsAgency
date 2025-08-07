from flask import Flask, request, render_template, redirect, url_for, session, jsonify
from pymongo import MongoClient
from flask_cors import CORS
from dotenv import load_dotenv
import cloudinary.uploader
import cloudinary
import requests
import os
import bcrypt
from bson import ObjectId
import pycountry
import traceback
from openai import OpenAI
from pypdf import PdfReader
import io
import re
import numpy as np

# Load environment variables FIRST
load_dotenv()

# OpenAI client (reads OPENAI_API_KEY from env)
openai_client = OpenAI()



# =========================
# Telegram Bot Constants
# =========================
LANGUAGE, EMAIL = range(2)  # Conversation states
LANGUAGES = ["English", "Spanish", "Portuguese", "Russian", "Serbian"]

# App links + signup guide
APP_URL_ANDROID = "https://iulia.s3.amazonaws.com/apps/livegirl_host.apk"
APP_URL_IOS     = "https://apps.apple.com/sa/app/halo-meditation-sleep/id1668970568"
SIGNUP_VIDEO    = "https://youtube.com/shorts/COPJyTKqthI?si=B-ZSom5UOoUJWZsV"

# Admin (your personal Telegram numeric chat ID)
ADMIN_CHAT_ID = int(os.getenv("TELEGRAM_CHAT_ID", "0"))

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
knowledge_collection = db["knowledge"]  # { _id, lang, chunk_id, text, embedding: [floats] }

# -------- Knowledge helpers (PDF -> chunks -> embeddings) --------
EMBED_MODEL = "text-embedding-3-small"

def _normalize_ws(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()

def chunk_text(text: str, max_tokens: int = 800) -> list[str]:
    """
    Simple chunker by characters ~ 4 chars ~= 1 token (rough heuristic).
    Adjust if you see too-long prompts.
    """
    text = _normalize_ws(text)
    max_chars = max_tokens * 4
    chunks = []
    start = 0
    while start < len(text):
        end = min(len(text), start + max_chars)
        # try to cut at sentence boundary
        cut = text.rfind(". ", start, end)
        if cut == -1 or cut < start + int(0.6 * max_chars):
            cut = end
        chunks.append(text[start:cut].strip())
        start = cut
    return [c for c in chunks if c]

def get_embedding(text: str) -> list[float]:
    emb = openai_client.embeddings.create(
        model=EMBED_MODEL,
        input=text
    )
    return emb.data[0].embedding

def upsert_pdf_chunks(file_bytes: bytes, lang: str):
    reader = PdfReader(io.BytesIO(file_bytes))
    full_text = ""
    for page in reader.pages:
        full_text += (page.extract_text() or "") + "\n"
    chunks = chunk_text(full_text, max_tokens=800)

    docs = []
    for idx, ch in enumerate(chunks):
        emb = get_embedding(ch)
        docs.append({
            "lang": lang,
            "chunk_id": f"{lang}-{idx}",
            "text": ch,
            "embedding": emb,
        })

    # clear old docs for that lang, then insert
    knowledge_collection.delete_many({"lang": lang})
    if docs:
        knowledge_collection.insert_many(docs)
    return len(docs)

def search_knowledge(query: str, lang: str, k: int = 5) -> list[dict]:
    q_emb = np.array(get_embedding(query))
    scored = []
    for doc in knowledge_collection.find({"lang": lang}):
        if "embedding" not in doc: 
            continue
        v = np.array(doc["embedding"])
        sim = float(np.dot(q_emb, v) / (np.linalg.norm(q_emb)*np.linalg.norm(v) + 1e-9))
        scored.append((sim, doc))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [d for _, d in scored[:k]]

def build_context_for_intro(lang: str) -> str:
    # broad query to pull the best overview chunks
    docs = search_knowledge("overview, role, pay, requirements, onboarding, policies", lang, k=6)
    return "\n\n".join(d["text"] for d in docs)

def build_context_for_question(lang: str, question: str) -> str:
    docs = search_knowledge(question, lang, k=6)
    return "\n\n".join(d["text"] for d in docs)
# -------- end knowledge helpers --------

# Cloudinary setup
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
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
    # If browser-based location exists, add Google Maps link
    lat = data.get("geo_latitude")
    lon = data.get("geo_longitude")

    if lat and lon:
        try:
            float(lat)
            float(lon)
            maps_url = f"https://maps.google.com/?q={lat},{lon}"
            message += f"\n📍 *Browser Location:*\nLat: `{lat}`, Lon: `{lon}`\n[View on Google Maps]({maps_url})\n"
        except:
            message += f"\n📍 *Browser Location:* Unavailable\n"
    else:
        message += f"\n📍 *Browser Location:* Not shared\n"
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
        latitude = request.form.get("latitude")
        longitude = request.form.get("longitude")
        geo_accuracy = request.form.get("geoAccuracy")
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
            **geo,
            "geo_latitude": latitude,
            "geo_longitude": longitude,
            "geo_accuracy": geo_accuracy,
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
        message = (
            f"📥 *Application Details*\n\n"
            f"👩🏻 *Name:* {app.get('name')}\n"
            f"🎂 *Age:* {app.get('age')}\n"
            f"📧 *Email:* {app.get('email')}\n"
            f"📱 *Phone:* +{app.get('contact')}\n"
            f"🌍 *Nationality:* {app.get('country')}\n"
            f"📸 *Instagram:* {app.get('instagram', '—')}\n"
            f"🎵 *TikTok:* {app.get('tiktok', '—')}\n"
            f"📬 *Telegram:* @{app.get('telegram', '')}\n"
            f"🛰️ *City:* {app.get('ip_city', '—')}\n"
            f"🌐 *Region:* {app.get('ip_region', '—')}\n"
            f"🏳️ *Country:* {app.get('ip_country', '—')}"
        )

        print(f"\n➡️ Sending message to {tg_id} for {app.get('email')}")
        try:
            msg_res = requests.post(
                f"https://api.telegram.org/bot{os.getenv('TELEGRAM_BOT_TOKEN')}/sendMessage",
                json={"chat_id": tg_id, "text": message, "parse_mode": "Markdown"}
            )
            print("✅ Text sent", msg_res.status_code, msg_res.text)
        except Exception as e:
            print("❌ Telegram message failed:", e)

        photo_urls = app.get("photos", [])
        if photo_urls:
            media_group = [{"type": "photo", "media": url} for url in photo_urls[:10]]  # max 10 per group
            try:
                response = requests.post(
                    f"https://api.telegram.org/bot{os.getenv('TELEGRAM_BOT_TOKEN')}/sendMediaGroup",
                    json={"chat_id": tg_id, "media": media_group}
                )
                print("✅ Grouped photo response:", response.status_code, response.text)
            except Exception as e:
                print("❌ Telegram sendMediaGroup failed:", e)


    return jsonify({"status": "ok"})

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
@app.route("/admin/upload-pdf", methods=["POST"])
def admin_upload_pdf():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    if "file" not in request.files:
        return jsonify({"error": "No file"}), 400
    lang = request.form.get("lang", "English")
    f = request.files["file"]
    data = f.read()
    try:
        n = upsert_pdf_chunks(data, lang)
        return jsonify({"status": "ok", "chunks": n, "lang": lang})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ===== Telegram Webhook (no python-telegram-bot) =====
from datetime import datetime

# simple session collection for bot conversation
sessions = db["bot_sessions"]  # docs: { chat_id, state, language, email, updated_at }

def tg_send_message(chat_id, text, reply_markup=None, parse_mode=None):
    payload = {"chat_id": chat_id, "text": text}
    if parse_mode:
        payload["parse_mode"] = parse_mode
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{os.getenv('TELEGRAM_BOT_TOKEN')}/sendMessage",
            json=payload,
            timeout=15,
        )
        return r.status_code, r.text
    except Exception as e:
        print("Telegram sendMessage error:", e)
        return 500, str(e)

def set_state(chat_id, **fields):
    fields["updated_at"] = datetime.utcnow()
    sessions.update_one(
        {"chat_id": chat_id},
        {"$set": fields, "$setOnInsert": {"chat_id": chat_id}},
        upsert=True,
    )

def get_state(chat_id):
    return sessions.find_one({"chat_id": chat_id}) or {}
@app.route("/settings", methods=["GET"])
def settings_page():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("settings.html")
    
@app.route("/webhook", methods=["POST"])
def telegram_webhook():
    update = request.get_json(force=True, silent=True) or {}
    msg = update.get("message") or update.get("edited_message") or {}
    if not msg:
        return "ok", 200

    chat = msg.get("chat") or {}
    chat_id = chat.get("id")
    if not chat_id:
        return "ok", 200

    text = (msg.get("text") or "").strip()

    # /start → ask for language
    if text.lower().startswith("/start"):
        set_state(chat_id, state="awaiting_language")
        keyboard = {
            "keyboard": [[{"text": lang}] for lang in LANGUAGES],
            "resize_keyboard": True,
            "one_time_keyboard": True,
        }
        tg_send_message(
            chat_id,
            "👋 Welcome! Please choose your preferred language:",
            reply_markup=keyboard,
        )
        return "ok", 200

    st = get_state(chat_id)
    state = st.get("state")

    # language → ask for email
    if state == "awaiting_language":
        language = text.strip()
        if language not in LANGUAGES:
            tg_send_message(chat_id, "Please pick a language from the buttons.")
            return "ok", 200

        set_state(chat_id, state="awaiting_email", language=language)
        tg_send_message(
            chat_id,
            "📧 Please enter your email (same one you used in the application):",
        )
        return "ok", 200

    # email → verify + save → GPT job intro (with knowledge)
    if state == "awaiting_email":
        email = text.strip().lower()
        applicant = applications_collection.find_one({"email": email})

        if not applicant:
            tg_send_message(
                chat_id,
                "❌ Sorry, we couldn’t find your application with that email. Please try again.",
            )
            return "ok", 200

        # Save telegram_id + language onto the applicant
        applications_collection.update_one(
            {"_id": applicant["_id"]},
            {"$set": {"telegram_id": chat_id, "language": st.get("language")}},
        )

        # Use retrieved context from the PDF
        chosen_lang = st.get("language", "English")
        context = build_context_for_intro(chosen_lang)  # <- from your knowledge helpers
        if not context:
            context = "No uploaded knowledge yet. Provide a short generic overview."

        prompt_user = (
            f"Speak in {chosen_lang}. Using ONLY the provided context, briefly explain the job, "
            f"benefits, pay cadence, and requirements in 120–180 words. Invite the applicant to ask questions.\n\n"
            f"=== CONTEXT START ===\n{context}\n=== CONTEXT END ==="
        )

        try:
            gpt_response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a recruiter. Answer strictly from context. If something is missing, say you'll confirm with an admin.",
                    },
                    {"role": "user", "content": prompt_user},
                ],
                temperature=0.4,
            )
            intro_text = gpt_response.choices[0].message.content
        except Exception as e:
            print("OpenAI intro error:", e)
            intro_text = (
                "Here’s a quick overview of the role and process. (Context not available right now.) "
                "Feel free to ask any questions!"
            )

        tg_send_message(chat_id, intro_text)
        set_state(chat_id, state="job_intro", email=email)
        return "ok", 200

    # continuous Q&A with GPT (with knowledge) until they accept
    if state == "job_intro":
        user_msg = text.strip()

        # accept → terms
        if user_msg.lower() in {"accept", "i accept", "yes"}:
            set_state(chat_id, state="awaiting_terms")
            tg_send_message(
                chat_id,
                "📜 Great! Please confirm you accept our terms of service and privacy policy. "
                "Reply with *I accept* to continue.",
                parse_mode="Markdown",
            )
            return "ok", 200

        # Otherwise answer with GPT using knowledge
        chosen_lang = st.get("language", "English")
        context = build_context_for_question(chosen_lang, user_msg)  # <- from helpers
        if not context:
            context = "No relevant context segments found."

        qna_prompt = (
            f"Use the context to answer in {chosen_lang}, friendly and concise.\n"
            f"Question: {user_msg}\n\n"
            f"=== CONTEXT START ===\n{context}\n=== CONTEXT END ==="
        )

        try:
            gpt_answer = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You answer applicant questions about the job clearly using the provided context only.",
                    },
                    {"role": "user", "content": qna_prompt},
                ],
                temperature=0.5,
            )
            answer = gpt_answer.choices[0].message.content
        except Exception as e:
            print("OpenAI Q&A error:", e)
            answer = "Thanks for the question! If you’re ready, type *I accept* to proceed."
        tg_send_message(chat_id, answer, parse_mode="Markdown")
        return "ok", 200

    # TERMS → Q&A prompt
    if state == "awaiting_terms":
        if text.strip().lower() not in ["i accept", "accept", "yes"]:
            tg_send_message(chat_id, "Please type *I accept* to continue.", parse_mode="Markdown")
            return "ok", 200
        set_state(chat_id, state="qna_or_skip")
        tg_send_message(
            chat_id,
            "❓ Do you have any questions? Send them now, or type *skip*.",
            parse_mode="Markdown",
        )
        return "ok", 200

    # Optional Q&A → Platform
    if state == "qna_or_skip":
        if text.strip().lower() != "skip":
            tg_send_message(chat_id, "Thanks! Our team will reply if needed. Type *skip* to continue.")
            return "ok", 200
        keyboard = {
            "keyboard": [[{"text": "Android"}], [{"text": "iOS"}]],
            "resize_keyboard": True,
            "one_time_keyboard": True,
        }
        set_state(chat_id, state="awaiting_platform")
        tg_send_message(chat_id, "📱 Which phone do you use? (Android or iOS)", reply_markup=keyboard)
        return "ok", 200

    # Platform → send links + video → ask App ID
    if state == "awaiting_platform":
        choice = text.strip().lower()
        if choice not in ["android", "ios"]:
            tg_send_message(chat_id, "Please choose *Android* or *iOS* from the buttons.", parse_mode="Markdown")
            return "ok", 200
        link = APP_URL_ANDROID if choice == "android" else APP_URL_IOS
        tg_send_message(chat_id, f"⬇️ Download the app:\n{link}")
        tg_send_message(chat_id, f"🎬 Sign-up guide:\n{SIGNUP_VIDEO}")
        set_state(chat_id, state="awaiting_app_id")
        tg_send_message(chat_id, "Please send your *Application ID* now.", parse_mode="Markdown")
        return "ok", 200

    # Save App ID → waiting msg → notify admin
    if state == "awaiting_app_id":
        app_id = text.strip()
        email = st.get("email")

        if email:
            applications_collection.update_one(
                {"email": email},
                {"$set": {"application_id": app_id}},
            )

        set_state(chat_id, state="waiting_approval")
        tg_send_message(chat_id, "✅ Received. Please wait 1–2 working days for approval.")

        # Notify admin with summary + photos
        try:
            if ADMIN_CHAT_ID:
                app_doc = applications_collection.find_one({"email": email}) if email else None
                if app_doc:
                    summary = (
                        f"📝 Applicant\n"
                        f"• Name: {app_doc.get('name')}\n"
                        f"• Email: {app_doc.get('email')}\n"
                        f"• App ID: {app_doc.get('application_id')}\n"
                        f"• Country: {app_doc.get('country')}\n"
                        f"• Phone: +{app_doc.get('contact')}\n"
                        f"• Telegram ID: {chat_id}\n"
                        f"Reply with:  *activated {app_doc.get('email')}*  to approve."
                    )
                    tg_send_message(ADMIN_CHAT_ID, summary, parse_mode="Markdown")

                    photos = (app_doc.get("photos") or [])[:10]
                    if photos:
                        media_group = [{"type": "photo", "media": u} for u in photos]
                        requests.post(
                            f"https://api.telegram.org/bot{os.getenv('TELEGRAM_BOT_TOKEN')}/sendMediaGroup",
                            json={"chat_id": ADMIN_CHAT_ID, "media": media_group},
                            timeout=20,
                        )
        except Exception as e:
            print("Admin notify error:", e)

        return "ok", 200

    # Admin fast-approval (message like: "activated user@example.com")
    if ADMIN_CHAT_ID and chat_id == ADMIN_CHAT_ID:
        parts = text.strip().split()
        if len(parts) == 2 and parts[0].lower() in ["activated", "approve", "approved"]:
            target_email = parts[1].lower()
            applicant = applications_collection.find_one({"email": target_email})
            if not applicant:
                tg_send_message(ADMIN_CHAT_ID, f"❌ No applicant with email {target_email}")
                return "ok", 200

            applications_collection.update_one(
                {"_id": applicant["_id"]},
                {"$set": {"status": "activated"}},
            )

            tgt_chat_id = applicant.get("telegram_id")
            if tgt_chat_id:
                tg_send_message(int(tgt_chat_id), "🎉 Your account has been activated. You can log in now.")
            tg_send_message(ADMIN_CHAT_ID, f"✅ Activated {target_email}")
            return "ok", 200

    # fallback
    tg_send_message(chat_id, "Please type /start to begin.")
    return "ok", 200
# ===== end Telegram Webhook =====


if __name__ == "__main__":
    print("✅ Flask server ready on port", PORT)
    app.run(host="0.0.0.0", port=PORT)

