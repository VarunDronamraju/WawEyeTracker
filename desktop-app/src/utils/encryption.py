"""
Local Encryption Utility
Handles local data encryption for privacy
"""

import os
import hashlib
import secrets
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from typing import Optional
import keyring
import base64

class LocalEncryption:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.service_name = "WellnessAtWork"
        self.key_name = f"encryption_key_{user_id}"
    
    def _derive_key_from_password(self, password: str, salt: bytes) -> bytes:
        """Derive encryption key from user password"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key
    
    def get_or_create_encryption_key(self, user_password: str) -> bytes:
        """Get existing or create new encryption key"""
        try:
            # Try to get existing key from keychain
            stored_key = keyring.get_password(self.service_name, self.key_name)
            if stored_key:
                return base64.urlsafe_b64decode(stored_key.encode())
        except:
            pass
        
        # Create new key
        salt = secrets.token_bytes(16)
        key = self._derive_key_from_password(user_password, salt)
        
        # Store in keychain
        try:
            keyring.set_password(self.service_name, self.key_name, 
                               base64.urlsafe_b64encode(key).decode())
            # Store salt separately
            keyring.set_password(self.service_name, f"salt_{self.user_id}", 
                               base64.urlsafe_b64encode(salt).decode())
        except:
            pass
        
        return key
    
    def encrypt_data(self, data: str, key: bytes) -> str:
        """Encrypt string data"""
        try:
            f = Fernet(key)
            encrypted_data = f.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted_data).decode()
        except Exception as e:
            print(f"Encryption failed: {e}")
            return data
    
    def decrypt_data(self, encrypted_data: str, key: bytes) -> str:
        """Decrypt string data"""
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
            f = Fernet(key)
            decrypted_data = f.decrypt(encrypted_bytes)
            return decrypted_data.decode()
        except Exception as e:
            print(f"Decryption failed: {e}")
            return encrypted_data
