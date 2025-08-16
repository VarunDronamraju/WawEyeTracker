#!/usr/bin/env python3
"""
Wellness at Work API - Curl Commands Generator
Generates all curl commands for manual API testing
"""

import json
import uuid
from datetime import datetime, timedelta

def generate_curl_commands():
    """Generate all curl commands for API testing"""
    
    base_url = "http://localhost:8000"
    test_email = f"testuser_{uuid.uuid4().hex[:8]}@example.com"
    test_password = "TestPass123!"
    
    print("="*80)
    print("🔧 WELLNESS AT WORK API - CURL COMMANDS")
    print("="*80)
    print(f"Base URL: {base_url}")
    print(f"Test Email: {test_email}")
    print(f"Test Password: {test_password}")
    print("="*80)
    
    # Store tokens and session ID for later use
    access_token = "YOUR_ACCESS_TOKEN_HERE"  # Will be updated after login
    refresh_token = "YOUR_REFRESH_TOKEN_HERE"  # Will be updated after login
    session_id = "YOUR_SESSION_ID_HERE"  # Will be updated after session creation
    
    commands = []
    
    # 1. HEALTH CHECK
    print("\n🏥 HEALTH CHECK ENDPOINTS")
    print("-" * 40)
    
    commands.append({
        "name": "Health Check",
        "command": f"curl -X GET {base_url}/health -H 'Content-Type: application/json' -v"
    })
    
    commands.append({
        "name": "OpenAPI Schema",
        "command": f"curl -X GET {base_url}/api/openapi.json -H 'Content-Type: application/json' -v"
    })
    
    # 2. AUTHENTICATION
    print("\n🔐 AUTHENTICATION ENDPOINTS")
    print("-" * 40)
    
    register_data = {
        "email": test_email,
        "password": test_password,
        "consent_gdpr": True,
        "data_retention_days": 365
    }
    
    commands.append({
        "name": "User Registration",
        "command": f"curl -X POST {base_url}/api/auth/register \\\n  -H 'Content-Type: application/json' \\\n  -d '{json.dumps(register_data)}' \\\n  -v"
    })
    
    login_data = {
        "email": test_email,
        "password": test_password
    }
    
    commands.append({
        "name": "User Login",
        "command": f"curl -X POST {base_url}/api/auth/login \\\n  -H 'Content-Type: application/json' \\\n  -d '{json.dumps(login_data)}' \\\n  -v"
    })
    
    commands.append({
        "name": "Get Current User",
        "command": f"curl -X GET {base_url}/api/auth/me \\\n  -H 'Content-Type: application/json' \\\n  -H 'Authorization: Bearer {access_token}' \\\n  -v"
    })
    
    refresh_data = {
        "refresh_token": refresh_token
    }
    
    commands.append({
        "name": "Refresh Token",
        "command": f"curl -X POST {base_url}/api/auth/refresh \\\n  -H 'Content-Type: application/json' \\\n  -d '{json.dumps(refresh_data)}' \\\n  -v"
    })
    
    # 3. BLINK TRACKING
    print("\n👁️ BLINK TRACKING ENDPOINTS")
    print("-" * 40)
    
    session_data = {
        "device_id": f"test_device_{uuid.uuid4().hex[:8]}",
        "app_version": "1.0.0",
        "os_info": {
            "platform": "Windows",
            "version": "10.0.26100",
            "architecture": "x64"
        }
    }
    
    commands.append({
        "name": "Start Session",
        "command": f"curl -X POST {base_url}/api/blink/sessions \\\n  -H 'Content-Type: application/json' \\\n  -H 'Authorization: Bearer {access_token}' \\\n  -d '{json.dumps(session_data)}' \\\n  -v"
    })
    
    commands.append({
        "name": "Get User Sessions",
        "command": f"curl -X GET {base_url}/api/blink/sessions \\\n  -H 'Content-Type: application/json' \\\n  -H 'Authorization: Bearer {access_token}' \\\n  -v"
    })
    
    commands.append({
        "name": "Get Session",
        "command": f"curl -X GET {base_url}/api/blink/sessions/{session_id} \\\n  -H 'Content-Type: application/json' \\\n  -H 'Authorization: Bearer {access_token}' \\\n  -v"
    })
    
    # Blink batch data
    blink_data = [
        {
            "timestamp": datetime.now().isoformat(),
            "blink_count": 15,
            "confidence_score": 0.95,
            "eye_strain_score": 0.3,
            "interval_seconds": 60
        },
        {
            "timestamp": (datetime.now() + timedelta(minutes=1)).isoformat(),
            "blink_count": 12,
            "confidence_score": 0.92,
            "eye_strain_score": 0.4,
            "interval_seconds": 60
        }
    ]
    
    batch_data = {
        "session_id": session_id,
        "blink_data": blink_data
    }
    
    commands.append({
        "name": "Upload Blink Batch",
        "command": f"curl -X POST {base_url}/api/blink/sessions/{session_id}/blinks/batch \\\n  -H 'Content-Type: application/json' \\\n  -H 'Authorization: Bearer {access_token}' \\\n  -d '{json.dumps(batch_data)}' \\\n  -v"
    })
    
    commands.append({
        "name": "Get Session Data",
        "command": f"curl -X GET {base_url}/api/blink/sessions/{session_id}/data \\\n  -H 'Content-Type: application/json' \\\n  -H 'Authorization: Bearer {access_token}' \\\n  -v"
    })
    
    commands.append({
        "name": "Get User Analytics",
        "command": f"curl -X GET {base_url}/api/blink/analytics \\\n  -H 'Content-Type: application/json' \\\n  -H 'Authorization: Bearer {access_token}' \\\n  -v"
    })
    
    commands.append({
        "name": "End Session",
        "command": f"curl -X PUT {base_url}/api/blink/sessions/{session_id}/end \\\n  -H 'Content-Type: application/json' \\\n  -H 'Authorization: Bearer {access_token}' \\\n  -v"
    })
    
    # 4. GDPR COMPLIANCE
    print("\n📋 GDPR COMPLIANCE ENDPOINTS")
    print("-" * 40)
    
    commands.append({
        "name": "Get Data Summary",
        "command": f"curl -X GET {base_url}/api/gdpr/data-summary \\\n  -H 'Content-Type: application/json' \\\n  -H 'Authorization: Bearer {access_token}' \\\n  -v"
    })
    
    consent_data = {
        "consent_gdpr": True,
        "data_retention_days": 180
    }
    
    commands.append({
        "name": "Update Consent",
        "command": f"curl -X PUT {base_url}/api/gdpr/consent \\\n  -H 'Content-Type: application/json' \\\n  -H 'Authorization: Bearer {access_token}' \\\n  -d '{json.dumps(consent_data)}' \\\n  -v"
    })
    
    commands.append({
        "name": "Export User Data",
        "command": f"curl -X GET {base_url}/api/gdpr/export \\\n  -H 'Content-Type: application/json' \\\n  -H 'Authorization: Bearer {access_token}' \\\n  -v"
    })
    
    commands.append({
        "name": "Delete All User Data (DANGEROUS!)",
        "command": f"curl -X DELETE {base_url}/api/gdpr/delete-all-data \\\n  -H 'Content-Type: application/json' \\\n  -H 'Authorization: Bearer {access_token}' \\\n  -v"
    })
    
    # 5. LOGOUT
    print("\n🚪 LOGOUT ENDPOINTS")
    print("-" * 40)
    
    commands.append({
        "name": "Logout User",
        "command": f"curl -X POST {base_url}/api/auth/logout \\\n  -H 'Content-Type: application/json' \\\n  -H 'Authorization: Bearer {access_token}' \\\n  -v"
    })
    
    # 6. ERROR CASES
    print("\n⚠️ ERROR CASE TESTS")
    print("-" * 40)
    
    invalid_login = {
        "email": "invalid@example.com",
        "password": "wrongpassword"
    }
    
    commands.append({
        "name": "Invalid Login",
        "command": f"curl -X POST {base_url}/api/auth/login \\\n  -H 'Content-Type: application/json' \\\n  -d '{json.dumps(invalid_login)}' \\\n  -v"
    })
    
    commands.append({
        "name": "Access Without Token",
        "command": f"curl -X GET {base_url}/api/auth/me \\\n  -H 'Content-Type: application/json' \\\n  -v"
    })
    
    commands.append({
        "name": "Invalid Session ID",
        "command": f"curl -X GET {base_url}/api/blink/sessions/invalid-session-id \\\n  -H 'Content-Type: application/json' \\\n  -H 'Authorization: Bearer {access_token}' \\\n  -v"
    })
    
    # Print all commands
    for i, cmd in enumerate(commands, 1):
        print(f"\n{i:2d}. {cmd['name']}")
        print("-" * 50)
        print(cmd['command'])
        print()
    
    # Print usage instructions
    print("\n" + "="*80)
    print("📝 USAGE INSTRUCTIONS")
    print("="*80)
    print("1. Start your backend server on http://localhost:8000")
    print("2. Run the commands in order (some depend on previous results)")
    print("3. After login, update the access_token variable with your actual token")
    print("4. After creating a session, update the session_id variable")
    print("5. For PowerShell, replace 'curl' with 'Invoke-RestMethod'")
    print("\nExample PowerShell command:")
    print("Invoke-RestMethod -Uri 'http://localhost:8000/health' -Method GET")
    print("="*80)

if __name__ == "__main__":
    generate_curl_commands()
