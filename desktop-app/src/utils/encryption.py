import sqlite3
import hashlib
import secrets
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from typing import Optional
import keyring
import base64
import os

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
    
    def encrypt_database_file(self, db_path: str, key: bytes) -> bool:
        """Encrypt SQLite database file"""
        try:
            # Read database content
            with open(db_path, 'rb') as f:
                data = f.read()
            
            # Encrypt data
            f = Fernet(key)
            encrypted_data = f.encrypt(data)
            
            # Write encrypted file
            with open(f"{db_path}.encrypted", 'wb') as f:
                f.write(encrypted_data)
            
            # Remove original
            os.remove(db_path)
            os.rename(f"{db_path}.encrypted", db_path)
            
            return True
        except Exception as e:
            print(f"Encryption failed: {e}")
            return False
    
    def decrypt_database_file(self, db_path: str, key: bytes) -> bool:
        """Decrypt SQLite database file"""
        try:
            # Read encrypted file
            with open(db_path, 'rb') as f:
                encrypted_data = f.read()
            
            # Decrypt data
            f = Fernet(key)
            data = f.decrypt(encrypted_data)
            
            # Write decrypted file
            with open(f"{db_path}.decrypted", 'wb') as f:
                f.write(data)
            
            # Replace original
            os.remove(db_path)
            os.rename(f"{db_path}.decrypted", db_path)
            
            return True
        except Exception as e:
            print(f"Decryption failed: {e}")
            return False

class SecureDatabase:
    def __init__(self, db_path: str, encryption_key: bytes):
        self.db_path = db_path
        self.encryption_key = encryption_key
        self.connection = None
    
    def connect(self) -> sqlite3.Connection:
        """Connect to encrypted database"""
        if not os.path.exists(self.db_path):
            # Create new database
            self.connection = sqlite3.connect(self.db_path)
            self._initialize_schema()
        else:
            # Connect to existing database
            self.connection = sqlite3.connect(self.db_path)
        
        # Enable foreign keys
        self.connection.execute("PRAGMA foreign_keys = ON")
        return self.connection
    
    def _initialize_schema(self):
        """Initialize database schema"""
        with open('src/database/local_schema.sql', 'r') as f:
            schema_sql = f.read()
        
        # Execute schema
        self.connection.executescript(schema_sql)
        self.connection.commit()
    
    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()