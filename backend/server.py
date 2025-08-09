# server.py

from __future__ import annotations

import io
import os
import re
import time
import json
import uuid
import bcrypt
import cloudinary
import requests
import numpy as np
import pycountry
from bson import ObjectId
from dotenv import load_dotenv
from datetime import datetime
from pypdf import PdfReader            # PDF text extraction
from flask import (
    Flask, request, render_template, redirect, url_for,
    session, jsonify
)
from pymongo import MongoClient
import cloudinary.uploader
from openai import OpenAI
from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
from langchain.docstore.document import Document
from PyPDF2 import PdfReader
import json

# Initialize embeddings + vector store
embeddings = OpenAIEmbeddings(openai_api_key=os.getenv("OPENAI_API_KEY"))
vector_store = None  # Will store indexed documents
# =========================
# Boot / Config
# =========================
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "super-secret-key")

# Single CORS init (includes admin and frontend)
from flask_cors import CORS

ALLOWED_ORIGINS = [
    "https://cute-stars.onrender.com",  # new frontend on Render
]

CORS(
    app,
    resources={r"/*": {"origins": ALLOWED_ORIGINS}},
    supports_credentials=True
)


# Upload dir
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Session/cookie hardening (needed if you proxy over HTTPS)
app.config["MAX_CONTENT_LENGTH"] = 32 * 1024 * 1024  # 32 MB
app.config["SESSION_COOKIE_SAMESITE"] = "None"
app.config["SESSION_COOKIE_SECURE"] = True

# Mongo
MONGO_URI = os.getenv("MONGODB_URI")
PORT = int(os.getenv("PORT", 10000))
client = MongoClient(MONGO_URI)
db = client["CuteStarsDB"]
applications_collection = db["applications"]
users_collection = db["admin_users"]
knowledge_collection = db["knowledge"]          # flat rows: one record per chunk
sessions_coll = db["bot_sessions"]              # { chat_id, state, language, email, updated_at }
settings_collection = db["settings"]            # { webhook_enabled, bot_main_url, bot_alt_url }

# Cloudinary
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
)

# OpenAI client
openai_client = OpenAI()

# Telegram constants
LANGUAGE, EMAIL = range(2)
LANGUAGES = ["English", "Spanish", "Portuguese", "Russian", "Serbian"]
APP_URL_ANDROID = "https://iulia.s3.amazonaws.com/apps/livegirl_host.apk"
APP_URL_IOS     = "https://apps.apple.com/sa/app/halo-meditation-sleep/id1668970568"
SIGNUP_VIDEO    = "https://youtube.com/shorts/COPJyTKqthI?si=B-ZSom5UOoUJWZsV"
ADMIN_CHAT_ID   = int(os.getenv("TELEGRAM_CHAT_ID", "0"))

# In-memory doc list for admin table (metadata only)
DOCS: dict[str, dict] = {}

# =========================
# Guards
# =========================
@app.before_request
def guard_knowledge_routes():
    # Protect write actions; list/health can stay public
    if request.path.startswith("/knowledge") and request.method in {"POST", "DELETE"}:
        if "user" not in session:
            return jsonify({"ok": False, "error": "Unauthorized"}), 401

# =========================
# Embeddings / Index helpers (language-agnostic)
# =========================
EMBED_MODEL = "text-embedding-3-small"

def _normalize_ws(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip()

def chunk_text(text: str, max_tokens: int = 800) -> list[str]:
    """Rough char-based chunker (≈4 chars/token)."""
    text = _normalize_ws(text)
    max_chars = max_tokens * 4
    out, i, n = [], 0, len(text)
    while i < n:
        j = min(n, i + max_chars)
        cut = text.rfind(". ", i, j)
        if cut == -1 or cut < i + int(max_chars * 0.6):
            cut = j
        out.append(text[i:cut].strip())
        i = cut
    return [c for c in out if c]

def get_embedding(text: str) -> list[float]:
    return openai_client.embeddings.create(model=EMBED_MODEL, input=text).data[0].embedding

def index_into_vector_store(*, doc_id: str, name: str, kind: str, text: str) -> int:
    """
    Split `text` -> embed each chunk -> save flat rows into Mongo.
    Returns number of chunks written.
    """
    chunks = chunk_text(text, max_tokens=800)
    if not chunks:
        return 0

    rows = []
    for i, ch in enumerate(chunks):
        emb = get_embedding(ch)
        rows.append({
            "doc_id": doc_id,
            "name": name,
            "kind": kind,
            "chunk_index": i,
            "text": ch,
            "embedding": emb,
            "created_at": datetime.utcnow(),
            # language-agnostic knowledge
            "language": "all",
        })

    # Replace previous version of this doc_id if any
    knowledge_collection.delete_many({"doc_id": doc_id})
    knowledge_collection.insert_many(rows)
    return len(rows)

def search_knowledge(query: str, k: int = 6) -> list[dict]:
    """Cosine similarity over flat rows in `knowledge_collection`."""
    qv = np.array(get_embedding(query), dtype=np.float32)
    scored: list[tuple[float, dict]] = []
    # NOTE: paginate in production; this grabs first 2k rows for speed
    for row in knowledge_collection.find({}, {"_id": 0, "text": 1, "embedding": 1}).limit(2000):
        v = np.array(row.get("embedding", []), dtype=np.float32)
        if v.size == 0:
            continue
        sim = float(np.dot(qv, v) / (np.linalg.norm(qv) * np.linalg.norm(v) + 1e-9))
        scored.append((sim, row))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [row for _, row in scored[:k]]

def build_context_for_intro() -> str:
    docs = search_knowledge("overview, role, pay, onboarding, policies", k=6)
    return "\n\n".join(d["text"] for d in docs)

def build_context_for_question(question: str) -> str:
    docs = search_knowledge(question, k=6)
    return "\n\n".join(d["text"] for d in docs)

# =========================
# Misc helpers
# =========================
def country_to_flag(country_name):
    try:
        if not country_name:
            return ''
        country = pycountry.countries.get(name=country_name)
        if not country:
            country = pycountry.countries.search_fuzzy(country_name)[0]
        code = country.alpha_2
        return ''.join(chr(127397 + ord(c)) for c in code.upper())
    except Exception:
        return ''

def tg_send_message(chat_id, text, reply_markup=None, parse_mode=None):
    payload = {"chat_id": chat_id, "text": text}
    if parse_mode:
        payload["parse_mode"] = parse_mode
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{os.getenv('TELEGRAM_BOT_TOKEN')}/sendMessage",
            json=payload, timeout=15
        )
        return r.status_code, r.text
    except Exception as e:
        print("Telegram sendMessage error:", e)
        return 500, str(e)

def send_application_to_telegram(applicant, photo_urls=None):
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    if not token or not chat_id:
        print("⚠️ Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID; skipping Telegram notify.")
        return

    photo_urls = photo_urls or []
    flag = country_to_flag(applicant.get("country"))
    msg = [
        "📥 *New Application Received*",
        "",
        f"👩🏻 *Name:* {applicant.get('name')}",
        f"🎂 *Age:* {applicant.get('age')}",
        f"📧 *Email:* {applicant.get('email')}",
        f"📱 *Phone:* +{applicant.get('contact')}",
        f"🌍 *Nationality:* {flag} {applicant.get('country')}",
    ]
    if applicant.get("instagram"):
        msg.append(f"📸 *Instagram:* {applicant.get('instagram')}")
    if applicant.get("tiktok"):
        msg.append(f"🎵 *TikTok:* {applicant.get('tiktok')}")
    if applicant.get("telegram"):
        msg.append(f"📬 *Telegram:* @{applicant.get('telegram')}")
    if applicant.get("ip"):
        msg.append(f"\n🛰️ *IP Address:* {applicant.get('ip')}")
    if applicant.get("ip_city") or applicant.get("ip_country"):
        msg.append(f"🌐 *Location:* {applicant.get('ip_city')}, {applicant.get('ip_region')} ({applicant.get('ip_country')})")
    if applicant.get("ip_org"):
        msg.append(f"🏢 *ISP/Org:* {applicant.get('ip_org')}")

    lat = applicant.get("geo_latitude")
    lon = applicant.get("geo_longitude")
    acc = applicant.get("geo_accuracy")
    if lat and lon:
        try:
            float(lat); float(lon)
            maps_url = f"https://maps.google.com/?q={lat},{lon}"
            msg.append(f"\n📍 *Browser Location:*\nLat: `{lat}`, Lon: `{lon}` ({acc or '?'}m)\n[View on Google Maps]({maps_url})")
        except Exception:
            msg.append("\n📍 *Browser Location:* Unavailable")
    else:
        msg.append("\n📍 *Browser Location:* Not shared")

    text = "\n".join(msg)
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"},
            timeout=15,
        )
        if r.status_code != 200:
            print("❌ Telegram sendMessage error:", r.text)
    except Exception as e:
        print("❌ Telegram sendMessage exception:", e)

    if photo_urls:
        group = [{"type": "photo", "media": u} for u in photo_urls[:10]]
        try:
            r2 = requests.post(
                f"https://api.telegram.org/bot{token}/sendMediaGroup",
                json={"chat_id": chat_id, "media": group},
                timeout=20,
            )
            if r2.status_code != 200:
                print("❌ Telegram sendMediaGroup error:", r2.text)
        except Exception as e:
            print("❌ Telegram sendMediaGroup exception:", e)

def set_state(chat_id, **fields):
    fields["updated_at"] = datetime.utcnow()
    sessions_coll.update_one(
        {"chat_id": chat_id},
        {"$set": fields, "$setOnInsert": {"chat_id": chat_id}},
        upsert=True,
    )

def get_state(chat_id):
    return sessions_coll.find_one({"chat_id": chat_id}) or {}

# =========================
# Settings (ONE source of truth)
# =========================
def get_settings():
    s = settings_collection.find_one({}, {"_id": 0}) or {}
    return {
        "webhook_enabled": s.get("webhook_enabled", True),
        "bot_main_url": s.get("bot_main_url", "https://t.me/AiSiva_bot"),
        "bot_alt_url":  s.get("bot_alt_url",  "https://t.me/AlternateBot"),
    }

@app.route("/api/settings", methods=["GET"])
def api_get_settings():
    return jsonify(get_settings()), 200

@app.route("/api/settings", methods=["POST"])
def api_save_settings():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json(force=True) or {}
    settings_collection.update_one(
        {},
        {"$set": {
            "webhook_enabled": bool(data.get("webhook_enabled", True)),
            "bot_main_url": data.get("bot_main_url", "").strip(),
            "bot_alt_url":  data.get("bot_alt_url", "").strip(),
        }},
        upsert=True
    )
    return jsonify({"status": "ok"}), 200

@app.route("/public/bot-link", methods=["GET"])
def public_bot_link():
    s = get_settings()
    url = s.get("bot_main_url") if s.get("webhook_enabled", True) else s.get("bot_alt_url")
    return jsonify({"url": url}), 200

# =========================
# Basic pages
# =========================
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
    for app_doc in raw_data:
        try:
            app_doc["country_flag"] = country_to_flag(app_doc.get("country"))
        except Exception:
            app_doc["country_flag"] = ""
    return render_template("applications.html", apps=raw_data)

# =========================
# Application API
# =========================
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

        geo = {}
        client_ip = request.form.get("ip")
        client_city = request.form.get("geoCity")
        client_country = request.form.get("geoCountry")
        client_region = request.form.get("geoRegion")
        latitude = request.form.get("latitude")
        longitude = request.form.get("longitude")
        geo_accuracy = request.form.get("geoAccuracy")
        if client_ip:      geo["ip"] = client_ip
        if client_city:    geo["ip_city"] = client_city
        if client_country: geo["ip_country"] = client_country
        if client_region:  geo["ip_region"] = client_region

        if not all([name, age, email, contact, country]) or not photos:
            return jsonify({"message": "Missing required fields or photos."}), 400

        ip_address = request.headers.get("CF-Connecting-IP") or \
                     request.headers.get("X-Forwarded-For", request.remote_addr).split(",")[0].strip()

        try:
            res = requests.get(f"https://ipapi.co/{ip_address}/json/", timeout=10)
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

        try:
            send_application_to_telegram(applicant_data, uploaded_urls)
        except Exception as e:
            print("Telegram notify error:", e)

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

@app.route("/api/applications", methods=["GET"])
def api_applications():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    data = list(applications_collection.find({}, {"_id": 0}))
    for app_doc in data:
        try:
            app_doc["country_flag"] = country_to_flag(app_doc.get("country"))
        except Exception:
            app_doc["country_flag"] = ""
    return jsonify(data), 200

# =========================
# Users / Admin CRUD
# =========================
@app.route("/api/add-user", methods=["POST"])
def add_user():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    telegram = data.get("telegram")
    permissions = data.get("permissions", [])

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
    if not emails or not tg_id:
        return jsonify({"status": "error", "message": "Missing data"}), 400

    apps = list(applications_collection.find({"email": {"$in": emails}}))
    for app_doc in apps:
        message = (
            f"📥 *Application Details*\n\n"
            f"👩🏻 *Name:* {app_doc.get('name')}\n"
            f"🎂 *Age:* {app_doc.get('age')}\n"
            f"📧 *Email:* {app_doc.get('email')}\n"
            f"📱 *Phone:* +{app_doc.get('contact')}\n"
            f"🌍 *Nationality:* {app_doc.get('country')}\n"
            f"📸 *Instagram:* {app_doc.get('instagram', '—')}\n"
            f"🎵 *TikTok:* {app_doc.get('tiktok', '—')}\n"
            f"📬 *Telegram:* @{app_doc.get('telegram', '')}\n"
            f"🛰️ *City:* {app_doc.get('ip_city', '—')}\n"
            f"🌐 *Region:* {app_doc.get('ip_region', '—')}\n"
            f"🏳️ *Country:* {app_doc.get('ip_country', '—')}"
        )
        try:
            requests.post(
                f"https://api.telegram.org/bot{os.getenv('TELEGRAM_BOT_TOKEN')}/sendMessage",
                json={"chat_id": tg_id, "text": message, "parse_mode": "Markdown"}
            )
        except Exception as e:
            print("❌ Telegram message failed:", e)

        photo_urls = app_doc.get("photos", [])
        if photo_urls:
            media_group = [{"type": "photo", "media": url} for url in photo_urls[:10]]
            try:
                requests.post(
                    f"https://api.telegram.org/bot{os.getenv('TELEGRAM_BOT_TOKEN')}/sendMediaGroup",
                    json={"chat_id": tg_id, "media": media_group}
                )
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

    users_collection.update_one({"_id": ObjectId(user_id)}, {"$set": update_fields})
    return jsonify({"status": "User updated"})

@app.route("/api/delete-user/<user_id>", methods=["DELETE"])
def delete_user(user_id):
    users_collection.delete_one({"_id": ObjectId(user_id)})
    return jsonify({"status": "User deleted"})

@app.route("/create-admin")
def create_admin_user():
    username = "admin"
    password = "Stars2025!"
    if users_collection.find_one({"username": username}):
        return "⚠️ Admin already exists"
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    users_collection.insert_one({
        "username": username,
        "password_hash": hashed,
        "permissions": ["view", "edit", "delete"]
    })
    return "✅ Admin created"

# =========================
# Knowledge upload (admin PDF legacy button)
# =========================
@app.route("/admin/upload-pdf", methods=["POST"])
def admin_upload_pdf():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    if "file" not in request.files:
        return jsonify({"error": "No file"}), 400

    lang = request.form.get("lang", "English")   # kept for response compatibility
    f = request.files["file"]
    data = f.read()

    # Index via the unified indexer
    try:
        doc_id = f"adminpdf-{uuid.uuid4()}"
        combined = ""
        reader = PdfReader(io.BytesIO(data))
        for page in reader.pages:
            combined += (page.extract_text() or "") + "\n"
        chunks = index_into_vector_store(doc_id=doc_id, name=f.filename, kind="pdf", text=combined)
        # store meta for table
        DOCS[doc_id] = {
            "id": doc_id, "name": f.filename, "kind": "pdf",
            "size": len(data), "chunks": chunks, "created_at": time.time()
        }
        return jsonify({"status": "ok", "chunks": chunks, "lang": lang})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# =========================
# Telegram Webhook (RAG + multilingual flow)
# =========================

# --- RAG helpers for the bot (language-agnostic storage) ---
def _embed(text: str) -> np.ndarray:
    v = openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    ).data[0].embedding
    return np.array(v, dtype=np.float32)

def retrieve_context(query: str, k: int = 6) -> str:
    """Cosine-sim search over Mongo 'knowledge' chunks → joined context string."""
    qv = _embed(query)
    scored = []
    # Limit to a manageable batch; adjust as needed
    for row in knowledge_collection.find({}, {"_id": 0, "text": 1, "embedding": 1}).limit(2000):
        ev = np.array(row.get("embedding") or [], dtype=np.float32)
        if ev.size == 0:
            continue
        sim = float(np.dot(qv, ev) / (np.linalg.norm(qv) * np.linalg.norm(ev) + 1e-9))
        scored.append((sim, row["text"]))
    scored.sort(key=lambda x: x[0], reverse=True)
    return "\n\n".join([t for _, t in scored[:k]])

def build_context_for_intro() -> str:
    # broad warm-up query; storage can be in any language
    return retrieve_context("overview role pay onboarding policies", k=6)

def build_context_for_question(question: str) -> str:
    return retrieve_context(question, k=6)


@app.route("/webhook", methods=["POST"])
def telegram_webhook():
    import traceback

    try:
        update = request.get_json(force=True, silent=True) or {}
        print("DEBUG update:", json.dumps(update, ensure_ascii=False))

        msg = update.get("message") or update.get("edited_message") or {}
        if not msg:
            return "ok", 200

        chat = msg.get("chat") or {}
        chat_id = chat.get("id")
        if not chat_id:
            return "ok", 200

        text = (msg.get("text") or "").strip()

        # Respect admin toggle
        s_conf = get_settings()
        if not s_conf.get("webhook_enabled", True):
            print("Webhook disabled by settings.")
            return "ok", 200

        return handle_webhook_logic(chat_id, text, msg)

    except Exception as e:
        print("WEBHOOK CRASH:", e)
        traceback.print_exc()
        return "ok", 200


def handle_webhook_logic(chat_id, text, msg):
    LANGUAGES = ["English", "Spanish", "Portuguese", "Russian", "Serbian"]

    def t(lang, key):
        D = {
            "welcome_choose_lang": {
                "English":    "👋 Welcome! Please choose your preferred language:",
                "Spanish":    "👋 ¡Bienvenido! Elige tu idioma preferido:",
                "Portuguese": "👋 Bem-vindo! Escolha seu idioma preferido:",
                "Russian":    "👋 Добро пожаловать! Пожалуйста, выберите предпочтительный язык:",
                "Serbian":    "👋 Dobrodošli! Molimo izaberite svoj jezik:"
            },
            "pick_lang_from_buttons": {
                "English":    "Please pick a language from the buttons.",
                "Spanish":    "Por favor elige un idioma con los botones.",
                "Portuguese": "Por favor escolha um idioma nos botões.",
                "Russian":    "Пожалуйста, выберите язык с помощью кнопок.",
                "Serbian":    "Molimo izaberite jezik pomoću dugmadi."
            },
            "ask_email": {
                "English":    "📧 Please enter your email (same one you used in the application):",
                "Spanish":    "📧 Por favor ingrese su correo (el mismo que usó en la solicitud):",
                "Portuguese": "📧 Por favor insira seu e-mail (o mesmo usado na inscrição):",
                "Russian":    "📧 Пожалуйста, введите вашу почту (ту же, что в заявке):",
                "Serbian":    "📧 Molimo unesite svoj e-mail (isti kao u prijavi):"
            },
            "email_not_found": {
                "English":    "❌ Sorry, we couldn’t find your application with that email. Please try again.",
                "Spanish":    "❌ No pudimos encontrar su solicitud con ese correo electrónico. Inténtelo de nuevo.",
                "Portuguese": "❌ Não encontramos sua inscrição com esse e-mail. Tente novamente.",
                "Russian":    "❌ Не нашли вашу заявку с этим email. Попробуйте ещё раз.",
                "Serbian":    "❌ Nismo pronašli vašu prijavu sa tom e-poštom. Pokušajte ponovo."
            },
            "generic_intro_fallback": {
                "English":    "Here’s a quick overview of the role and process. Feel free to ask any questions!",
                "Spanish":    "Aquí tienes un breve resumen del puesto y proceso. ¡No dudes en preguntar!",
                "Portuguese": "Aqui está um breve resumo do cargo e do processo. Fique à vontade para perguntar!",
                "Russian":    "Краткий обзор роли и процесса. Не стесняйтесь задавать вопросы!",
                "Serbian":    "Evo kratkog pregleda uloge i procesa. Slobodno postavite pitanja!"
            },
            "confirm_no_questions_btn": {
                "English":    "✅ I understand — no questions",
                "Spanish":    "✅ Entiendo — sin preguntas",
                "Portuguese": "✅ Entendi — sem dúvidas",
                "Russian":    "✅ Понятно — вопросов нет",
                "Serbian":    "✅ Razumem — bez pitanja"
            },
            "prompt_confirm_or_ask": {
                "English":    "If you have no further questions, tap the button below to continue.",
                "Spanish":    "Si no tiene más preguntas, toque el botón abajo para continuar.",
                "Portuguese": "Se não tiver mais dúvidas, toque no botão abaixo para continuar.",
                "Russian":    "Если вопросов больше нет, нажмите кнопку ниже, чтобы продолжить.",
                "Serbian":    "Ako nemate više pitanja, pritisnite dugme ispod da nastavite."
            },
            "ask_platform": {
                "English":    "📱 Which phone do you use?",
                "Spanish":    "📱 ¿Qué teléfono usas?",
                "Portuguese": "📱 Qual telefone você usa?",
                "Russian":    "📱 Каким телефоном вы пользуетесь?",
                "Serbian":    "📱 Koji telefon koristite?"
            },
            "android": { "English": "Android", "Spanish": "Android", "Portuguese": "Android", "Russian": "Android", "Serbian": "Android" },
            "ios":     { "English": "iOS",     "Spanish": "iOS",     "Portuguese": "iOS",     "Russian": "iOS",     "Serbian": "iOS" },
            "choose_android_or_ios": {
                "English":    "Please choose Android or iOS from the buttons.",
                "Spanish":    "Por favor elija Android o iOS con los botones.",
                "Portuguese": "Por favor escolha Android ou iOS nos botões.",
                "Russian":    "Пожалуйста, выберите Android или iOS с помощью кнопок.",
                "Serbian":    "Molimo izaberite Android ili iOS pomoću dugmadi."
            },
            "download_link": {
                "English":    "⬇️ Download the app:\n{link}",
                "Spanish":    "⬇️ Descarga la app:\n{link}",
                "Portuguese": "⬇️ Baixe o app:\n{link}",
                "Russian":    "⬇️ Скачайте приложение:\n{link}",
                "Serbian":    "⬇️ Preuzmite aplikaciju:\n{link}"
            },
            "signup_video": {
                "English":    "🎬 Sign-up guide:\n{video}",
                "Spanish":    "🎬 Guía de registro:\n{video}",
                "Portuguese": "🎬 Guia de cadastro:\n{video}",
                "Russian":    "🎬 Видеогид по регистрации:\n{video}",
                "Serbian":    "🎬 Vodič za registraciju:\n{video}"
            },
            "ask_app_id": {
                "English":    "Please send your *Application ID* now.",
                "Spanish":    "Por favor envíe su *ID de solicitud* ahora.",
                "Portuguese": "Por favor envie seu *ID de inscrição* agora.",
                "Russian":    "Пожалуйста, отправьте сейчас ваш *ID заявки*.",
                "Serbian":    "Molimo pošaljite sada svoj *ID prijave*."
            },
            "thanks_wait": {
                "English":    "✅ Received. Your account will be reviewed. Activation usually takes 1–2 working days.",
                "Spanish":    "✅ Recibido. Revisaremos su cuenta. La activación suele tardar 1–2 días hábiles.",
                "Portuguese": "✅ Recebido. Sua conta será analisada. A ativação leva 1–2 dias úteis.",
                "Russian":    "✅ Получено. Ваша учетная запись будет рассмотрена. Обычно активация занимает 1–2 рабочих дня.",
                "Serbian":    "✅ Primljeno. Vaš nalog će biti pregledan. Aktivacija obično traje 1–2 radna dana."
            },
        }
        return D.get(key, {}).get(lang, D.get(key, {}).get("English", ""))

    def kb_language():
        return {
            "keyboard": [[{"text": l} ] for l in LANGUAGES],
            "resize_keyboard": True,
            "one_time_keyboard": True,
        }

    def kb_confirm(lang):
        return {
            "keyboard": [[{"text": t(lang, "confirm_no_questions_btn")}]],
            "resize_keyboard": True,
            "one_time_keyboard": False,
        }

    def kb_platform(lang):
        return {
            "keyboard": [[{"text": t(lang, "android")}], [{"text": t(lang, "ios")}]],
            "resize_keyboard": True,
            "one_time_keyboard": True,
        }

    # ---- STATES ----
    if text.lower().startswith("/start"):
        set_state(chat_id, state="awaiting_language")
        tg_send_message(chat_id, t("English", "welcome_choose_lang"), reply_markup=kb_language())
        return "ok", 200

    st = get_state(chat_id)
    state = st.get("state")
    lang = st.get("language", "English")

    # Choose language
    if state == "awaiting_language":
        if text not in LANGUAGES:
            tg_send_message(chat_id, t("English", "pick_lang_from_buttons"), reply_markup=kb_language())
            return "ok", 200
        set_state(chat_id, state="awaiting_email", language=text)
        tg_send_message(chat_id, t(text, "ask_email"))
        return "ok", 200

    # Email check → GPT intro
    if state == "awaiting_email":
        email = text.strip().lower()
        applicant = applications_collection.find_one({"email": email})
        if not applicant:
            tg_send_message(chat_id, t(lang, "email_not_found"))
            return "ok", 200

        applications_collection.update_one(
            {"_id": applicant["_id"]},
            {"$set": {"telegram_id": chat_id, "language": lang}},
        )

        try:
            context = build_context_for_intro()
            prompt_user = (
                f"Speak in {lang}. Using ONLY the provided context, briefly explain the job, "
                f"benefits, pay cadence, and requirements in 120–180 words. Invite the applicant to ask questions.\n\n"
                f"=== CONTEXT START ===\n{context}\n=== CONTEXT END ==="
            )
            gpt_response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system",
                     "content": "You are a recruiter. Answer strictly from context."},
                    {"role": "user", "content": prompt_user},
                ],
                temperature=0.4,
            )
            intro_text = gpt_response.choices[0].message.content
        except Exception as e:
            print("OpenAI intro error:", e)
            intro_text = t(lang, "generic_intro_fallback")

        tg_send_message(chat_id, intro_text)
        tg_send_message(chat_id, t(lang, "prompt_confirm_or_ask"), reply_markup=kb_confirm(lang))
        set_state(chat_id, state="job_intro", email=email)
        return "ok", 200

    # Q&A stage
    if state == "job_intro":
        if text == t(lang, "confirm_no_questions_btn"):
            set_state(chat_id, state="awaiting_platform")
            tg_send_message(chat_id, t(lang, "ask_platform"), reply_markup=kb_platform(lang))
            return "ok", 200

        try:
            context = build_context_for_question(text)
            qna_prompt = (
                f"Use the context to answer in {lang}, friendly and concise.\n"
                f"Question: {text}\n\n"
                f"=== CONTEXT START ===\n{context}\n=== CONTEXT END ==="
            )
            gpt_answer = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "Answer clearly using the provided context only."},
                    {"role": "user", "content": qna_prompt},
                ],
                temperature=0.5,
            )
            answer = gpt_answer.choices[0].message.content
        except Exception as e:
            print("OpenAI Q&A error:", e)
            answer = t(lang, "prompt_confirm_or_ask")

        tg_send_message(chat_id, answer, parse_mode="Markdown")
        tg_send_message(chat_id, t(lang, "prompt_confirm_or_ask"), reply_markup=kb_confirm(lang))
        return "ok", 200

    # Choose platform
    if state == "awaiting_platform":
        lower = text.strip().lower()
        is_android = lower == t(lang, "android").lower()
        is_ios = lower == t(lang, "ios").lower()
        if not (is_android or is_ios):
            tg_send_message(chat_id, t(lang, "choose_android_or_ios"), reply_markup=kb_platform(lang))
            return "ok", 200

        link = APP_URL_ANDROID if is_android else APP_URL_IOS
        tg_send_message(chat_id, t(lang, "download_link").format(link=link))
        tg_send_message(chat_id, t(lang, "signup_video").format(video=SIGNUP_VIDEO))
        tg_send_message(chat_id, t(lang, "ask_app_id"), parse_mode="Markdown")
        set_state(chat_id, state="awaiting_app_id")
        return "ok", 200

    # Receive App ID
    if state == "awaiting_app_id":
        app_id = text.strip()
        email = st.get("email")
        if email:
            applications_collection.update_one(
                {"email": email},
                {"$set": {"application_id": app_id}},
            )
        tg_send_message(chat_id, t(lang, "thanks_wait"))
        set_state(chat_id, state="waiting_approval")

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
                        f"Reply:  *activated {app_doc.get('email')}*"
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

    # Admin fast approval
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

    # Fallback
    tg_send_message(chat_id, "Please type /start to begin.")
    return "ok", 200

# =========================
# Knowledge upload/list/delete/search (JSON, JSONL, PDF)
# =========================
@app.route("/knowledge/health", methods=["GET"])
def knowledge_health():
    return jsonify({"ok": True, "service": "knowledge"})

@app.route("/knowledge/upload", methods=["POST"])
def upload_knowledge():
    global vector_store
    try:
        file = request.files.get("file")
        if not file:
            return jsonify({"error": "No file uploaded"}), 400

        filename = file.filename
        ext = os.path.splitext(filename)[1].lower()
        save_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(save_path)

        text_chunks = []

        # ===== PDF =====
        if ext == ".pdf":
            reader = PdfReader(save_path)
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    text_chunks.append(text.strip())

        # ===== JSON =====
        elif ext == ".json":
            with open(save_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                for entry in data:
                    text_chunks.append(json.dumps(entry, ensure_ascii=False))
            elif isinstance(data, dict):
                text_chunks.append(json.dumps(data, ensure_ascii=False))

        # ===== JSONL =====
        elif ext == ".jsonl":
            with open(save_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        try:
                            obj = json.loads(line.strip())
                            text_chunks.append(json.dumps(obj, ensure_ascii=False))
                        except json.JSONDecodeError:
                            continue

        else:
            return jsonify({"error": f"Unsupported file type: {ext}"}), 400

        # Convert chunks to LangChain Document objects
        docs = [Document(page_content=chunk) for chunk in text_chunks]

        # Create or update FAISS vector store
        if vector_store is None:
            vector_store = FAISS.from_documents(docs, embeddings)
        else:
            vector_store.add_documents(docs)

        return jsonify({
            "ok": True,
            "doc": {
                "name": filename,
                "kind": ext[1:],
                "size": os.path.getsize(save_path),
                "chunks": len(text_chunks)
            }
        })

    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500

@app.route("/knowledge", methods=["GET"])
def knowledge_list():
    return jsonify({"docs": list(DOCS.values())})

@app.route("/knowledge/<doc_id>", methods=["DELETE"])
def knowledge_delete(doc_id):
    if doc_id not in DOCS:
        return jsonify({"error": "Not found"}), 404
    knowledge_collection.delete_many({"doc_id": doc_id})
    del DOCS[doc_id]
    return jsonify({"ok": True})

@app.route("/knowledge/search", methods=["GET"])
def knowledge_search():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"error": "q required"}), 400
    qv = np.array(get_embedding(q))
    items = list(knowledge_collection.find({}, {"_id": 0, "text": 1, "embedding": 1, "name": 1, "doc_id": 1}).limit(500))
    scored = []
    for it in items:
        v = np.array(it["embedding"])
        sim = float(np.dot(qv, v) / (np.linalg.norm(qv) * np.linalg.norm(v) + 1e-9))
        scored.append((sim, it))
    scored.sort(key=lambda x: x[0], reverse=True)
    top = [{"score": round(s, 4), "name": it["name"], "doc_id": it["doc_id"], "text": it["text"][:300]} for s, it in scored[:5]]
    return jsonify({"results": top})

# =========================
# Main
# =========================
if __name__ == "__main__":
    print("✅ Flask server ready on port", PORT)
    app.run(host="0.0.0.0", port=PORT)
