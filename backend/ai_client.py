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
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
GOOGLE_CREDENTIALS_JSON   = os.getenv("GOOGLE_CREDENTIALS_JSON")
GOOGLE_CREDENTIALS_JSON_2 = os.getenv("GOOGLE_CREDENTIALS_JSON_2")

# Gemini Model Names for Vertex AI
GEMINI_PRIMARY_MODEL  = 'gemini-2.5-flash'
GEMINI_FALLBACK_MODEL = 'gemini-2.5-pro'

# --- Configure Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Dual-Project Round-Robin Load Balancer ---
# Each project has its own independent token cache so they never interfere.
_request_counter = 0  # Increments with every API call to alternate projects

_clients = [
    {
        "creds_json": GOOGLE_CREDENTIALS_JSON,
        "project_id": None,      # Populated on first use from JSON
        "credentials": None,
        "token": None,
        "expiry": 0,
    },
    {
        "creds_json": GOOGLE_CREDENTIALS_JSON_2,
        "project_id": None,
        "credentials": None,
        "token": None,
        "expiry": 0,
    },
]

# Per-project semaphores to prevent hammering the same project from multiple parallel tasks
_project_semaphores = [asyncio.Semaphore(1), asyncio.Semaphore(1)]
_last_request_time = [0.0, 0.0] # Track timing to enforce a gap

def _get_client_slot():
    """Returns the next client slot in round-robin order, skipping disabled slots."""
    global _request_counter
    # If second credential is missing or permanently disabled, always use slot 0
    if not _clients[1]["creds_json"] or _clients[1].get("disabled"):
        return 0
    slot = _request_counter % 2
    _request_counter += 1
    return slot

def get_access_token(slot: int = 0):
    """Fetches and caches an OAuth2 access token for the given project slot."""
    client = _clients[slot]
    now = time.time()
    
    if client["token"] and client["expiry"] > (now + 300):
        return client["token"], client["project_id"]

    try:
        if not client["credentials"]:
            creds_json = client["creds_json"]
            if creds_json:
                info = json.loads(creds_json)
                client["project_id"] = info.get("project_id", "fieldops-fe915")
                client["credentials"] = google.oauth2.service_account.Credentials.from_service_account_info(
                    info, scopes=['https://www.googleapis.com/auth/cloud-platform']
                )
            else:
                client["credentials"], _ = google.auth.default(scopes=['https://www.googleapis.com/auth/cloud-platform'])
                client["project_id"] = "fieldops-fe915"
        
        auth_req = google.auth.transport.requests.Request()
        client["credentials"].refresh(auth_req)
        client["token"]  = client["credentials"].token
        client["expiry"] = now + 3000
        return client["token"], client["project_id"]
    except Exception as e:
        logger.error(f"Auth Failure (slot {slot}): {e}")
        return None, None

async def _call_vertex_vision(prompt: str, model: str, file_path: str, mime_type: str, retries: int = 10):
    """Async call to Vertex AI via httpx with built-in retries and round-robin load balancing."""
    slot = _get_client_slot()
    
    async with _project_semaphores[slot]:
        # Enforce a small gap between requests on the same project
        now = time.time()
        elapsed = now - _last_request_time[slot]
        if elapsed < 2.0:
            await asyncio.sleep(2.0 - elapsed)
        
        token, project_id = get_access_token(slot)
        if not token: raise ValueError(f"Auth Token missing for slot {slot}. Check your credentials.")
        logger.info(f"[Slot {slot}] Project: {project_id} | Model: {model}")

        _last_request_time[slot] = time.time()

    url = f"https://{LOCATION}-aiplatform.googleapis.com/v1/projects/{project_id}/locations/{LOCATION}/publishers/google/models/{model}:generateContent"
    
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
                
                # Handle Rate Limiting (429) - Wait 30s (Vertex RPM usually resets in 60s)
                if resp.status_code == 429:
                    logger.warning(f"Quota Exceeded (429) on {project_id}. Waiting 30 seconds for reset (Attempt {attempt})...")
                    await asyncio.sleep(30)
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

def _clean_ai_json(raw_text: str) -> dict:
    """Attempts to clean and parse AI-generated JSON, handling common errors."""
    clean_text = raw_text.strip()
    try:
        # 1. Strip Markdown code blocks if present
        if "```json" in clean_text:
            clean_text = clean_text.split("```json")[1].split("```")[0].strip()
        elif "```" in clean_text:
            clean_text = clean_text.split("```")[1].split("```")[0].strip()
            
        # 2. Remove control characters (\x00-\x1F, except \n and \r)
        import re
        clean_text = re.sub(r'[\x00-\x09\x0B\x0C\x0E-\x1F\x7F]', '', clean_text)
            
        # 3. Attempt parsing
        return json.loads(clean_text)
    except Exception as e:
        logger.error(f"Initial AI JSON parse failed: {e}. Attempting deep clean...")
        try:
            # Deep clean: remove any non-standard whitespace and ensure valid quotes
            # Handle the specific case where AI might return a "Raw: { ..." string
            if clean_text.startswith("Raw:"):
                clean_text = clean_text.replace("Raw:", "", 1).strip()
            
            # Try to fix truncated JSON by appending closing braces if it looks like an object
            if clean_text.startswith("{") and not clean_text.endswith("}"):
                logger.warning("Detected potentially truncated JSON object. Attempting fix...")
                clean_text += "}"
            
            return json.loads(clean_text)
        except Exception as deep_e:
            logger.error(f"Deep clean failed. Raw head: {raw_text[:500]}")
            raise ValueError(f"AI returned invalid JSON: {deep_e}")

async def generate_structured_data(prompt: str, file_path: str, mime_type: str = "application/pdf", force_pro: bool = False):
    """Entry point with fallback logic and optional high-precision 'Pro' mode."""
    model = GEMINI_FALLBACK_MODEL if force_pro else GEMINI_PRIMARY_MODEL
    try:
        logger.info(f"Using model: {model}")
        result = await _call_vertex_vision(prompt, model, file_path, mime_type)
        return _clean_ai_json(result)
    except Exception as e:
        if force_pro: # If we already failed with Pro, give up
            raise e
        logger.warning(f"Primary failed: {e}. Trying fallback: {GEMINI_FALLBACK_MODEL}")
        result = await _call_vertex_vision(prompt, GEMINI_FALLBACK_MODEL, file_path, mime_type)
        return _clean_ai_json(result)

async def _call_vertex_text(prompt: str, model: str, retries: int = 5):
    """Async call to Vertex AI for text-only generation (also uses round-robin)."""
    slot = _get_client_slot()
    
    async with _project_semaphores[slot]:
        # Enforce a small gap
        now = time.time()
        elapsed = now - _last_request_time[slot]
        if elapsed < 2.0:
            await asyncio.sleep(2.0 - elapsed)

        token, project_id = get_access_token(slot)
        if not token: raise ValueError(f"Auth Token is missing for slot {slot}.")
        
        _last_request_time[slot] = time.time()

    url = f"https://{LOCATION}-aiplatform.googleapis.com/v1/projects/{project_id}/locations/{LOCATION}/publishers/google/models/{model}:generateContent"
    
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json"}
    }
    
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        delay = 2
        for attempt in range(1, retries + 1):
            try:
                resp = await client.post(url, json=payload, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    if 'candidates' in data and data['candidates']:
                        return data['candidates'][0]['content']['parts'][0]['text']
                    raise ValueError(f"AI returned an empty response: {data}")
                
                if resp.status_code == 429:
                    await asyncio.sleep(10)
                    continue
                if resp.status_code in [500, 503]:
                    await asyncio.sleep(delay)
                    delay *= 2
                    continue
                resp.raise_for_status()
            except (httpx.ConnectError, httpx.TimeoutException):
                if attempt < retries:
                    await asyncio.sleep(delay)
                    delay *= 2
                    continue
                raise
        raise Exception(f"AI Service Error: {resp.status_code} - {resp.text}")

async def generate_summary_json(prompt: str):
    """Generates an intelligent JSON summary from text without an image."""
    result = await _call_vertex_text(prompt, GEMINI_PRIMARY_MODEL)
    return _clean_ai_json(result)
