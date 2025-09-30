import whisper
import openai
import os
import json
import re
from datetime import datetime, timedelta
from dotenv import load_dotenv
from typing import List, Dict, Optional

# Load environment variables
load_dotenv()

# Initialize models
whisper_model = whisper.load_model("base")

# Set OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

class MeetingTranscriber:
    """Enhanced meeting transcription with AI-powered analysis"""
    
    def __init__(self):
        self.whisper_model = whisper_model
        self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    def transcribe_audio(self, file_path: str, language: str = "en") -> Dict:
        """
        Transcribe audio file with timestamps and speaker detection
        """
        try:
            print(f"🎙️ Transcribing audio file: {file_path}")
            
            # Transcribe with Whisper
            result = self.whisper_model.transcribe(
                file_path,
                language=language if language != "auto" else None,
                word_timestamps=True,
                verbose=False
            )
            
            # Process segments for better speaker detection
            processed_segments = self._process_segments(result["segments"])
            
            return {
                "full_text": result["text"],
                "segments": processed_segments,
                "language": result.get("language", language),
                "duration": result.get("duration", 0)
            }
            
        except Exception as e:
            print(f"❌ Error transcribing audio: {e}")
            return {"full_text": "", "segments": [], "language": language, "duration": 0}
    
    def _process_segments(self, segments: List) -> List[Dict]:
        """Process segments and assign speakers"""
        processed = []
        current_speaker = 1
        last_end_time = 0
        
        for i, segment in enumerate(segments):
            # Simple speaker detection based on timing gaps
            if segment["start"] - last_end_time > 2.0:  # 2+ second gap
                current_speaker = 2 if current_speaker == 1 else 1
            
            processed.append({
                "speaker": f"Speaker {current_speaker}",
                "start_time": segment["start"],
                "end_time": segment["end"],
                "text": segment["text"].strip(),
                "confidence": segment.get("avg_logprob", 0.0)
            })
            
            last_end_time = segment["end"]
        
        return processed
    
    def summarize_meeting(self, transcript: str, meeting_title: str = "Meeting") -> Dict:
        """
        Generate AI-powered meeting summary with key points
        """
        try:
            print("📝 Generating meeting summary...")
            
            prompt = f"""
            Please analyze this meeting transcript and provide a comprehensive summary:

            MEETING: {meeting_title}
            TRANSCRIPT: {transcript}

            Please provide:
            1. A brief executive summary (2-3 sentences)
            2. Key discussion points (bullet points)
            3. Important decisions made
            4. Main participants and their contributions
            5. Topics that need follow-up

            Format your response as JSON with these keys:
            - executive_summary
            - key_points (array)
            - decisions (array)
            - participants (array)
            - follow_up_topics (array)
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1500,
                temperature=0.7
            )
            
            # Parse JSON response
            summary_text = response.choices[0].message.content
            try:
                summary = json.loads(summary_text)
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                summary = {
                    "executive_summary": summary_text[:500] + "...",
                    "key_points": [],
                    "decisions": [],
                    "participants": [],
                    "follow_up_topics": []
                }
            
            return summary
            
        except Exception as e:
            print(f"❌ Error generating summary: {e}")
            return {
                "executive_summary": "Error generating summary",
                "key_points": [],
                "decisions": [],
                "participants": [],
                "follow_up_topics": []
            }
    
    def extract_action_items(self, transcript: str, participants: List[str] = None) -> List[Dict]:
        """
        Extract action items with deadlines and assignees
        """
        try:
            print("✅ Extracting action items...")
            
            participants_list = participants or ["Team Member"]
            participants_str = ", ".join(participants_list)
            
            prompt = f"""
            Analyze this meeting transcript and extract all action items, tasks, and follow-ups mentioned.

            TRANSCRIPT: {transcript}
            KNOWN PARTICIPANTS: {participants_str}

            For each action item, identify:
            1. What needs to be done (clear, actionable description)
            2. Who should do it (assign to a participant if mentioned, otherwise "Unassigned")
            3. When it should be done (extract or infer deadline, default to 1 week if not specified)
            4. Priority level (High/Medium/Low based on urgency indicators)
            5. Category (Research, Development, Communication, Decision, etc.)

            Return as JSON array with objects containing:
            - title: Brief action item title
            - description: Detailed description
            - assignee: Person responsible
            - due_date: Date in YYYY-MM-DD format
            - priority: High/Medium/Low
            - category: Action type
            - context: Relevant meeting context

            Current date: {datetime.now().strftime('%Y-%m-%d')}
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
                temperature=0.3
            )
            
            # Parse JSON response
            action_items_text = response.choices[0].message.content
            try:
                action_items = json.loads(action_items_text)
                if not isinstance(action_items, list):
                    action_items = []
            except json.JSONDecodeError:
                # Fallback: extract action items using regex patterns
                action_items = self._extract_action_items_fallback(transcript)
            
            # Add generated IDs and timestamps
            for i, item in enumerate(action_items):
                item["id"] = i + 1
                item["status"] = "pending"
                item["created_at"] = datetime.now().isoformat()
            
            return action_items
            
        except Exception as e:
            print(f"❌ Error extracting action items: {e}")
            return []
    
    def _extract_action_items_fallback(self, transcript: str) -> List[Dict]:
        """Fallback method to extract action items using regex patterns"""
        action_patterns = [
            r"(?:need to|should|must|will|going to|action item|todo|task)\s+(.+?)(?:\.|$)",
            r"([A-Za-z\s]+)\s+(?:will|should|needs to)\s+(.+?)(?:\.|$)",
            r"follow up (?:on|with)\s+(.+?)(?:\.|$)",
            r"by\s+(\w+day|\d+/\d+|\d+-\d+-\d+|next week|tomorrow).*?([^.]+)"
        ]
        
        action_items = []
        for pattern in action_patterns:
            matches = re.finditer(pattern, transcript, re.IGNORECASE)
            for match in matches:
                action_items.append({
                    "title": match.group(1)[:100] if match.group(1) else "Follow-up Item",
                    "description": match.group(0),
                    "assignee": "Unassigned",
                    "due_date": (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'),
                    "priority": "Medium",
                    "category": "Follow-up",
                    "context": "Extracted from transcript"
                })
        
        return action_items[:10]  # Limit to 10 items
    
    def generate_meeting_report(self, audio_file: str, meeting_title: str = "Meeting", 
                              language: str = "en", participants: List[str] = None) -> Dict:
        """
        Complete meeting analysis: transcription, summary, and action items
        """
        print(f"🚀 Starting comprehensive meeting analysis for: {meeting_title}")
        
        # Step 1: Transcribe audio
        transcription_result = self.transcribe_audio(audio_file, language)
        
        if not transcription_result["full_text"]:
            return {"error": "Failed to transcribe audio"}
        
        # Step 2: Generate summary
        summary = self.summarize_meeting(transcription_result["full_text"], meeting_title)
        
        # Step 3: Extract action items
        action_items = self.extract_action_items(
            transcription_result["full_text"], 
            participants or summary.get("participants", [])
        )
        
        # Step 4: Compile complete report
        report = {
            "meeting_info": {
                "title": meeting_title,
                "date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "duration_minutes": round(transcription_result["duration"] / 60, 1),
                "language": transcription_result["language"],
                "participants": summary.get("participants", [])
            },
            "transcription": {
                "full_text": transcription_result["full_text"],
                "segments": transcription_result["segments"]
            },
            "summary": summary,
            "action_items": action_items,
            "stats": {
                "total_segments": len(transcription_result["segments"]),
                "total_action_items": len(action_items),
                "high_priority_items": len([item for item in action_items if item.get("priority") == "High"])
            }
        }
        
        print(f"✅ Analysis complete! Found {len(action_items)} action items")
        return report
    
    def save_report(self, report: Dict, output_file: str = None):
        """Save meeting report to JSON file"""
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"meeting_report_{timestamp}.json"
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            print(f"📄 Report saved to: {output_file}")
            return output_file
        except Exception as e:
            print(f"❌ Error saving report: {e}")
            return None


# Main function for command-line usage
def main():
    """Main function to run meeting transcription from command line"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python transcribe.py <audio_file> [meeting_title] [language]")
        print("Example: python transcribe.py meeting.mp3 'Sprint Planning' en")
        return
    
    audio_file = sys.argv[1]
    meeting_title = sys.argv[2] if len(sys.argv) > 2 else "Meeting"
    language = sys.argv[3] if len(sys.argv) > 3 else "en"
    
    # Check if audio file exists
    if not os.path.exists(audio_file):
        print(f"❌ Audio file not found: {audio_file}")
        return
    
    # Initialize transcriber
    transcriber = MeetingTranscriber()
    
    # Generate complete report
    report = transcriber.generate_meeting_report(
        audio_file=audio_file,
        meeting_title=meeting_title,
        language=language
    )
    
    if "error" in report:
        print(f"❌ {report['error']}")
        return
    
    # Save report
    output_file = transcriber.save_report(report)
    
    # Print summary
    print("\n" + "="*60)
    print(f"📊 MEETING ANALYSIS SUMMARY")
    print("="*60)
    print(f"Title: {report['meeting_info']['title']}")
    print(f"Duration: {report['meeting_info']['duration_minutes']} minutes")
    print(f"Language: {report['meeting_info']['language']}")
    print(f"Action Items: {report['stats']['total_action_items']}")
    print(f"High Priority: {report['stats']['high_priority_items']}")
    
    print(f"\n📝 Executive Summary:")
    print(f"   {report['summary']['executive_summary']}")
    
    print(f"\n✅ Top Action Items:")
    for i, item in enumerate(report['action_items'][:3], 1):
        print(f"   {i}. {item['title']} - Due: {item['due_date']} ({item['priority']} priority)")
    
    print(f"\n📄 Full report saved to: {output_file}")


if __name__ == "__main__":
    main()   