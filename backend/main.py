from fastapi import FastAPI, UploadFile, File, HTTPException, Request, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from config import Config
from tasks import process_audio_presentation
from utils.whatsapp import send_whatsapp_message, download_media
import shutil
import os
import uuid
import json

# Ensure directories exist
Config.ensure_dirs()

app = FastAPI(title="Voice-to-Presentation API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Voice-to-Presentation API is running"}

@app.post("/upload-audio/")
async def upload_audio(file: UploadFile = File(...)):
    """
    Endpoint to upload audio from the web frontend.
    """
    file_id = str(uuid.uuid4())
    extension = os.path.splitext(file.filename)[1]
    file_path = os.path.join(Config.UPLOAD_DIR, f"{file_id}{extension}")
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Trigger background task
    task = process_audio_presentation.delay(file_path)
    
    return {"task_id": task.id, "message": "Processing started"}

@app.get("/task/{task_id}")
async def get_task_status(task_id: str):
    """
    Check the status of a Celery task.
    """
    from tasks import celery_app
    task_result = celery_app.AsyncResult(task_id)
    
    response = {
        "task_id": task_id,
        "status": task_result.status,
        "result": task_result.result if task_result.ready() else None
    }
    return response

@app.get("/download/{filename}")
async def download_pptx(filename: str):
    """
    Download the generated PPTX file.
    """
    file_path = os.path.join(Config.OUTPUT_DIR, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path, filename=filename)
    raise HTTPException(status_code=404, detail="File not found")

# WhatsApp Webhook
@app.get("/webhook")
async def verify_webhook(request: Request):
    """
    Verifies the webhook for WhatsApp.
    """
    verify_token = Config.WHATSAPP_VERIFY_TOKEN
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    
    if mode and token:
        if mode == "subscribe" and token == verify_token:
            return int(challenge)
        else:
            raise HTTPException(status_code=403, detail="Verification failed")
    return {"status": "ok"}

@app.post("/webhook")
async def receive_whatsapp_message(request: Request):
    """
    Receives messages from WhatsApp.
    """
    data = await request.json()
    
    try:
        entry = data['entry'][0]
        changes = entry['changes'][0]
        value = changes['value']
        messages = value.get('messages')
        
        if messages:
            message = messages[0]
            sender_id = message['from']
            
            if message['type'] == 'audio':
                audio_id = message['audio']['id']
                
                # Reply "Processing..."
                send_whatsapp_message(sender_id, "Processing your audio presentation...")
                
                # Download audio
                audio_filename = f"{audio_id}.ogg"
                audio_path = os.path.join(Config.UPLOAD_DIR, audio_filename)
                download_media(audio_id, audio_path)
                
                # Trigger background task with WhatsApp recipient
                process_audio_presentation.delay(audio_path, whatsapp_to=sender_id)
                
            else:
                send_whatsapp_message(sender_id, "Please send an audio message to generate a presentation.")
                
    except Exception as e:
        print(f"Error processing webhook: {e}")
        
    return {"status": "received"}
