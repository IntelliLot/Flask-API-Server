"""
Google Cloud Storage utility for uploading parking images
Organizes images by user_id/node_id/timestamp structure
"""

import os
import logging
from datetime import datetime
from typing import Optional, Tuple
import cv2
import numpy as np
from google.cloud import storage
from google.oauth2 import service_account

logger = logging.getLogger(__name__)


class GCSStorageManager:
    """Manages Google Cloud Storage operations for parking images"""

    def __init__(self):
        """Initialize GCS client"""
        self.enabled = os.getenv('GCS_ENABLE', 'true').lower() == 'true'

        if not self.enabled:
            logger.info("GCS storage is disabled")
            return

        self.bucket_name = os.getenv('GCS_BUCKET_NAME')
        self.credentials_path = os.getenv('GCS_CREDENTIALS_PATH')

        if not self.bucket_name:
            logger.warning("GCS_BUCKET_NAME not set, storage disabled")
            self.enabled = False
            return

        try:
            # Initialize GCS client
            if self.credentials_path and os.path.exists(self.credentials_path):
                credentials = service_account.Credentials.from_service_account_file(
                    self.credentials_path
                )
                self.client = storage.Client(credentials=credentials)
                logger.info(f"✅ GCS client initialized with credentials file")
            else:
                # Use default credentials (for GCP environments)
                self.client = storage.Client()
                logger.info(
                    f"✅ GCS client initialized with default credentials")

            self.bucket = self.client.bucket(self.bucket_name)
            logger.info(f"✅ Connected to GCS bucket: {self.bucket_name}")

        except Exception as e:
            logger.error(f"❌ Failed to initialize GCS client: {e}")
            self.enabled = False

    def upload_image(
        self,
        image: np.ndarray,
        user_id: str,
        node_id: str,
        timestamp: Optional[datetime] = None,
        image_type: str = "raw"
    ) -> Optional[Tuple[str, str]]:
        """
        Upload image to Google Cloud Storage

        Args:
            image: OpenCV image (numpy array)
            user_id: User ID (from JWT)
            node_id: Node/Camera ID (from request)
            timestamp: Timestamp for the image (default: current time)
            image_type: Type of image ('raw', 'annotated', etc.)

        Returns:
            Tuple of (blob_path, public_url) or None if failed
        """
        if not self.enabled:
            logger.debug("GCS storage disabled, skipping upload")
            return None

        if timestamp is None:
            timestamp = datetime.utcnow()

        try:
            # Create hierarchical path: user_id/node_id/YYYY/MM/DD/image_timestamp.jpg
            blob_path = self._generate_blob_path(
                user_id, node_id, timestamp, image_type)

            # Encode image to JPEG
            success, buffer = cv2.imencode(
                '.jpg', image, [cv2.IMWRITE_JPEG_QUALITY, 90])
            if not success:
                logger.error("Failed to encode image to JPEG")
                return None

            image_bytes = buffer.tobytes()

            # Upload to GCS
            blob = self.bucket.blob(blob_path)
            blob.upload_from_string(
                image_bytes,
                content_type='image/jpeg'
            )

            # Set metadata
            blob.metadata = {
                'user_id': user_id,
                'node_id': node_id,
                'image_type': image_type,
                'upload_timestamp': datetime.utcnow().isoformat(),
                'capture_timestamp': timestamp.isoformat()
            }
            blob.patch()

            # Try to make blob publicly readable (works if bucket allows public access)
            try:
                blob.make_public()
                public_url = blob.public_url
                logger.debug(f"✅ Image made public: {blob_path}")
            except Exception as e:
                # If public access fails, generate a signed URL (works with private buckets)
                logger.debug(
                    f"⚠️ Could not make public, using signed URL: {e}")
                from datetime import timedelta
                public_url = blob.generate_signed_url(
                    expiration=timedelta(days=7),  # 7 days expiration
                    method='GET'
                )

            logger.info(f"✅ Image uploaded to GCS: {blob_path}")
            return blob_path, public_url

        except Exception as e:
            logger.error(f"❌ Failed to upload image to GCS: {e}")
            return None

    def upload_image_bytes(
        self,
        image_bytes: bytes,
        user_id: str,
        node_id: str,
        timestamp: Optional[datetime] = None,
        image_type: str = "raw",
        content_type: str = "image/jpeg"
    ) -> Optional[Tuple[str, str]]:
        """
        Upload image bytes directly to Google Cloud Storage

        Args:
            image_bytes: Image as bytes
            user_id: User ID
            node_id: Node/Camera ID
            timestamp: Timestamp
            image_type: Type of image
            content_type: MIME type

        Returns:
            Tuple of (blob_path, public_url) or None if failed
        """
        if not self.enabled:
            logger.debug("GCS storage disabled, skipping upload")
            return None

        if timestamp is None:
            timestamp = datetime.utcnow()

        try:
            blob_path = self._generate_blob_path(
                user_id, node_id, timestamp, image_type)

            blob = self.bucket.blob(blob_path)
            blob.upload_from_string(
                image_bytes,
                content_type=content_type
            )

            blob.metadata = {
                'user_id': user_id,
                'node_id': node_id,
                'image_type': image_type,
                'upload_timestamp': datetime.utcnow().isoformat(),
                'capture_timestamp': timestamp.isoformat()
            }
            blob.patch()

            # Try to make blob publicly readable (works if bucket allows public access)
            try:
                blob.make_public()
                public_url = blob.public_url
                logger.debug(f"✅ Image made public: {blob_path}")
            except Exception as e:
                # If public access fails, generate a signed URL (works with private buckets)
                logger.debug(
                    f"⚠️ Could not make public, using signed URL: {e}")
                from datetime import timedelta
                public_url = blob.generate_signed_url(
                    expiration=timedelta(days=7),  # 7 days expiration
                    method='GET'
                )

            logger.info(f"✅ Image bytes uploaded to GCS: {blob_path}")
            return blob_path, public_url

        except Exception as e:
            logger.error(f"❌ Failed to upload image bytes to GCS: {e}")
            return None

    def _generate_blob_path(
        self,
        user_id: str,
        node_id: str,
        timestamp: datetime,
        image_type: str
    ) -> str:
        """
        Generate hierarchical blob path
        Format: user_id/node_id/YYYY/MM/DD/HH/image_type_YYYYMMDD_HHMMSS_microseconds.jpg

        Example: user123/node_01/2025/11/02/14/raw_20251102_143052_123456.jpg
        """
        date_str = timestamp.strftime('%Y/%m/%d/%H')
        filename = f"{image_type}_{timestamp.strftime('%Y%m%d_%H%M%S')}_{timestamp.microsecond}.jpg"

        blob_path = f"{user_id}/{node_id}/{date_str}/{filename}"
        return blob_path

    def get_signed_url(self, blob_path: str, expiration_minutes: int = 60) -> Optional[str]:
        """
        Generate a signed URL for private access to an image

        Args:
            blob_path: Path to the blob in GCS
            expiration_minutes: URL expiration time in minutes

        Returns:
            Signed URL string or None if failed
        """
        if not self.enabled:
            return None

        try:
            from datetime import timedelta

            blob = self.bucket.blob(blob_path)
            signed_url = blob.generate_signed_url(
                expiration=timedelta(minutes=expiration_minutes),
                method='GET'
            )

            return signed_url

        except Exception as e:
            logger.error(f"❌ Failed to generate signed URL: {e}")
            return None

    def delete_image(self, blob_path: str) -> bool:
        """
        Delete an image from GCS

        Args:
            blob_path: Path to the blob in GCS

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False

        try:
            blob = self.bucket.blob(blob_path)
            blob.delete()
            logger.info(f"✅ Image deleted from GCS: {blob_path}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to delete image from GCS: {e}")
            return False

    def list_user_images(
        self,
        user_id: str,
        node_id: Optional[str] = None,
        limit: int = 100
    ) -> list:
        """
        List images for a user (optionally filtered by node_id)

        Args:
            user_id: User ID
            node_id: Optional node ID filter
            limit: Maximum number of results

        Returns:
            List of blob names
        """
        if not self.enabled:
            return []

        try:
            prefix = f"{user_id}/"
            if node_id:
                prefix = f"{user_id}/{node_id}/"

            blobs = self.client.list_blobs(
                self.bucket_name,
                prefix=prefix,
                max_results=limit
            )

            return [blob.name for blob in blobs]

        except Exception as e:
            logger.error(f"❌ Failed to list images: {e}")
            return []


# Global instance
gcs_storage = GCSStorageManager()
