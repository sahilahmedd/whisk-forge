import httpx
import uuid
import time
import json
from typing import Dict, Any, Optional

class WhiskClient:
    BASE_URL = "https://aisandbox-pa.googleapis.com/v1/whisk:generateImage"
    
    def __init__(self, token: str, cookies: Optional[Dict[str, str]] = None):
        self.token = token
        self.cookies = cookies or {}
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "text/plain;charset=UTF-8",
            "Origin": "https://labs.google",
            "Referer": "https://labs.google/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
            "Accept": "*/*"
        }
        # Initialize client with cookies if provided
        self.client = httpx.Client(headers=self.headers, cookies=self.cookies, timeout=60.0)

    def validate_session(self) -> Optional[Dict[str, Any]]:
        """
        Checks if the session is valid by hitting the auth endpoint.
        Returns session data if valid, None otherwise.
        """
        try:
            # User requested a 10s delay before checking session? 
            # Or maybe they meant the token is valid for a short time?
            # "check the valid session after 10 sec dely" -> Let's respect this if it was a specific instruction for the flow.
            # But blocking for 10s in the UI thread is bad. The UI calls this.
            # I will implement the logic to fetch and return data here. The delay should be handled by the caller or if strictly necessary here.
            # Given the context of "after 10 sec dely", I'll add a small sleep if this is running in a thread, but for now let's just fetch.
            
            resp = self.client.get("https://labs.google/fx/api/auth/session")
            resp.raise_for_status()
            data = resp.json()
            
            # Update token if present
            if "access_token" in data:
                self.token = data["access_token"]
                self.headers["Authorization"] = f"Bearer {self.token}"
                self.client.headers.update(self.headers)
                
            return data
        except Exception as e:
            print(f"Session validation failed: {e}")
            return None

    def generate_image(self, 
                       prompt: str, 
                       aspect_ratio: str = "IMAGE_ASPECT_RATIO_LANDSCAPE", 
                       image_model: str = "IMAGEN_3_5",
                       seed: Optional[int] = None,
                       workflow_id: Optional[str] = None) -> Dict[str, Any]:
        
        if not workflow_id:
            workflow_id = str(uuid.uuid4())
            
        payload = {
            "clientContext": {
                "workflowId": workflow_id,
                "tool": "BACKBONE",
                "sessionId": f";{int(time.time() * 1000)}"
            },
            "imageModelSettings": {
                "imageModel": image_model,
                "aspectRatio": aspect_ratio
            },
            "prompt": prompt,
            "mediaCategory": "MEDIA_CATEGORY_BOARD"
        }
        
        if seed is not None:
            payload["seed"] = seed
            
        try:
            print(f"Generating image with model: {image_model}, aspect: {aspect_ratio}")
            print(f"Payload: {json.dumps(payload, indent=2)}")
            # Mask token for logging
            masked_headers = self.client.headers.copy()
            if "Authorization" in masked_headers:
                masked_headers["Authorization"] = masked_headers["Authorization"][:15] + "..."
            print(f"Headers: {masked_headers}")
            
            response = self.client.post(self.BASE_URL, json=payload)
            print(f"Response Status: {response.status_code}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            print(f"HTTP Error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            print(f"Request Error: {e}")
            raise

    def close(self):
        self.client.close()
