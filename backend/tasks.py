from celery import Celery
from config import Config
from services.gemini_service import analyze_audio
from services.pptx_service import generate_pptx
from utils.whatsapp import send_whatsapp_document
import os
import uuid
import logging

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

celery_app = Celery("worker", broker=Config.REDIS_URL, backend=Config.REDIS_URL)

@celery_app.task(name="process_audio_presentation", bind=True)
def process_audio_presentation(self, audio_path: str, whatsapp_to: str = None):
    """
    Background task to process audio, generate PPTX, and optionally send via WhatsApp.
    """
    logger.info(f"🚀 TASK STARTED: Processing {audio_path}")
    
    # Debug: Check if audio file exists
    if not os.path.exists(audio_path):
        error_msg = f"❌ Audio file not found at: {audio_path}"
        logger.error(error_msg)
        
        # DEBUG: List uploads directory to see what IS there
        try:
            uploads_dir = os.path.dirname(audio_path)
            if os.path.exists(uploads_dir):
                files = os.listdir(uploads_dir)
                logger.error(f"📂 Directory content of {uploads_dir}: {files}")
            else:
                logger.error(f"📂 Directory {uploads_dir} DOES NOT EXIST!")
        except Exception as list_err:
            logger.error(f"Could not list directory: {list_err}")

        return {"status": "error", "error": error_msg}

    try:
        # Step 1: Analyze Audio with Gemini
        logger.info("🤖 Step 1: Sending audio to Gemini...")
        presentation_data = analyze_audio(audio_path)
        logger.info(f"✅ Gemini Response: {str(presentation_data)[:100]}...") # Log first 100 chars
        
        if "title" not in presentation_data:
             logger.error(f"❌ Gemini returned invalid data: {presentation_data}")
             return {"status": "error", "error": "AI failed to extract structure from audio"}

        # Step 2: Generate PPTX
        filename = f"presentation_{uuid.uuid4()}.pptx"
        logger.info(f"🎨 Step 2: Generating PPTX: {filename}")
        
        try:
            pptx_path = generate_pptx(presentation_data, filename)
            logger.info(f"✅ PPTX Generation called. Returned path: {pptx_path}")
        except Exception as pptx_error:
            logger.error(f"❌ Error in generate_pptx: {pptx_error}")
            raise pptx_error

        # Debug: Check if PPTX file exists physically
        if os.path.exists(pptx_path):
            logger.info(f"💾 FILE VERIFIED: {pptx_path} exists on disk. Size: {os.path.getsize(pptx_path)} bytes")
        else:
            # Try to list directory content to see where it went
            output_dir = os.path.dirname(pptx_path)
            if os.path.exists(output_dir):
                dir_content = os.listdir(output_dir)
                logger.error(f"❌ FILE MISSING: {pptx_path} not found. Directory {output_dir} contains: {dir_content}")
            else:
                logger.error(f"❌ DIRECTORY MISSING: {output_dir} does not exist!")
            
            return {"status": "error", "error": f"File generated but not found at {pptx_path}"}
        
        # Step 3: Send via WhatsApp if recipient provided
        if whatsapp_to:
            logger.info(f"📱 Step 3: Sending to WhatsApp {whatsapp_to}")
            send_whatsapp_document(whatsapp_to, pptx_path, filename)
            
        return {
            "status": "success", 
            "pptx_path": pptx_path, 
            "filename": filename,
            "debug_info": {
                "audio_found": True,
                "ai_success": True,
                "file_created": True,
                "path": pptx_path
            }
        }

    except Exception as e:
        logger.error(f"🔥 CRITICAL TASK ERROR: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {"status": "error", "error": str(e), "traceback": traceback.format_exc()}
