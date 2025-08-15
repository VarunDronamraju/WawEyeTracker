import sqlite3
import json
import hashlib
import time
import threading
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from cryptography.fernet import Fernet
import keyring

from ..core.eye_tracker import BlinkEvent
from ..utils.encryption import LocalEncryption

@dataclass
class BlinkDataRecord:
    id: str
    session_id: str
    timestamp: float
    blink_count: int
    confidence_score: float
    eye_strain_score: Optional[float]
    interval_seconds: int
    synced: bool
    sync_attempts: int
    created_at: float

@dataclass
class SessionRecord:
    id: str
    user_id: str
    device_id: str
    start_time: float
    end_time: Optional[float]
    total_blinks: int
    app_version: str
    os_info: str
    synced: bool
    created_at: float

class DataManager:
    """Manages local data storage with encryption"""
    
    def __init__(self, user_id: str, app_data_dir: str = None):
        self.user_id = user_id
        self.app_data_dir = Path(app_data_dir) if app_data_dir else Path.home() / ".wellness-at-work"
        self.app_data_dir.mkdir(exist_ok=True)
        
        # Database path
        self.db_path = self.app_data_dir / f"wellness_data_{user_id}.db"
        
        # Encryption setup
        self.encryption = LocalEncryption(user_id)
        self.encryption_key = None
        
        # Thread lock for database operations
        self.db_lock = threading.Lock()
        
        # Initialize database
        self._initialize_database()
    
    def initialize_encryption(self, user_password: str) -> bool:
        """Initialize encryption with user password"""
        try:
            self.encryption_key = self.encryption.get_or_create_encryption_key(user_password)
            return True
        except Exception as e:
            print(f"Failed to initialize encryption: {e}")
            return False
    
    def _initialize_database(self):
        """Initialize SQLite database with schema"""
        with self.db_lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Enable foreign keys
            cursor.execute("PRAGMA foreign_keys = ON")
            
            # Create tables
            cursor.executescript("""
                -- Local blink data
                CREATE TABLE IF NOT EXISTS local_blink_data (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    blink_count INTEGER NOT NULL,
                    confidence_score REAL DEFAULT 1.0,
                    eye_strain_score REAL,
                    interval_seconds INTEGER DEFAULT 60,
                    synced BOOLEAN DEFAULT FALSE,
                    sync_attempts INTEGER DEFAULT 0,
                    created_at REAL NOT NULL
                );
                
                -- Local sessions
                CREATE TABLE IF NOT EXISTS local_sessions (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    device_id TEXT NOT NULL,
                    start_time REAL NOT NULL,
                    end_time REAL,
                    total_blinks INTEGER DEFAULT 0,
                    app_version TEXT,
                    os_info TEXT,
                    synced BOOLEAN DEFAULT FALSE,
                    created_at REAL NOT NULL
                );
                
                -- Sync queue
                CREATE TABLE IF NOT EXISTS sync_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    endpoint TEXT NOT NULL,
                    method TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    headers TEXT,
                    retry_count INTEGER DEFAULT 0,
                    max_retries INTEGER DEFAULT 5,
                    next_retry REAL,
                    created_at REAL NOT NULL,
                    status TEXT DEFAULT 'pending'
                );
                
                -- User settings
                CREATE TABLE IF NOT EXISTS user_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at REAL NOT NULL
                );
                
                -- GDPR consent history
                CREATE TABLE IF NOT EXISTS consent_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    consent_type TEXT NOT NULL,
                    consent_given BOOLEAN NOT NULL,
                    timestamp REAL NOT NULL,
                    version TEXT NOT NULL
                );
                
                -- Create indexes
                CREATE INDEX IF NOT EXISTS idx_blink_session ON local_blink_data(session_id, timestamp);
                CREATE INDEX IF NOT EXISTS idx_blink_sync ON local_blink_data(synced, created_at);
                CREATE INDEX IF NOT EXISTS idx_sync_queue_status ON sync_queue(status, next_retry);
                CREATE INDEX IF NOT EXISTS idx_sessions_user ON local_sessions(user_id, start_time DESC);
            """)
            
            conn.commit()
            conn.close()
    
    def create_session(self, device_id: str, app_version: str, os_info: Dict[str, Any]) -> str:
        """Create a new tracking session"""
        session_id = self._generate_id()
        session = SessionRecord(
            id=session_id,
            user_id=self.user_id,
            device_id=device_id,
            start_time=time.time(),
            end_time=None,
            total_blinks=0,
            app_version=app_version,
            os_info=json.dumps(os_info),
            synced=False,
            created_at=time.time()
        )
        
        with self.db_lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO local_sessions 
                (id, user_id, device_id, start_time, end_time, total_blinks, app_version, os_info, synced, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session.id, session.user_id, session.device_id, session.start_time,
                session.end_time, session.total_blinks, session.app_version,
                session.os_info, session.synced, session.created_at
            ))
            
            conn.commit()
            conn.close()
        
        return session_id
    
    def end_session(self, session_id: str, total_blinks: int):
        """End a tracking session"""
        with self.db_lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE local_sessions 
                SET end_time = ?, total_blinks = ? 
                WHERE id = ?
            """, (time.time(), total_blinks, session_id))
            
            conn.commit()
            conn.close()
    
    def store_blink_data(self, session_id: str, blink_events: List[BlinkEvent]) -> int:
        """Store blink data with aggregation"""
        if not blink_events:
            return 0
        
        # Continuing from where it was cut off...
        # Aggregate blinks by minute intervals
        aggregated_data = self._aggregate_blink_data(blink_events)
        
        records_stored = 0
        with self.db_lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for interval_start, blinks_in_interval in aggregated_data.items():
                record_id = self._generate_id()
                avg_confidence = sum(b.confidence for b in blinks_in_interval) / len(blinks_in_interval)
                
                # Calculate eye strain score (simple heuristic)
                eye_strain_score = self._calculate_eye_strain_score(blinks_in_interval)
                
                record = BlinkDataRecord(
                    id=record_id,
                    session_id=session_id,
                    timestamp=interval_start,
                    blink_count=len(blinks_in_interval),
                    confidence_score=avg_confidence,
                    eye_strain_score=eye_strain_score,
                    interval_seconds=60,
                    synced=False,
                    sync_attempts=0,
                    created_at=time.time()
                )
                
                cursor.execute("""
                    INSERT OR REPLACE INTO local_blink_data 
                    (id, session_id, timestamp, blink_count, confidence_score, eye_strain_score, 
                     interval_seconds, synced, sync_attempts, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    record.id, record.session_id, record.timestamp, record.blink_count,
                    record.confidence_score, record.eye_strain_score, record.interval_seconds,
                    record.synced, record.sync_attempts, record.created_at
                ))
                
                records_stored += 1
            
            conn.commit()
            conn.close()
        
        return records_stored
    
    def _aggregate_blink_data(self, blink_events: List[BlinkEvent]) -> Dict[float, List[BlinkEvent]]:
        """Aggregate blink events into 1-minute intervals"""
        aggregated = {}
        
        for event in blink_events:
            # Round timestamp to minute boundary
            interval_start = int(event.timestamp / 60) * 60
            
            if interval_start not in aggregated:
                aggregated[interval_start] = []
            
            aggregated[interval_start].append(event)
        
        return aggregated
    
    def _calculate_eye_strain_score(self, blinks_in_interval: List[BlinkEvent]) -> float:
        """Calculate eye strain score for a time interval"""
        blink_count = len(blinks_in_interval)
        avg_confidence = sum(b.confidence for b in blinks_in_interval) / len(blinks_in_interval)
        
        # Normal blink rate is 15-20 per minute
        # Lower blink rate indicates higher eye strain
        if blink_count < 10:
            base_strain = 0.8  # High strain
        elif blink_count < 15:
            base_strain = 0.6  # Medium strain
        elif blink_count <= 20:
            base_strain = 0.2  # Low strain
        else:
            base_strain = 0.4  # Medium strain (too many blinks can also indicate issues)
        
        # Adjust based on confidence (lower confidence = higher strain)
        confidence_factor = 1.0 - avg_confidence
        strain_score = min(1.0, base_strain + (confidence_factor * 0.2))
        
        return strain_score
    
    def get_unsynced_data(self, limit: int = 100) -> Tuple[List[BlinkDataRecord], List[SessionRecord]]:
        """Get unsynced data for cloud synchronization"""
        with self.db_lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get unsynced blink data
            cursor.execute("""
                SELECT * FROM local_blink_data 
                WHERE synced = FALSE 
                ORDER BY created_at ASC 
                LIMIT ?
            """, (limit,))
            
            blink_rows = cursor.fetchall()
            blink_records = [BlinkDataRecord(*row) for row in blink_rows]
            
            # Get unsynced sessions
            cursor.execute("""
                SELECT * FROM local_sessions 
                WHERE synced = FALSE 
                ORDER BY created_at ASC
            """)
            
            session_rows = cursor.fetchall()
            session_records = [SessionRecord(*row) for row in session_rows]
            
            conn.close()
        
        return blink_records, session_records
    
    def mark_as_synced(self, record_ids: List[str], record_type: str = 'blink'):
        """Mark records as synced"""
        if not record_ids:
            return
        
        table_name = 'local_blink_data' if record_type == 'blink' else 'local_sessions'
        placeholders = ','.join(['?' for _ in record_ids])
        
        with self.db_lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(f"""
                UPDATE {table_name} 
                SET synced = TRUE 
                WHERE id IN ({placeholders})
            """, record_ids)
            
            conn.commit()
            conn.close()
    
    def increment_sync_attempts(self, record_ids: List[str]):
        """Increment sync attempt counter for failed syncs"""
        if not record_ids:
            return
        
        placeholders = ','.join(['?' for _ in record_ids])
        
        with self.db_lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(f"""
                UPDATE local_blink_data 
                SET sync_attempts = sync_attempts + 1 
                WHERE id IN ({placeholders})
            """, record_ids)
            
            conn.commit()
            conn.close()
    
    def store_setting(self, key: str, value: Any):
        """Store user setting"""
        with self.db_lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO user_settings (key, value, updated_at)
                VALUES (?, ?, ?)
            """, (key, json.dumps(value), time.time()))
            
            conn.commit()
            conn.close()
    
    def get_setting(self, key: str, default=None):
        """Get user setting"""
        with self.db_lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT value FROM user_settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            
            conn.close()
        
        if row:
            return json.loads(row[0])
        return default
    
    def store_consent(self, consent_type: str, consent_given: bool, version: str):
        """Store GDPR consent record"""
        with self.db_lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO consent_history (user_id, consent_type, consent_given, timestamp, version)
                VALUES (?, ?, ?, ?, ?)
            """, (self.user_id, consent_type, consent_given, time.time(), version))
            
            conn.commit()
            conn.close()
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        with self.db_lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            stats = {}
            
            # Count records in each table
            for table in ['local_blink_data', 'local_sessions', 'sync_queue']:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                stats[f"{table}_count"] = cursor.fetchone()[0]
            
            # Unsynced counts
            cursor.execute("SELECT COUNT(*) FROM local_blink_data WHERE synced = FALSE")
            stats['unsynced_blinks'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM local_sessions WHERE synced = FALSE")
            stats['unsynced_sessions'] = cursor.fetchone()[0]
            
            # Database size
            stats['db_size_mb'] = self.db_path.stat().st_size / (1024 * 1024)
            
            conn.close()
        
        return stats
    
    def cleanup_old_data(self, days_to_keep: int = 30):
        """Clean up old data based on retention policy"""
        cutoff_time = time.time() - (days_to_keep * 24 * 3600)
        
        with self.db_lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Delete old synced blink data
            cursor.execute("""
                DELETE FROM local_blink_data 
                WHERE synced = TRUE AND created_at < ?
            """, (cutoff_time,))
            
            deleted_blinks = cursor.rowcount
            
            # Delete old synced sessions
            cursor.execute("""
                DELETE FROM local_sessions 
                WHERE synced = TRUE AND created_at < ?
            """, (cutoff_time,))
            
            deleted_sessions = cursor.rowcount
            
            conn.commit()
            conn.close()
        
        return deleted_blinks, deleted_sessions
    
    def export_data(self, output_path: str, format: str = 'json') -> bool:
        """Export all user data for GDPR compliance"""
        try:
            with self.db_lock:
                conn = sqlite3.connect(self.db_path)
                
                # Get all data
                data = {
                    'user_id': self.user_id,
                    'export_timestamp': time.time(),
                    'blink_data': [],
                    'sessions': [],
                    'settings': [],
                    'consent_history': []
                }
                
                # Export blink data
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM local_blink_data")
                columns = [desc[0] for desc in cursor.description]
                for row in cursor.fetchall():
                    data['blink_data'].append(dict(zip(columns, row)))
                
                # Export sessions
                cursor.execute("SELECT * FROM local_sessions")
                columns = [desc[0] for desc in cursor.description]
                for row in cursor.fetchall():
                    data['sessions'].append(dict(zip(columns, row)))
                
                # Export settings
                cursor.execute("SELECT * FROM user_settings")
                columns = [desc[0] for desc in cursor.description]
                for row in cursor.fetchall():
                    data['settings'].append(dict(zip(columns, row)))
                
                # Export consent history
                cursor.execute("SELECT * FROM consent_history")
                columns = [desc[0] for desc in cursor.description]
                for row in cursor.fetchall():
                    data['consent_history'].append(dict(zip(columns, row)))
                
                conn.close()
            
            # Write to file
            if format.lower() == 'json':
                with open(output_path, 'w') as f:
                    json.dump(data, f, indent=2)
            else:
                # CSV export would go here
                pass
            
            return True
            
        except Exception as e:
            print(f"Export failed: {e}")
            return False
    
    def delete_all_data(self) -> bool:
        """Delete all user data for GDPR compliance"""
        try:
            with self.db_lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # Delete all data
                cursor.execute("DELETE FROM local_blink_data")
                cursor.execute("DELETE FROM local_sessions")
                cursor.execute("DELETE FROM sync_queue")
                cursor.execute("DELETE FROM user_settings")
                cursor.execute("DELETE FROM consent_history")
                
                conn.commit()
                conn.close()
            
            # Remove database file
            if self.db_path.exists():
                self.db_path.unlink()
            
            return True
            
        except Exception as e:
            print(f"Data deletion failed: {e}")
            return False
    
    def _generate_id(self) -> str:
        """Generate unique ID for records"""
        return hashlib.md5(f"{time.time()}{self.user_id}".encode()).hexdigest()