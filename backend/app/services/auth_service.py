from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import jwt
import uuid
from typing import Optional
import traceback

from ..models.models import User
from ..models.schemas import UserCreate
from ..utils.security import security_manager
from ..utils.config import settings

class AuthService:
    def __init__(self):
        self.secret_key = settings.SECRET_KEY
        self.algorithm = settings.ALGORITHM
        self.access_token_expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire_days = settings.REFRESH_TOKEN_EXPIRE_DAYS

    def create_user(self, db: Session, user_data: UserCreate) -> User:
        """Create a new user with hashed password"""
        try:
            print(f"Creating user with email: {user_data.email}")
            
            # Generate salt and hash password
            salt = security_manager.generate_salt()
            print(f"Generated salt: {salt[:10]}...")
            
            password_hash = security_manager.hash_password(user_data.password, salt)
            print(f"Generated password hash: {password_hash[:20]}...")
            
            # Create user instance with explicit values
            user_id = str(uuid.uuid4())
            now = datetime.utcnow()
            
            user = User(
                id=user_id,
                email=user_data.email,
                password_hash=password_hash,
                salt=salt,
                consent_gdpr=user_data.consent_gdpr,
                consent_timestamp=now if user_data.consent_gdpr else None,
                created_at=now,
                updated_at=now,
                is_active=True,
                data_retention_days=365
            )
            
            print(f"User object created: {user.id}")
            
            # Save to database
            db.add(user)
            print("User added to session")
            
            db.commit()
            print("Database committed")
            
            db.refresh(user)
            print(f"User refreshed: {user.email}")
            
            return user
            
        except Exception as e:
            print(f"Error in create_user: {str(e)}")
            traceback.print_exc()
            db.rollback()
            raise Exception(f"Failed to create user: {str(e)}")

    def authenticate_user(self, db: Session, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password"""
        try:
            user = db.query(User).filter(User.email == email, User.is_active == True).first()
            if not user:
                return None
            
            # Verify password
            if security_manager.verify_password(password, user.salt, user.password_hash):
                return user
            
            return None
        except Exception as e:
            print(f"Authentication error: {str(e)}")
            return None

    def create_access_token(self, data: dict) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire, "type": "access"})
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def create_refresh_token(self, data: dict) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        to_encode.update({"exp": expire, "type": "refresh"})
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def verify_token(self, token: str) -> Optional[dict]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.JWTError:
            return None

    def get_user_by_id(self, db: Session, user_id: str) -> Optional[User]:
        """Get user by ID"""
        return db.query(User).filter(User.id == user_id, User.is_active == True).first()