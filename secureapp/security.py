import hashlib, os, base64

def hash_password(password: str) -> str:
    """Hash a password for storing."""
    salt = os.urandom(16)
    pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return base64.b64encode(salt + pwdhash).decode('utf-8')

def verify_password(stored_password: str, provided_password: str) -> bool:
    """Verify a stored password against one provided by user"""
    stored_password_bytes = base64.b64decode(stored_password.encode('utf-8'))
    salt = stored_password_bytes[:16]
    stored_pwdhash = stored_password_bytes[16:]
    pwdhash = hashlib.pbkdf2_hmac('sha256', provided_password.encode('utf-8'), salt, 100000)
    return pwdhash == stored_pwdhash