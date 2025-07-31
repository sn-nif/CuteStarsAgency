from dotenv import load_dotenv
import os
from pymongo import MongoClient
from flask import Flask

# Load environment variables from .env
load_dotenv()

# Get Mongo URI and port from environment
MONGO_URI = os.getenv("MONGODB_URI")
PORT = int(os.getenv("PORT", 10000))

# Connect to MongoDB
client = MongoClient(MONGO_URI)
db = client["CuteStarsDB"]

# Create a basic Flask app
app = Flask(__name__)

@app.route("/")
def home():
    return "✅ CuteStars backend is connected to MongoDB!"

if __name__ == "__main__":
    print("✅ Connected to MongoDB")
    app.run(host="0.0.0.0", port=PORT)
