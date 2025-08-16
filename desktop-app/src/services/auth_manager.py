"""
Authentication Manager - JWT token management and user authentication
Handles login, logout, token refresh, and GDPR consent
"""

import json
import keyring
import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from dataclasses import dataclass

@dataclass
class User:
    """User data class"""
    id: str
    email: str
    gdpr_consent: bool = False
    consent_timestamp: Optional[datetime] = None

class AuthManager:
    """Manages user authentication and session"""
    
    def __init__(self, config):
        self.config = config
        self.current_user: Optional[User] = None
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None
        
        # Load saved tokens
        self.load_stored_tokens()
        
    def login(self, email: str, password: str) -> bool:
        """Authenticate user with email and password"""
        try:
            response = requests.post(
                f"{self.config.api_base_url}/auth/login",
                json={"email": email, "password": password},
                timeout=self.config.api_timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Store tokens
                self.access_token = data["access_token"]
                self.refresh_token = data["refresh_token"]
                self.token_expires_at = datetime.now() + timedelta(seconds=data["expires_in"])
                
                # Store user info
                user_data = data["user"]
                self.current_user = User(
                    id=user_data["id"],
                    email=user_data["email"],
                    gdpr_consent=user_data.get("gdpr_consent", False),
                    consent_timestamp=datetime.fromisoformat(user_data["consent_timestamp"]) 
                    if user_data.get("consent_timestamp") else None
                )
                
                # Save tokens securely
                self.store_tokens()
                
                return True
            else:
                return False
                
        except Exception as e:
            print(f"Login error: {e}")
            return False
            
    def logout(self):
        """Logout user and clear tokens"""
        try:
            if self.access_token:
                # Notify server of logout
                requests.post(
                    f"{self.config.api_base_url}/auth/logout",
                    headers={"Authorization": f"Bearer {self.access_token}"},
                    timeout=self.config.api_timeout
                )
        except Exception:
            pass  # Ignore logout errors
            
        # Clear local data
        self.current_user = None
        self.access_token = None
        self.refresh_token = None
        self.token_expires_at = None
        
        # Clear stored tokens
        self.clear_stored_tokens()
        
    def refresh_access_token(self) -> bool:
        """Refresh access token using refresh token"""
        if not self.refresh_token:
            return False
            
        try:
            response = requests.post(
                f"{self.config.api_base_url}/auth/refresh",
                json={"refresh_token": self.refresh_token},
                timeout=self.config.api_timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                
                self.access_token = data["access_token"]
                self.token_expires_at = datetime.now() + timedelta(seconds=data["expires_in"])
                
                # Update refresh token if provided
                if "refresh_token" in data:
                    self.refresh_token = data["refresh_token"]
                    
                # Save updated tokens
                self.store_tokens()
                
                return True
            else:
                # Refresh failed, need to login again
                self.logout()
                return False
                
        except Exception as e:
            print(f"Token refresh error: {e}")
            return False
            
    def is_authenticated(self) -> bool:
        """Check if user is currently authenticated"""
        if not self.access_token or not self.current_user:
            return False
            
        # Check if token is expired
        if self.token_expires_at and datetime.now() >= self.token_expires_at:
            # Try to refresh token
            return self.refresh_access_token()
            
        return True
        
    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """Get current user data"""
        if self.current_user:
            return {
                "id": self.current_user.id,
                "email": self.current_user.email,
                "gdpr_consent": self.current_user.gdpr_consent,
                "consent_timestamp": self.current_user.consent_timestamp.isoformat() 
                if self.current_user.consent_timestamp else None
            }
        return None
        
    def get_auth_headers(self) -> Dict[str, str]:
        """Get headers for authenticated API requests"""
        if self.access_token:
            return {"Authorization": f"Bearer {self.access_token}"}
        return {}
        
    def has_gdpr_consent(self) -> bool:
        """Check if user has provided GDPR consent"""
        return self.current_user.gdpr_consent if self.current_user else False
        
    def set_gdpr_consent(self, consent: bool) -> bool:
        """Set GDPR consent status"""
        if not self.current_user:
            return False
            
        try:
            response = requests.put(
                f"{self.config.api_base_url}/user/consent",
                json={"gdpr_consent": consent},
                headers=self.get_auth_headers(),
                timeout=self.config.api_timeout
            )
            
            if response.status_code == 200:
                self.current_user.gdpr_consent = consent
                self.current_user.consent_timestamp = datetime.now()
                return True
            else:
                return False
                
        except Exception as e:
            print(f"GDPR consent error: {e}")
            return False
            
    def store_tokens(self):
        """Store tokens securely using keyring"""
        try:
            service_name = "WellnessAtWork"
            username = self.current_user.email if self.current_user else "default"
            
            token_data = {
                "access_token": self.access_token,
                "refresh_token": self.refresh_token,
                "expires_at": self.token_expires_at.isoformat() if self.token_expires_at else None,
                "user": {
                    "id": self.current_user.id,
                    "email": self.current_user.email,
                    "gdpr_consent": self.current_user.gdpr_consent,
                    "consent_timestamp": self.current_user.consent_timestamp.isoformat() 
                    if self.current_user.consent_timestamp else None
                } if self.current_user else None
            }
            
            keyring.set_password(service_name, username, json.dumps(token_data))
            
        except Exception as e:
            print(f"Error storing tokens: {e}")
            
    def load_stored_tokens(self):
        """Load stored tokens from keyring"""
        try:
            service_name = "WellnessAtWork"
            
            # Try to get stored data (we don't know the username yet)
            # This is a limitation - in production, you might store username separately
            stored_data = keyring.get_password(service_name, "default")
            
            if stored_data:
                token_data = json.loads(stored_data)
                
                self.access_token = token_data.get("access_token")
                self.refresh_token = token_data.get("refresh_token")
                
                if token_data.get("expires_at"):
                    self.token_expires_at = datetime.fromisoformat(token_data["expires_at"])
                    
                if token_data.get("user"):
                    user_data = token_data["user"]
                    self.current_user = User(
                        id=user_data["id"],
                        email=user_data["email"],
                        gdpr_consent=user_data.get("gdpr_consent", False),
                        consent_timestamp=datetime.fromisoformat(user_data["consent_timestamp"]) 
                        if user_data.get("consent_timestamp") else None
                    )
                    
        except Exception as e:
            print(f"Error loading stored tokens: {e}")
            
    def clear_stored_tokens(self):
        """Clear stored tokens from keyring"""
        try:
            service_name = "WellnessAtWork"
            username = self.current_user.email if self.current_user else "default"
            
            keyring.delete_password(service_name, username)
            
        except Exception as e:
            print(f"Error clearing stored tokens: {e}")
