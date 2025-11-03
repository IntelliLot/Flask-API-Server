#!/usr/bin/env python3
"""
Fix GCS URLs for existing parking data records
Regenerates signed URLs for all images stored in GCS
"""

import sys
import logging
from datetime import timedelta, datetime
from config.database import db
from utils.gcs_storage import gcs_storage

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def fix_gcs_urls(dry_run=True):
    """
    Fix GCS URLs for all parking data records

    Args:
        dry_run: If True, only show what would be updated without making changes
    """
    if not gcs_storage.enabled:
        logger.error("❌ GCS storage is not enabled. Cannot fix URLs.")
        return

    logger.info("🔍 Scanning database for records with GCS images...")

    # Find all records with GCS paths
    query = {
        '$or': [
            {'gcs_storage.raw_image.path': {'$exists': True, '$ne': None}},
            {'gcs_storage.annotated_image.path': {'$exists': True, '$ne': None}}
        ]
    }

    total_records = db.parking_data.count_documents(query)
    logger.info(f"📊 Found {total_records} records with GCS images")

    if total_records == 0:
        logger.info("✅ No records to fix")
        return

    if dry_run:
        logger.info("🔬 DRY RUN MODE - No changes will be made")
        logger.info("    Run with --apply to actually update the database")

    # Process records
    updated_count = 0
    error_count = 0

    cursor = db.parking_data.find(query)

    for record in cursor:
        record_id = record['_id']
        gcs_data = record.get('gcs_storage', {})

        try:
            updated = False

            # Fix raw image URL
            raw_image = gcs_data.get('raw_image')
            if raw_image and raw_image.get('path'):
                blob_path = raw_image['path']
                logger.info(f"  🔄 Generating signed URL for: {blob_path}")

                # Generate signed URL (7 days expiration)
                new_url = gcs_storage.get_signed_url(
                    blob_path, expiration_minutes=7*24*60)

                if new_url:
                    if not dry_run:
                        db.parking_data.update_one(
                            {'_id': record_id},
                            {'$set': {'gcs_storage.raw_image.url': new_url}}
                        )
                    logger.info(f"    ✅ Raw image URL updated")
                    updated = True
                else:
                    logger.warning(
                        f"    ⚠️ Failed to generate URL for raw image")

            # Fix annotated image URL
            annotated_image = gcs_data.get('annotated_image')
            if annotated_image and annotated_image.get('path'):
                blob_path = annotated_image['path']
                logger.info(f"  🔄 Generating signed URL for: {blob_path}")

                new_url = gcs_storage.get_signed_url(
                    blob_path, expiration_minutes=7*24*60)

                if new_url:
                    if not dry_run:
                        db.parking_data.update_one(
                            {'_id': record_id},
                            {'$set': {'gcs_storage.annotated_image.url': new_url}}
                        )
                    logger.info(f"    ✅ Annotated image URL updated")
                    updated = True
                else:
                    logger.warning(
                        f"    ⚠️ Failed to generate URL for annotated image")

            if updated:
                updated_count += 1
                logger.info(f"✅ Record {record_id} - URLs updated")

        except Exception as e:
            error_count += 1
            logger.error(f"❌ Error processing record {record_id}: {e}")

    # Summary
    logger.info("\n" + "="*60)
    logger.info("SUMMARY")
    logger.info("="*60)
    logger.info(f"Total records found: {total_records}")
    logger.info(f"Successfully updated: {updated_count}")
    logger.info(f"Errors: {error_count}")

    if dry_run:
        logger.info("\n🔬 This was a DRY RUN - no changes were made")
        logger.info("   Run with --apply to actually update the database")
    else:
        logger.info("\n✅ Database updated successfully!")
        logger.info("   Note: Signed URLs expire after 7 days")
        logger.info("   Run this script periodically to refresh URLs")


def make_bucket_public():
    """
    Attempt to make all existing blobs public
    This requires bucket-level permissions
    """
    if not gcs_storage.enabled:
        logger.error("❌ GCS storage is not enabled")
        return

    logger.info("🔍 Attempting to make all blobs public...")
    logger.info("⚠️  This requires Storage Object Admin permissions")

    try:
        blobs = gcs_storage.client.list_blobs(gcs_storage.bucket_name)
        count = 0
        success = 0

        for blob in blobs:
            count += 1
            try:
                blob.make_public()
                success += 1
                logger.info(f"✅ Made public: {blob.name}")
            except Exception as e:
                logger.warning(f"⚠️ Could not make public {blob.name}: {e}")

        logger.info(f"\n✅ Processed {count} blobs, {success} made public")

    except Exception as e:
        logger.error(f"❌ Error: {e}")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Fix GCS URLs for parking data images'
    )
    parser.add_argument(
        '--apply',
        action='store_true',
        help='Actually apply changes (default is dry-run)'
    )
    parser.add_argument(
        '--make-public',
        action='store_true',
        help='Attempt to make all GCS blobs public (requires admin permissions)'
    )

    args = parser.parse_args()

    if args.make_public:
        response = input(
            "⚠️  This will attempt to make ALL blobs public. Continue? (yes/no): ")
        if response.lower() == 'yes':
            make_bucket_public()
        else:
            logger.info("Cancelled")
        return

    # Fix URLs
    fix_gcs_urls(dry_run=not args.apply)


if __name__ == "__main__":
    main()
