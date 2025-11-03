# 🚀 Quick Start Guide - IntelliLot Dashboard & API Keys

## For Organizations (Web Dashboard Users)

### Step 1: Access the Landing Page
```
http://localhost:5001/
```

### Step 2: Create Your Account
1. Click **"Get Started Free"** button
2. Fill in the signup form:
   - **Username**: Your login username (min 3 characters)
   - **Password**: Secure password (min 6 characters)
   - **Organization Name**: Your company/organization name
   - **Location**: Physical address of your parking lot
   - **Parking Capacity**: Total number of parking slots
3. Click **"Create Account"**
4. You'll be redirected to login

### Step 3: Login to Dashboard
1. Click **"Login"** button on landing page
2. Enter your username and password
3. Click **"Login to Dashboard"**
4. You're now in your organization dashboard!

### Step 4: Generate API Key
1. In the dashboard, click **"+ Generate New API Key"**
2. Enter a name for this key:
   - Examples: "Raspberry Pi #1", "Entrance Camera", "Exit Camera"
3. Click generate
4. Your API key appears in a card below
5. Click **"Copy"** button to copy the key

### Step 5: Use API Key in Edge Device
1. Paste the copied API key into your edge device code
2. See `edge_device_client.py` for example
3. Your device will now send data to your dashboard!

---

## For Edge Device Developers (Raspberry Pi, etc.)

### Quick Integration

1. **Get Your API Key** from dashboard (see above)

2. **Install Python Script**:
```bash
# Copy edge_device_client.py to your device
wget http://your-server.com/edge_device_client.py
# Or copy manually
```

3. **Edit Configuration**:
```python
# Open edge_device_client.py
API_URL = "http://your-server.com"
API_KEY = "paste-your-64-char-api-key-here"
CAMERA_ID = "entrance_camera_01"
```

4. **Install Dependencies**:
```bash
pip install requests
```

5. **Run**:
```bash
python edge_device_client.py
```

### Quick Test with cURL

```bash
# Test your API key
curl -X POST http://localhost:5001/parking/update \
  -H "Authorization: Bearer YOUR_API_KEY_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "camera_id": "test_camera",
    "coordinates": [[100,150,200,250]],
    "total_slots": 1,
    "occupied_slots": 1,
    "empty_slots": 0,
    "occupancy_rate": 100.0
  }'
```

**Expected Response**:
```json
{
  "success": true,
  "document_id": "...",
  "message": "Parking data updated successfully"
}
```

---

## File Structure

```
YoloParklot/
├── templates/
│   ├── landing.html          ← NEW: Landing page
│   ├── dashboard.html         ← NEW: Organization dashboard
│   └── index.html             (Old dashboard, now at /old-dashboard)
│
├── apis/
│   ├── auth_api.py            ← UPDATED: Added credential endpoints
│   ├── parking_api.py         ← UPDATED: API key authentication
│   └── web_api.py             ← UPDATED: New routes
│
├── models/
│   └── user.py                ← UPDATED: API credential methods
│
├── middlewares/
│   └── auth_middleware.py     ← UPDATED: API key support
│
├── auth/
│   └── jwt_handler.py         ← UPDATED: Request context support
│
├── edge_device_client.py      ← NEW: Example edge device code
├── LANDING_PAGE_GUIDE.md      ← NEW: Complete documentation
└── QUICK_START_DASHBOARD.md   ← This file
```

---

## Routes

### Public Routes
- `GET /` - Landing page (signup/login)
- `GET /health` - Health check
- `POST /auth/register` - Create account
- `POST /auth/login` - Login

### Protected Routes (Requires JWT Token)
- `GET /dashboard` - Organization dashboard
- `GET /auth/profile` - Get user profile
- `GET /auth/credentials` - List API keys
- `POST /auth/credentials/generate` - Generate API key
- `POST /auth/credentials/<id>/revoke` - Revoke API key
- `POST /auth/credentials/<id>/activate` - Activate API key
- `DELETE /auth/credentials/<id>` - Delete API key

### Edge Device Routes (JWT or API Key)
- `POST /parking/update` - Send parking data
- `POST /parking/updateRaw` - Send raw image for processing

### Legacy Routes
- `GET /old-dashboard` - Original dashboard interface
- `GET /testing` - API testing interface

---

## Authentication Methods

### Method 1: JWT Token (Dashboard)
```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```
- **Lifetime**: 1 hour (default)
- **Use**: Web dashboard
- **Get via**: `/auth/login` endpoint

### Method 2: API Key (Edge Devices)
```http
Authorization: Bearer abc123def456...64-char-token
```
- **Lifetime**: Until revoked
- **Use**: Raspberry Pi, IoT devices
- **Get via**: Dashboard → Generate API Key

---

## Common Tasks

### Create Multiple API Keys
Useful when you have multiple edge devices:

1. Dashboard → Generate API Key → "Entrance Camera"
2. Dashboard → Generate API Key → "Exit Camera"
3. Dashboard → Generate API Key → "Overflow Lot Camera"

Each device gets its own key!

### Revoke Compromised Key
If an API key is leaked:

1. Dashboard → Find the key
2. Click **"Revoke"** button
3. Key immediately stops working
4. Generate a new key
5. Update device with new key

### Monitor Key Usage
Check when each device last sent data:

1. Dashboard → View credentials list
2. See "Created" timestamp
3. (Future: last_used timestamp will be displayed)

### Delete Old Keys
Remove unused keys:

1. Dashboard → Find the key
2. Click **"Delete"** button
3. Confirm deletion
4. Key permanently removed

---

## Troubleshooting

### Can't Login
**Issue**: "Invalid username or password"

**Solutions**:
- Check username (case-sensitive)
- Reset password (contact admin)
- Try registering again with different username

### API Key Not Working
**Issue**: "Authentication required"

**Solutions**:
- Verify key is copied completely (64 characters)
- Check key status is "active" in dashboard
- Ensure using correct Authorization header format:
  ```
  Authorization: Bearer YOUR_KEY
  ```

### Dashboard Shows 0 API Keys
**Issue**: No keys visible after generating

**Solutions**:
- Refresh the page
- Check browser console for errors (F12)
- Verify MongoDB connection
- Try generating again

### Edge Device Can't Connect
**Issue**: "Cannot connect to server"

**Solutions**:
- Check API_URL is correct
- Ensure server is running: `python app.py`
- Test with curl first
- Check firewall/network settings

---

## Next Steps

### 1. Production Deployment
- Update `API_URL` to your production domain
- Set strong `JWT_SECRET_KEY` in environment
- Enable HTTPS/SSL
- Deploy to cloud (AWS, GCP, Azure)

### 2. Integrate Real Detection
- Replace mock detection in `edge_device_client.py`
- Use YOLOv8 model
- Connect to camera (OpenCV, picamera)
- Add error handling and retry logic

### 3. Monitor & Scale
- Track API key usage
- Monitor server logs
- Set up alerts for downtime
- Scale MongoDB for production load

---

## Support & Documentation

- **Full Guide**: `LANDING_PAGE_GUIDE.md`
- **API Docs**: `UPDATERAW_API_EXPLAINED.md`
- **Raspberry Pi Setup**: `RASPBERRY_PI_AUTHENTICATION_GUIDE.md`
- **Architecture**: System design documentation

---

## Example Workflow

```
Organization Setup (One-time):
1. Visit landing page
2. Create account (30 seconds)
3. Login to dashboard
4. Generate API key (10 seconds)
5. Copy key

Edge Device Setup (Per device):
1. Install Python on Raspberry Pi
2. Copy edge_device_client.py
3. Edit: Paste API key
4. Run: python edge_device_client.py
5. Device starts sending data!

Monitoring (Ongoing):
1. Visit dashboard anytime
2. View parking statistics
3. Manage API keys
4. Monitor device activity
```

---

## Summary

✅ **Landing page** for professional first impression  
✅ **Self-service signup** - no manual account creation  
✅ **Dashboard** for credential management  
✅ **API keys** that never expire (until revoked)  
✅ **Copy-paste integration** for edge devices  
✅ **Multiple keys** for multiple devices  
✅ **Revoke/activate** keys on-demand  
✅ **Usage tracking** coming soon  
✅ **Backward compatible** with existing JWT system  

**You're all set! 🎉**

Start by visiting: `http://localhost:5001/`
