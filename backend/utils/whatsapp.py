import requests
from config import Config
import os

def send_whatsapp_message(to: str, message: str):
    """
    Sends a text message via WhatsApp Cloud API.
    """
    url = f"https://graph.facebook.com/v18.0/{Config.WHATSAPP_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {Config.WHATSAPP_API_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message}
    }
    response = requests.post(url, headers=headers, json=data)
    return response.json()

def send_whatsapp_document(to: str, file_path: str, filename: str):
    """
    Sends a document via WhatsApp Cloud API.
    """
    # First, upload the media to get a media ID (simplified for now, assumes direct media upload or link)
    # WhatsApp Cloud API usually requires uploading media first to get an ID for large files,
    # or sending a link. For this implementation, we'll try to use the media upload endpoint.
    
    url = f"https://graph.facebook.com/v18.0/{Config.WHATSAPP_PHONE_NUMBER_ID}/media"
    headers = {
        "Authorization": f"Bearer {Config.WHATSAPP_API_TOKEN}"
    }
    
    files = {
        'file': (filename, open(file_path, 'rb'), 'application/vnd.openxmlformats-officedocument.presentationml.presentation')
    }
    
    data = {
        'messaging_product': 'whatsapp'
    }
    
    # Step 1: Upload Media
    upload_response = requests.post(url, headers=headers, files=files, data=data)
    upload_result = upload_response.json()
    
    if 'id' not in upload_result:
        print(f"Failed to upload media: {upload_result}")
        return
        
    media_id = upload_result['id']
    
    # Step 2: Send Message with Media ID
    msg_url = f"https://graph.facebook.com/v18.0/{Config.WHATSAPP_PHONE_NUMBER_ID}/messages"
    msg_headers = {
        "Authorization": f"Bearer {Config.WHATSAPP_API_TOKEN}",
        "Content-Type": "application/json"
    }
    msg_data = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "document",
        "document": {
            "id": media_id,
            "filename": filename,
            "caption": "Here is your generated presentation!"
        }
    }
    
    requests.post(msg_url, headers=msg_headers, json=msg_data)

def download_media(media_id: str, output_path: str):
    """
    Downloads media from WhatsApp.
    """
    # Get media URL
    url = f"https://graph.facebook.com/v18.0/{media_id}"
    headers = {
        "Authorization": f"Bearer {Config.WHATSAPP_API_TOKEN}"
    }
    response = requests.get(url, headers=headers)
    media_url = response.json().get('url')
    
    if media_url:
        # Download content
        media_content = requests.get(media_url, headers=headers)
        with open(output_path, 'wb') as f:
            f.write(media_content.content)
