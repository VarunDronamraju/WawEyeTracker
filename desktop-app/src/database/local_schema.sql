-- Local SQLite schema for offline storage

-- Local blink data with sync tracking
CREATE TABLE local_blink_data (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    timestamp INTEGER NOT NULL,
    blink_count INTEGER NOT NULL,
    confidence_score REAL DEFAULT 1.0,
    eye_strain_score REAL,
    interval_seconds INTEGER DEFAULT 60,
    synced BOOLEAN DEFAULT FALSE,
    sync_attempts INTEGER DEFAULT 0,
    created_at INTEGER NOT NULL
);

-- Sync queue for offline operations
CREATE TABLE sync_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    endpoint TEXT NOT NULL,
    method TEXT NOT NULL,
    payload TEXT NOT NULL,
    headers TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 5,
    next_retry INTEGER,
    created_at INTEGER NOT NULL,
    status TEXT DEFAULT 'pending' -- 'pending', 'success', 'failed'
);

-- Local sessions tracking
CREATE TABLE local_sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    device_id TEXT NOT NULL,
    start_time INTEGER NOT NULL,
    end_time INTEGER,
    total_blinks INTEGER DEFAULT 0,
    app_version TEXT,
    os_info TEXT,
    synced BOOLEAN DEFAULT FALSE,
    created_at INTEGER NOT NULL
);

-- User preferences and settings
CREATE TABLE user_settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at INTEGER NOT NULL
);

-- GDPR consent tracking
CREATE TABLE consent_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    consent_type TEXT NOT NULL,
    consent_given BOOLEAN NOT NULL,
    timestamp INTEGER NOT NULL,
    version TEXT NOT NULL
);

-- Create indexes for performance
CREATE INDEX idx_local_blink_session ON local_blink_data(session_id, timestamp);
CREATE INDEX idx_local_blink_sync ON local_blink_data(synced, created_at);
CREATE INDEX idx_sync_queue_status ON sync_queue(status, next_retry);
CREATE INDEX idx_local_sessions_user ON local_sessions(user_id, start_time DESC);