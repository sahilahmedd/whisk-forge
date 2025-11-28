import json
import base64
import os
import re
from typing import Optional, Dict, Any, Tuple

def parse_cookie_json(json_str: str) -> Tuple[Optional[str], Dict[str, str]]:
    """
    Parses the Cookie Exporter JSON and extracts the Google access token and all cookies.
    Returns: (token, cookies_dict)
    """
    token = None
    cookies = {}
    
    try:
        # Parse JSON to get all cookies
        data = json.loads(json_str)
        if isinstance(data, list):
            for cookie in data:
                if isinstance(cookie, dict) and 'name' in cookie and 'value' in cookie:
                    cookies[cookie['name']] = str(cookie['value'])
                    
                    # Try to find token in values if not already found via regex
                    if not token and str(cookie['value']).startswith('ya29.'):
                        token = cookie['value']
        
        # If token not found in loop, try regex as fallback
        if not token:
            match = re.search(r'(ya29\.[a-zA-Z0-9_\-]+)', json_str)
            if match:
                token = match.group(1)
        
        # Fallback 2: If still no ya29 token, look for session tokens
        if not token:
            # Check for specific known session cookie names
            if '__Secure-next-auth.session-token' in cookies:
                token = cookies['__Secure-next-auth.session-token']
            elif '_Secure-next-auth.session-token' in cookies:
                token = cookies['_Secure-next-auth.session-token']
            
            # Fallback 3: Look for any cookie with 'session-token' in the name
            if not token:
                for name, value in cookies.items():
                    if 'session-token' in name:
                        token = value
                        break
                
        return token, cookies
    except Exception as e:
        print(f"Error parsing cookie JSON: {e}")
        return None, {}

def save_image(encoded_image: str, output_path: str) -> bool:
    """Decodes base64 image and saves to file."""
    try:
        # Remove header if present (e.g. data:image/jpeg;base64,...)
        if ',' in encoded_image:
            encoded_image = encoded_image.split(',', 1)[1]
            
        image_data = base64.b64decode(encoded_image)
        with open(output_path, "wb") as f:
            f.write(image_data)
        return True
    except Exception as e:
        print(f"Error saving image to {output_path}: {e}")
        return False

def save_metadata(metadata: Dict[str, Any], output_path: str) -> bool:
    """Saves metadata to a JSON file."""
    try:
        with open(output_path, "w", encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving metadata to {output_path}: {e}")
        return False

def sanitize_filename(text: str) -> str:
    """Sanitizes text for use in filenames."""
    # Keep alphanumeric, spaces, hyphens, underscores
    text = re.sub(r'[^\w\s-]', '', text)
    return text.strip().replace(' ', '_')
