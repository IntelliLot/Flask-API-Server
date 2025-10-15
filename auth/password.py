"""
Password utilities for hashing and verification
"""

try:
    import bcrypt
    BCRYPT_AVAILABLE = True
except ImportError:
    BCRYPT_AVAILABLE = False
    print("⚠️  Warning: bcrypt not installed. Password hashing disabled.")


def hash_password(password: str) -> str:
    """
    Hash password using bcrypt
    
    Args:
        password: Plain text password
    
    Returns:
        Hashed password string
    """
    if not BCRYPT_AVAILABLE:
        # Fallback for when bcrypt is not available (NOT SECURE - dev only)
        return password
    
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    """
    Verify password against hash
    
    Args:
        password: Plain text password to verify
        hashed: Hashed password from database
    
    Returns:
        True if password matches, False otherwise
    """
    if not BCRYPT_AVAILABLE:
        # Fallback for when bcrypt is not available (NOT SECURE - dev only)
        return password == hashed
    
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
