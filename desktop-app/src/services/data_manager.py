"""
Data Manager - Local SQLite storage and cloud synchronization
Handles offline data storage, encryption, and sync queue management
"""

import sqlite3
import json
import time
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os

@dataclass
class BlinkRecord:
    """Blink data record"""
    id: Optional[str] = None
    session_id: str = ""
    timestamp: datetime = None
    blink_count: int = 0
    confidence_score: float = 1.0
    synced: bool = False
    created_at: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)

@dataclass 
class Session:
    """Tracking session"""
    id: str
    user_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    total_blinks: int = 0
    device_id: str = ""
    app_version: str = "1.0.0"
    
class DataManager:
    """Manages local data storage and cloud synchronization"""
    
    def __init__(self, config, auth_manager):
        self.config = config
        self.auth_manager = auth_manager
        
        # Database
        self.db_path = config.get_data_dir() / "wellness_tracker.db"
        self.encryption_key = None
        
        # Current session
        self.current_session: Optional[Session] = None
        self.session_start_time = None
        
        # Sync management
        self.sync_lock = threading.Lock()
        self.pending_records: List[BlinkRecord] = []
        
        # Initialize database
        self.init_database()
        self.init_encryption()
        
    def init_database(self):
        """Initialize SQLite database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create tables
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS sessions (
                        id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        start_time TEXT NOT NULL,
                        end_time TEXT,
                        total_blinks INTEGER DEFAULT 0,
                        device_id TEXT,
                        app_version TEXT,
                        synced BOOLEAN DEFAULT FALSE,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS blink_data (
                        id TEXT PRIMARY KEY,
                        session_id TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        blink_count INTEGER NOT NULL,
                        confidence_score REAL DEFAULT 1.0,
                        synced BOOLEAN DEFAULT FALSE,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (session_id) REFERENCES sessions (id)
                    )
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS sync_queue (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        endpoint TEXT NOT NULL,
                        method TEXT NOT NULL,
                        data TEXT NOT NULL,
                        retry_count INTEGER DEFAULT 0,
                        last_attempt TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create indexes
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_blink_data_session 
                    ON blink_data(session_id, timestamp)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_blink_data_sync 
                    ON blink_data(synced, created_at)
                """)
                
                conn.commit()
                
        except Exception as e:
            print(f"Database initialization error: {e}")
            
    def init_encryption(self):
        """Initialize encryption for sensitive data"""
        if not self.config.encrypt_local_data:
            return
            
        try:
            # Use user's email as part of key derivation
            user = self.auth_manager.get_current_user()
            if user and user.get('email'):
                password = user['email'].encode()
                
                # Generate salt (store in config or derive deterministically)
                salt = b'wellness_at_work_salt_2024'  # In production, use random salt
                
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=salt,
                    iterations=100000,
                )
                key = base64.urlsafe_b64encode(kdf.derive(password))
                self.encryption_key = Fernet(key)
                
        except Exception as e:
            print(f"Encryption initialization error: {e}")
            
    def encrypt_data(self, data: str) -> str:
        """Encrypt sensitive data"""
        if self.encryption_key:
            try:
                return self.encryption_key.encrypt(data.encode()).decode()
            except Exception:
                pass
        return data
        
    def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        if self.encryption_key:
            try:
                return self.encryption_key.decrypt(encrypted_data.encode()).decode()
            except Exception:
                pass
        return encrypted_data
        
    def start_session(self) -> str:
        """Start a new tracking session"""
        try:
            user = self.auth_manager.get_current_user()
            if not user:
                raise Exception("User not authenticated")
                
            session_id = f"session_{int(time.time() * 1000)}"
            device_id = self.get_device_id()
            
            self.current_session = Session(
                id=session_id,
                user_id=user['id'],
                start_time=datetime.now(timezone.utc),
                device_id=device_id
            )
            
            self.session_start_time = time.time()
            
            # Save to database
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO sessions (id, user_id, start_time, device_id, app_version)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    session_id,
                    user['id'],
                    self.current_session.start_time.isoformat(),
                    device_id,
                    "1.0.0"
                ))
                conn.commit()
                
            # Queue for sync
            self.queue_session_start(self.current_session)
            
            return session_id
            
        except Exception as e:
            print(f"Error starting session: {e}")
            return ""
            
    def end_session(self):
        """End current tracking session"""
        if not self.current_session:
            return
            
        try:
            end_time = datetime.now(timezone.utc)
            total_blinks = self.get_session_blink_count(self.current_session.id)
            
            # Update session
            self.current_session.end_time = end_time
            self.current_session.total_blinks = total_blinks
            
            # Save to database
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE sessions 
                    SET end_time = ?, total_blinks = ?
                    WHERE id = ?
                """, (
                    end_time.isoformat(),
                    total_blinks,
                    self.current_session.id
                ))
                conn.commit()
                
            # Queue for sync
            self.queue_session_end(self.current_session)
            
            self.current_session = None
            self.session_start_time = None
            
        except Exception as e:
            print(f"Error ending session: {e}")
            
    def add_blink_record(self, blink_count: int, confidence_score: float = 1.0):
        """Add a blink record to current session"""
        if not self.current_session:
            return
            
        try:
            record = BlinkRecord(
                id=f"blink_{int(time.time() * 1000000)}",
                session_id=self.current_session.id,
                blink_count=blink_count,
                confidence_score=confidence_score
            )
            
            # Save to database
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO blink_data (id, session_id, timestamp, blink_count, confidence_score)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    record.id,
                    record.session_id,
                    record.timestamp.isoformat(),
                    record.blink_count,
                    record.confidence_score
                ))
                conn.commit()
                
            # Add to pending sync
            with self.sync_lock:
                self.pending_records.append(record)
                
                # Batch sync when we reach the limit
                if len(self.pending_records) >= self.config.batch_size:
                    self.sync_pending_records()
                    
        except Exception as e:
            print(f"Error adding blink record: {e}")
            
    def get_session_duration(self) -> int:
        """Get current session duration in seconds"""
        if self.session_start_time:
            return int(time.time() - self.session_start_time)
        return 0
        
    def get_session_blink_count(self, session_id: str) -> int:
        """Get total blink count for session"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT SUM(blink_count) FROM blink_data WHERE session_id = ?
                """, (session_id,))
                result = cursor.fetchone()
                return result[0] if result[0] else 0
        except Exception:
            return 0
            
    def get_device_id(self) -> str:
        """Get unique device identifier"""
        import platform
        import hashlib
        
        # Create device ID from system info
        system_info = f"{platform.node()}-{platform.system()}-{platform.machine()}"
        device_id = hashlib.md5(system_info.encode()).hexdigest()[:16]
        return f"device_{device_id}"
        
    def queue_session_start(self, session: Session):
        """Queue session start for sync"""
        data = {
            "session_id": session.id,
            "start_time": session.start_time.isoformat(),
            "device_id": session.device_id,
            "app_version": session.app_version
        }
        
        self.add_to_sync_queue("/sessions", "POST", data)
        
    def queue_session_end(self, session: Session):
        """Queue session end for sync"""
        data = {
            "end_time": session.end_time.isoformat() if session.end_time else None,
            "total_blinks": session.total_blinks
        }
        
        self.add_to_sync_queue(f"/sessions/{session.id}", "PUT", data)
        
    def sync_pending_records(self):
        """Sync pending blink records"""
        with self.sync_lock:
            if not self.pending_records:
                return
                
            # Prepare batch data
            batch_data = []
            for record in self.pending_records:
                batch_data.append({
                    "timestamp": record.timestamp.isoformat(),
                    "blink_count": record.blink_count,
                    "confidence_score": record.confidence_score
                })
                
            # Queue for sync
            if self.current_session:
                endpoint = f"/sessions/{self.current_session.id}/blinks/batch"
                self.add_to_sync_queue(endpoint, "POST", {"blinks": batch_data})
                
            # Clear pending records
            self.pending_records.clear()
            
    def add_to_sync_queue(self, endpoint: str, method: str, data: Dict[str, Any]):
        """Add item to sync queue"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO sync_queue (endpoint, method, data)
                    VALUES (?, ?, ?)
                """, (endpoint, method, json.dumps(data)))
                conn.commit()
        except Exception as e:
            print(f"Error adding to sync queue: {e}")
            
    def export_user_data(self) -> Dict[str, Any]:
        """Export all user data for GDPR compliance"""
        try:
            user = self.auth_manager.get_current_user()
            if not user:
                return {}
                
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get sessions
                cursor.execute("""
                    SELECT * FROM sessions WHERE user_id = ?
                """, (user['id'],))
                sessions = cursor.fetchall()
                
                # Get blink data
                cursor.execute("""
                    SELECT bd.* FROM blink_data bd
                    JOIN sessions s ON bd.session_id = s.id
                    WHERE s.user_id = ?
                """, (user['id'],))
                blink_data = cursor.fetchall()
                
                return {
                    "user_id": user['id'],
                    "export_date": datetime.now(timezone.utc).isoformat(),
                    "sessions": sessions,
                    "blink_data": blink_data
                }
                
        except Exception as e:
            print(f"Error exporting data: {e}")
            return {}
            
    def delete_user_data(self):
        """Delete all user data for GDPR compliance"""
        try:
            user = self.auth_manager.get_current_user()
            if not user:
                return
                
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Delete blink data first (foreign key constraint)
                cursor.execute("""
                    DELETE FROM blink_data 
                    WHERE session_id IN (
                        SELECT id FROM sessions WHERE user_id = ?
                    )
                """, (user['id'],))
                
                # Delete sessions
                cursor.execute("""
                    DELETE FROM sessions WHERE user_id = ?
                """, (user['id'],))
                
                conn.commit()
                
        except Exception as e:
            print(f"Error deleting user data: {e}")