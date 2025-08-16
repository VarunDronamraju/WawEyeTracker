"""
Sync Manager - Handles online/offline synchronization
Background sync with retry logic and conflict resolution
"""

import threading
import time
import sqlite3
import json
from datetime import datetime, timezone
from typing import List, Dict, Any
from PyQt6.QtCore import QObject, pyqtSignal, QTimer

class SyncManager(QObject):
    """Manages synchronization between local and cloud data"""
    
    # Signals
    sync_started = pyqtSignal()
    sync_completed = pyqtSignal(int, int)  # success_count, error_count
    sync_error = pyqtSignal(str)
    connection_status_changed = pyqtSignal(bool)  # online/offline
    
    def __init__(self, config, auth_manager, api_client, data_manager):
        super().__init__()
        self.config = config
        self.auth_manager = auth_manager
        self.api_client = api_client
        self.data_manager = data_manager
        
        # Sync state
        self.is_online = False
        self.sync_in_progress = False
        self.sync_thread = None
        
        # Timers
        self.sync_timer = QTimer()
        self.sync_timer.timeout.connect(self.sync_pending_data)
        
        self.health_check_timer = QTimer()
        self.health_check_timer.timeout.connect(self.check_connection)
        
        # Start background tasks
        self.start_background_sync()
        
    def start_background_sync(self):
        """Start background synchronization timers"""
        # Check connection every 30 seconds
        self.health_check_timer.start(30000)
        
        # Sync pending data based on config interval
        self.sync_timer.start(self.config.sync_interval * 1000)
        
        # Initial connection check
        self.check_connection()
        
    def stop_background_sync(self):
        """Stop background synchronization"""
        self.sync_timer.stop()
        self.health_check_timer.stop()
        
        if self.sync_thread and self.sync_thread.is_alive():
            self.sync_thread.join(timeout=5.0)
            
    def check_connection(self):
        """Check if backend is accessible"""
        try:
            response = self.api_client.health_check()
            new_status = response.success
            
            if new_status != self.is_online:
                self.is_online = new_status
                self.connection_status_changed.emit(self.is_online)
                
                if self.is_online:
                    # Connection restored, trigger sync
                    self.sync_pending_data()
                    
        except Exception as e:
            if self.is_online:
                self.is_online = False
                self.connection_status_changed.emit(False)
                
    def sync_pending_data(self):
        """Sync all pending data to cloud"""
        if not self.is_online or self.sync_in_progress:
            return
            
        if not self.auth_manager.is_authenticated():
            return
            
        # Start sync in background thread
        self.sync_thread = threading.Thread(target=self._perform_sync)
        self.sync_thread.start()
        
    def _perform_sync(self):
        """Perform synchronization (runs in background thread)"""
        self.sync_in_progress = True
        self.sync_started.emit()
        
        success_count = 0
        error_count = 0
        
        try:
            # Get pending sync items
            sync_items = self._get_sync_queue_items()
            
            for item in sync_items:
                try:
                    # Process sync item
                    success = self._process_sync_item(item)
                    
                    if success:
                        success_count += 1
                        self._mark_sync_item_completed(item['id'])
                    else:
                        error_count += 1
                        self._increment_retry_count(item['id'])
                        
                except Exception as e:
                    error_count += 1
                    self._increment_retry_count(item['id'])
                    print(f"Sync item error: {e}")
                    
            # Sync pending blink data
            pending_records = self.data_manager.pending_records.copy()
            if pending_records:
                try:
                    self.data_manager.sync_pending_records()
                    success_count += len(pending_records)
                except Exception as e:
                    error_count += len(pending_records)
                    print(f"Blink data sync error: {e}")
                    
        except Exception as e:
            self.sync_error.emit(str(e))
            
        finally:
            self.sync_in_progress = False
            self.sync_completed.emit(success_count, error_count)
            
    def _get_sync_queue_items(self) -> List[Dict[str, Any]]:
        """Get items from sync queue"""
        try:
            with sqlite3.connect(self.data_manager.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, endpoint, method, data, retry_count, last_attempt
                    FROM sync_queue 
                    WHERE retry_count < 5
                    ORDER BY created_at ASC
                    LIMIT 50
                """)
                
                columns = [desc[0] for desc in cursor.description]
                items = []
                
                for row in cursor.fetchall():
                    item = dict(zip(columns, row))
                    item['data'] = json.loads(item['data'])
                    items.append(item)
                    
                return items
                
        except Exception as e:
            print(f"Error getting sync queue items: {e}")
            return []
            
    def _process_sync_item(self, item: Dict[str, Any]) -> bool:
        """Process a single sync queue item"""
        try:
            endpoint = item['endpoint']
            method = item['method']
            data = item['data']
            
            # Map method string to HTTPMethod enum
            from utils.api_client import HTTPMethod
            
            method_map = {
                'GET': HTTPMethod.GET,
                'POST': HTTPMethod.POST,
                'PUT': HTTPMethod.PUT,
                'DELETE': HTTPMethod.DELETE
            }
            
            http_method = method_map.get(method)
            if not http_method:
                return False
                
            # Make API request
            response = self.api_client.request(http_method, endpoint, data)
            
            return response.success
            
        except Exception as e:
            print(f"Error processing sync item: {e}")
            return False
            
    def _mark_sync_item_completed(self, item_id: int):
        """Mark sync item as completed and remove from queue"""
        try:
            with sqlite3.connect(self.data_manager.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM sync_queue WHERE id = ?", (item_id,))
                conn.commit()
        except Exception as e:
            print(f"Error marking sync item completed: {e}")
            
    def _increment_retry_count(self, item_id: int):
        """Increment retry count for failed sync item"""
        try:
            with sqlite3.connect(self.data_manager.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE sync_queue 
                    SET retry_count = retry_count + 1, 
                        last_attempt = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (item_id,))
                conn.commit()
        except Exception as e:
            print(f"Error incrementing retry count: {e}")
            
    def force_sync(self):
        """Force immediate synchronization"""
        if not self.sync_in_progress:
            self.sync_pending_data()
            
    def get_sync_status(self) -> Dict[str, Any]:
        """Get current sync status"""
        try:
            with sqlite3.connect(self.data_manager.db_path) as conn:
                cursor = conn.cursor()
                
                # Count pending items
                cursor.execute("SELECT COUNT(*) FROM sync_queue WHERE retry_count < 5")
                pending_count = cursor.fetchone()[0]
                
                # Count failed items
                cursor.execute("SELECT COUNT(*) FROM sync_queue WHERE retry_count >= 5")
                failed_count = cursor.fetchone()[0]
                
                # Count unsynced blink data
                cursor.execute("SELECT COUNT(*) FROM blink_data WHERE synced = FALSE")
                unsynced_blinks = cursor.fetchone()[0]
                
                return {
                    "online": self.is_online,
                    "sync_in_progress": self.sync_in_progress,
                    "pending_items": pending_count,
                    "failed_items": failed_count,
                    "unsynced_blinks": unsynced_blinks,
                    "pending_records": len(self.data_manager.pending_records)
                }
                
        except Exception as e:
            print(f"Error getting sync status: {e}")
            return {
                "online": False,
                "sync_in_progress": False,
                "pending_items": 0,
                "failed_items": 0,
                "unsynced_blinks": 0,
                "pending_records": 0
            }
