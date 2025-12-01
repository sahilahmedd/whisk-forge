import sys
import os
import json
import time
from src.services.whisk_api import WhiskAPI
from src.utils.config_manager import ConfigManager
from src.core.utils import parse_cookie_json

def main():
    print("--- WhiskForge Debug Generator ---")
    
    print("Please paste your Cookie JSON here (press Enter twice to finish):")
    lines = []
    while True:
        line = input()
        if not line:
            break
        lines.append(line)
    
    cookie_str = "\n".join(lines)
    token, cookies = parse_cookie_json(cookie_str)
    
    if not token or not cookies:
        print("Failed to parse cookies/token.")
        return

    print(f"Token: {token[:10]}...")
    
    print("Initializing API...")
    api = WhiskAPI(token=token, cookies=cookies) 
    
    print("Validating Session...")
    data = api.validate_session()
    if data:
        print("Session Valid!")
        print(f"Token: {api.token[:10]}...")
    else:
        print("Session Validation Failed.")
        return

    print("Attempting Generation...")
    try:
        prompt = "A cute robot fixing a computer, 3d render, high quality"
        print(f"Prompt: {prompt}")
        resp = api.generate_image(prompt)
        print("Response received.")
        
        if "imagePanels" in resp:
            print("Image Panels found.")
            count = 0
            for panel in resp["imagePanels"]:
                for img in panel.get("generatedImages", []):
                    if img.get("encodedImage"):
                        count += 1
            print(f"Found {count} images.")
        else:
            print("No imagePanels in response.")
            print(json.dumps(resp, indent=2))
            
    except Exception as e:
        print(f"Generation failed: {e}")

if __name__ == "__main__":
    main()
