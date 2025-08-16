from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import jwt

from ...database.connection import get_db
from ...models.models import User, BlinkSession, BlinkData
from ...models.schemas import BlinkSessionCreate, BlinkDataCreate, BlinkSessionResponse
from ...utils.config import settings

router = APIRouter(prefix="/blink", tags=["blink tracking"])
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
    except Exception as e:
        print(f"Auth error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

@router.post("/sessions", response_model=BlinkSessionResponse)
async def start_session(
    session_data: BlinkSessionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Start a new blink tracking session"""
    try:
        session = BlinkSession(
            user_id=current_user.id,
            device_id=session_data.device_id,
            app_version=session_data.app_version,
            os_info=str(session_data.os_info) if session_data.os_info else None,
            start_time=datetime.utcnow()
        )
        
        db.add(session)
        db.commit()
        db.refresh(session)
        
        return session
    except Exception as e:
        db.rollback()
        print(f"Session creation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create session"
        )

@router.get("/sessions")
async def get_user_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 10,
    offset: int = 0
):
    """Get user's blink tracking sessions"""
    try:
        sessions = db.query(BlinkSession).filter(
            BlinkSession.user_id == current_user.id
        ).offset(offset).limit(limit).all()
        
        return sessions
    except Exception as e:
        print(f"Get sessions error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve sessions"
        )

@router.get("/sessions/{session_id}")
async def get_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific session details"""
    try:
        session = db.query(BlinkSession).filter(
            BlinkSession.id == session_id,
            BlinkSession.user_id == current_user.id
        ).first()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        return session
    except HTTPException:
        raise
    except Exception as e:
        print(f"Get session error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve session"
        )

@router.get("/analytics")
async def get_user_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's blink analytics"""
    try:
        # Get basic stats
        total_sessions = db.query(BlinkSession).filter(BlinkSession.user_id == current_user.id).count()
        total_blinks = db.query(BlinkData).join(BlinkSession).filter(
            BlinkSession.user_id == current_user.id
        ).count()
        
        return {
            "user_id": current_user.id,
            "total_sessions": total_sessions,
            "total_blinks": total_blinks,
            "average_blinks_per_session": total_blinks / total_sessions if total_sessions > 0 else 0
        }
    except Exception as e:
        print(f"Analytics error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve analytics"
        )
