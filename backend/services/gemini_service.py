import json
import os
from config import Config

# Safe import for Gemini
try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    print("Warning: google.generativeai not installed or failed to import.")
    HAS_GEMINI = False

if HAS_GEMINI and Config.GOOGLE_API_KEY:
    try:
        genai.configure(api_key=Config.GOOGLE_API_KEY)
    except Exception as e:
        print(f"Error configuring Gemini: {e}")

def analyze_audio(audio_path: str) -> dict:
    """
    Uploads audio to Gemini and extracts structured presentation data.
    """
    if not HAS_GEMINI:
        return {
            "title": "System Error",
            "slides": [{"title": "Gemini Library Missing", "bullet_points": ["The AI library failed to load."], "speaker_notes": "Check server logs."}]
        }

    try:
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        
        # Upload the file
        audio_file = genai.upload_file(path=audio_path)
        
        prompt = """
        Analyze this audio as a presentation expert. 
        Return a VALID JSON object (do not wrap in markdown code blocks) with the following structure:
        {
            "title": "Presentation Title",
            "slides": [
                {
                    "title": "Slide Title",
                    "bullet_points": ["Point 1", "Point 2", "Point 3"],
                    "speaker_notes": "Notes for the speaker"
                }
            ]
        }
        The tone should be professional. Ensure the output is pure JSON.
        """
        
        response = model.generate_content([prompt, audio_file])
        
        # Clean up response text if it contains markdown code blocks
        text = response.text
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
            
        if text.endswith("```"):
            text = text[:-3]
            
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            # Fallback or error handling
            print(f"Failed to decode JSON: {text}")
            return {
                "title": "Error Generating Presentation",
                "slides": [
                    {
                        "title": "Error",
                        "bullet_points": ["Could not parse AI response."],
                        "speaker_notes": f"Raw response: {text}"
                    }
                ]
            }
            
    except Exception as e:
        print(f"Error in analyze_audio: {e}")
        return {
            "title": "Processing Error",
            "slides": [
                {
                    "title": "AI Processing Failed",
                    "bullet_points": [str(e)],
                    "speaker_notes": "Check server logs for details."
                }
            ]
        }
