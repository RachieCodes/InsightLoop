"""
Zoom OAuth Integration Example for InsightLoop
Shows how to automatically transcribe Zoom meetings using OAuth
"""
import asyncio
from datetime import datetime, timedelta
from zoom_integration import ZoomOAuthConnector, ZoomMeetingManager


async def demo_zoom_oauth_integration():
    """Demonstrate Zoom OAuth integration capabilities"""
    
    print("🔄 InsightLoop Zoom OAuth Integration Demo")
    print("=" * 50)
    
    # Initialize Zoom connector
    zoom = ZoomOAuthConnector()
    manager = ZoomMeetingManager()
    
    # Check if we're authenticated
    if not zoom.load_tokens():
        print("❌ Not authenticated with Zoom")
        print("Run: python zoom_integration.py auth")
        return
    
    try:
        # 1. List upcoming meetings
        print("\n📅 Listing upcoming meetings...")
        meetings = manager.list_upcoming_meetings()
        
        # 2. Enable auto-recording for all meetings
        print("\n🎬 Enabling auto-recording...")
        manager.enable_auto_transcription()
        
        # 3. Create a test meeting (optional)
        print("\n➕ Creating test meeting...")
        start_time = datetime.now() + timedelta(hours=1)
        meeting = zoom.create_meeting(
            topic="InsightLoop Demo Meeting",
            start_time=start_time,
            duration_minutes=30,
            auto_record=True
        )
        
        if meeting:
            print(f"✅ Meeting created!")
            print(f"   Join URL: {meeting.get('join_url')}")
            print(f"   Meeting ID: {meeting.get('id')}")
            print(f"   Password: {meeting.get('password', 'N/A')}")
        
        # 4. Start monitoring (this would run continuously)
        print("\n🔍 Ready for meeting monitoring...")
        print("   (Use 'python zoom_integration.py monitor' to start)")
        print("   This will listen for meeting events and auto-transcribe")
        
    except Exception as e:
        print(f"❌ Error in demo: {e}")
        print("\n💡 Make sure you have:")
        print("   1. Valid Zoom OAuth credentials in .env")
        print("   2. Completed authentication flow")
        print("   3. Internet connection")


def setup_oauth_guide():
    """Show OAuth setup guide"""
    
    print("🛠️ Zoom OAuth Setup Guide")
    print("=" * 40)
    print("""
To use Zoom OAuth integration:

1. 📝 Create OAuth App:
   • Go to https://marketplace.zoom.us/develop/create
   • Choose "OAuth" app type
   • Configure redirect URI: http://localhost:8080/oauth/callback

2. 🔑 Get OAuth Credentials:
   • Copy Client ID and Client Secret
   • Add to your .env file:
     ZOOM_CLIENT_ID=your_client_id
     ZOOM_CLIENT_SECRET=your_client_secret

3. � Authenticate:
   • Run: python zoom_integration.py auth
   • Follow browser instructions
   • Copy authorization code when prompted

4. ✅ Test Integration:
   • python zoom_integration.py list
   • python zoom_integration.py enable
   
📖 Full guide: python oauth_setup_guide.py
    """)


def quick_oauth_meeting_transcription():
    """Quick example for transcribing existing Zoom recordings with OAuth"""
    
    print("⚡ Quick Zoom Recording Transcription (OAuth)")
    print("=" * 50)
    
    zoom = ZoomOAuthConnector()
    
    # Check authentication
    if not zoom.load_tokens():
        print("❌ Not authenticated. Run: python zoom_integration.py auth")
        return
    
    try:
        # Get recent meetings
        meetings = zoom.get_user_meetings(meeting_type="live")
        
        if not meetings:
            print("No live meetings found. Checking recent meetings...")
            meetings = zoom.get_user_meetings()
        
        for meeting in meetings[:3]:  # Check last 3 meetings
            meeting_id = meeting.get("id")
            topic = meeting.get("topic", "Untitled")
            
            print(f"\n🔍 Checking recordings for: {topic}")
            
            # Get recordings
            recordings = zoom.get_meeting_recordings(meeting_id)
            
            if recordings:
                print(f"   Found {len(recordings)} recording(s)")
                
                for recording in recordings:
                    if recording.get("file_type") in ["MP4", "M4A"]:
                        download_url = recording.get("download_url")
                        
                        if download_url:
                            # Download and transcribe
                            filename = f"zoom_{meeting_id}_{recording.get('file_type', 'mp4').lower()}"
                            
                            if zoom.download_recording(
                                download_url, 
                                zoom.access_token, 
                                filename
                            ):
                                print(f"   📁 Downloaded: {filename}")
                                print(f"   🎙️ Starting transcription...")
                                
                                # Use our transcription service
                                from transcribe import MeetingTranscriber
                                
                                transcriber = MeetingTranscriber()
                                report = transcriber.generate_meeting_report(
                                    audio_file=filename,
                                    meeting_title=topic
                                )
                                
                                if "error" not in report:
                                    output_file = transcriber.save_report(report)
                                    print(f"   ✅ Analysis complete: {output_file}")
                                else:
                                    print(f"   ❌ Transcription failed: {report['error']}")
            else:
                print(f"   No recordings found for this meeting")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        if "401" in str(e) or "403" in str(e):
            print("Authentication issue. Try: python zoom_integration.py auth")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "demo":
            asyncio.run(demo_zoom_oauth_integration())
        elif command == "setup":
            setup_oauth_guide()
        elif command == "quick":
            quick_oauth_meeting_transcription()
        else:
            print(f"Unknown command: {command}")
    else:
        print("""
🔄 InsightLoop Zoom OAuth Integration Examples

Commands:
  python zoom_example.py demo    # Full OAuth integration demo
  python zoom_example.py setup   # OAuth setup guide
  python zoom_example.py quick   # Quick transcription of existing recordings

Setup Steps:
  1. python oauth_setup_guide.py              # Detailed setup guide
  2. python zoom_integration.py auth          # Authenticate with Zoom
  3. python zoom_integration.py list          # Test authentication

Features:
  ✅ OAuth 2.0 authentication (secure)
  ✅ Automatic meeting recording
  ✅ Real-time transcription when meetings end
  ✅ Action item extraction
  ✅ Meeting summaries
        """)