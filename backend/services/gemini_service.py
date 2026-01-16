import google.generativeai as genai
import json
import os
from config import Config

genai.configure(api_key=Config.GOOGLE_API_KEY)

def analyze_audio(audio_path: str) -> dict:
    """
    Uploads audio to Gemini and extracts structured presentation data.
    """
    model = genai.GenerativeModel('gemini-1.5-flash')
    
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
