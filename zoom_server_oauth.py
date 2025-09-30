"""
Zoom Server-to-Server OAuth Integration for InsightLoop
No app activation required - works immediately!
"""
import os
import json
import asyncio
import requests
import base64
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()


class ZoomServerToServerConnector:
    """
    Zoom integration using Server-to-Server OAuth
    No browser authentication required!
    """
    
    def __init__(self):
        self.account_id = os.getenv("ZOOM_ACCOUNT_ID")
        self.client_id = os.getenv("ZOOM_CLIENT_ID")
        self.client_secret = os.getenv("ZOOM_CLIENT_SECRET")
        self.base_url = "https://api.zoom.us/v2"
        self.oauth_url = "https://zoom.us/oauth/token"
        self.access_token = None
        self.token_expires = None
        
    def get_access_token(self) -> str:
        """Get access token using Server-to-Server OAuth"""
        
        # Check if current token is still valid
        if self.access_token and self.token_expires and datetime.now() < self.token_expires:
            return self.access_token
        
        if not all([self.account_id, self.client_id, self.client_secret]):
            raise ValueError("""
❌ Missing Zoom Server-to-Server OAuth credentials!

Please add these to your .env file:
ZOOM_ACCOUNT_ID=your_account_id
ZOOM_CLIENT_ID=your_client_id  
ZOOM_CLIENT_SECRET=your_client_secret

Get these from: https://marketplace.zoom.us/develop/create
Choose "Server-to-Server OAuth" app type.
            """)
        
        try:
            # Create basic auth header
            credentials = f"{self.client_id}:{self.client_secret}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            
            headers = {
                'Authorization': f'Basic {encoded_credentials}',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            data = {
                'grant_type': 'account_credentials',
                'account_id': self.account_id
            }
            
            response = requests.post(self.oauth_url, headers=headers, data=data)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data.get('access_token')
            expires_in = token_data.get('expires_in', 3600)
            self.token_expires = datetime.now() + timedelta(seconds=expires_in - 60)  # Refresh 1 min early
            
            print("✅ Successfully authenticated with Zoom!")
            return self.access_token
            
        except requests.exceptions.HTTPError as e:
            error_response = e.response.json() if e.response.content else {}
            error_message = error_response.get('message', str(e))
            error_code = error_response.get('code', 'Unknown')
            
            print(f"❌ Authentication failed: {error_message} (Code: {error_code})")
            
            if "Invalid client" in error_message:
                print("💡 Check your Client ID and Client Secret in .env")
            elif "Invalid account" in error_message:
                print("💡 Check your Account ID in .env")
            elif "4700" in str(error_code):
                print("💡 Make sure you created a 'Server-to-Server OAuth' app, not regular OAuth")
            
            raise
        except Exception as e:
            print(f"❌ Error getting access token: {e}")
            raise
    
    def get_headers(self) -> Dict:
        """Get authenticated headers for API requests"""
        return {
            'Authorization': f'Bearer {self.get_access_token()}',
            'Content-Type': 'application/json'
        }
    
    def test_connection(self) -> bool:
        """Test the connection to Zoom API"""
        try:
            url = f"{self.base_url}/users/me"
            response = requests.get(url, headers=self.get_headers())
            response.raise_for_status()
            
            user_data = response.json()
            email = user_data.get('email', 'Unknown')
            account_id = user_data.get('account_id', 'Unknown')
            
            print(f"✅ Connection successful!")
            print(f"   Account: {email}")
            print(f"   Account ID: {account_id}")
            
            return True
            
        except Exception as e:
            print(f"❌ Connection test failed: {e}")
            return False
    
    def get_user_meetings(self, user_id: str = "me", meeting_type: str = "scheduled") -> List[Dict]:
        """Get list of user's meetings"""
        try:
            url = f"{self.base_url}/users/{user_id}/meetings"
            
            # Zoom API expects different parameter values
            type_mapping = {
                "scheduled": "scheduled",
                "upcoming": "scheduled", 
                "live": "live",
                "previous": "previous"
            }
            
            params = {
                "type": type_mapping.get(meeting_type, "scheduled"), 
                "page_size": 30
            }
            
            response = requests.get(url, headers=self.get_headers(), params=params)
            response.raise_for_status()
            
            data = response.json()
            meetings = data.get("meetings", [])
            
            # Filter for upcoming meetings if requested
            if meeting_type == "upcoming":
                now = datetime.now()
                meetings = [m for m in meetings if datetime.fromisoformat(m.get("start_time", "").replace("Z", "+00:00")) > now]
            
            return meetings
            
        except Exception as e:
            print(f"❌ Error fetching meetings: {e}")
            return []
    
    def enable_cloud_recording(self, meeting_id: str) -> bool:
        """Enable cloud recording for a meeting"""
        try:
            url = f"{self.base_url}/meetings/{meeting_id}"
            data = {
                "settings": {
                    "auto_recording": "cloud",
                    "recording_authentication": False,
                    "participant_video": True,
                    "host_video": True
                }
            }
            
            response = requests.patch(url, headers=self.get_headers(), json=data)
            response.raise_for_status()
            
            print(f"✅ Cloud recording enabled for meeting {meeting_id}")
            return True
            
        except Exception as e:
            print(f"❌ Error enabling recording: {e}")
            return False
    
    def create_meeting(self, topic: str, start_time: datetime, 
                      duration_minutes: int = 60, auto_record: bool = True) -> Optional[Dict]:
        """Create a new Zoom meeting with recording enabled"""
        try:
            url = f"{self.base_url}/users/me/meetings"
            
            # Format time for Zoom API (UTC timezone)
            start_time_str = start_time.strftime("%Y-%m-%dT%H:%M:%S") + "Z"
            
            data = {
                "topic": topic,
                "type": 2,  # Scheduled meeting
                "start_time": start_time_str,
                "duration": duration_minutes,
                "timezone": "UTC",
                "settings": {
                    "auto_recording": "cloud" if auto_record else "none",
                    "participant_video": True,
                    "host_video": True,
                    "join_before_host": False,
                    "mute_upon_entry": True,
                    "waiting_room": True,
                    "approval_type": 2  # No registration required
                }
            }
            
            response = requests.post(url, headers=self.get_headers(), json=data)
            response.raise_for_status()
            
            meeting_data = response.json()
            print(f"✅ Meeting created successfully!")
            print(f"   Topic: {meeting_data.get('topic')}")
            print(f"   Join URL: {meeting_data.get('join_url')}")
            print(f"   Meeting ID: {meeting_data.get('id')}")
            print(f"   Password: {meeting_data.get('password', 'None')}")
            
            return meeting_data
            
        except Exception as e:
            print(f"❌ Error creating meeting: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_details = e.response.json()
                    print(f"   Details: {error_details}")
                except:
                    print(f"   Response: {e.response.text}")
            return None
    
    def get_meeting_recordings(self, meeting_id: str) -> List[Dict]:
        """Get recordings for a specific meeting"""
        try:
            url = f"{self.base_url}/meetings/{meeting_id}/recordings"
            response = requests.get(url, headers=self.get_headers())
            response.raise_for_status()
            
            data = response.json()
            return data.get("recording_files", [])
            
        except Exception as e:
            print(f"❌ Error fetching recordings: {e}")
            return []
    
    def download_recording(self, download_url: str, output_path: str) -> bool:
        """Download recording file from Zoom"""
        try:
            headers = self.get_headers()
            response = requests.get(download_url, headers=headers, stream=True)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"✅ Recording downloaded to: {output_path}")
            return True
            
        except Exception as e:
            print(f"❌ Error downloading recording: {e}")
            return False


class ZoomServerToServerManager:
    """High-level manager for Zoom Server-to-Server integration"""
    
    def __init__(self):
        self.zoom = ZoomServerToServerConnector()
    
    def test_setup(self):
        """Test the complete setup"""
        print("🧪 Testing Zoom Server-to-Server OAuth Setup")
        print("=" * 50)
        
        try:
            # Test connection
            if self.zoom.test_connection():
                print("\n📅 Testing meeting list...")
                meetings = self.zoom.get_user_meetings()
                print(f"   Found {len(meetings)} meetings")
                
                print("\n✅ Setup test completed successfully!")
                print("   You can now use all Zoom integration features.")
                return True
            else:
                return False
                
        except Exception as e:
            print(f"❌ Setup test failed: {e}")
            return False
    
    def list_upcoming_meetings(self) -> List[Dict]:
        """Get and display upcoming meetings"""
        meetings = self.zoom.get_user_meetings(meeting_type="upcoming")
        
        print(f"📅 Found {len(meetings)} upcoming meetings:")
        for meeting in meetings:
            start_time = meeting.get("start_time", "")
            topic = meeting.get("topic", "Untitled")
            meeting_id = meeting.get("id", "")
            
            print(f"   • {topic}")
            print(f"     Time: {start_time}")
            print(f"     ID: {meeting_id}")
            print()
        
        return meetings
    
    def enable_auto_transcription(self, meeting_id: str = None):
        """Enable automatic transcription for meetings"""
        if meeting_id:
            # Enable for specific meeting
            self.zoom.enable_cloud_recording(meeting_id)
        else:
            # Enable for all upcoming meetings
            meetings = self.zoom.get_user_meetings(meeting_type="upcoming")
            for meeting in meetings:
                self.zoom.enable_cloud_recording(meeting.get("id"))
        
        print("✅ Auto-transcription enabled!")
    
    def create_test_meeting(self):
        """Create a test meeting"""
        start_time = datetime.now() + timedelta(hours=1)
        
        meeting = self.zoom.create_meeting(
            topic="InsightLoop Test Meeting",
            start_time=start_time,
            duration_minutes=30,
            auto_record=True
        )
        
        return meeting


# CLI interface
def main():
    """Command-line interface for Server-to-Server integration"""
    import sys
    
    if len(sys.argv) < 2:
        print("""
🚀 Zoom Server-to-Server OAuth Integration for InsightLoop

Usage:
  python zoom_server_oauth.py test       # Test setup
  python zoom_server_oauth.py list       # List upcoming meetings
  python zoom_server_oauth.py enable     # Enable recording for all meetings
  python zoom_server_oauth.py create     # Create test meeting

Setup:
  1. Create Server-to-Server OAuth app at https://marketplace.zoom.us/
  2. Add to .env file:
     ZOOM_ACCOUNT_ID=your_account_id
     ZOOM_CLIENT_ID=your_client_id
     ZOOM_CLIENT_SECRET=your_client_secret
  3. Run: python zoom_server_oauth.py test

✅ Benefits:
  • No app activation required
  • Works immediately  
  • No browser authentication
  • Perfect for automation
        """)
        return
    
    command = sys.argv[1].lower()
    manager = ZoomServerToServerManager()
    
    if command == "test":
        manager.test_setup()
    
    elif command == "list":
        manager.list_upcoming_meetings()
    
    elif command == "enable":
        manager.enable_auto_transcription()
    
    elif command == "create":
        meeting = manager.create_test_meeting()
        if meeting:
            print(f"\n🎉 Test meeting created!")
            print(f"Join at: {meeting.get('join_url')}")
    
    else:
        print(f"❌ Unknown command: {command}")


if __name__ == "__main__":
    main()