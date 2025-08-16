from pydantic import BaseModel, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

class BlinkDataPoint(BaseModel):
    """Single blink data point"""
    timestamp: datetime
    blink_count: int
    confidence_score: float = 1.0
    eye_strain_score: Optional[float] = None
    interval_seconds: int = 60
    
    @validator('blink_count')
    def validate_blink_count(cls, v):
        if v < 0 or v > 100:  # Reasonable bounds
            raise ValueError('Blink count must be between 0 and 100')
        return v
    
    @validator('confidence_score')
    def validate_confidence(cls, v):
        if v < 0.0 or v > 1.0:
            raise ValueError('Confidence score must be between 0.0 and 1.0')
        return v

class BlinkBatch(BaseModel):
    """Batch of blink data points"""
    session_id: uuid.UUID
    blink_data: List[BlinkDataPoint]
    
    @validator('blink_data')
    def validate_batch_size(cls, v):
        if len(v) > 1000:  # Limit batch size
            raise ValueError('Batch size cannot exceed 1000 points')
        return v

class SessionCreate(BaseModel):
    """Session creation schema"""
    device_id: str
    app_version: str
    os_info: Dict[str, Any]
    
    @validator('device_id')
    def validate_device_id(cls, v):
        if not v or len(v) > 100:
            raise ValueError('Device ID must be 1-100 characters')
        return v

class SessionUpdate(BaseModel):
    """Session update schema"""
    end_time: Optional[datetime] = None
    total_blinks: Optional[int] = None

class SessionResponse(BaseModel):
    """Session response schema"""
    id: uuid.UUID
    user_id: uuid.UUID
    device_id: str
    start_time: datetime
    end_time: Optional[datetime]
    session_duration_seconds: Optional[int]
    total_blinks: int
    app_version: Optional[str]
    os_info: Optional[Dict[str, Any]]
    created_at: datetime
    
    class Config:
        from_attributes = True

class BlinkDataResponse(BaseModel):
    """Blink data response schema"""
    id: uuid.UUID
    session_id: uuid.UUID
    timestamp: datetime
    blink_count: int
    confidence_score: float
    eye_strain_score: Optional[float]
    interval_seconds: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class AnalyticsResponse(BaseModel):
    """Analytics response schema"""
    user_id: uuid.UUID
    period: str
    total_sessions: int
    total_blinks: int
    average_blinks_per_minute: float
    average_session_duration: float
    eye_strain_average: Optional[float]
    trends: Dict[str, Any]