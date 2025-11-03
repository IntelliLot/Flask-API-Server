#!/usr/bin/env python3
"""
Script to make existing GCS images publicly accessible
Run this once to fix any previously uploaded images
"""

import os
import sys
import logging
from google.cloud import storage
from google.oauth2 import service_account

# Get environment variables


def get_env(key, default=None):
    """Get environment variable with optional default"""
    return os.environ.get(key, default)


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def make_bucket_images_public(bucket_name: str, credentials_path: str = None):
    """Make all images in bucket publicly readable"""

    try:
        # Initialize GCS client
        if credentials_path and os.path.exists(credentials_path):
            credentials = service_account.Credentials.from_service_account_file(
                credentials_path
            )
            client = storage.Client(credentials=credentials)
            logger.info(f"✅ GCS client initialized with credentials file")
        else:
            client = storage.Client()
            logger.info(f"✅ GCS client initialized with default credentials")

        bucket = client.bucket(bucket_name)
        logger.info(f"✅ Connected to bucket: {bucket_name}")

        # List all blobs
        blobs = client.list_blobs(bucket_name)

        count = 0
        success = 0
        failed = 0

        for blob in blobs:
            count += 1
            try:
                # Make blob publicly readable
                blob.make_public()
                success += 1
                if count % 10 == 0:
                    logger.info(
                        f"Processed {count} images... ({success} successful)")
            except Exception as e:
                failed += 1
                logger.error(f"Failed to make {blob.name} public: {e}")

        logger.info("\n" + "="*60)
        logger.info("SUMMARY")
        logger.info("="*60)
        logger.info(f"Total images: {count}")
        logger.info(f"✅ Made public: {success}")
        logger.info(f"❌ Failed: {failed}")
        logger.info("="*60 + "\n")

        return success, failed

    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return 0, 0


def make_user_images_public(bucket_name: str, user_id: str, credentials_path: str = None):
    """Make all images for a specific user publicly readable"""

    try:
        # Initialize GCS client
        if credentials_path and os.path.exists(credentials_path):
            credentials = service_account.Credentials.from_service_account_file(
                credentials_path
            )
            client = storage.Client(credentials=credentials)
        else:
            client = storage.Client()

        bucket = client.bucket(bucket_name)

        # List blobs with user prefix
        prefix = f"{user_id}/"
        blobs = client.list_blobs(bucket_name, prefix=prefix)

        count = 0
        success = 0
        failed = 0

        logger.info(f"Making images public for user: {user_id}")

        for blob in blobs:
            count += 1
            try:
                blob.make_public()
                success += 1
                if count % 10 == 0:
                    logger.info(f"Processed {count} images...")
            except Exception as e:
                failed += 1
                logger.error(f"Failed to make {blob.name} public: {e}")

        logger.info(
            f"\n✅ Made {success}/{count} images public for user {user_id}")

        return success, failed

    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return 0, 0


def main():
    """Main function"""
    print("="*60)
    print("GCS IMAGE PERMISSIONS FIX")
    print("="*60 + "\n")

    bucket_name = get_env('GCS_BUCKET_NAME')
    credentials_path = get_env('GCS_CREDENTIALS_PATH')

    if not bucket_name:
        logger.error("❌ GCS_BUCKET_NAME not set in environment")
        sys.exit(1)

    print(f"Bucket: {bucket_name}")
    print(f"Credentials: {credentials_path or 'Default'}")
    print()

    # Ask user what to do
    print("Options:")
    print("1. Make ALL images in bucket public")
    print("2. Make images for specific user public")
    print("3. Exit")
    print()

    choice = input("Enter choice (1-3): ").strip()

    if choice == '1':
        confirm = input(
            f"\n⚠️  Make ALL images in '{bucket_name}' public? (yes/no): ")
        if confirm.lower() == 'yes':
            print("\nProcessing...\n")
            make_bucket_images_public(bucket_name, credentials_path)
        else:
            print("❌ Cancelled")

    elif choice == '2':
        user_id = input("\nEnter user ID: ").strip()
        if user_id:
            print("\nProcessing...\n")
            make_user_images_public(bucket_name, user_id, credentials_path)
        else:
            print("❌ Invalid user ID")

    else:
        print("❌ Exiting")


if __name__ == "__main__":
    main()
