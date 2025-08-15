import bcrypt
import jwt
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from cryptography.fernet import Fernet
from passlib.context import CryptContext

class SecurityManager:
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 30
        self.refresh_token_expire_days = 7
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    def generate_salt(self) -> str:
        """Generate cryptographically secure salt"""
        return secrets.token_hex(32)
    
    def hash_password(self, password: str, salt: str) -> str:
        """Hash password with salt using bcrypt"""
        salted_password = f"{password}{salt}"
        return self.pwd_context.hash(salted_password)
    
    def verify_password(self, password: str, salt: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        salted_password = f"{password}{salt}"
        return self.pwd_context.verify(salted_password, hashed_password)
    
    def create_access_token(self, data: Dict[str, Any]) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire, "type": "access"})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        to_encode.update({"exp": expire, "type": "refresh"})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            if payload.get("type") != token_type:
                return None
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.JWTError:
            return None
    
    def generate_encryption_key(self) -> bytes:
        """Generate encryption key for local data"""
        return Fernet.generate_key()
    
    def encrypt_data(self, data: str, key: bytes) -> str:
        """Encrypt data using Fernet"""
        f = Fernet(key)
        encrypted_data = f.encrypt(data.encode())
        return encrypted_data.decode()
    
    def decrypt_data(self, encrypted_data: str, key: bytes) -> str:
        """Decrypt data using Fernet"""
        f = Fernet(key)
        decrypted_data = f.decrypt(encrypted_data.encode())
        return decrypted_data.decode()