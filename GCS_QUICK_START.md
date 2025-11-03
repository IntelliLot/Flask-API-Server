# 🚀 Quick Start: Google Cloud Storage Integration

## What's New?

Your parking detection system now **automatically uploads images to Google Cloud Storage** with smart organization:

```
your-bucket/
├── user_abc123/              ← Each user gets their own folder
│   ├── raspberry_pi_01/      ← Each node/device has its folder
│   │   ├── 2025/11/02/14/    ← Organized by date and hour
│   │   │   ├── raw_20251102_143052_123456.jpg
│   │   │   ├── annotated_20251102_143052_123456.jpg
```

---

## ⚡ Quick Setup (5 minutes)

### 1. Create GCS Bucket
```bash
# Via gcloud CLI
gcloud storage buckets create gs://your-parking-images-bucket --location=us-central1

# Or use Google Cloud Console: https://console.cloud.google.com/storage
```

### 2. Create Service Account & Download Key
```bash
# Create service account
gcloud iam service-accounts create parking-storage \
    --display-name="Parking Storage Service"

# Grant permissions
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:parking-storage@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/storage.objectAdmin"

# Create and download key
gcloud iam service-accounts keys create gcs-credentials.json \
    --iam-account=parking-storage@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

### 3. Configure Application
```bash
# Add to .env file
cat >> .env << EOF
GCS_BUCKET_NAME=your-parking-images-bucket
GCS_CREDENTIALS_PATH=./gcs-credentials.json
GCS_ENABLE=true
EOF
```

### 4. Install Dependencies
```bash
pip install google-cloud-storage
```

### 5. Test It!
```bash
python3 raspi_client_example.py
```

---

## 📤 Usage from Raspberry Pi

### Updated Configuration
```python
# raspi_client_example.py
SERVER_URL = "http://192.168.1.100:5001"
USERNAME = "raspi_parkinglot_01"
PASSWORD = "SecurePassword123!"
CAMERA_ID = "raspi_camera_01"
NODE_ID = "raspberry_pi_01"  # ← NEW: Unique node identifier
```

### What Happens Now?

When you call `/parking/updateRaw`:

1. **Image uploaded** → Server processes with YOLO
2. **Raw image saved** → `user_id/node_id/2025/11/02/14/raw_*.jpg`
3. **Annotated image saved** → `user_id/node_id/2025/11/02/14/annotated_*.jpg`
4. **Paths stored in MongoDB** → Easy retrieval later

### Response Includes GCS Info
```json
{
  "success": true,
  "document_id": "...",
  "occupied_slots": 35,
  "gcs_storage": {
    "enabled": true,
    "raw_image": {
      "path": "user123/node_01/2025/11/02/14/raw_20251102_143052_123456.jpg",
      "url": "https://storage.googleapis.com/bucket/..."
    },
    "annotated_image": {
      "path": "user123/node_01/2025/11/02/14/annotated_20251102_143052_123456.jpg",
      "url": "https://storage.googleapis.com/bucket/..."
    }
  }
}
```

---

## 🎯 Key Changes

### API Changes
- **New parameter:** `node_id` (optional, defaults to `camera_id`)
- **New response fields:** `gcs_storage` with paths and URLs
- **Backward compatible:** Works without GCS if disabled

### MongoDB Schema
```javascript
{
  // ... existing fields ...
  "node_id": "raspberry_pi_01",  // NEW
  "gcs_storage": {               // NEW
    "raw_image": {
      "path": "...",
      "url": "..."
    },
    "annotated_image": {
      "path": "...",
      "url": "..."
    }
  }
}
```

---

## 💰 Estimated Costs

### Small Setup (1 Camera)
- Images: ~2,160/month (1 every 20 min)
- Storage: ~1 GB/month
- **Cost: ~$0.02/month** 💵

### Medium Setup (10 Cameras)
- Images: ~21,600/month
- Storage: ~10 GB/month
- **Cost: ~$0.20/month** 💵

### Large Setup (100 Cameras)
- Images: ~216,000/month
- Storage: ~100 GB/month
- **Cost: ~$2.00/month** 💵

*Based on Standard storage at $0.020/GB/month*

---

## 🔄 Disable GCS (Optional)

To run without cloud storage:

```bash
# In .env
GCS_ENABLE=false
```

Application works normally, just skips cloud upload.

---

## 📚 Full Documentation

- **[GCS_SETUP_GUIDE.md](GCS_SETUP_GUIDE.md)** - Complete setup guide with troubleshooting
- **[UPDATERAW_API_EXPLAINED.md](UPDATERAW_API_EXPLAINED.md)** - API documentation
- **[RASPBERRY_PI_AUTHENTICATION_GUIDE.md](RASPBERRY_PI_AUTHENTICATION_GUIDE.md)** - Raspberry Pi setup

---

## ✅ Checklist

- [ ] Created GCS bucket
- [ ] Created service account
- [ ] Downloaded `gcs-credentials.json`
- [ ] Updated `.env` file
- [ ] Installed `google-cloud-storage`
- [ ] Added `NODE_ID` to Raspberry Pi config
- [ ] Tested upload with `raspi_client_example.py`
- [ ] Verified images in GCS console
- [ ] Checked MongoDB for GCS paths

---

## 🎉 Benefits

✅ **Never lose images** - Stored in Google's infrastructure  
✅ **Organized automatically** - By user, node, and date  
✅ **Searchable** - Find images by time range easily  
✅ **Scalable** - Handle millions of images  
✅ **Cost-effective** - Pay only for storage used  
✅ **Multi-tenant** - Each user's data is isolated  
✅ **Backward compatible** - Existing code still works  

Ready to deploy! 🚀
