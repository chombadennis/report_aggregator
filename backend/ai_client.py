import asyncio
import time
import json
import logging
import base64
import os
import httpx
import google.auth
import google.auth.transport.requests
import google.oauth2.service_account
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()

# --- Project Configuration ---
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT_ID", "fieldops-fe915")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
GOOGLE_CREDENTIALS_JSON = os.getenv("GOOGLE_CREDENTIALS_JSON")

# Gemini Model Names for Vertex AI (Standard versions for this project)
GEMINI_PRIMARY_MODEL = 'gemini-2.5-flash'
GEMINI_FALLBACK_MODEL = 'gemini-2.5-pro'

# --- Configure Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Global Cache for Performance ---
_ACCESS_TOKEN = None
_TOKEN_EXPIRY = 0
_CREDENTIALS = None

def get_access_token():
    """Fetches and caches an OAuth2 access token."""
    global _ACCESS_TOKEN, _TOKEN_EXPIRY, _CREDENTIALS
    
    now = time.time()
    if _ACCESS_TOKEN and _TOKEN_EXPIRY > (now + 300):
        return _ACCESS_TOKEN

    try:
        if not _CREDENTIALS:
            if GOOGLE_CREDENTIALS_JSON:
                info = json.loads(GOOGLE_CREDENTIALS_JSON)
                _CREDENTIALS = google.oauth2.service_account.Credentials.from_service_account_info(
                    info, scopes=['https://www.googleapis.com/auth/cloud-platform']
                )
            else:
                _CREDENTIALS, _ = google.auth.default(scopes=['https://www.googleapis.com/auth/cloud-platform'])
        
        auth_req = google.auth.transport.requests.Request()
        _CREDENTIALS.refresh(auth_req)
        
        _ACCESS_TOKEN = _CREDENTIALS.token
        _TOKEN_EXPIRY = now + 3000
        return _ACCESS_TOKEN
    except Exception as e:
        logger.error(f"Auth Failure: {e}")
        return None

async def _call_vertex_vision(prompt: str, model: str, file_path: str, mime_type: str, retries: int = 10):
    """Async call to Vertex AI via httpx with built-in retries and exponential backoff."""
    token = get_access_token()
    if not token: raise ValueError("Auth Token is missing. Please check your credentials.")

    url = f"https://{LOCATION}-aiplatform.googleapis.com/v1/projects/{PROJECT_ID}/locations/{LOCATION}/publishers/google/models/{model}:generateContent"
    
    with open(file_path, "rb") as f:
        file_data = base64.b64encode(f.read()).decode("utf-8")
        
    payload = {
        "contents": [{
            "role": "user",
            "parts": [
                {"text": prompt},
                {"inline_data": {"mime_type": mime_type, "data": file_data}}
            ]
        }],
        "generationConfig": {
            "responseMimeType": "application/json"
        }
    }
    
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        delay = 2
        for attempt in range(1, retries + 1):
            try:
                resp = await client.post(url, json=payload, headers=headers)
                
                # Success
                if resp.status_code == 200:
                    data = resp.json()
                    if 'candidates' in data and data['candidates']:
                        return data['candidates'][0]['content']['parts'][0]['text']
                    raise ValueError(f"AI returned an empty response: {data}")
                
                # Handle Rate Limiting (429) - Wait 90s as per fieldOps standard
                if resp.status_code == 429:
                    logger.warning(f"Quota Exceeded (429). Waiting 90 seconds for reset (Attempt {attempt})...")
                    await asyncio.sleep(90)
                    continue
                
                # Handle Server Overload (500, 503) - Exponential Backoff
                if resp.status_code in [500, 503]:
                    logger.warning(f"AI Busy (Status {resp.status_code}). Retrying in {delay}s...")
                    await asyncio.sleep(delay)
                    delay *= 2
                    continue
                
                # Any other error
                resp.raise_for_status()

            except (httpx.ConnectError, httpx.TimeoutException) as e:
                logger.error(f"Network issue (Attempt {attempt}): {e}")
                if attempt < retries:
                    await asyncio.sleep(delay)
                    delay *= 2
                    continue
                raise Exception(f"Failed to connect to AI service after {retries} attempts.")

        raise Exception(f"AI Service Error: {resp.status_code} - {resp.text}")

async def generate_structured_data(prompt: str, file_path: str, mime_type: str = "application/pdf", force_pro: bool = False):
    """Entry point with fallback logic and optional high-precision 'Pro' mode."""
    model = GEMINI_FALLBACK_MODEL if force_pro else GEMINI_PRIMARY_MODEL
    try:
        logger.info(f"Using model: {model}")
        result = await _call_vertex_vision(prompt, model, file_path, mime_type)
        return json.loads(result)
    except Exception as e:
        if force_pro: # If we already failed with Pro, give up
            raise e
        logger.warning(f"Primary failed: {e}. Trying fallback: {GEMINI_FALLBACK_MODEL}")
        result = await _call_vertex_vision(prompt, GEMINI_FALLBACK_MODEL, file_path, mime_type)
        return json.loads(result)
