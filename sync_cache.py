import os
import zipfile
import io
import sys

def create_cache_zip():
    """Zips the local backend/cache folder into an in-memory byte buffer."""
    cache_dir = "backend/cache"
    if not os.path.exists(cache_dir):
        # Fallback if run from backend folder
        cache_dir = "cache"
        if not os.path.exists(cache_dir):
            print(f"Error: Local cache folder not found in 'backend/cache' or 'cache'.")
            sys.exit(1)
    print(f"Packaging local cache folder '{cache_dir}'...")
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(cache_dir):
            for file in files:
                full_path = os.path.join(root, file)
                # Keep the folder structure inside the zip
                relative_path = os.path.relpath(full_path, os.path.dirname(cache_dir)).replace("\\", "/")
                
                # Check if it is a JSON file and sanitize it to standard UTF-8
                if file.endswith(".json"):
                    content = None
                    # 1. Try reading as standard UTF-8 first
                    try:
                        with open(full_path, "r", encoding="utf-8") as f:
                            content = f.read()
                    except UnicodeDecodeError:
                        # 2. If it fails, fallback to cp1252 (Windows default)
                        try:
                            with open(full_path, "r", encoding="cp1252") as f:
                                content = f.read()
                        except Exception:
                            pass
                            
                    if content is not None:
                        try:
                            import json
                            data = json.loads(content)
                            # Re-dump to clean UTF-8 string (preserving unicode characters)
                            clean_json = json.dumps(data, ensure_ascii=False, indent=2)
                            zf.writestr(relative_path, clean_json.encode("utf-8"))
                            continue
                        except Exception as e:
                            print(f"Warning: Failed to parse JSON for {file}: {e}")
                            
                # Fallback for standard files or folders
                zf.write(full_path, relative_path)
                
    zip_buffer.seek(0)
    return zip_buffer.getvalue()

def main():
    print("==================================================")
    print("🚀 Construction Aggregator - Cache Sync Utility")
    print("==================================================")
    
    # 1. Get Production URL
    default_url = "https://report-aggregator-avqo.onrender.com"
    prod_url = input(f"Production Backend URL [{default_url}]: ").strip()
    if not prod_url:
        prod_url = default_url
    prod_url = prod_url.rstrip("/")
    
    # 2. Get Bearer Token
    print("\nTo upload to production, we need your Administrator Bearer Token.")
    print("How to get it:")
    print("  1. Open your production dashboard in Google Chrome / Edge.")
    print("  2. Press F12 to open Developer Tools, and click the 'Network' tab.")
    print("  3. Refresh the page, click on any API call (like 'insights' or 'trends').")
    print("  4. Look under 'Request Headers' for the 'Authorization' header.")
    print("  5. Copy the entire value (starts with 'Bearer ey...').\n")
    
    token = input("Paste your Authorization Token: ").strip()
    if not token:
        print("Error: Authorization token is required to upload.")
        sys.exit(1)
        
    if not token.startswith("Bearer "):
        token = f"Bearer {token}"
        
    # 3. Create the ZIP
    zip_data = create_cache_zip()
    print(f"ZIP Created successfully! Size: {len(zip_data) / 1024:.2f} KB")
    
    # 4. Upload to production using httpx (already installed in venv)
    print(f"\nUploading cache to {prod_url}/api/admin/restore-cache...")
    
    try:
        import httpx
    except ImportError:
        print("Error: 'httpx' is not installed in the current Python environment. Please make sure you are running this with the virtual environment Python.")
        sys.exit(1)
        
    headers = {
        "Authorization": token
    }
    
    files = {
        "file": ("cache.zip", zip_data, "application/zip")
    }
    
    try:
        with httpx.Client(timeout=120.0) as client:
            response = client.post(f"{prod_url}/api/admin/restore-cache", headers=headers, files=files)
            
            if response.status_code == 200:
                result = response.json()
                print("\n✅ SUCCESS!")
                print(f"Server Response: {result.get('msg')}")
                print("\nAll local daily/weekly reports have been successfully restored in production persistent disk!")
            else:
                print(f"\n❌ FAILED (Status Code: {response.status_code})")
                try:
                    detail = response.json().get('detail')
                    print(f"Error Detail: {detail}")
                except Exception:
                    print(f"Raw Response: {response.text}")
    except Exception as e:
        print(f"\n❌ Network Connection Error: {e}")

if __name__ == "__main__":
    main()
