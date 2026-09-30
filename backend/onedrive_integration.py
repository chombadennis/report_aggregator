import os
import json
import logging
import httpx
import urllib.parse
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

router = APIRouter()

# Use local data folder for storing token and file config
DATA_DIR = "cache"
CONFIG_FILE = os.path.join(DATA_DIR, "onedrive_config.json")

MS_TOKEN_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
MS_AUTH_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize"

def get_config() -> dict:
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading config: {e}")
    return {}

def save_config(data: dict):
    os.makedirs(DATA_DIR, exist_ok=True)
    config = get_config()
    config.update(data)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)

@router.get("/api/onedrive/auth-url")
def get_auth_url():
    client_id = os.getenv("MICROSOFT_CLIENT_ID")
    redirect_uri = os.getenv("MICROSOFT_REDIRECT_URI")
    
    if not client_id or not redirect_uri:
        raise HTTPException(status_code=500, detail="Microsoft OAuth env variables not set.")
        
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "files.readwrite offline_access user.read",
        "response_mode": "query"
    }
    query = urllib.parse.urlencode(params)
    return {"url": f"{MS_AUTH_URL}?{query}"}

from fastapi.responses import RedirectResponse

@router.get("/api/integrations/onedrive/callback")
async def handle_callback(code: str):
    client_id = os.getenv("MICROSOFT_CLIENT_ID")
    client_secret = os.getenv("MICROSOFT_CLIENT_SECRET")
    redirect_uri = os.getenv("MICROSOFT_REDIRECT_URI")
    
    if not client_id or not client_secret or not redirect_uri:
        raise HTTPException(status_code=500, detail="Microsoft OAuth env variables not set.")
        
    data = {
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code"
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(MS_TOKEN_URL, data=data)
        if response.status_code != 200:
            logger.error(f"Failed to exchange OneDrive OAuth code: {response.text}")
            raise HTTPException(status_code=400, detail=f"OneDrive Token Exchange Error: {response.text}")
            
        token_data = response.json()
        
        # Save refresh token to local json
        if "refresh_token" in token_data:
            save_config({
                "refresh_token": token_data["refresh_token"],
                "is_linked": True
            })
            return RedirectResponse(url="http://localhost:3000/dashboard", status_code=302)
        else:
            raise HTTPException(status_code=400, detail="No refresh token returned.")

async def get_access_token() -> str:
    config = get_config()
    refresh_token = config.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="OneDrive is not linked (No refresh token).")
        
    client_id = os.getenv("MICROSOFT_CLIENT_ID")
    client_secret = os.getenv("MICROSOFT_CLIENT_SECRET")
    
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token"
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(MS_TOKEN_URL, data=data)
        if response.status_code != 200:
            logger.error(f"Failed to refresh OneDrive token: {response.text}")
            raise HTTPException(status_code=401, detail="OneDrive Token Refresh Error. Please relink account.")
        result = response.json()
        return result["access_token"]

@router.get("/api/onedrive/status")
async def get_onedrive_status():
    config = get_config()
    return {
        "is_linked": config.get("is_linked", False),
        "selected_file": config.get("selected_file_name")
    }

@router.get("/api/onedrive/files")
async def list_onedrive_files(folder_id: Optional[str] = None):
    access_token = await get_access_token()
    
    if folder_id:
        url = f"https://graph.microsoft.com/v1.0/me/drive/items/{folder_id}/children?$select=id,name,folder,file"
    else:
        url = "https://graph.microsoft.com/v1.0/me/drive/root/children?$select=id,name,folder,file"
        
    headers = {"Authorization": f"Bearer {access_token}"}
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, headers=headers)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=f"Error fetching files: {response.text}")
            
        data = response.json()
        items = []
        for item in data.get("value", []):
            is_folder = "folder" in item
            if is_folder or ("file" in item and item["name"].lower().endswith(".xlsx")):
                items.append({
                    "id": item["id"],
                    "name": item["name"],
                    "type": "folder" if is_folder else "file"
                })
        
        # Sort folders first, then alphabetically
        items.sort(key=lambda x: (0 if x["type"] == "folder" else 1, x["name"].lower()))
        return items

from pydantic import BaseModel
class SelectFileRequest(BaseModel):
    item_id: str
    file_name: str

@router.post("/api/onedrive/select-file")
async def select_onedrive_file(req: SelectFileRequest):
    save_config({
        "selected_item_id": req.item_id,
        "selected_file_name": req.file_name
    })
    return {"status": "success", "msg": f"Selected file: {req.file_name}"}

@router.post("/api/onedrive/sync-evm")
async def sync_evm():
    config = get_config()
    item_id = config.get("selected_item_id")
    if not item_id:
        raise HTTPException(status_code=400, detail="No Excel file selected for sync.")
        
    access_token = await get_access_token()
    
    # 1. Get sheets first to find the first sheet name
    sheets_url = f"https://graph.microsoft.com/v1.0/me/drive/items/{item_id}/workbook/worksheets"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        sheets_resp = await client.get(sheets_url, headers=headers)
        if sheets_resp.status_code != 200:
            raise HTTPException(status_code=sheets_resp.status_code, detail="Failed to fetch worksheets.")
        
        sheets_data = sheets_resp.json()
        if not sheets_data.get("value"):
            raise HTTPException(status_code=400, detail="No sheets found in the selected Excel file.")
            
        first_sheet = sheets_data["value"][0]["name"]
        
    # 2. Get usedRange of the first sheet
    range_url = f"https://graph.microsoft.com/v1.0/me/drive/items/{item_id}/workbook/worksheets/{first_sheet}/usedRange"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        range_resp = await client.get(range_url, headers=headers)
        if range_resp.status_code != 200:
            raise HTTPException(status_code=range_resp.status_code, detail="Failed to fetch used range data.")
            
        data = range_resp.json()
        values = data.get("values", [])
        
    # 3. Parse the tables from the values
    main_table_data = []
    blocks_table_data = []
    
    in_main_table = False
    in_blocks_table = False
    
    main_desc_idx = -1
    main_total_pct_idx = -1
    main_contract_val_idx = -1
    main_comp_done_idx = -1
    
    block_name_idx = -1
    block_done_idx = -1
    
    for row in values:
        if not row:
            continue
            
        row_strs = [str(cell).strip() if cell is not None else "" for cell in row]
        row_joined = "".join(row_strs).strip()
        
        # Check for empty row (used to detect end of tables)
        if not row_joined:
            in_main_table = False
            in_blocks_table = False
            continue
            
        # Detect Main Table Headers
        if "DESCRIPTION" in row_strs and "% of Component to Total" in row_strs:
            in_main_table = True
            in_blocks_table = False
            main_desc_idx = row_strs.index("DESCRIPTION")
            main_total_pct_idx = row_strs.index("% of Component to Total")
            try:
                main_contract_val_idx = row_strs.index("% Contribution of Work Done to Contract Value")
            except:
                main_contract_val_idx = -1
            try:
                main_comp_done_idx = row_strs.index("% of Component Done to Respective Value")
            except:
                main_comp_done_idx = -1
            continue
            
        # Detect Blocks Table Headers
        if "Block" in row_strs and "% Done Per Block" in row_strs:
            in_blocks_table = True
            in_main_table = False
            block_name_idx = row_strs.index("Block")
            block_done_idx = row_strs.index("% Done Per Block")
            continue
            
        # Extract Main Table Row
        if in_main_table and main_desc_idx != -1:
            desc = row_strs[main_desc_idx] if len(row_strs) > main_desc_idx else ""
            if desc and desc != "DESCRIPTION":
                main_table_data.append({
                    "description": desc,
                    "component_to_total": row_strs[main_total_pct_idx] if main_total_pct_idx != -1 and len(row_strs) > main_total_pct_idx else "",
                    "contribution_to_contract": row_strs[main_contract_val_idx] if main_contract_val_idx != -1 and len(row_strs) > main_contract_val_idx else "",
                    "component_done": row_strs[main_comp_done_idx] if main_comp_done_idx != -1 and len(row_strs) > main_comp_done_idx else ""
                })
                
        # Extract Blocks Table Row
        if in_blocks_table and block_name_idx != -1:
            block = row_strs[block_name_idx] if len(row_strs) > block_name_idx else ""
            if block and block != "Block":
                blocks_table_data.append({
                    "block": block,
                    "done_per_block": row_strs[block_done_idx] if block_done_idx != -1 and len(row_strs) > block_done_idx else ""
                })

    return {
        "status": "success",
        "main_table": main_table_data,
        "blocks_table": blocks_table_data
    }
