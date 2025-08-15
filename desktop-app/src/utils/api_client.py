import requests
import json
import time
from typing import Dict, Any, Optional, List
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class APIClient:
    """API client for communicating with cloud backend"""
    
    def __init__(self, base_url: str = "https://api.wellnessatwork.com"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.auth_token = None
        self.refresh_token = None
        
        # Setup retry strategy
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            method_whitelist=["HEAD", "GET", "OPTIONS", "POST", "PUT"],
            backoff_factor=1
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Default headers
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'WellnessAtWork/1.0'
        })
    
    def set_auth_token(self, token: str, refresh_token: str = None):
        """Set authentication token"""
        self.auth_token = token
        self.refresh_token = refresh_token
        self.session.headers.update({
            'Authorization': f'Bearer {token}'
        })
    
    def login(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Login and get auth tokens"""
        try:
            response = self.session.post(f"{self.base_url}/api/auth/login", json={
                'email': email,
                'password': password
            })
            
            if response.status_code == 200:
                data = response.json()
                self.set_auth_token(data['access_token'], data.get('refresh_token'))
                return data
            else:
                return None
                
        except Exception as e:
            print(f"Login failed: {e}")
            return None
    
    def refresh_auth_token(self) -> bool:
        """Refresh authentication token"""
        if not self.refresh_token:
            return False
        
        try:
            response = self.session.post(f"{self.base_url}/api/auth/refresh", json={
                'refresh_token': self.refresh_token
            })
            
            if response.status_code == 200:
                data = response.json()
                self.set_auth_token(data['access_token'], data.get('refresh_token'))
                return True
            else:
                return False
                
        except Exception as e:
            print(f"Token refresh failed: {e}")
            return False
    
    def get(self, endpoint: str, params: Dict[str, Any] = None) -> Optional[requests.Response]:
        """Make GET request"""
        try:
            response = self.session.get(f"{self.base_url}{endpoint}", params=params)
            return self._handle_response(response)
        except Exception as e:
            print(f"GET request failed: {e}")
            return None
    
    def post(self, endpoint: str, data: Dict[str, Any] = None) -> Optional[requests.Response]:
        """Make POST request"""
        try:
            response = self.session.post(f"{self.base_url}{endpoint}", json=data)
            return self._handle_response(response)
        except Exception as e:
            print(f"POST request failed: {e}")
            return None
    
    def put(self, endpoint: str, data: Dict[str, Any] = None) -> Optional[requests.Response]:
        """Make PUT request"""
        try:
            response = self.session.put(f"{self.base_url}{endpoint}", json=data)
            return self._handle_response(response)
        except Exception as e:
            print(f"PUT request failed: {e}")
            return None
    
    def delete(self, endpoint: str) -> Optional[requests.Response]:
        """Make DELETE request"""
        try:
            response = self.session.delete(f"{self.base_url}{endpoint}")
            return self._handle_response(response)
        except Exception as e:
            print(f"DELETE request failed: {e}")
            return None
    
    def _handle_response(self, response: requests.Response) -> Optional[requests.Response]:
        """Handle API response with token refresh"""
        if response.status_code == 401 and self.refresh_token:
            # Try to refresh token
            if self.refresh_auth_token():
                # Retry the original request
                return response
        
        return response if response.status_code < 400 else None
    
    def check_health(self) -> bool:
        """Check API health"""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False