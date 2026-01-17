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
    # Updated based on user preference (2.5 worked best)
    models_to_try = [
        'gemini-2.5-flash',
        'gemini-2.0-flash',
        'gemini-flash-latest'
    ]
    
    last_error = None
    
    # Upload the file ONCE (it can be reused across model calls usually, but let's re-upload to be safe or just upload once)
    # Actually, upload_file returns a file object that is tied to the account.
    try:
        print(f"Uploading audio file: {audio_path}")
        audio_file = genai.upload_file(path=audio_path)
        print(f"Audio uploaded: {audio_file.name}")
        
        # Wait for file to be active
        while audio_file.state.name == "PROCESSING":
            print("⏳ Waiting for audio file to process...")
            time.sleep(2)
            audio_file = genai.get_file(audio_file.name)
            
        if audio_file.state.name == "FAILED":
             raise Exception("Audio file processing failed by Google")
             
    except Exception as upload_err:
        return {
            "title": "Upload Error",
            "slides": [{"title": "Audio Upload Failed", "bullet_points": [str(upload_err)], "speaker_notes": "Check API Key and Internet."}]
        }

    prompt = """
    ### ROL DEL SISTEMA
    Actúa como un Consultor de Estrategia Senior y Director Creativo de Agencia (estilo Ogilvy/McKinsey).
    Tu trabajo NO es explicar temas, sino VENDER ideas.

    ### INPUT
    Recibirás un archivo de audio. Tu tarea es analizarlo para extraer:
    1. TEMA PRINCIPAL (De qué se habla. Ej: "Leones")
    2. OBJETIVO DE LA PRESENTACIÓN (Qué se quiere conseguir. Ej: "Vender consultoría")
    Si no son explícitos, infiérelo del audio.

    ### INSTRUCCIONES DE "MOTOR DE METÁFORA" (CRÍTICO)
    Si el TEMA detectado es un objeto o animal (ej: "Leones", "Café", "Legos"):
    1. NO hagas una presentación educativa sobre el objeto.
    2. ÚSALO COMO METÁFORA para una solución de negocio B2B.
       - Ejemplo: "Leones" -> "Dominio de Mercado / Liderazgo".
       - Ejemplo: "Café" -> "Productividad y Energía Corporativa".
       - Ejemplo: "Legos" -> "Arquitectura Modular y Escalabilidad".

    ### REGLAS DE SEGURIDAD Y FORMATO
    1. IDIOMA: Estrictamente ESPAÑOL DE NEGOCIOS (Neutro/Profesional).
    2. CONCISIÓN: Prohibido usar párrafos de más de 2 líneas. Usa listas (Bullet points).
    3. TONO: Persuasivo, directo, orientado a ROI (Retorno de Inversión) y KPIs.

    ### ESTRUCTURA OBLIGATORIA (8 SLIDES)
    Genera exactamente 8 diapositivas siguiendo este flujo narrativo:

    --- SLIDE 1: EL GANCHO (PORTADA) ---
    - TÍTULO: (Máx 7 palabras. Potente. Ej: "Despierta la Rentabilidad")
    - SUBTÍTULO: (La promesa de valor)

    --- SLIDE 2: EL DOLOR (CONTEXTO) ---
    - TÍTULO: (Ej: "El Coste de la Ineficiencia")
    - PUNTOS DE DOLOR: (3 problemas actuales del mercado/cliente)
    - DATO DE IMPACTO: (Una cifra inventada realista sobre pérdidas)

    --- SLIDE 3: LA SOLUCIÓN (TU TEMA) ---
    - TÍTULO: (Presenta el producto/concepto)
    - BENEFICIOS: (Ventaja competitiva, ahorro, innovación)

    --- SLIDE 4: EVIDENCIA (DATOS) ---
    - TÍTULO: Resultados Proyectados
    - DATOS: (ROI, Ahorro de tiempo, Satisfacción)

    --- SLIDE 5: AUTORIDAD (COMPARATIVA) ---
    - TÍTULO: Por qué somos diferentes
    - COMPARATIVA: (Tradicional vs Nuestra Solución)

    --- SLIDE 6: EL EQUIPO / PROCESO ---
    - TÍTULO: Implementación sin Fricción
    - PASOS: (Auditoría, Despliegue, Optimización)

    --- SLIDE 7: CASOS DE USO ---
    - TÍTULO: Impacto Real
    - CONTENIDO: (Frase contundente / Testimonio)

    --- SLIDE 8: CIERRE (CTA) ---
    - TÍTULO: (Frase final inspiradora)
    - CALL TO ACTION: (Ej: "Agenda tu Demo")

    ### FORMATO DE SALIDA (JSON OBLIGATORIO)
    Devuelve SOLO un JSON válido con esta estructura:
    {
        "title": "Título de impacto (máx 7 palabras)",
        "interpretation": "Resumen del TEMA, OBJETIVO y AUDIENCIA detectados.",
        "visual_style": {
            "background_color": "#HexColor",
            "text_color": "#HexColor",
            "accent_color": "#HexColor",
            "vibe": "Descripción del estilo (ej: Minimalista, Salvaje, Corporativo)"
        },
        "slides": [
            {
                "title": "Título Slide (Orientado a la acción)",
                "layout_type": "Title Only | 2 Columns | Image & Text | 3 Big Numbers | Comparison Table | 4 Steps Process | Testimonial | Minimalist Center",
                "bullet_points": ["Punto clave 1", "Punto clave 2", "Punto clave 3"],
                "image_query": "Descripción visual detallada en INGLÉS (ELEMENTO VISUAL SUGERIDO + Estilo). Generar SOLO para slides 3, 4 y 7. Para el resto, usar null o string vacío.",
                "speaker_notes": "Notas de diseño y discurso."
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
