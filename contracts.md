# Frontend-Backend Integration Contracts

## API Endpoints Required

### 1. Application Submission
- **POST** `/api/applications`
- **Body**: `{ name, age, email, contact, instagram, tiktok, twitter, photos[] }`
- **Response**: `{ id, status, message, submittedAt }`

### 2. File Upload
- **POST** `/api/upload/photos`
- **Body**: FormData with photo files
- **Response**: `{ urls: string[] }`

### 3. Get Applications (Admin)
- **GET** `/api/applications`
- **Response**: `{ applications: Application[] }`

## Data Models

### Application Schema
```json
{
  "id": "string",
  "name": "string",
  "age": "number",
  "email": "string",
  "contact": "string",
  "instagram": "string",
  "tiktok": "string", 
  "twitter": "string",
  "photos": ["string[]"],
  "status": "pending|approved|rejected",
  "submittedAt": "datetime",
  "reviewedAt": "datetime?"
}
```

## Mock Data to Replace

### Current Mock in `/app/frontend/src/utils/mock.js`:
- `mockApplications` array will be removed
- `mockAPI.submitApplication()` will use real endpoint
- Form submission will upload photos first, then submit application
- Success/error handling will use real API responses

## Frontend Changes Required

### 1. Remove Mock Dependencies
- Remove `import { mockApplications } from "../utils/mock"`
- Replace mock API calls with axios calls to backend

### 2. Photo Upload Integration
- Add chunked file upload for large photos
- Show upload progress
- Handle upload errors gracefully

### 3. Form Submission Flow
1. Validate form data
2. Upload photos if any (get URLs)
3. Submit application with photo URLs
4. Show success/error message
5. Reset form on success

## Backend Implementation Plan

### 1. MongoDB Models
- Application collection with schema above
- Photo storage handling (local/cloud)

### 2. File Upload Handler
- Multer for file processing
- Image validation and compression
- Secure file storage

### 3. Application CRUD
- Create application endpoint
- Validation and sanitization
- Email notifications (future)

## Integration Points

### Error Handling
- Network errors
- Validation errors  
- File upload errors
- Server errors

### Success Flow
- Photo upload success
- Application submission success
- Form reset and user feedback