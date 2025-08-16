from pydantic import BaseModel, EmailStr, validator
from typing import Optional, Dict, Any
from datetime import datetime
import uuid

class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr

class UserCreate(UserBase):
    """User creation schema"""
    password: str
    consent_gdpr: bool = False
    data_retention_days: int = 365
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v

class UserLogin(BaseModel):
    """User login schema"""
    email: EmailStr
    password: str

class UserResponse(UserBase):
    """User response schema"""
    id: uuid.UUID
    consent_gdpr: bool
    consent_timestamp: Optional[datetime]
    data_retention_days: int
    created_at: datetime
    last_login: Optional[datetime]
    is_active: bool
    is_verified: bool
    
    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    """User update schema"""
    email: Optional[EmailStr] = None
    consent_gdpr: Optional[bool] = None
    data_retention_days: Optional[int] = None

class TokenResponse(BaseModel):
    """Token response schema"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class TokenRefresh(BaseModel):
    """Token refresh schema"""
    refresh_token: str