#!/usr/bin/env python3
"""
MongoDB Index Setup Script

Creates necessary indexes for the api_credentials collection
to ensure optimal performance for API key lookups and queries.

Run: python setup_indexes.py
"""

from config.database import db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def setup_indexes():
    """Create indexes for api_credentials collection"""

    print("="*70)
    print("🗄️  Setting up MongoDB indexes for api_credentials")
    print("="*70)

    if not db.is_connected():
        print("❌ Database not connected. Please check MongoDB connection.")
        return False

    try:
        collection = db.api_credentials

        # 1. Unique index on api_key for fast lookups
        print("\n1. Creating unique index on 'api_key'...")
        collection.create_index('api_key', unique=True)
        print("   ✅ Index created: api_key (unique)")

        # 2. Index on user_id for listing user's credentials
        print("\n2. Creating index on 'user_id'...")
        collection.create_index('user_id')
        print("   ✅ Index created: user_id")

        # 3. Compound index on user_id + status for filtered queries
        print("\n3. Creating compound index on 'user_id' + 'status'...")
        collection.create_index([('user_id', 1), ('status', 1)])
        print("   ✅ Index created: user_id + status")

        # 4. Index on status for admin queries
        print("\n4. Creating index on 'status'...")
        collection.create_index('status')
        print("   ✅ Index created: status")

        # 5. Index on created_at for sorting
        print("\n5. Creating index on 'created_at'...")
        collection.create_index('created_at')
        print("   ✅ Index created: created_at")

        # List all indexes
        print("\n📋 Existing indexes:")
        indexes = collection.index_information()
        for index_name, index_info in indexes.items():
            keys = index_info['key']
            unique = ' (unique)' if index_info.get('unique', False) else ''
            print(f"   • {index_name}: {keys}{unique}")

        print("\n" + "="*70)
        print("✅ All indexes created successfully!")
        print("="*70)

        return True

    except Exception as e:
        print(f"\n❌ Error creating indexes: {e}")
        return False


def setup_user_indexes():
    """Create indexes for users collection (if not already present)"""

    print("\n🗄️  Setting up MongoDB indexes for users collection")
    print("="*70)

    if not db.is_connected():
        print("❌ Database not connected.")
        return False

    try:
        collection = db.users

        # Index on username (should already exist, but ensure it's unique)
        print("\n1. Creating unique index on 'username'...")
        collection.create_index('username', unique=True)
        print("   ✅ Index created: username (unique)")

        # Index on user_id for fast lookups
        print("\n2. Creating index on 'user_id'...")
        collection.create_index('user_id', unique=True)
        print("   ✅ Index created: user_id (unique)")

        # Index on status
        print("\n3. Creating index on 'status'...")
        collection.create_index('status')
        print("   ✅ Index created: status")

        print("\n✅ User indexes verified/created!")

        return True

    except Exception as e:
        print(f"\n❌ Error creating user indexes: {e}")
        return False


def setup_parking_data_indexes():
    """Create indexes for parking_data collection"""

    print("\n🗄️  Setting up MongoDB indexes for parking_data collection")
    print("="*70)

    if not db.is_connected():
        print("❌ Database not connected.")
        return False

    try:
        collection = db.parking_data

        # Compound index on user_id + timestamp for queries
        print("\n1. Creating compound index on 'user_id' + 'timestamp'...")
        collection.create_index([('user_id', 1), ('timestamp', -1)])
        print("   ✅ Index created: user_id + timestamp")

        # Index on camera_id
        print("\n2. Creating index on 'camera_id'...")
        collection.create_index('camera_id')
        print("   ✅ Index created: camera_id")

        # Compound index on user_id + camera_id + timestamp
        print("\n3. Creating compound index on 'user_id' + 'camera_id' + 'timestamp'...")
        collection.create_index(
            [('user_id', 1), ('camera_id', 1), ('timestamp', -1)])
        print("   ✅ Index created: user_id + camera_id + timestamp")

        print("\n✅ Parking data indexes verified/created!")

        return True

    except Exception as e:
        print(f"\n❌ Error creating parking_data indexes: {e}")
        return False


def main():
    """Main function"""

    print("\n🚀 MongoDB Index Setup for IntelliLot")
    print("="*70)

    # Connect to database
    db.connect()

    if not db.is_connected():
        print("\n❌ Failed to connect to MongoDB")
        print("Please check your MongoDB connection settings in config/database.py")
        return

    print(f"✅ Connected to MongoDB")
    print(f"   Database: {db.db_name}")

    # Setup indexes for all collections
    success_count = 0

    if setup_indexes():
        success_count += 1

    if setup_user_indexes():
        success_count += 1

    if setup_parking_data_indexes():
        success_count += 1

    # Summary
    print("\n" + "="*70)
    print("📊 Setup Summary")
    print("="*70)
    print(f"Collections processed: 3")
    print(f"Successfully indexed: {success_count}/3")

    if success_count == 3:
        print("\n🎉 All indexes created successfully!")
        print("\nYour database is now optimized for:")
        print("  • Fast API key lookups")
        print("  • Efficient user queries")
        print("  • Quick parking data retrieval")
        print("  • Sorted time-series data")
    else:
        print("\n⚠️  Some indexes failed to create. Check errors above.")

    print("="*70)


if __name__ == "__main__":
    main()
