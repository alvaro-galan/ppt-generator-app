import json
import os
from config import Config
import time

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

    # List of models to try in order of preference
    # Updated based on availability logs (v1beta/v1)
    models_to_try = [
        'gemini-2.0-flash',
        'gemini-2.5-flash',
        'gemini-flash-latest',
        'gemini-1.5-pro-latest'
    ]
    
    last_error = None
    
    # Upload the file ONCE (it can be reused across model calls usually, but let's re-upload to be safe or just upload once)
    # Actually, upload_file returns a file object that is tied to the account.
    try:
        print(f"Uploading audio file: {audio_path}")
        audio_file = genai.upload_file(path=audio_path)
        print(f"Audio uploaded: {audio_file.name}")
    except Exception as upload_err:
        return {
            "title": "Upload Error",
            "slides": [{"title": "Audio Upload Failed", "bullet_points": [str(upload_err)], "speaker_notes": "Check API Key and Internet."}]
        }

    prompt = """
    ROLE: Eres un generador de contenido experto para presentaciones.
    INPUT: Recibirás un tema corto (ej: "Leones") o una transcripción.
    TASK: 
    1. Interpreta la solicitud del usuario.
    2. Diseña un estilo visual (colores, vibe) acorde al tema.
    3. Genera el contenido educativo Y define qué imagen debería acompañar a cada slide.
    
    OUTPUT FORMAT: Devuelve SOLO un JSON válido (sin markdown ```json) con esta estructura EXACTA:
    {
        "title": "Título de la presentación",
        "interpretation": "Breve resumen de la solicitud",
        "visual_style": {
            "background_color": "#HexColor (ej: #1a1a1a para dark mode, #f0f0f0 para light)",
            "text_color": "#HexColor (que contraste bien con el fondo)",
            "accent_color": "#HexColor (para títulos o destacados)",
            "vibe": "Descripción del estilo (ej: Minimalista, Salvaje, Corporativo)"
        },
        "slides": [
            {
                "title": "Título Slide 1",
                "bullet_points": ["Punto clave 1", "Punto clave 2", "Punto clave 3"],
                "image_query": "Descripción visual detallada en INGLÉS para generar una imagen (ej: 'Majestic lion roaring at sunset, realistic style, 4k')",
                "speaker_notes": "Notas para el orador detalladas."
            }
        ]
    }
    """

    for model_name in models_to_try:
        try:
            print(f"🔄 Trying Gemini Model: {model_name}...")
            model = genai.GenerativeModel(model_name)
            
            response = model.generate_content([prompt, audio_file])
            
            # If we get here, it worked! Process response
            text = response.text
            if text.startswith("```json"):
                text = text[7:]
            elif text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
                
            try:
                result = json.loads(text.strip())
                print(f"✅ Success with model: {model_name}")
                return result
            except json.JSONDecodeError:
                print(f"❌ Failed to decode JSON from {model_name}")
                last_error = f"JSON Decode Error with {model_name}"
                continue # Try next model if JSON fails (unlikely but possible)

        except Exception as e:
            print(f"⚠️ Model {model_name} failed: {e}")
            last_error = str(e)
            
            # Smart Retry for Rate Limits
            if "429" in str(e) or "quota" in str(e).lower():
                 print(f"⏳ Rate Limit Hit on {model_name}. Waiting 15 seconds before next model...")
                 time.sleep(15)
            else:
                 time.sleep(2)
            
            continue

    # If all models failed, try to list available models for debugging
    available_models_info = "Could not list models."
    try:
        available = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available.append(m.name)
        available_models_info = "Available: " + ", ".join(available)
    except Exception as list_err:
        available_models_info = f"List models failed: {list_err}"

    return {
        "title": "Processing Error",
        "slides": [
            {
                "title": "All AI Models Failed",
                "bullet_points": [
                    f"Last error: {last_error}", 
                    f"Tried: {', '.join(models_to_try)}",
                    f"Debug info: {available_models_info}"
                ],
                "speaker_notes": "Check server logs for details."
            }
        ]
    }
