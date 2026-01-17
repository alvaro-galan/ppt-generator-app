import requests
import time
import os
from config import Config

class PlusAIService:
    BASE_URL = "https://api.plusdocs.com/r/v0"

    @staticmethod
    def generate_presentation(prompt: str, filename: str) -> str:
        """
        Generates a presentation using Plus AI API and downloads it.
        Returns the local path to the downloaded PPTX file.
        """
        if not Config.PLUSAI_API_KEY:
            raise ValueError("PLUSAI_API_KEY is not configured")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {Config.PLUSAI_API_KEY}"
        }

        # 1. Create Request
        print(f"🚀 Plus AI: Sending prompt: '{prompt}'")
        response = requests.post(
            f"{PlusAIService.BASE_URL}/presentation",
            headers=headers,
            json={"prompt": prompt, "numberOfSlides": 8} # Default to ~8 slides
        )

        if response.status_code not in [200, 201, 202]:
            raise Exception(f"Plus AI Create Failed ({response.status_code}): {response.text}")

        data = response.json()
        polling_url = data["pollingUrl"]
        
        # 2. Poll for completion
        print(f"⏳ Plus AI: Polling {polling_url}")
        
        max_retries = 60 # 5 minutes max (5s * 60)
        pptx_url = None

        for _ in range(max_retries):
            time.sleep(5)
            poll_resp = requests.get(polling_url, headers=headers)
            
            if poll_resp.status_code != 200:
                print(f"⚠️ Polling warning: {poll_resp.status_code}")
                continue

            poll_data = poll_resp.json()
            status = poll_data.get("status")

            if status == "GENERATED":
                pptx_url = poll_data.get("url")
                print("✅ Plus AI: Generation Complete!")
                break
            elif status == "FAILED":
                raise Exception(f"Plus AI Generation Failed: {poll_data}")
            else:
                print(f"... status: {status}")
        
        if not pptx_url:
            raise Exception("Plus AI timed out generating presentation")

        # 3. Download File
        print(f"⬇️ Downloading PPTX from {pptx_url}")
        doc_resp = requests.get(pptx_url)
        
        output_path = os.path.join(Config.OUTPUT_DIR, filename)
        with open(output_path, "wb") as f:
            f.write(doc_resp.content)
            
        return output_path
