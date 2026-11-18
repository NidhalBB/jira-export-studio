#!/usr/bin/env python3
"""
Debug script to test Jira connection without the web app.
Run this to verify your Jira credentials work.
"""

import base64
import sys
import requests

def test_jira_connection(base_url, email, api_token):
    """Test Jira API connection with the provided credentials."""
    
    print(f"\n🔍 Testing Jira Connection")
    print(f"   URL: {base_url}")
    print(f"   Email: {email}")
    print(f"   Token: {'*' * (len(api_token) - 4) + api_token[-4:]}\n")
    
    # Validate inputs
    if not base_url.startswith(("http://", "https://")):
        print("❌ ERROR: Base URL must start with http:// or https://")
        return False
    
    if not email or "@" not in email:
        print("❌ ERROR: Invalid email address")
        return False
    
    if not api_token:
        print("❌ ERROR: API token is empty")
        return False
    
    # Create session with auth
    try:
        base_url = base_url.rstrip("/")
        auth_b64 = base64.b64encode(f"{email}:{api_token}".encode()).decode()
        
        headers = {
            "Authorization": f"Basic {auth_b64}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        
        # Test the connection
        print("📡 Sending test request to /rest/api/3/myself...")
        response = requests.get(
            f"{base_url}/rest/api/3/myself",
            headers=headers,
            timeout=10,
            verify=True  # Enable SSL verification
        )
        
        print(f"   Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ SUCCESS! Connected as: {data.get('displayName', 'Unknown')}")
            print(f"   Email: {data.get('emailAddress', 'Unknown')}")
            print(f"   Account ID: {data.get('accountId', 'Unknown')}")
            return True
        elif response.status_code == 401:
            print(f"\n❌ ERROR: Unauthorized (401)")
            print(f"   Your credentials are incorrect.")
            print(f"   - Check your email address")
            print(f"   - Check your API token")
            print(f"   - Verify the token hasn't expired")
            return False
        elif response.status_code == 403:
            print(f"\n❌ ERROR: Forbidden (403)")
            print(f"   You don't have permission to access this Jira instance.")
            return False
        elif response.status_code == 404:
            print(f"\n❌ ERROR: Not Found (404)")
            print(f"   The Jira URL might be incorrect.")
            print(f"   Got: {base_url}")
            return False
        else:
            print(f"\n❌ ERROR: Unexpected status code {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
            
    except requests.exceptions.SSLError as e:
        print(f"\n❌ ERROR: SSL Certificate Error")
        print(f"   This might be due to corporate network settings or proxy.")
        print(f"   Details: {str(e)[:100]}")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"\n❌ ERROR: Connection Error")
        print(f"   Cannot reach the Jira URL. Check the domain and network.")
        print(f"   Details: {str(e)[:100]}")
        return False
    except requests.exceptions.Timeout:
        print(f"\n❌ ERROR: Connection Timeout")
        print(f"   The Jira server took too long to respond.")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {type(e).__name__}")
        print(f"   {str(e)}")
        return False


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python debug_connection.py <base_url> <email> <api_token>")
        print("\nExample:")
        print("  python debug_connection.py https://mycompany.atlassian.net user@example.com my_api_token_123")
        sys.exit(1)
    
    base_url = sys.argv[1]
    email = sys.argv[2]
    api_token = sys.argv[3]
    
    success = test_jira_connection(base_url, email, api_token)
    sys.exit(0 if success else 1)
