from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str
    consent_gdpr: bool = False

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(UserBase):
    id: str
    consent_gdpr: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    user_id: str

class TokenData(BaseModel):
    user_id: Optional[str] = None

class BlinkDataCreate(BaseModel):
    session_id: str
    timestamp: datetime
    blink_count: int
    confidence_score: Optional[float] = 1.0

class BlinkSessionCreate(BaseModel):
    device_id: str
    app_version: Optional[str] = None
    os_info: Optional[dict] = None

class BlinkSessionResponse(BaseModel):
    id: str
    user_id: str
    device_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    total_blinks: int
    
    class Config:
        from_attributes = True
