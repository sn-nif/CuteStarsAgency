from fastapi import FastAPI, APIRouter, HTTPException, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime
import shutil
import aiofiles

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Create uploads directory
UPLOAD_DIR = ROOT_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# Serve uploaded files
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

# Define Models
class ApplicationCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    age: int = Field(..., ge=18, le=35)
    email: EmailStr
    contact: str = Field(..., min_length=10, max_length=20)
    instagram: Optional[str] = Field(None, max_length=50)
    tiktok: Optional[str] = Field(None, max_length=50)
    twitter: Optional[str] = Field(None, max_length=50)
    photos: Optional[List[str]] = Field(default_factory=list)

class Application(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    age: int
    email: str
    contact: str
    instagram: Optional[str] = None
    tiktok: Optional[str] = None
    twitter: Optional[str] = None
    photos: List[str] = Field(default_factory=list)
    status: str = Field(default="pending")
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    reviewed_at: Optional[datetime] = None

class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str

# Add your routes to the router instead of directly to app
@api_router.get("/")
async def root():
    return {"message": "Cute Stars API - Ready to serve"}

@api_router.post("/upload/photo")
async def upload_photo(photo: UploadFile = File(...)):
    """Upload a single photo and return the URL"""
    try:
        # Validate file type
        if not photo.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Validate file size (10MB max)
        if photo.size > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File size must be less than 10MB")
        
        # Generate unique filename
        file_extension = photo.filename.split('.')[-1].lower()
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        file_path = UPLOAD_DIR / unique_filename
        
        # Save file
        async with aiofiles.open(file_path, 'wb') as buffer:
            content = await photo.read()
            await buffer.write(content)
        
        # Return URL
        base_url = os.environ.get('REACT_APP_BACKEND_URL', 'http://localhost:8001')
        photo_url = f"{base_url}/uploads/{unique_filename}"
        
        return {"url": photo_url, "filename": unique_filename}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Photo upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Photo upload failed")

@api_router.post("/applications", response_model=Application)
async def create_application(application_data: ApplicationCreate):
    """Create a new talent application"""
    try:
        # Create application object
        application = Application(**application_data.dict())
        
        # Check if email already exists
        existing_app = await db.applications.find_one({"email": application.email})
        if existing_app:
            raise HTTPException(status_code=400, detail="Application with this email already exists")
        
        # Save to database
        app_dict = application.dict()
        result = await db.applications.insert_one(app_dict)
        
        if result.inserted_id:
            logger.info(f"New application created: {application.email}")
            return application
        else:
            raise HTTPException(status_code=500, detail="Failed to save application")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Application creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Application submission failed")

@api_router.get("/applications", response_model=List[Application])
async def get_applications():
    """Get all applications (admin endpoint)"""
    try:
        applications = await db.applications.find().sort("submitted_at", -1).to_list(1000)
        return [Application(**app) for app in applications]
    except Exception as e:
        logger.error(f"Failed to fetch applications: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch applications")

@api_router.get("/applications/{application_id}", response_model=Application)
async def get_application_by_id(application_id: str):
    """Get a specific application by ID"""
    try:
        application = await db.applications.find_one({"id": application_id})
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")
        return Application(**application)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch application: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch application")

@api_router.put("/applications/{application_id}/status")
async def update_application_status(application_id: str, status: str = Form(...)):
    """Update application status (admin endpoint)"""
    try:
        if status not in ["pending", "approved", "rejected"]:
            raise HTTPException(status_code=400, detail="Invalid status")
        
        update_data = {
            "status": status,
            "reviewed_at": datetime.utcnow()
        }
        
        result = await db.applications.update_one(
            {"id": application_id},
            {"$set": update_data}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Application not found")
        
        return {"message": f"Application status updated to {status}"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update application status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update application status")

# Legacy status check endpoints
@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    _ = await db.status_checks.insert_one(status_obj.dict())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)