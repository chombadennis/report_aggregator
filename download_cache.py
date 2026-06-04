import os
import zipfile
import io
import sys

def extract_cache_zip(zip_bytes):
    """Extracts the zip bytes into the local backend/cache folder."""
    cache_dir = "backend/cache"
    if not os.path.exists("backend"):
        # Fallback if run from backend folder
        cache_dir = "cache"
        
    print(f"Extracting production cache into '{cache_dir}'...")
    os.makedirs(cache_dir, exist_ok=True)
    
    zip_archive = zipfile.ZipFile(io.BytesIO(zip_bytes))
    extracted_count = 0
    
    for member in zip_archive.infolist():
        filename = member.filename.replace("\\", "/").lstrip("/")
        
        # Clean paths to avoid nested cache/cache directories
        if filename.startswith("backend/cache/"):
            cleaned_path = filename[len("backend/cache/"):]
        elif filename.startswith("cache/"):
            cleaned_path = filename[len("cache/"):]
        else:
            cleaned_path = filename
            
        if not cleaned_path or cleaned_path.endswith("/"):
            continue
            
        target_path = os.path.join(cache_dir, cleaned_path)
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        
        with zip_archive.open(member) as source, open(target_path, "wb") as target:
            target.write(source.read())
        extracted_count += 1
        
    print(f"Successfully extracted {extracted_count} items into '{cache_dir}'!")

def main():
    print("==================================================")
    print("🚀 Construction Aggregator - Cache Download Utility")
    print("==================================================")
    
    # 1. Get Production URL
    default_url = "https://report-aggregator-avqo.onrender.com"
    prod_url = input(f"Production Backend URL [{default_url}]: ").strip()
    if not prod_url:
        prod_url = default_url
    prod_url = prod_url.rstrip("/")
    
    # 2. Get Bearer Token
    print("\nTo download from production, we need your Administrator Bearer Token.")
    print("How to get it:")
    print("  1. Open your production dashboard in Google Chrome / Edge.")
    print("  2. Press F12 to open Developer Tools, and click the 'Network' tab.")
    print("  3. Refresh the page, click on any API call (like 'insights' or 'trends').")
    print("  4. Look under 'Request Headers' for the 'Authorization' header.")
    print("  5. Copy the entire value (starts with 'Bearer ey...').\n")
    
    token = input("Paste your Authorization Token: ").strip()
    if not token:
        print("Error: Authorization token is required to download.")
        sys.exit(1)
        
    if not token.startswith("Bearer "):
        token = f"Bearer {token}"
        
    # 3. Download from production using httpx
    print(f"\nDownloading cache from {prod_url}/api/admin/backup-cache...")
    
    try:
        import httpx
    except ImportError:
        print("Error: 'httpx' is not installed in the current Python environment. Please make sure you run this script within the virtual environment.")
        sys.exit(1)
        
    headers = {
        "Authorization": token
    }
    
    try:
        with httpx.Client(timeout=120.0) as client:
            response = client.get(f"{prod_url}/api/admin/backup-cache", headers=headers)
            
            if response.status_code == 200:
                print("Download complete! Processing ZIP file...")
                extract_cache_zip(response.content)
                print("\n✅ SUCCESS!")
                print("Your local cache folder matches your production persistent disk exactly!")
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
