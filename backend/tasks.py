from celery import Celery
from config import Config
from services.gemini_service import analyze_audio
from services.pptx_service import generate_pptx
from utils.whatsapp import send_whatsapp_document
import os

celery_app = Celery("worker", broker=Config.REDIS_URL, backend=Config.REDIS_URL)

@celery_app.task(name="process_audio_presentation")
def process_audio_presentation(audio_path: str, whatsapp_to: str = None):
    """
    Background task to process audio, generate PPTX, and optionally send via WhatsApp.
    """
    try:
        # Step 1: Analyze Audio with Gemini
        presentation_data = analyze_audio(audio_path)
        
        # Step 2: Generate PPTX
        # Create a filename based on the title or a timestamp/uuid
        import uuid
        filename = f"presentation_{uuid.uuid4()}.pptx"
        pptx_path = generate_pptx(presentation_data, filename)
        
        # Step 3: Send via WhatsApp if recipient provided
        if whatsapp_to:
            send_whatsapp_document(whatsapp_to, pptx_path, filename)
            
        return {"status": "success", "pptx_path": pptx_path, "filename": filename}
    except Exception as e:
        print(f"Error processing task: {e}")
        return {"status": "error", "error": str(e)}
