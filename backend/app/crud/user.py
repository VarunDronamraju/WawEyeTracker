from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import Optional, List
from datetime import datetime
import uuid

from ..models.models import User, RefreshToken, AuditLog
from ..schemas.user import UserCreate, UserUpdate
from ..utils.security import security_manager

class UserCRUD:
    """User CRUD operations"""
    
    def get_user_by_id(self, db: Session, user_id: uuid.UUID) -> Optional[User]:
        """Get user by ID"""
        return db.query(User).filter(User.id == user_id).first()
    
    def get_user_by_email(self, db: Session, email: str) -> Optional[User]:
        """Get user by email"""
        return db.query(User).filter(User.email == email).first()
    
    def create_user(self, db: Session, user: UserCreate) -> User:
        """Create new user"""
        salt = security_manager.generate_salt()
        password_hash = security_manager.hash_password(user.password, salt)
        
        db_user = User(
            email=user.email,
            password_hash=password_hash,
            salt=salt,
            consent_gdpr=user.consent_gdpr,
            consent_timestamp=datetime.utcnow() if user.consent_gdpr else None,
            data_retention_days=user.data_retention_days
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        # Log user creation
        self._log_event(db, db_user.id, "user_created", {"email": user.email})
        
        return db_user
    
    def authenticate_user(self, db: Session, email: str, password: str) -> Optional[User]:
        """Authenticate user"""
        user = self.get_user_by_email(db, email)
        if not user:
            return None
        
        if not security_manager.verify_password(password, user.salt, user.password_hash):
            # Log failed login
            self._log_event(db, user.id, "login_failed", {"email": email})
            return None
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.commit()
        
        # Log successful login
        self._log_event(db, user.id, "login_success", {"email": email})
        
        return user
    
    def update_user(self, db: Session, user_id: uuid.UUID, user_update: UserUpdate) -> Optional[User]:
        """Update user"""
        user = self.get_user_by_id(db, user_id)
        if not user:
            return None
        
        update_data = user_update.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(user, field, value)
        
        user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(user)
        
        # Log user update
        self._log_event(db, user_id, "user_updated", update_data)
        
        return user
    
    def delete_user(self, db: Session, user_id: uuid.UUID) -> bool:
        """Delete user (GDPR compliance)"""
        user = self.get_user_by_id(db, user_id)
        if not user:
            return False
        
        # Log deletion before removing user
        self._log_event(db, user_id, "user_deleted", {"email": user.email})
        
        db.delete(user)
        db.commit()
        return True
    
    def create_refresh_token(self, db: Session, user_id: uuid.UUID, token: str, expires_at: datetime) -> RefreshToken:
        """Create refresh token"""
        refresh_token = RefreshToken(
            user_id=user_id,
            token=token,
            expires_at=expires_at
        )
        
        db.add(refresh_token)
        db.commit()
        db.refresh(refresh_token)
        
        return refresh_token
    
    def get_refresh_token(self, db: Session, token: str) -> Optional[RefreshToken]:
        """Get refresh token"""
        return db.query(RefreshToken).filter(
            and_(
                RefreshToken.token == token,
                RefreshToken.is_revoked == False,
                RefreshToken.expires_at > datetime.utcnow()
            )
        ).first()
    
    def revoke_refresh_token(self, db: Session, token: str) -> bool:
        """Revoke refresh token"""
        refresh_token = db.query(RefreshToken).filter(RefreshToken.token == token).first()
        if refresh_token:
            refresh_token.is_revoked = True
            db.commit()
            return True
        return False
    
    def _log_event(self, db: Session, user_id: uuid.UUID, event_type: str, event_data: dict):
        """Log audit event"""
        audit_log = AuditLog(
            user_id=user_id,
            event_type=event_type,
            event_data=event_data
        )
        db.add(audit_log)
        db.commit()

user_crud = UserCRUD()