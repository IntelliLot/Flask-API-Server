# 📦 Google Cloud Storage Integration Guide

## Overview

This guide explains how to set up and use Google Cloud Storage (GCS) for storing parking lot images. Images are automatically organized in a hierarchical structure:

```
bucket_name/
├── user_id_1/
│   ├── node_id_1/
│   │   ├── 2025/
│   │   │   ├── 11/
│   │   │   │   ├── 02/
│   │   │   │   │   ├── 14/
│   │   │   │   │   │   ├── raw_20251102_143052_123456.jpg
│   │   │   │   │   │   ├── annotated_20251102_143052_123456.jpg
│   ├── node_id_2/
│   │   ├── 2025/...
├── user_id_2/
│   ├── node_id_1/...
```

**Structure:** `user_id/node_id/YYYY/MM/DD/HH/image_type_timestamp.jpg`

---

## 🔧 Setup Guide

### Step 1: Create Google Cloud Storage Bucket

1. **Go to Google Cloud Console**
   - Visit: https://console.cloud.google.com/storage

2. **Create a new bucket**
   ```
   Bucket name: your-parking-images-bucket
   Location: Choose closest to your server (e.g., us-central1)
   Storage class: Standard
   Access control: Fine-grained (recommended)
   ```

3. **Configure bucket permissions (optional)**
   - For public access to images, make bucket public
   - For private access, use signed URLs (recommended)

### Step 2: Create Service Account

1. **Go to IAM & Service Accounts**
   - Visit: https://console.cloud.google.com/iam-admin/serviceaccounts

2. **Create Service Account**
   ```
   Name: parking-storage-service
   Description: Service account for parking image storage
   Role: Storage Object Admin
   ```

3. **Create and Download JSON Key**
   - Click on the service account
   - Go to "Keys" tab
   - Click "Add Key" → "Create new key" → "JSON"
   - Download the JSON file
   - Save it as `gcs-credentials.json` in your project root

### Step 3: Configure Application

1. **Update `.env` file**
   ```bash
   # Google Cloud Storage Configuration
   GCS_BUCKET_NAME=your-parking-images-bucket
   GCS_CREDENTIALS_PATH=./gcs-credentials.json
   GCS_ENABLE=true
   ```

2. **Install dependencies**
   ```bash
   pip install google-cloud-storage
   ```

3. **Secure the credentials file**
   ```bash
   chmod 600 gcs-credentials.json
   
   # Add to .gitignore
   echo "gcs-credentials.json" >> .gitignore
   ```

### Step 4: Test Connection

Run this test script:

```python
from utils.gcs_storage import gcs_storage

# Check if GCS is enabled
if gcs_storage.enabled:
    print("✅ GCS is enabled")
    print(f"   Bucket: {gcs_storage.bucket_name}")
    
    # List existing images for a user
    images = gcs_storage.list_user_images('test_user', limit=5)
    print(f"   Found {len(images)} images")
else:
    print("❌ GCS is disabled")
```

---

## 🚀 Usage

### Automatic Upload (via updateRaw API)

Images are automatically uploaded when using the `/parking/updateRaw` endpoint:

```python
import requests

response = requests.post(
    'http://your-server:5001/parking/updateRaw',
    headers={'Authorization': f'Bearer {token}'},
    files={'image': open('parking.jpg', 'rb')},
    data={
        'coordinates': '[[100,150,200,250]]',
        'camera_id': 'camera_01',
        'node_id': 'raspberry_pi_01'  # Important: Include node_id
    }
)

result = response.json()
print(result['gcs_storage'])
# Output:
# {
#   'enabled': True,
#   'raw_image': {
#     'path': 'user123/node_01/2025/11/02/14/raw_20251102_143052_123456.jpg',
#     'url': 'https://storage.googleapis.com/bucket/user123/...'
#   },
#   'annotated_image': {
#     'path': 'user123/node_01/2025/11/02/14/annotated_20251102_143052_123456.jpg',
#     'url': 'https://storage.googleapis.com/bucket/user123/...'
#   }
# }
```

### Manual Upload

```python
from utils.gcs_storage import gcs_storage
import cv2
from datetime import datetime

# Load image
image = cv2.imread('parking_lot.jpg')

# Upload to GCS
result = gcs_storage.upload_image(
    image=image,
    user_id='user_abc123',
    node_id='raspberry_pi_01',
    timestamp=datetime.utcnow(),
    image_type='raw'
)

if result:
    blob_path, public_url = result
    print(f"✅ Uploaded: {blob_path}")
    print(f"   URL: {public_url}")
```

### Generate Signed URL (Private Access)

```python
from utils.gcs_storage import gcs_storage

# Get signed URL that expires in 1 hour
blob_path = 'user123/node_01/2025/11/02/14/raw_20251102_143052_123456.jpg'
signed_url = gcs_storage.get_signed_url(blob_path, expiration_minutes=60)

print(f"Signed URL: {signed_url}")
# This URL can be shared and will be valid for 1 hour
```

### List User Images

```python
from utils.gcs_storage import gcs_storage

# List all images for a user
all_images = gcs_storage.list_user_images('user_abc123', limit=100)

# List images for specific node
node_images = gcs_storage.list_user_images('user_abc123', node_id='raspberry_pi_01', limit=50)

print(f"Found {len(node_images)} images")
for img_path in node_images:
    print(f"  - {img_path}")
```

### Delete Image

```python
from utils.gcs_storage import gcs_storage

blob_path = 'user123/node_01/2025/11/02/14/raw_20251102_143052_123456.jpg'
success = gcs_storage.delete_image(blob_path)

if success:
    print("✅ Image deleted")
```

---

## 📊 MongoDB Integration

Images paths and URLs are automatically stored in MongoDB:

```javascript
{
  "_id": ObjectId("..."),
  "user_id": "user_abc123",
  "camera_id": "camera_01",
  "node_id": "raspberry_pi_01",
  "timestamp": ISODate("2025-11-02T14:30:52.123Z"),
  
  // ... other parking data ...
  
  "gcs_storage": {
    "raw_image": {
      "path": "user_abc123/raspberry_pi_01/2025/11/02/14/raw_20251102_143052_123456.jpg",
      "url": "https://storage.googleapis.com/your-bucket/..."
    },
    "annotated_image": {
      "path": "user_abc123/raspberry_pi_01/2025/11/02/14/annotated_20251102_143052_123456.jpg",
      "url": "https://storage.googleapis.com/your-bucket/..."
    }
  }
}
```

---

## 🔒 Security Best Practices

### 1. Use Private Buckets
```bash
# Make bucket private
gsutil iam ch -d allUsers:objectViewer gs://your-bucket-name
```

### 2. Use Signed URLs
```python
# Generate temporary access URLs
signed_url = gcs_storage.get_signed_url(blob_path, expiration_minutes=15)
```

### 3. Rotate Service Account Keys
- Rotate keys every 90 days
- Use Google Cloud Key Management Service (KMS) for production

### 4. Set Lifecycle Rules
Delete old images automatically:

```json
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "Delete"},
        "condition": {
          "age": 90,
          "matchesPrefix": [""]
        }
      }
    ]
  }
}
```

Apply with:
```bash
gsutil lifecycle set lifecycle.json gs://your-bucket-name
```

### 5. Enable Versioning (Optional)
```bash
gsutil versioning set on gs://your-bucket-name
```

---

## 📈 Cost Optimization

### Storage Costs (US Multi-Region)
- Standard: $0.020 per GB/month
- Nearline: $0.010 per GB/month (30-day min)
- Coldline: $0.004 per GB/month (90-day min)

### Estimate Monthly Costs

**Example Setup:**
- 10 parking lots (nodes)
- 1 image every 60 seconds
- Image size: 200 KB (raw) + 250 KB (annotated) = 450 KB
- Storage: 30 days

**Calculation:**
```
Images per month = 10 nodes × 1440 images/day × 30 days = 432,000 images
Storage = 432,000 × 0.45 MB = 194.4 GB
Cost = 194.4 GB × $0.020 = $3.89/month
```

### Optimization Tips

1. **Reduce image frequency**
   - Upload every 2-5 minutes instead of every 60s
   - Saves: ~80% storage costs

2. **Use compression**
   - JPEG quality 85 instead of 90
   - Saves: ~20-30% file size

3. **Store only annotated images**
   - Skip raw image upload
   - Saves: ~44% storage

4. **Use Nearline storage for old images**
   - Move images older than 7 days to Nearline
   - Saves: ~50% on old data

5. **Delete old images**
   - Delete images older than 30 days
   - Saves: based on retention needs

---

## 🐛 Troubleshooting

### Problem: "GCS client initialization failed"

**Solution:**
```bash
# Check credentials file exists
ls -la gcs-credentials.json

# Verify JSON is valid
python3 -c "import json; json.load(open('gcs-credentials.json'))"

# Check environment variables
echo $GCS_BUCKET_NAME
echo $GCS_CREDENTIALS_PATH
```

### Problem: "Bucket not found"

**Solution:**
```bash
# List buckets
gsutil ls

# Create bucket if needed
gsutil mb -l us-central1 gs://your-bucket-name
```

### Problem: "Permission denied"

**Solution:**
```bash
# Check service account permissions
gcloud projects get-iam-policy YOUR_PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:YOUR_SERVICE_ACCOUNT"

# Add Storage Object Admin role
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:YOUR_SERVICE_ACCOUNT" \
  --role="roles/storage.objectAdmin"
```

### Problem: "Images uploading slowly"

**Solution:**
- Use closest region to your server
- Compress images before upload
- Upload in background/async (future enhancement)

---

## 🎯 Image Organization Benefits

### By User ID
- ✅ Multi-tenant isolation
- ✅ Easy user data export/deletion (GDPR)
- ✅ Per-user storage quota management

### By Node ID
- ✅ Track multiple cameras/devices per user
- ✅ Easy per-device debugging
- ✅ Device-specific analytics

### By Date/Time Hierarchy
- ✅ Efficient date range queries
- ✅ Easy archival/deletion of old data
- ✅ Faster file listing operations
- ✅ Clear visual organization

---

## 📖 API Response Example

When you upload via `/parking/updateRaw`, the response includes GCS information:

```json
{
  "success": true,
  "document_id": "673f45a2b1c9d4e5f6g7h8i9",
  "total_slots": 50,
  "occupied_slots": 35,
  "empty_slots": 15,
  "occupancy_rate": 70.0,
  "timestamp": "2025-11-02T14:30:52.123Z",
  "processing_time_ms": 456.2,
  
  "gcs_storage": {
    "enabled": true,
    "raw_image": {
      "path": "user_abc123/raspberry_pi_01/2025/11/02/14/raw_20251102_143052_123456.jpg",
      "url": "https://storage.googleapis.com/your-bucket/user_abc123/raspberry_pi_01/2025/11/02/14/raw_20251102_143052_123456.jpg"
    },
    "annotated_image": {
      "path": "user_abc123/raspberry_pi_01/2025/11/02/14/annotated_20251102_143052_123456.jpg",
      "url": "https://storage.googleapis.com/your-bucket/user_abc123/raspberry_pi_01/2025/11/02/14/annotated_20251102_143052_123456.jpg"
    }
  },
  
  "svg_code": "<svg>...</svg>",
  "slots_details": [...]
}
```

---

## 🚀 Quick Start Checklist

- [ ] Create GCS bucket
- [ ] Create service account with Storage Object Admin role
- [ ] Download JSON credentials
- [ ] Update `.env` with bucket name and credentials path
- [ ] Install `google-cloud-storage` package
- [ ] Test with `raspi_client_example.py`
- [ ] Include `node_id` in all upload requests
- [ ] Check MongoDB for GCS paths after upload
- [ ] Set up lifecycle rules for automatic cleanup
- [ ] Monitor storage costs in GCP Console

---

## 📚 Related Documentation

- [UPDATERAW_API_EXPLAINED.md](UPDATERAW_API_EXPLAINED.md) - Complete updateRaw API docs
- [RASPBERRY_PI_AUTHENTICATION_GUIDE.md](RASPBERRY_PI_AUTHENTICATION_GUIDE.md) - Raspberry Pi setup
- [Google Cloud Storage Docs](https://cloud.google.com/storage/docs) - Official GCS documentation

---

## 🎉 Benefits Summary

✅ **Scalable:** Handle millions of images  
✅ **Organized:** Hierarchical structure by user/node/date  
✅ **Searchable:** Easy to find images by date range  
✅ **Cost-effective:** Pay only for what you use  
✅ **Reliable:** 99.95% SLA, auto-replicated  
✅ **Accessible:** Public URLs or signed URLs  
✅ **Integrated:** Automatically stored in MongoDB  
✅ **Secure:** IAM-based access control  

Your parking images are now professionally managed in the cloud! 🎊
