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

    @staticmethod
    def create_api_credential(user_id: str, name: str, api_key: str) -> Dict[str, Any]:
        """
        Create a new API credential for a user

        Args:
            user_id: User's unique ID
            name: Name/description for the credential
            api_key: Generated API key

        Returns:
            Created credential document
        """
        if not db.is_connected():
            raise Exception("Database not connected")

        credential_id = str(uuid.uuid4())

        credential = {
            'credential_id': credential_id,
            'user_id': user_id,
            'name': name,
            'api_key': api_key,
            'status': 'active',
            'created_at': datetime.utcnow(),
            'last_used': None,
            'usage_count': 0
        }

        db.api_credentials.insert_one(credential)
        return credential

    @staticmethod
    def get_user_credentials(user_id: str) -> list:
        """Get all API credentials for a user"""
        if not db.is_connected():
            return []

        credentials = list(db.api_credentials.find(
            {'user_id': user_id},
            {'_id': 0}
        ).sort('created_at', -1))

        return credentials

    @staticmethod
    def find_by_api_key(api_key: str) -> Optional[Dict[str, Any]]:
        """Find user by API key"""
        if not db.is_connected():
            return None

        credential = db.api_credentials.find_one(
            {'api_key': api_key, 'status': 'active'})
        if not credential:
            return None

        # Update last used timestamp and usage count
        db.api_credentials.update_one(
            {'credential_id': credential['credential_id']},
            {
                '$set': {'last_used': datetime.utcnow()},
                '$inc': {'usage_count': 1}
            }
        )

        # Return user info
        return User.find_by_user_id(credential['user_id'])

    @staticmethod
    def revoke_credential(user_id: str, credential_id: str) -> bool:
        """Revoke an API credential"""
        if not db.is_connected():
            return False

        result = db.api_credentials.update_one(
            {'credential_id': credential_id, 'user_id': user_id},
            {'$set': {'status': 'revoked'}}
        )
        return result.modified_count > 0

    @staticmethod
    def activate_credential(user_id: str, credential_id: str) -> bool:
        """Activate an API credential"""
        if not db.is_connected():
            return False

        result = db.api_credentials.update_one(
            {'credential_id': credential_id, 'user_id': user_id},
            {'$set': {'status': 'active'}}
        )
        return result.modified_count > 0

    @staticmethod
    def delete_credential(user_id: str, credential_id: str) -> bool:
        """Delete an API credential"""
        if not db.is_connected():
            return False

        result = db.api_credentials.delete_one(
            {'credential_id': credential_id, 'user_id': user_id}
        )
        return result.deleted_count > 0
