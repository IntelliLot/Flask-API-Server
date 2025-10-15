# 🚀 Quick Start Guide - Parking Detection API

## 30-Second Setup

```bash
# 1. Install dependencies
pip install Flask flask-cors Flask-JWT-Extended pymongo bcrypt python-dotenv opencv-python ultralytics numpy

# 2. Start MongoDB (choose one):
docker run -d -p 27017:27017 mongo:latest           # Docker
# OR
sudo systemctl start mongodb                         # Linux service

# 3. Configure environment
cp .env.example .env
# Edit .env: Change JWT_SECRET_KEY!

# 4. Run server
python app.py

# 5. Open browser
# http://localhost:5001/
```

---

## 📝 Complete Workflow Example

### Step 1: Register Your Parking Business

```bash
curl -X POST http://localhost:5001/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "downtown_parking",
    "password": "SecurePass123!",
    "organization_name": "Downtown Parking LLC",
    "location": "123 Main Street, City, State 12345",
    "size": 150,
    "verification": "business_license_verified",
    "details": {
      "email": "admin@downtown-parking.com",
      "phone": "+1-555-0199"
    }
  }'
```

**Response:**
```json
{
  "success": true,
  "user_id": "a7b3c4d5-e6f7-8901-2345-6789abcdef01",
  "username": "downtown_parking",
  "organization_name": "Downtown Parking LLC"
}
```

✅ **Save your `user_id` - you'll need it!**

---

### Step 2: Login and Get Token

```bash
curl -X POST http://localhost:5001/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "downtown_parking",
    "password": "SecurePass123!"
  }'
```

**Response:**
```json
{
  "success": true,
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI...",
  "user_id": "a7b3c4d5-e6f7-8901-2345-6789abcdef01",
  "username": "downtown_parking",
  "expires_in": 3600
}
```

✅ **Save your `access_token` - use it in all requests!**

---

### Step 3: Send Frames from React App

**JavaScript Example:**

```javascript
// Login once, save token
async function login() {
  const response = await fetch('http://localhost:5001/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      username: 'downtown_parking',
      password: 'SecurePass123!'
    })
  });
  const data = await response.json();
  localStorage.setItem('token', data.access_token);
  localStorage.setItem('userId', data.user_id);
}

// Send frames from camera
async function sendParkingFrame(imageBlob) {
  const token = localStorage.getItem('token');
  
  // Define your parking slots (get these from your lot layout)
  const parkingSlots = [
    [100, 200, 200, 280],  // Slot 1: [x1, y1, x2, y2]
    [210, 200, 310, 280],  // Slot 2
    [320, 200, 420, 280],  // Slot 3
    // ... more slots
  ];
  
  const formData = new FormData();
  formData.append('image', imageBlob);
  formData.append('coordinates', JSON.stringify(parkingSlots));
  formData.append('camera_id', 'entrance_camera_1');
  
  const response = await fetch('http://localhost:5001/updateRaw', {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` },
    body: formData
  });
  
  const result = await response.json();
  console.log(`Occupancy: ${result.occupancy_rate}%`);
  console.log(`Occupied: ${result.occupied_slots}/${result.total_slots}`);
  
  return result;
}

// React Component Example
function ParkingMonitor() {
  const [occupancy, setOccupancy] = useState(null);
  
  const captureAndSend = async () => {
    // Get image from video stream
    const canvas = document.createElement('canvas');
    const video = document.querySelector('video');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext('2d').drawImage(video, 0, 0);
    
    // Convert to blob
    canvas.toBlob(async (blob) => {
      const result = await sendParkingFrame(blob);
      setOccupancy(result);
    }, 'image/jpeg', 0.8);
  };
  
  return (
    <div>
      <video autoPlay />
      <button onClick={captureAndSend}>Check Parking</button>
      {occupancy && (
        <div>
          <h3>Occupancy: {occupancy.occupancy_rate}%</h3>
          <p>{occupancy.empty_slots} slots available</p>
        </div>
      )}
    </div>
  );
}
```

---

### Step 4: Or Send Pre-Processed Data (Edge Device)

If your edge device already processes the image:

```javascript
async function sendProcessedData(cameraId, occupancyData) {
  const token = localStorage.getItem('token');
  
  const response = await fetch('http://localhost:5001/update', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      camera_id: cameraId,
      total_slots: 50,
      occupied_slots: 35,
      empty_slots: 15,
      occupancy_rate: 70.0,
      total_cars_detected: 42,
      slots_details: [
        { slot_number: 1, occupied: true, status: 'OCCUPIED' },
        { slot_number: 2, occupied: false, status: 'EMPTY' }
        // ... more slots
      ]
    })
  });
  
  return response.json();
}
```

---

### Step 5: Get Your Parking Data

```javascript
async function getParkingHistory() {
  const token = localStorage.getItem('token');
  const userId = localStorage.getItem('userId');
  
  const response = await fetch(
    `http://localhost:5001/parking-data/${userId}?camera_id=entrance_camera_1&limit=100`,
    { headers: { 'Authorization': `Bearer ${token}` } }
  );
  
  const data = await response.json();
  
  console.log(`Total records: ${data.total_count}`);
  console.log(`Latest occupancy: ${data.latest.occupancy_rate}%`);
  
  return data.data; // Array of all records
}
```

---

## 🎯 Common Use Cases

### Use Case 1: Real-Time Web Dashboard

```javascript
// Update every 10 seconds
setInterval(async () => {
  const result = await sendParkingFrame(getCameraFrame());
  updateDashboard(result);
}, 10000);
```

### Use Case 2: Mobile App Integration

```javascript
// Capture from phone camera
const capturePhoto = async () => {
  const photo = await Camera.getPhoto({
    quality: 90,
    resultType: CameraResultType.Blob
  });
  return await sendParkingFrame(photo.blob);
};
```

### Use Case 3: Raspberry Pi Edge Device

```python
import requests
import cv2
import time

TOKEN = "your_jwt_token"
CAMERA_ID = "pi_camera_1"
API_URL = "http://your-server.com:5001/updateRaw"

coordinates = [[100,200,200,280], [210,200,310,280]]  # Your slots

cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        continue
    
    # Encode image
    _, buffer = cv2.imencode('.jpg', frame)
    
    # Send to server
    files = {'image': ('frame.jpg', buffer.tobytes(), 'image/jpeg')}
    data = {
        'coordinates': str(coordinates),
        'camera_id': CAMERA_ID
    }
    headers = {'Authorization': f'Bearer {TOKEN}'}
    
    response = requests.post(API_URL, files=files, data=data, headers=headers)
    result = response.json()
    
    print(f"Occupancy: {result['occupancy_rate']}%")
    
    time.sleep(30)  # Check every 30 seconds
```

---

## 🔍 Query Examples

### Get Latest Data

```bash
TOKEN="your_token_here"
USER_ID="your_user_id"

curl -X GET "http://localhost:5001/parking-data/$USER_ID?limit=1" \
  -H "Authorization: Bearer $TOKEN"
```

### Get Data for Specific Camera

```bash
curl -X GET "http://localhost:5001/parking-data/$USER_ID?camera_id=entrance_camera_1&limit=50" \
  -H "Authorization: Bearer $TOKEN"
```

### Get Date Range

```bash
curl -X GET "http://localhost:5001/parking-data/$USER_ID?start_date=2025-10-01T00:00:00Z&end_date=2025-10-15T23:59:59Z" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 📊 Response Examples

### /updateRaw Response

```json
{
  "success": true,
  "document_id": "671234567890abcdef123456",
  "total_slots": 50,
  "total_cars_detected": 42,
  "occupied_slots": 35,
  "empty_slots": 15,
  "occupancy_rate": 70.0,
  "svg_code": "<svg width=\"1920\" height=\"1080\">...</svg>",
  "slots_details": [
    {
      "slot_number": 1,
      "rectangle": {"x1": 100, "y1": 200, "x2": 200, "y2": 280},
      "dimensions": {"width": 100, "height": 80},
      "occupied": true,
      "status": "OCCUPIED"
    }
  ],
  "timestamp": "2025-10-15T22:30:00.000Z",
  "processing_time_ms": 145.23
}
```

### /parking-data Response

```json
{
  "success": true,
  "user_id": "a7b3c4d5-e6f7-8901-2345-6789abcdef01",
  "total_count": 2450,
  "returned_count": 50,
  "latest": {
    "timestamp": "2025-10-15T22:45:00.000Z",
    "camera_id": "entrance_camera_1",
    "total_slots": 50,
    "occupied_slots": 38,
    "occupancy_rate": 76.0
  },
  "data": [...]
}
```

---

## ⚠️ Important Notes

### Security
- **ALWAYS change `JWT_SECRET_KEY` in production!**
- Use HTTPS in production
- Never commit `.env` file to git

### Token Management
- Tokens expire after 1 hour (default)
- Store token securely in your app
- Re-login when token expires

### Coordinates Format
```javascript
// Each slot: [x1, y1, x2, y2]
// Where (x1,y1) = top-left, (x2,y2) = bottom-right
const coordinates = [
  [100, 200, 200, 280],  // ✅ Correct
  [100, 200, 100, 80]    // ❌ Wrong (x2 < x1, y2 < y1)
];
```

---

## 🆘 Troubleshooting

### "Authentication service not available"
```bash
pip install Flask-JWT-Extended pymongo bcrypt python-dotenv flask-cors
```

### "MongoDB connection failed"
```bash
# Check MongoDB is running
sudo systemctl status mongodb
# OR
docker ps | grep mongo
```

### "Token has expired"
```javascript
// Login again to get new token
await login();
```

---

## 📚 Full Documentation

- **Complete API Docs**: [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
- **System README**: [README.md](README.md)

---

**Need help? Check the logs - the server provides detailed logging for debugging!**
