# InsightLoop
A comprehensive tool that transcribes meetings, summarizes key points, and auto-generates action items with deadlines

## 🎯 Use Case: 
Remote teams and freelancers use it to stay aligned without rewatching hour-long Zoom calls or long YouTube videos

## ✨ Features:
- **Real-time transcription** with speaker diarization
- **AI-powered summaries** with key points extraction
- **Automatic action item generation** with deadlines and assignees
- **Multi-language support** with auto-detection
- **Slack/Notion integration** ready (coming soon)
- **JSON export** for easy integration

## 🚀 Quick Start

### 1. Setup
```bash
# Clone and enter directory
cd InsightLoop

# Install dependencies
pip install openai openai-whisper python-dotenv

# Set up your OpenAI API key
cp .env.example .env
# Edit .env and add your OpenAI API key
```

### 2. Basic Usage
```bash
# Transcribe and analyze a meeting
python transcribe.py meeting.mp3 "Sprint Planning" en

# Or use in Python
from transcribe import MeetingTranscriber

transcriber = MeetingTranscriber()
report = transcriber.generate_meeting_report(
    audio_file="meeting.mp3",
    meeting_title="Team Standup",
    language="en"
)
```

### 3. What You Get
- **Complete transcript** with speaker identification
- **Executive summary** of the meeting
- **Key discussion points** and decisions
- **Action items** with:
  - Clear descriptions
  - Assigned team members
  - Due dates
  - Priority levels
  - Categories

## 📁 Output Example
```json
{
  "meeting_info": {
    "title": "Sprint Planning",
    "date": "2024-01-15 14:30:00",
    "duration_minutes": 45.2,
    "language": "en"
  },
  "summary": {
    "executive_summary": "Team discussed Q1 objectives...",
    "key_points": ["Discussed new feature requirements", "..."],
    "decisions": ["Approved budget increase", "..."]
  },
  "action_items": [
    {
      "title": "Prepare user research report",
      "assignee": "Alice",
      "due_date": "2024-01-22",
      "priority": "High",
      "category": "Research"
    }
  ]
}
```

## 🎙️ Supported Formats
- Audio: MP3, WAV, M4A, FLAC, OGG
- Video: MP4, MOV, AVI (audio extracted automatically)
- Languages: 20+ languages with auto-detection

## 🔧 Advanced Usage

### Custom Analysis
```python
transcriber = MeetingTranscriber()

# Step-by-step analysis
transcript = transcriber.transcribe_audio("meeting.mp3")
summary = transcriber.summarize_meeting(transcript["full_text"])
action_items = transcriber.extract_action_items(transcript["full_text"])
```

### Batch Processing
```python
import os
for audio_file in os.listdir("meetings/"):
    if audio_file.endswith(('.mp3', '.wav')):
        report = transcriber.generate_meeting_report(f"meetings/{audio_file}")
        transcriber.save_report(report, f"reports/{audio_file}.json")
```


## 🛠️ Coming Soon
- [ ] Real-time transcription from microphone
- [ ] Slack integration for automatic posting
- [ ] Notion database sync
- [ ] Web interface
- [ ] Custom AI models
- [ ] Speaker identification improvements

## 📝 Requirements
- Python 3.8+
- OpenAI API key
- ~2GB disk space for Whisper models
- Internet connection for AI analysis

