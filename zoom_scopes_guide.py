"""
Zoom Scopes Configuration Guide
"""

def show_scopes_guide():
    print("🔧 Zoom App Scopes Configuration")
    print("=" * 40)
    print("""
✅ GOOD NEWS: Authentication is working perfectly!
❌ ISSUE: Your app needs additional scopes

🎯 REQUIRED SCOPES:
==================
You need to add these scopes to your Zoom app:

✅ meeting:read                    (for listing meetings)
✅ meeting:write                   (for creating meetings)  
✅ meeting:write:admin             (for advanced meeting management)
✅ recording:read                  (for accessing recordings)
✅ recording:write                 (for managing recordings)
✅ user:read                       (for user information)

🚀 HOW TO ADD SCOPES:
====================
1. Go to https://marketplace.zoom.us/user/build
2. Find your "InsightLoop" app and click "Manage"
3. Go to the "Scopes" tab
4. Add ALL the scopes listed above
5. Click "Done" 
6. Wait 1-2 minutes for changes to take effect

⚡ CURRENT STATUS:
=================
✅ Authentication: Working
✅ API Connection: Working  
❌ Meeting Creation: Missing scopes
❌ Meeting Listing: Missing scopes

🧪 TEST AFTER ADDING SCOPES:
============================
python zoom_server_oauth.py test
python zoom_server_oauth.py create
python zoom_server_oauth.py list

💡 NOTE: 
After adding scopes, you might need to wait 1-2 minutes 
for the changes to propagate through Zoom's systems.
    """)

def check_available_scopes():
    """Test what scopes are currently available"""
    import os
    import requests
    import base64
    from dotenv import load_dotenv
    
    load_dotenv()
    
    try:
        # Get access token to check scopes
        client_id = os.getenv("ZOOM_CLIENT_ID")
        client_secret = os.getenv("ZOOM_CLIENT_SECRET") 
        account_id = os.getenv("ZOOM_ACCOUNT_ID")
        
        credentials = f"{client_id}:{client_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        headers = {
            'Authorization': f'Basic {encoded_credentials}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'grant_type': 'account_credentials',
            'account_id': account_id
        }
        
        response = requests.post("https://zoom.us/oauth/token", headers=headers, data=data)
        response.raise_for_status()
        
        token_data = response.json()
        access_token = token_data.get('access_token')
        scope = token_data.get('scope', '')
        
        print("🔍 CURRENT SCOPES IN YOUR TOKEN:")
        print("=" * 35)
        if scope:
            scopes = scope.split(' ')
            for s in sorted(scopes):
                print(f"✅ {s}")
        else:
            print("❌ No scopes found in token")
        
        print(f"\n📊 Total scopes: {len(scopes) if scope else 0}")
        
        # Check what's missing
        required_scopes = [
            'meeting:read',
            'meeting:write', 
            'meeting:write:admin',
            'recording:read',
            'recording:write',
            'user:read'
        ]
        
        missing_scopes = [s for s in required_scopes if s not in scope]
        
        if missing_scopes:
            print(f"\n❌ MISSING REQUIRED SCOPES:")
            for s in missing_scopes:
                print(f"   • {s}")
            print(f"\nAdd these to your Zoom app configuration!")
        else:
            print(f"\n✅ All required scopes are present!")
            
    except Exception as e:
        print(f"❌ Error checking scopes: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "check":
        check_available_scopes()
    else:
        show_scopes_guide()
        print("\n" + "="*40)
        print("💡 Run 'python zoom_scopes_guide.py check' to see current scopes")