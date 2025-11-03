# 🚀 IntelliLot - Smart Parking Detection Platform

## New Landing Page & Dashboard System

This document explains the new landing page, organization dashboard, and API credential management system that has been added to the YoloParklot project.

---

## 🎯 What's New?

### 1. **Professional Landing Page** (`/`)
- Modern, responsive design explaining the project
- Features section highlighting YOLOv8 AI detection, cloud API, edge device support
- Step-by-step setup guide
- Technology stack showcase
- Login/Signup modals with form validation
- Call-to-action buttons

### 2. **Organization Dashboard** (`/dashboard`)
- User profile display with organization info
- API credential management (generate, revoke, activate, delete)
- Copyable API keys for edge devices
- Code examples in Python, cURL, and JavaScript
- Statistics display (active API keys, parking capacity, location)
- Link to old dashboard for backward compatibility

### 3. **API Credential System**
- Generate secure API keys (64-character tokens)
- Each key can have a custom name (e.g., "Raspberry Pi #1")
- Revoke/activate keys without deleting them
- Delete keys permanently
- Track usage (last used timestamp, usage count)
- Support both JWT tokens and API keys for authentication

---

## 🌐 User Flow

### For New Organizations

```
1. Visit Landing Page (/)
   ↓
2. Click "Get Started Free"
   ↓
3. Fill Signup Form:
   - Username
   - Password
   - Organization Name
   - Location
   - Parking Capacity
   ↓
4. Account Created → Redirected to Login
   ↓
5. Login with Credentials
   ↓
6. Dashboard Opens (/dashboard)
   ↓
7. Generate API Key
   ↓
8. Copy API Key
   ↓
9. Paste into Edge Device Code
   ↓
10. Edge Device Starts Sending Data
```

### For Existing Users

```
1. Visit Landing Page (/)
   ↓
2. Click "Login"
   ↓
3. Enter Credentials
   ↓
4. Dashboard Opens
   ↓
5. Manage API Keys & View Stats
```

---

## 📁 New Files Created

### Templates
- `templates/landing.html` - Landing page with signup/login modals
- `templates/dashboard.html` - Organization dashboard with credential management

### Modified Files
- `apis/auth_api.py` - Added credential endpoints
- `apis/web_api.py` - Added landing, dashboard, old-dashboard routes
- `apis/parking_api.py` - Updated to support API key authentication
- `models/user.py` - Added API credential methods
- `middlewares/auth_middleware.py` - Added `api_key_or_token_required` decorator
- `auth/jwt_handler.py` - Updated to support API key user context

---

## 🔑 API Credential Endpoints

### Generate New API Key
```http
POST /auth/credentials/generate
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "name": "Raspberry Pi Entrance Camera"
}
```

**Response:**
```json
{
  "success": true,
  "credential": {
    "credential_id": "uuid",
    "api_key": "secure-64-char-token",
    "name": "Raspberry Pi Entrance Camera",
    "status": "active",
    "created_at": "2025-11-02T..."
  }
}
```

### Get All API Keys
```http
GET /auth/credentials
Authorization: Bearer <jwt_token>
```

### Revoke API Key
```http
POST /auth/credentials/<credential_id>/revoke
Authorization: Bearer <jwt_token>
```

### Activate API Key
```http
POST /auth/credentials/<credential_id>/activate
Authorization: Bearer <jwt_token>
```

### Delete API Key
```http
DELETE /auth/credentials/<credential_id>
Authorization: Bearer <jwt_token>
```

### Get User Profile
```http
GET /auth/profile
Authorization: Bearer <jwt_token>
```

---

## 🖥️ Edge Device Integration

### Using API Key in Python (Raspberry Pi)

```python
import requests
import json
from datetime import datetime

# Configuration
API_URL = "http://your-server.com"
API_KEY = "your-generated-api-key-from-dashboard"  # 64-char token
CAMERA_ID = "entrance_camera_01"

def send_parking_data(coordinates, occupied_count, total_count):
    """Send parking detection results to cloud API"""
    
    url = f"{API_URL}/parking/update"
    headers = {
        "Authorization": f"Bearer {API_KEY}",  # Use API key as Bearer token
        "Content-Type": "application/json"
    }
    
    payload = {
        "camera_id": CAMERA_ID,
        "coordinates": coordinates,
        "total_slots": total_count,
        "occupied_slots": occupied_count,
        "empty_slots": total_count - occupied_count,
        "occupancy_rate": (occupied_count / total_count) * 100,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    response = requests.post(url, json=payload, headers=headers)
    return response.json()

# Example usage
parking_coords = [[100, 150, 200, 250], [220, 150, 320, 250]]
result = send_parking_data(parking_coords, 15, 50)
print(result)
```

### Using API Key in cURL

```bash
curl -X POST http://your-server.com/parking/update \
  -H "Authorization: Bearer YOUR_API_KEY_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "camera_id": "test_camera_01",
    "coordinates": [[100,150,200,250]],
    "total_slots": 50,
    "occupied_slots": 35,
    "empty_slots": 15,
    "occupancy_rate": 70.0
  }'
```

---

## 🔐 Authentication Methods

The system now supports **TWO authentication methods**:

### 1. JWT Token (for web dashboard)
- Used by dashboard UI
- Short-lived (1 hour default)
- Contains user_id and username
- Obtained via `/auth/login`

### 2. API Key (for edge devices)
- Used by Raspberry Pi, IoT devices
- Long-lived (no expiration)
- 64-character secure token
- Can be revoked/activated anytime
- Obtained from dashboard

### How It Works

Both `/parking/update` and `/parking/updateRaw` endpoints accept **either**:

```http
Authorization: Bearer <jwt_token>
```

**OR**

```http
Authorization: Bearer <api_key>
```

The middleware automatically detects which one is provided and authenticates accordingly.

---

## 🗄️ Database Schema

### New Collection: `api_credentials`

```javascript
{
  "_id": ObjectId("..."),
  "credential_id": "uuid",
  "user_id": "user-uuid",
  "name": "Raspberry Pi #1",
  "api_key": "64-char-secure-token",
  "status": "active",  // or "revoked"
  "created_at": ISODate("..."),
  "last_used": ISODate("..."),
  "usage_count": 42
}
```

**Indexes:**
- `api_key` (unique, for fast lookup)
- `user_id` (for listing user's credentials)
- `status` (for filtering active keys)

---

## 🎨 Frontend Features

### Landing Page (`landing.html`)
- **Hero Section**: Eye-catching gradient with project description
- **Features Grid**: 6 feature cards with icons
- **Setup Steps**: 4-step guide with colored numbers
- **Tech Stack Badges**: Technologies used
- **Modals**: Login and signup forms with validation
- **Responsive Design**: Mobile-friendly

### Dashboard (`dashboard.html`)
- **Welcome Banner**: User greeting with organization name
- **Stats Cards**: Active keys, capacity, location
- **Credential Cards**: Each API key in a card with copy button
- **Code Tabs**: Python, cURL, JavaScript examples
- **Empty State**: Friendly message when no keys exist
- **Real-time Updates**: Immediate UI refresh after actions

---

## 🚀 Deployment Steps

### 1. Start the Server

```bash
python app.py
```

Server runs on `http://localhost:5001`

### 2. Open Landing Page

Navigate to: `http://localhost:5001/`

### 3. Create Account

1. Click "Get Started Free"
2. Fill in organization details
3. Submit form

### 4. Login

1. Enter username and password
2. Redirected to dashboard

### 5. Generate API Key

1. Click "Generate New API Key"
2. Enter name (e.g., "Raspberry Pi Main Entrance")
3. Click generate
4. Copy the API key

### 6. Use in Edge Device

Paste the API key into your edge device code and start sending data!

---

## 🔄 Migration from Old System

### Before (Manual Process)
1. Manually create user via `/auth/register` API
2. Login to get JWT token
3. Store JWT token in edge device
4. JWT expires every hour → need to re-login

### After (Automated Dashboard)
1. Organizations self-signup via landing page
2. Generate API keys from dashboard
3. API keys never expire (until revoked)
4. Easy management: revoke/activate/delete
5. Multiple API keys per organization

### Backward Compatibility

- Old dashboard still available at `/old-dashboard`
- JWT authentication still works everywhere
- Existing edge devices using JWT continue to work
- No breaking changes to existing API endpoints

---

## 📊 Usage Tracking

Each time an API key is used:
- `last_used` timestamp is updated
- `usage_count` is incremented

This helps you:
- Identify inactive keys
- Monitor device activity
- Debug connectivity issues

---

## 🔒 Security Features

### API Key Security
- 64-character secure random tokens
- Generated using Python's `secrets.token_urlsafe(48)`
- Stored in database (no encryption needed as they're random)
- Can be revoked instantly

### Best Practices
1. **Unique keys per device**: Generate separate keys for each edge device
2. **Name your keys**: Use descriptive names like "RasPi Camera 1"
3. **Revoke compromised keys**: Immediately revoke if leaked
4. **Monitor usage**: Check last_used and usage_count regularly
5. **Delete unused keys**: Remove old/inactive keys

---

## 🎯 Use Cases

### Scenario 1: Parking Lot Operator
- Manages 3 parking locations
- Each location has 2 cameras
- Generates 6 API keys (one per camera)
- Names them: "Location A - Entrance", "Location A - Exit", etc.
- Monitors all data from single dashboard

### Scenario 2: IoT Company
- Deploys 100 Raspberry Pi devices
- Generates 100 API keys (one per device)
- Tracks which devices are active via last_used
- Revokes keys for decommissioned devices

### Scenario 3: Developer Testing
- Generates test API key
- Uses in development/staging
- Deletes after testing complete

---

## 🐛 Troubleshooting

### Issue: "Authentication required"
**Solution**: Check Authorization header format:
```http
Authorization: Bearer YOUR_API_KEY
```

### Issue: API key not working
**Solution**: 
1. Verify key is "active" status in dashboard
2. Check if you copied the full key (no spaces)
3. Ensure using correct endpoint URL

### Issue: Can't login to dashboard
**Solution**:
1. Clear browser localStorage: `localStorage.clear()`
2. Try registering a new account
3. Check MongoDB connection

### Issue: Dashboard blank/not loading
**Solution**:
1. Open browser console (F12)
2. Check for JavaScript errors
3. Verify Flask server is running
4. Check `/auth/profile` endpoint

---

## 📚 Related Documentation

- [UPDATERAW_API_EXPLAINED.md](UPDATERAW_API_EXPLAINED.md) - UpdateRaw API details
- [RASPBERRY_PI_AUTHENTICATION_GUIDE.md](RASPBERRY_PI_AUTHENTICATION_GUIDE.md) - Edge device setup
- [API_DOCUMENTATION.md](API_DOCUMENTATION.md) - Complete API reference

---

## 🎉 Summary

The new landing page and dashboard system provides:

✅ **Self-service signup** for organizations  
✅ **Easy API key management** from dashboard  
✅ **No manual account creation** needed  
✅ **Better security** with revocable keys  
✅ **Usage tracking** for monitoring  
✅ **Code examples** for quick integration  
✅ **Professional UI** for better UX  
✅ **Backward compatible** with existing systems  

Organizations can now:
1. Sign up instantly
2. Generate API credentials
3. Deploy edge devices
4. Monitor their parking lots

All without any manual intervention! 🚀
