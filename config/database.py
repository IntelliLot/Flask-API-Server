"""
MongoDB Database Configuration and Connection Management
"""

import os
import logging
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure

logger = logging.getLogger(__name__)


class Database:
    """MongoDB Database Manager"""
    
    _instance = None
    _client = None
    _db = None
    
    def __new__(cls):
        """Singleton pattern to ensure only one database connection"""
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize database connection"""
        # Don't connect immediately - let it happen lazily
        pass
    
    def connect(self):
        """Connect to MongoDB and create indexes"""
        if self._client is not None:
            return  # Already connected
            
        try:
            mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
            db_name = os.getenv('MONGODB_DB_NAME', 'parking_detection')
            
            self._client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
            
            # Test connection
            self._client.admin.command('ping')
            
            self._db = self._client[db_name]
            
            # Create indexes
            self._create_indexes()
            
            logger.info(f"✅ Connected to MongoDB: {db_name}")
            
        except ConnectionFailure as e:
            logger.error(f"❌ MongoDB connection failed: {e}")
            logger.error(f"   Make sure MongoDB is running on: {mongodb_uri}")
            self._db = None
        except Exception as e:
            logger.error(f"❌ Database initialization error: {e}")
            self._db = None
    
    def _create_indexes(self):
        """Create database indexes for better performance"""
        if self._db is None:
            return
        
        try:
            # Users collection indexes
            users = self._db['users']
            users.create_index([('username', ASCENDING)], unique=True)
            users.create_index([('user_id', ASCENDING)], unique=True)
            
            # Parking data collection indexes
            parking_data = self._db['parking_data']
            parking_data.create_index([('user_id', ASCENDING)])
            parking_data.create_index([('camera_id', ASCENDING)])
            parking_data.create_index([('timestamp', DESCENDING)])
            parking_data.create_index([('user_id', ASCENDING), ('camera_id', ASCENDING)])
            parking_data.create_index([('user_id', ASCENDING), ('timestamp', DESCENDING)])
            
            logger.info("✅ Database indexes created")
            
        except Exception as e:
            logger.warning(f"⚠️  Index creation warning: {e}")
    
    @property
    def db(self):
        """Get database instance (lazy connection)"""
        if self._db is None:
            self.connect()
        return self._db
    
    @property
    def users(self):
        """Get users collection (lazy connection)"""
        if self._db is None:
            self.connect()
        if self._db is None:
            raise Exception("Database not connected")
        return self._db['users']
    
    @property
    def parking_data(self):
        """Get parking_data collection (lazy connection)"""
        if self._db is None:
            self.connect()
        if self._db is None:
            raise Exception("Database not connected")
        return self._db['parking_data']
    
    def is_connected(self):
        """Check if database is connected"""
        return self._db is not None
    
    def close(self):
        """Close database connection"""
        if self._client:
            self._client.close()
            logger.info("Database connection closed")


# Global database instance
db = Database()
