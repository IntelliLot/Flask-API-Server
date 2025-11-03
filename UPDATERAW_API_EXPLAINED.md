# 📸 UpdateRaw API - Complete Explanation

## Overview

The `updateRaw` API is one of two parking data ingestion endpoints in your system. It's designed for **server-side processing** where the edge device/client sends a **raw image + parking slot coordinates**, and the backend server performs the YOLO detection and occupancy calculation.

---

## 🔄 Two API Approaches

Your system supports two different data flow patterns:

### 1. **UpdateRaw API** (Server-Side Processing)
```
Client/React App → Sends RAW IMAGE → Server (YOLOv8) → MongoDB
```

### 2. **Update API** (Edge Processing)
```
Edge Device (YOLOv8) → Sends RESULTS → Server → MongoDB
```

---

## 📊 UpdateRaw API Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    CLIENT / REACT APP                            │
│                                                                  │
│  User uploads image                                              │
│  User defines parking slot coordinates                           │
│       │                                                           │
│       ▼                                                           │
│  Create FormData:                                                │
│    - image: parking_lot.jpg                                      │
│    - coordinates: [[x1,y1,x2,y2], ...]                          │
│    - camera_id: "camera_01"                                      │
│       │                                                           │
│       ▼                                                           │
│  POST /parking/updateRaw                                         │
│  Authorization: Bearer <JWT_TOKEN>                               │
└──────────────────────────────┬───────────────────────────────────┘
                               │
                               │ HTTP Request with Image
                               │
┌──────────────────────────────▼───────────────────────────────────┐
│                    BACKEND SERVER (Flask)                         │
│                                                                  │
│  1. Authenticate JWT Token                                       │
│       │                                                           │
│       ▼                                                           │
│  2. Extract user_id from token                                   │
│       │                                                           │
│       ▼                                                           │
│  3. Decode image (base64 or file upload)                         │
│       │                                                           │
│       ▼                                                           │
│  4. Initialize YOLOv8 Detection System                           │
│     ParkingDetectionSystem(parking_positions)                    │
│       │                                                           │
│       ▼                                                           │
│  5. Run YOLO Detection                                           │
│     - Detect all vehicles in image                               │
│     - Get bounding boxes and confidence scores                   │
│       │                                                           │
│       ▼                                                           │
│  6. Calculate Occupancy                                          │
│     - Check which parking slots contain vehicles                 │
│     - Mark slots as occupied/empty                               │
│       │                                                           │
│       ▼                                                           │
│  7. Generate Visualization                                       │
│     - Create SVG with color-coded slots                          │
│     - Generate slot details array                                │
│       │                                                           │
│       ▼                                                           │
│  8. Save to MongoDB                                              │
│     - Store all detection results                                │
│     - Store coordinates, statistics, SVG                         │
│       │                                                           │
│       ▼                                                           │
│  9. Return Response                                              │
│     {                                                            │
│       success: true,                                             │
│       document_id: "...",                                        │
│       total_slots: 50,                                           │
│       occupied_slots: 35,                                        │
│       svg_code: "<svg>...</svg>",                                │
│       slots_details: [...]                                       │
│     }                                                            │
└──────────────────────────────┬───────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                         MongoDB                                  │
│                                                                  │
│  parking_data collection:                                        │
│  {                                                               │
│    user_id: "...",                                               │
│    camera_id: "camera_01",                                       │
│    timestamp: "2025-10-16T...",                                  │
│    total_slots: 50,                                              │
│    occupied_slots: 35,                                           │
│    empty_slots: 15,                                              │
│    occupancy_rate: 70.0,                                         │
│    coordinates: [[x1,y1,x2,y2], ...],                           │
│    slots_details: [...],                                         │
│    processing_time_ms: 456.2                                     │
│  }                                                               │
└─────────────────────────────────────────────────────────────────┘
```

---

## 💻 UpdateRaw API Code Breakdown

### Endpoint Definition
```python
@parking_bp.route('/updateRaw', methods=['POST'])
@token_required  # ← JWT authentication required
def update_raw():
```

### Input Processing
```python
# Accepts TWO formats:
# 1. Multipart form-data (file upload)
if 'image' not in request.files:
    return jsonify({'error': 'Missing image file'}), 400

image_file = request.files['image']
image_bytes = image_file.read()
image = decode_image(image_bytes)

coordinates = json.loads(request.form.get('coordinates', '[]'))
camera_id = request.form.get('camera_id')

# 2. JSON with base64 image
data = request.get_json()
image = decode_image(data['image'])  # Decodes base64
coordinates = data.get('coordinates')
camera_id = data.get('camera_id')
```

### YOLO Detection
```python
# Initialize detection system with parking slot positions
parking_rectangles = [tuple(coord) for coord in coordinates]
system = ParkingDetectionSystem(parking_positions=parking_rectangles)

# Process frame - THIS IS WHERE YOLO RUNS
annotated_frame, statistics, processing_time = system.process_frame(image)

# Get detailed detection results
vehicle_detections = system.vehicle_detector.detect_vehicles(image)
occupancy = system.parking_manager.detect_occupancy(vehicle_detections)
```

### Result Generation
```python
# Generate visualization
slots_details = generate_slot_details(parking_rectangles, occupancy)
svg_code = generate_svg(
    parking_rectangles,
    occupancy,
    image_dims['width'],
    image_dims['height']
)
```

### Save to Database
```python
document_id = ParkingData.create_from_raw_processing(
    user_id=user_id,
    camera_id=camera_id,
    total_slots=statistics.get('total_slots', 0),
    total_cars_detected=len(vehicle_detections),
    occupied_slots=statistics.get('occupied_slots', 0),
    empty_slots=statistics.get('empty_slots', 0),
    occupancy_rate=statistics.get('occupancy_rate', 0.0),
    slots_details=slots_details,
    coordinates=coordinates,
    image_dimensions=image_dims,
    processing_time_ms=round(processing_time * 1000, 2)
)
```

---

## 📤 Request Format

### Option 1: Multipart Form-Data (File Upload)
```http
POST /parking/updateRaw HTTP/1.1
Host: localhost:5001
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary

------WebKitFormBoundary
Content-Disposition: form-data; name="image"; filename="parking.jpg"
Content-Type: image/jpeg

[binary image data]
------WebKitFormBoundary
Content-Disposition: form-data; name="coordinates"

[[100, 150, 200, 250], [220, 150, 320, 250], [340, 150, 440, 250]]
------WebKitFormBoundary
Content-Disposition: form-data; name="camera_id"

camera_entrance_01
------WebKitFormBoundary--
```

### Option 2: JSON with Base64 Image
```http
POST /parking/updateRaw HTTP/1.1
Host: localhost:5001
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "image": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD...",
  "coordinates": [
    [100, 150, 200, 250],
    [220, 150, 320, 250],
    [340, 150, 440, 250]
  ],
  "camera_id": "camera_entrance_01"
}
```

---

## 📥 Response Format

```json
{
  "success": true,
  "document_id": "507f1f77bcf86cd799439011",
  "total_slots": 50,
  "total_cars_detected": 35,
  "occupied_slots": 35,
  "empty_slots": 15,
  "occupancy_rate": 70.0,
  "svg_code": "<svg width='1920' height='1080'>...</svg>",
  "slots_details": [
    {
      "slot_id": 0,
      "coordinates": [100, 150, 200, 250],
      "is_occupied": true
    },
    {
      "slot_id": 1,
      "coordinates": [220, 150, 320, 250],
      "is_occupied": false
    }
  ],
  "timestamp": "2025-10-16T10:30:45.123Z",
  "processing_time_ms": 456.2
}
```

---

## 🎯 Use Cases for UpdateRaw

### ✅ When to Use UpdateRaw

1. **React Web Application**
   - User uploads parking lot image
   - User defines parking slot coordinates
   - Frontend sends image to backend for processing
   - Server has GPU for fast YOLO inference

2. **Mobile App with Camera**
   - App captures parking lot photo
   - Sends to server for processing
   - Gets back occupancy results and visualization

3. **Testing & Development**
   - Quick testing without edge device
   - Prototyping new parking lot layouts
   - Debugging detection accuracy

4. **Centralized ML Model**
   - One YOLOv8 model on server
   - Multiple clients can use it
   - Easy to update model without updating clients

5. **Low-Power Edge Devices**
   - Device only has camera (no GPU)
   - Can't run YOLO locally
   - Sends images to powerful server

### ❌ When NOT to Use UpdateRaw

1. **High-Frequency Real-Time Updates**
   - Sending full images every 5 seconds = bandwidth issue
   - Use `/parking/update` instead (edge processing)

2. **Bandwidth Limited Networks**
   - Uploading images constantly uses lots of data
   - Better to process on edge, send results only

3. **Offline Operation Required**
   - If network goes down, updateRaw fails
   - Edge processing can queue results locally

4. **Privacy Concerns**
   - Full images sent to server
   - Edge processing keeps images local

---

## 🔄 UpdateRaw vs Update API

| Feature | UpdateRaw | Update |
|---------|-----------|--------|
| **Input** | Raw image + coordinates | Pre-processed results |
| **Processing Location** | Server (backend) | Edge device |
| **Payload Size** | Large (image ~100KB-2MB) | Small (JSON ~1-5KB) |
| **Server Load** | High (YOLO inference) | Low (just storage) |
| **Bandwidth** | High | Low |
| **Client Requirements** | Just camera | Camera + GPU + YOLO |
| **Latency** | Higher (upload + process) | Lower (just upload) |
| **Use Case** | Web app, mobile app | Edge devices, IoT cameras |
| **Update Frequency** | Low (30-60s) | High (5-10s) |

---

## 🌐 Real-World Example: React Web App

### Frontend Code (React)
```javascript
const uploadParkingImage = async (imageFile, coordinates) => {
  const token = localStorage.getItem('access_token');
  
  // Create form data
  const formData = new FormData();
  formData.append('image', imageFile);
  formData.append('coordinates', JSON.stringify(coordinates));
  formData.append('camera_id', 'web_upload_01');
  
  // Send to updateRaw endpoint
  const response = await fetch('http://localhost:5001/parking/updateRaw', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
    },
    body: formData
  });
  
  const result = await response.json();
  
  // Display results
  if (result.success) {
    console.log(`Occupancy: ${result.occupancy_rate}%`);
    console.log(`Occupied: ${result.occupied_slots}/${result.total_slots}`);
    
    // Show SVG visualization
    document.getElementById('svg-result').innerHTML = result.svg_code;
  }
};

// Usage
const handleImageUpload = (event) => {
  const file = event.target.files[0];
  const coordinates = [
    [100, 150, 200, 250],
    [220, 150, 320, 250],
    // ... more slots
  ];
  
  uploadParkingImage(file, coordinates);
};
```

---

## 🔍 What Happens Behind the Scenes

### Step-by-Step Processing

1. **Authentication** (0.1ms)
   ```python
   @token_required  # Verifies JWT token
   user_id = jwt_handler.get_current_user_id()
   ```

2. **Image Decoding** (10-50ms)
   ```python
   # Converts base64 or file upload to OpenCV image
   image = decode_image(image_bytes)
   # Result: numpy array (height, width, 3) - RGB image
   ```

3. **Validation** (1ms)
   ```python
   validate_coordinates(coordinates)
   # Ensures: x2 > x1, y2 > y1, within image bounds
   ```

4. **YOLO Inference** (200-500ms) ← MAIN COMPUTATION
   ```python
   system = ParkingDetectionSystem(parking_positions)
   vehicle_detections = system.vehicle_detector.detect_vehicles(image)
   
   # Returns list of detected vehicles:
   # [
   #   {'bbox': [x1, y1, x2, y2], 'confidence': 0.92, 'class': 'car'},
   #   {'bbox': [x1, y1, x2, y2], 'confidence': 0.87, 'class': 'truck'},
   #   ...
   # ]
   ```

5. **Occupancy Calculation** (5-20ms)
   ```python
   occupancy = system.parking_manager.detect_occupancy(vehicle_detections)
   
   # Checks if any vehicle overlaps with each parking slot
   # Returns: [True, False, True, True, False, ...]
   # True = occupied, False = empty
   ```

6. **Visualization Generation** (10-30ms)
   ```python
   svg_code = generate_svg(rectangles, occupancy, width, height)
   
   # Creates SVG with:
   # - Green rectangles for empty slots
   # - Red rectangles for occupied slots
   # - Labels with slot numbers
   ```

7. **Database Storage** (10-50ms)
   ```python
   document_id = ParkingData.create_from_raw_processing(...)
   
   # Inserts document into MongoDB:
   # parking_data.insert_one({
   #   user_id, camera_id, timestamp,
   #   occupancy data, coordinates, svg, etc.
   # })
   ```

8. **Response Generation** (1ms)
   ```python
   return jsonify(response), 201
   ```

**Total Time: ~250-700ms** (varies based on image size, server hardware)

---

## 💾 Data Stored in MongoDB

```javascript
{
  "_id": ObjectId("507f1f77bcf86cd799439011"),
  "user_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "camera_id": "camera_entrance_01",
  "timestamp": ISODate("2025-10-16T10:30:45.123Z"),
  
  // Occupancy Statistics
  "total_slots": 50,
  "total_cars_detected": 35,
  "occupied_slots": 35,
  "empty_slots": 15,
  "occupancy_rate": 70.0,
  
  // Detection Details
  "coordinates": [
    [100, 150, 200, 250],
    [220, 150, 320, 250],
    // ... all slot coordinates
  ],
  "slots_details": [
    {"slot_id": 0, "coordinates": [100, 150, 200, 250], "is_occupied": true},
    {"slot_id": 1, "coordinates": [220, 150, 320, 250], "is_occupied": false},
    // ... all slots
  ],
  
  // Metadata
  "image_dimensions": {"width": 1920, "height": 1080},
  "processing_time_ms": 456.2,
  "source": "raw_processing",  // Indicates updateRaw was used
  
  // For analytics/display
  "svg_code": "<svg>...</svg>"  // Optional: can be regenerated
}
```

---

## 🎨 SVG Visualization Example

The `svg_code` returned looks like:

```html
<svg width="1920" height="1080" xmlns="http://www.w3.org/2000/svg">
  <!-- Empty Slot (Green) -->
  <rect x="100" y="150" width="100" height="100" 
        fill="rgba(0, 255, 0, 0.3)" 
        stroke="#00FF00" stroke-width="3"/>
  <text x="150" y="200" fill="white" font-size="20">1</text>
  
  <!-- Occupied Slot (Red) -->
  <rect x="220" y="150" width="100" height="100" 
        fill="rgba(255, 0, 0, 0.3)" 
        stroke="#FF0000" stroke-width="3"/>
  <text x="270" y="200" fill="white" font-size="20">2</text>
  
  <!-- More slots... -->
</svg>
```

This SVG can be:
- Displayed directly in web browsers
- Downloaded as a file
- Embedded in reports
- Used for visualization dashboards

---

## 🔒 Security & Authentication

```python
@token_required  # This decorator does:
def update_raw():
    # 1. Checks Authorization header
    # 2. Validates JWT token
    # 3. Extracts user_id from token
    # 4. Attaches to request context
    
    user_id = jwt_handler.get_current_user_id()
    # Now we know WHO is making the request
    # Data is saved with this user_id
```

**Why this matters:**
- Multi-tenant system: Each user sees only their data
- Access control: Can't access other users' parking data
- Audit trail: Know who processed what and when

### 🍓 Authentication from Raspberry Pi or IoT Device

To upload images from a Raspberry Pi or other IoT device:

**Step 1: Register (one-time)**
```bash
curl -X POST http://your-server:5001/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "raspi_parkinglot_01",
    "password": "SecurePassword123!",
    "organization_name": "My Parking Lot",
    "location": "123 Main St",
    "size": 50
  }'
```

**Step 2: Login to get JWT token**
```bash
curl -X POST http://your-server:5001/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "raspi_parkinglot_01",
    "password": "SecurePassword123!"
  }'
```

Response:
```json
{
  "success": true,
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "expires_in": 3600
}
```

**Step 3: Use token in updateRaw request**
```bash
TOKEN="eyJhbGciOiJIUzI1NiIs..."

curl -X POST http://your-server:5001/parking/updateRaw \
  -H "Authorization: Bearer $TOKEN" \
  -F "image=@parking.jpg" \
  -F 'coordinates=[[100,150,200,250]]' \
  -F "camera_id=raspi_01"
```

📖 **See [RASPBERRY_PI_AUTHENTICATION_GUIDE.md](RASPBERRY_PI_AUTHENTICATION_GUIDE.md) for complete Python code examples and automatic token refresh handling!**

---

## 📊 Performance Considerations

### Factors Affecting Speed

| Factor | Impact | Optimization |
|--------|--------|--------------|
| Image size | High | Resize before upload (max 1920x1080) |
| Number of slots | Medium | Limit to reasonable number (<200) |
| YOLO model | High | Use GPU, smaller model variant |
| Network latency | Medium | Deploy server close to users |
| MongoDB writes | Low | Already optimized with indexes |

### Recommended Limits
- **Max image size:** 5 MB
- **Max parking slots:** 200 per image
- **Update frequency:** Max 1 request per 30 seconds per user
- **Concurrent users:** Depends on server specs

---

## 🛠️ Testing UpdateRaw API

### Using cURL
```bash
TOKEN="your_jwt_token_here"

curl -X POST http://localhost:5001/parking/updateRaw \
  -H "Authorization: Bearer $TOKEN" \
  -F "image=@parking_lot.jpg" \
  -F 'coordinates=[[100,150,200,250],[220,150,320,250]]' \
  -F "camera_id=test_camera_01"
```

### Using Python
```python
import requests

token = "your_jwt_token_here"

with open('parking_lot.jpg', 'rb') as f:
    files = {'image': f}
    data = {
        'coordinates': '[[100,150,200,250],[220,150,320,250]]',
        'camera_id': 'test_camera_01'
    }
    headers = {'Authorization': f'Bearer {token}'}
    
    response = requests.post(
        'http://localhost:5001/parking/updateRaw',
        files=files,
        data=data,
        headers=headers
    )
    
    print(response.json())
```

### Using Web Interface
1. Open `http://localhost:5001/` (main UI)
2. Upload image
3. Enter coordinates
4. Click "Detect Parking"
5. View results with SVG visualization

---

## 🎯 Summary

**UpdateRaw API is for:**
- Web applications where users upload images
- Centralized processing with powerful server
- When you want server to run YOLO detection
- Testing and prototyping

**Key Benefits:**
- ✅ Simple client (just send image)
- ✅ Centralized ML model management
- ✅ Complete detection results stored
- ✅ SVG visualization included

**Trade-offs:**
- ⚠️ Higher bandwidth usage (full images)
- ⚠️ Higher server load (YOLO inference)
- ⚠️ Lower update frequency possible
- ⚠️ Images sent to server (privacy consideration)

For high-frequency real-time monitoring from edge devices with local processing capability, use `/parking/update` instead!

---

**Related Documentation:**
- [RASPBERRY_PI_AUTHENTICATION_GUIDE.md](RASPBERRY_PI_AUTHENTICATION_GUIDE.md) - **🍓 Raspberry Pi authentication & upload guide**
- [EDGE_APP_API_DOCUMENTATION.md](EDGE_APP_API_DOCUMENTATION.md) - Full API reference
- [EDGE_APP_ARCHITECTURE.md](EDGE_APP_ARCHITECTURE.md) - System architecture
- [API_DOCUMENTATION.md](API_DOCUMENTATION.md) - Complete backend API docs
