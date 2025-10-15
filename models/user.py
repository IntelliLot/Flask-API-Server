"""
User Model - Handles parking owner accounts
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from config.database import db


class User:
    """User model for parking owners"""
    
    @staticmethod
    def create(username: str, hashed_password: str, organization_name: str,
               location: str, size: int, verification: str = 'pending',
               details: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Create a new user
        
        Args:
            username: Unique username
            hashed_password: Bcrypt hashed password
            organization_name: Organization/Company name
            location: Physical address
            size: Parking lot capacity
            verification: Verification status
            details: Additional user details
        
        Returns:
            Created user document
        """
        if not db.is_connected():
            raise Exception("Database not connected")
        
        user_id = str(uuid.uuid4())
        
        user_document = {
            'user_id': user_id,
            'username': username,
            'password': hashed_password,
            'organization_name': organization_name,
            'location': location,
            'size': int(size),
            'verification': verification,
            'details': details or {},
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'status': 'active'
        }
        
        db.users.insert_one(user_document)
        
        # Remove password from return value
        user_document.pop('password', None)
        return user_document
    
    @staticmethod
    def find_by_username(username: str) -> Optional[Dict[str, Any]]:
        """Find user by username"""
        if not db.is_connected():
            return None
        return db.users.find_one({'username': username})
    
    @staticmethod
    def find_by_user_id(user_id: str) -> Optional[Dict[str, Any]]:
        """Find user by user_id"""
        if not db.is_connected():
            return None
        user = db.users.find_one({'user_id': user_id})
        if user:
            user.pop('password', None)  # Don't return password
        return user
    
    @staticmethod
    def update_last_login(user_id: str) -> bool:
        """Update user's last login timestamp"""
        if not db.is_connected():
            return False
        
        result = db.users.update_one(
            {'user_id': user_id},
            {'$set': {'last_login': datetime.utcnow()}}
        )
        return result.modified_count > 0
    
    @staticmethod
    def username_exists(username: str) -> bool:
        """Check if username already exists"""
        if not db.is_connected():
            return False
        return db.users.count_documents({'username': username}) > 0
    
    @staticmethod
    def update_status(user_id: str, status: str) -> bool:
        """Update user account status"""
        if not db.is_connected():
            return False
        
        result = db.users.update_one(
            {'user_id': user_id},
            {'$set': {'status': status, 'updated_at': datetime.utcnow()}}
        )
        return result.modified_count > 0
