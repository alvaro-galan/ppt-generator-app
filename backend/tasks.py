from celery import Celery
from config import Config
from services.gemini_service import analyze_audio
from services.pptx_service import generate_pptx
from services.plus_service import PlusAIService
from utils.whatsapp import send_whatsapp_document
import os
import uuid
import logging
import subprocess
import traceback

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

celery_app = Celery("worker", broker=Config.REDIS_URL, backend=Config.REDIS_URL)

@celery_app.task(name="process_audio_presentation", bind=True)
def process_audio_presentation(self, audio_path: str, whatsapp_to: str = None):
    """
    Background task to process audio, generate PPTX, convert to PDF, and optionally send via WhatsApp.
    """
    logger.info(f"🚀 TASK STARTED: Processing {audio_path}")
    
    # Debug: Check if audio file exists
    if not os.path.exists(audio_path):
        error_msg = f"❌ Audio file not found at: {audio_path}"
        logger.error(error_msg)
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
        
        # Debug Log for Plus AI Key
        if Config.PLUSAI_API_KEY:
             logger.info(f"🔑 PLUSAI_API_KEY detected: {Config.PLUSAI_API_KEY[:5]}***")
        else:
             logger.warning("⚠️ PLUSAI_API_KEY is missing or empty.")

        try:
            if Config.PLUSAI_API_KEY:
                # Use Plus AI (Professional)
                logger.info("✨ Using Plus AI API for generation...")
                # Create a prompt from the title and interpretation
                prompt_text = (
                    f"Create a professional, visually engaging presentation about '{presentation_data.get('title', 'Topic')}'.\n\n"
                    f"Key context and focus: {presentation_data.get('interpretation', '')}.\n\n"
                    f"Target Audience: General Professional.\n"
                    f"Tone: Educational and Inspiring."
                )
                # Ensure prompt isn't too long or weird characters
                prompt_text = prompt_text[:2000] 
                pptx_path = PlusAIService.generate_presentation(prompt_text, filename)
            else:
                # Use Local Generator (Basic)
                logger.info("🛠️ Using Local Generator...")
                pptx_path = generate_pptx(presentation_data, filename)
                
            logger.info(f"✅ PPTX Generation called. Returned path: {pptx_path}")
        except Exception as pptx_error:
            logger.error(f"❌ Error in generate_pptx: {pptx_error}")
            raise pptx_error

        # Debug: Check if PPTX file exists physically
        if os.path.exists(pptx_path):
            logger.info(f"💾 FILE VERIFIED: {pptx_path} exists on disk. Size: {os.path.getsize(pptx_path)} bytes")
        else:
            return {"status": "error", "error": f"File generated but not found at {pptx_path}"}
        
        # Step 2.5: Convert to PDF
        pdf_filename = filename.replace(".pptx", ".pdf")
        pdf_path = pptx_path.replace(".pptx", ".pdf")
        output_dir = os.path.dirname(pptx_path)
        
        logger.info(f"📄 Step 2.5: Converting to PDF: {pdf_filename}")
        
        try:
            # Run LibreOffice headless conversion
            cmd = [
                "libreoffice", "--headless", "--convert-to", "pdf", 
                "--outdir", output_dir, 
                pptx_path
            ]
            process = subprocess.run(cmd, capture_output=True, text=True)
            
            if process.returncode == 0 and os.path.exists(pdf_path):
                logger.info(f"✅ PDF Generated successfully at {pdf_path}")
            else:
                logger.error(f"❌ PDF Conversion failed. Stderr: {process.stderr}")
                pdf_filename = None # Mark as failed but return PPTX
                
        except Exception as pdf_error:
            logger.error(f"❌ Exception converting to PDF: {pdf_error}")
            pdf_filename = None

        # Step 3: Send via WhatsApp if recipient provided
        if whatsapp_to:
            logger.info(f"📱 Step 3: Sending to WhatsApp {whatsapp_to}")
            send_whatsapp_document(whatsapp_to, pptx_path, filename)
            if pdf_filename and os.path.exists(pdf_path):
                 send_whatsapp_document(whatsapp_to, pdf_path, pdf_filename)
            
        return {
            "status": "success", 
            "pptx_path": pptx_path, 
            "filename": filename,
            "pdf_filename": pdf_filename,
            "interpretation": presentation_data.get("interpretation", "AI Analysis complete."),
            "debug_info": {
                "audio_found": True,
                "ai_success": True,
                "file_created": True,
                "path": pptx_path
            }
        }

    except Exception as e:
        logger.error(f"🔥 CRITICAL TASK ERROR: {e}")
        logger.error(traceback.format_exc())
        return {"status": "error", "error": str(e), "traceback": traceback.format_exc()}
