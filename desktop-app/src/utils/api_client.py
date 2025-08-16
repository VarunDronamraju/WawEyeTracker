"""
API Client - Backend communication with retry logic and error handling
Handles all API calls to the cloud backend
"""

import requests
import time
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

class HTTPMethod(Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"

@dataclass
class APIResponse:
    """API response wrapper"""
    success: bool
    status_code: int
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class APIClient:
    """Client for backend API communication"""
    
    def __init__(self, config, auth_manager):
        self.config = config
        self.auth_manager = auth_manager
        self.base_url = config.api_base_url
        self.timeout = config.api_timeout
        self.max_retries = 3
        self.retry_delay = 1.0
        
    def request(
        self, 
        method: HTTPMethod, 
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        authenticated: bool = True,
        retries: int = None
    ) -> APIResponse:
        """Make HTTP request with retry logic"""
        
        if retries is None:
            retries = self.max_retries
            
        url = f"{self.base_url}{endpoint}"
        
        # Prepare headers
        request_headers = {"Content-Type": "application/json"}
        if headers:
            request_headers.update(headers)
            
        # Add authentication if required
        if authenticated:
            auth_headers = self.auth_manager.get_auth_headers()
            request_headers.update(auth_headers)
            
        for attempt in range(retries + 1):
            try:
                # Make request
                if method == HTTPMethod.GET:
                    response = requests.get(url, headers=request_headers, timeout=self.timeout)
                elif method == HTTPMethod.POST:
                    response = requests.post(url, json=data, headers=request_headers, timeout=self.timeout)
                elif method == HTTPMethod.PUT:
                    response = requests.put(url, json=data, headers=request_headers, timeout=self.timeout)
                elif method == HTTPMethod.DELETE:
                    response = requests.delete(url, headers=request_headers, timeout=self.timeout)
                else:
                    return APIResponse(False, 400, error="Invalid HTTP method")
                    
                # Handle authentication errors
                if response.status_code == 401 and authenticated:
                    # Try to refresh token
                    if self.auth_manager.refresh_access_token():
                        # Retry with new token
                        auth_headers = self.auth_manager.get_auth_headers()
                        request_headers.update(auth_headers)
                        continue
                    else:
                        return APIResponse(False, 401, error="Authentication failed")
                        
                # Handle success
                if 200 <= response.status_code < 300:
                    try:
                        data = response.json() if response.content else {}
                        return APIResponse(True, response.status_code, data)
                    except json.JSONDecodeError:
                        return APIResponse(True, response.status_code, {})
                        
                # Handle client errors (don't retry)
                if 400 <= response.status_code < 500:
                    try:
                        error_data = response.json()
                        error_msg = error_data.get("detail", f"HTTP {response.status_code}")
                    except json.JSONDecodeError:
                        error_msg = f"HTTP {response.status_code}"
                    return APIResponse(False, response.status_code, error=error_msg)
                    
                # Handle server errors (retry)
                if response.status_code >= 500 and attempt < retries:
                    time.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff
                    continue
                    
                # Final attempt failed
                return APIResponse(False, response.status_code, error=f"HTTP {response.status_code}")
                
            except requests.exceptions.Timeout:
                if attempt < retries:
                    time.sleep(self.retry_delay)
                    continue
                return APIResponse(False, 408, error="Request timeout")
                
            except requests.exceptions.ConnectionError:
                if attempt < retries:
                    time.sleep(self.retry_delay)
                    continue
                return APIResponse(False, 0, error="Connection error")
                
            except Exception as e:
                return APIResponse(False, 0, error=str(e))
                
        return APIResponse(False, 0, error="Max retries exceeded")
        
    # Convenience methods for specific endpoints
    
    def login(self, email: str, password: str) -> APIResponse:
        """Login user"""
        return self.request(
            HTTPMethod.POST, 
            "/auth/login",
            {"email": email, "password": password},
            authenticated=False
        )
        
    def logout(self) -> APIResponse:
        """Logout user"""
        return self.request(HTTPMethod.POST, "/auth/logout")
        
    def refresh_token(self, refresh_token: str) -> APIResponse:
        """Refresh access token"""
        return self.request(
            HTTPMethod.POST,
            "/auth/refresh",
            {"refresh_token": refresh_token},
            authenticated=False
        )
        
    def create_session(self, session_data: Dict[str, Any]) -> APIResponse:
        """Create new tracking session"""
        return self.request(HTTPMethod.POST, "/sessions", session_data)
        
    def update_session(self, session_id: str, session_data: Dict[str, Any]) -> APIResponse:
        """Update tracking session"""
        return self.request(HTTPMethod.PUT, f"/sessions/{session_id}", session_data)
        
    def upload_blink_data(self, session_id: str, blink_data: List[Dict[str, Any]]) -> APIResponse:
        """Upload batch of blink data"""
        return self.request(
            HTTPMethod.POST, 
            f"/sessions/{session_id}/blinks/batch",
            {"blinks": blink_data}
        )
        
    def get_user_profile(self) -> APIResponse:
        """Get user profile"""
        return self.request(HTTPMethod.GET, "/user/profile")
        
    def update_gdpr_consent(self, consent: bool) -> APIResponse:
        """Update GDPR consent"""
        return self.request(HTTPMethod.PUT, "/user/consent", {"gdpr_consent": consent})
        
    def export_user_data(self) -> APIResponse:
        """Export user data for GDPR compliance"""
        return self.request(HTTPMethod.GET, "/gdpr/export")
        
    def delete_user_data(self) -> APIResponse:
        """Delete all user data"""
        return self.request(HTTPMethod.DELETE, "/user/data")
        
    def get_analytics(self, time_range: str = "week") -> APIResponse:
        """Get user analytics"""
        return self.request(HTTPMethod.GET, f"/analytics?range={time_range}")
        
    def health_check(self) -> APIResponse:
        """Check API health"""
        return self.request(HTTPMethod.GET, "/health", authenticated=False)