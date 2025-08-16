from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Dict, Any
import jwt
import json
from datetime import datetime

from ...database.connection import get_db
from ...models.models import User, BlinkSession, BlinkData, DataOperation
from ...utils.config import settings

router = APIRouter(prefix="/gdpr", tags=["GDPR compliance"])
security = HTTPBearer(auto_error=False)

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)) -> User:
    """Get current authenticated user"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization token required"
        )
    
    try:
        token = credentials.credentials
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

@router.get("/data-summary")
async def get_data_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get summary of user's data"""
    try:
        sessions_count = db.query(BlinkSession).filter(BlinkSession.user_id == current_user.id).count()
        blink_data_count = db.query(BlinkData).join(BlinkSession).filter(
            BlinkSession.user_id == current_user.id
        ).count()
        
        return {
            "user_data": {
                "email": current_user.email,
                "created_at": current_user.created_at,
                "consent_gdpr": current_user.consent_gdpr
            },
            "tracking_data": {
                "total_sessions": sessions_count,
                "total_blink_records": blink_data_count
            }
        }
    except Exception as e:
        print(f"Data summary error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve data summary"
        )

@router.put("/consent")
async def update_consent(
    consent_data: Dict[str, bool],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update GDPR consent"""
    try:
        current_user.consent_gdpr = consent_data.get("consent_gdpr", False)
        current_user.consent_timestamp = datetime.utcnow()
        current_user.updated_at = datetime.utcnow()
        
        db.commit()
        
        return {"message": "Consent updated successfully", "consent_gdpr": current_user.consent_gdpr}
    except Exception as e:
        db.rollback()
        print(f"Consent update error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update consent"
        )

@router.get("/export")
async def export_user_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export all user data"""
    try:
        # Get all user sessions
        sessions = db.query(BlinkSession).filter(BlinkSession.user_id == current_user.id).all()
        
        # Get all blink data
        blink_data = db.query(BlinkData).join(BlinkSession).filter(
            BlinkSession.user_id == current_user.id
        ).all()
        
        export_data = {
            "user_profile": {
                "id": current_user.id,
                "email": current_user.email,
                "consent_gdpr": current_user.consent_gdpr,
                "created_at": current_user.created_at.isoformat(),
                "last_login": current_user.last_login.isoformat() if current_user.last_login else None
            },
            "sessions": [
                {
                    "id": session.id,
                    "device_id": session.device_id,
                    "start_time": session.start_time.isoformat(),
                    "end_time": session.end_time.isoformat() if session.end_time else None,
                    "total_blinks": session.total_blinks
                }
                for session in sessions
            ],
            "blink_data": [
                {
                    "session_id": data.session_id,
                    "timestamp": data.timestamp.isoformat(),
                    "blink_count": data.blink_count,
                    "confidence_score": data.confidence_score
                }
                for data in blink_data
            ]
        }
        
        return export_data
    except Exception as e:
        print(f"Export error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export data"
        )
