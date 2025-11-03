# GCS Image Preview Fix Guide

## Problem

Images uploaded to Google Cloud Storage show "Image Not Available" on the dashboard because:
1. GCS buckets are private by default
2. Public URLs don't work without proper bucket permissions
3. Need either public access or signed URLs

## Solution Implemented

The code has been updated to automatically handle both scenarios:

### 1. **Try Public Access First**
- Attempts to make each blob public (`blob.make_public()`)
- If bucket allows public access, generates standard public URLs
- Works if bucket has "allUsers" viewer permission

### 2. **Fallback to Signed URLs** ⭐ 
- If public access fails, automatically generates signed URLs
- Signed URLs work with private buckets (no bucket config needed!)
- URLs are valid for 7 days
- More secure than public access

## What Changed

### `utils/gcs_storage.py`
Both `upload_image()` and `upload_image_bytes()` now:
```python
# Try to make blob publicly readable
try:
    blob.make_public()
    public_url = blob.public_url
except Exception:
    # Fallback to signed URL (works with private buckets)
    from datetime import timedelta
    public_url = blob.generate_signed_url(
        expiration=timedelta(days=7),
        method='GET'
    )
```
5. Dashboard can display the image ✅

### For Existing Images (Manual Fix Required)
Existing images uploaded before this fix need to be made public manually.

## Fixing Existing Images

### Option 1: Using the Fix Script (Recommended)

## Fixing Existing Images

If you already have images in the database with broken URLs, run:

```bash
# Dry run (see what would be fixed)
python3 fix_gcs_urls.py

# Actually fix the URLs
python3 fix_gcs_urls.py --apply
```

This script:
- Scans all parking_data records
- Finds records with GCS images
- Regenerates signed URLs for all images
- Updates the database with new URLs

## Option 1: No GCS Configuration Needed (Recommended) ⭐

✅ **Just restart your server and it will work!**

The code now automatically uses signed URLs, which work with private buckets.

```bash
# Just restart your Flask server
python3 main_app.py
# or
docker-compose restart
```

**Advantages:**
- ✅ No bucket configuration needed
- ✅ More secure (URLs expire)
- ✅ Works immediately
- ✅ No extra permissions needed

**Note:** 
- Signed URLs expire after 7 days
- New uploads get fresh URLs automatically
- Old URLs need to be refreshed with `fix_gcs_urls.py`

## Option 2: Enable Public Access on GCS Bucket

If you prefer permanent public URLs without expiration:

### Step 1: Make Bucket Public
```bash
# Using gsutil
gsutil iam ch allUsers:objectViewer gs://YOUR_BUCKET_NAME
```

Or via Google Cloud Console:
1. Go to [Google Cloud Storage](https://console.cloud.google.com/storage)
2. Click on your bucket
3. Go to "Permissions" tab
4. Click "+ GRANT ACCESS"
5. Add:
   - **New principals:** `allUsers`
   - **Role:** Storage Object Viewer
6. Click "Save"

### Step 2: Make Existing Blobs Public
```bash
python3 fix_gcs_urls.py --make-public
```

**Advantages:**
- ✅ URLs never expire
- ✅ Simpler URLs

**Disadvantages:**
- ⚠️ Requires bucket configuration
- ⚠️ Less secure (anyone with URL can access)
- ⚠️ Requires Storage Object Admin permissions

## Testing

### Test New Uploads
```bash
# Send a test request to updateRaw
curl -X POST http://localhost:5000/parking/updateRaw \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "image=@test_image.jpg" \
  -F "camera_id=test_camera" \
  -F "coordinates=[[100,100,200,200]]"

# Check the response for gcs_storage.raw_image.url
# The URL should now be accessible
```

### Test Image Access
```bash
# Copy a URL from the API response and test it
curl -I "https://storage.googleapis.com/your-bucket/..."

# Should return 200 OK
```

### Test Dashboard
1. Go to your dashboard: `http://localhost:5000`
2. Navigate to parking data/images section
3. Images should now load instead of "Image Not Available"

## Maintenance

### For Signed URLs (Option 1)

Since signed URLs expire, you should periodically refresh them:

```bash
# Add to cron (run weekly)
0 0 * * 0 cd /path/to/project && python3 fix_gcs_urls.py --apply
```

Or create a scheduled task:

```python
# In your Flask app (optional)
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler

def refresh_gcs_urls():
    """Refresh expired signed URLs"""
    from fix_gcs_urls import fix_gcs_urls
    fix_gcs_urls(dry_run=False)

scheduler = BackgroundScheduler()
scheduler.add_job(refresh_gcs_urls, 'cron', day_of_week='sun', hour=2)
scheduler.start()
```

### For Public URLs (Option 2)

No maintenance needed - URLs are permanent!

## Troubleshooting

### Images Still Not Loading

**Check 1: GCS is Enabled**
```bash
# In .env file
GCS_ENABLE=true
GCS_BUCKET_NAME=your-bucket-name
GCS_CREDENTIALS_PATH=./gcs-credentials.json
```

**Check 2: Credentials Are Valid**
```bash
# Test GCS access
python3 -c "from utils.gcs_storage import gcs_storage; print('GCS Enabled:', gcs_storage.enabled)"
```

**Check 3: URLs in Database**
```python
# Check a record
from config.database import db
record = db.parking_data.find_one({'gcs_storage.raw_image.url': {'$exists': True}})
print(record.get('gcs_storage'))
```

**Check 4: Test URL Directly**
```bash
# Copy a URL from database and test
curl -I "THE_URL_FROM_DATABASE"
```

### Error: "Failed to generate signed URL"

This means credentials don't have permission to sign URLs.

**Solution:** Use public bucket (Option 2) or check service account permissions.

Required permission: `iam.serviceAccounts.signBlob`

```bash
# Grant permission
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:YOUR_SERVICE_ACCOUNT@..." \
  --role="roles/iam.serviceAccountTokenCreator"
```

### CORS Issues

If images load but browser shows CORS errors:

```bash
# Set CORS policy on bucket
cat > cors.json << EOF
[
  {
    "origin": ["*"],
    "method": ["GET"],
    "responseHeader": ["Content-Type"],
    "maxAgeSeconds": 3600
  }
]
EOF

gsutil cors set cors.json gs://YOUR_BUCKET_NAME
```

## Security Considerations

### Signed URLs (Option 1)
- ✅ More secure - URLs expire
- ✅ Can revoke access by not renewing
- ⚠️ Requires periodic refresh
- ⚠️ URLs are long and complex

### Public URLs (Option 2)
- ⚠️ Anyone with URL can access forever
- ⚠️ Can't revoke access without deleting blob
- ✅ No expiration issues
- ✅ Simple, short URLs

**Recommendation:** Use signed URLs (Option 1) for production systems handling sensitive data.

## Quick Commands Reference

```bash
# Check if GCS is working
python3 -c "from utils.gcs_storage import gcs_storage; print('Enabled:', gcs_storage.enabled)"

# Fix existing image URLs (dry run)
python3 fix_gcs_urls.py

# Fix existing image URLs (apply changes)
python3 fix_gcs_urls.py --apply

# Make all blobs public (requires permissions)
python3 fix_gcs_urls.py --make-public

# Test API endpoint
curl -X POST http://localhost:5000/parking/updateRaw \
  -H "Authorization: Bearer TOKEN" \
  -F "image=@test.jpg" \
  -F "camera_id=test" \
  -F "coordinates=[[100,100,200,200]]"
```

## Summary

**✅ Recommended Solution:** 
- Do nothing! Code now automatically uses signed URLs
- Just restart your server
- Run `fix_gcs_urls.py --apply` to fix old images
- Optional: Set up weekly cron job to refresh URLs


**Alternative:**
- Make bucket public for permanent URLs
- More setup but no expiration issues

Both solutions work - choose based on your security requirements!
