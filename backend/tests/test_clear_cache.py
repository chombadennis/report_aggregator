import os
import sys
import unittest
import shutil
from fastapi.testclient import TestClient

# Add parent directory to sys.path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app, require_admin, get_current_user

class TestClearCache(unittest.TestCase):
    def setUp(self):
        # Override FastAPI dependencies for testing to bypass Clerk authentication
        app.dependency_overrides[get_current_user] = lambda: {"email": "admin@example.com"}
        app.dependency_overrides[require_admin] = lambda: {"email": "admin@example.com"}
        
        # Create a mock cache directory
        self.test_cache_dir = "test_cache_temp"
        os.makedirs(self.test_cache_dir, exist_ok=True)
        
        # Create some mock cache files
        self.test_files = [
            "WEEKLY_12345.json",
            "WEEKLY_67890.json",
            "daily_11111.json",
            "test_other.json"
        ]
        for f in self.test_files:
            with open(os.path.join(self.test_cache_dir, f), "w") as out:
                out.write('{"mock": true}')

        self.client = TestClient(app)

    def tearDown(self):
        # Clean up mock cache directory
        if os.path.exists(self.test_cache_dir):
            shutil.rmtree(self.test_cache_dir)
        # Clear FastAPI dependency overrides
        app.dependency_overrides.clear()

    def test_clear_cache_weekly_pattern(self):
        # We temporarily rename test_cache_temp to cache (backing up any existing cache)
        has_real_cache = os.path.exists("cache")
        if has_real_cache:
            os.rename("cache", "cache_backup_temp")
            
        try:
            os.rename(self.test_cache_dir, "cache")
            
            # Request to clear WEEKLY_*.json files
            response = self.client.post("/api/admin/clear-cache", data={"pattern": "WEEKLY_*.json"})
            
            self.assertEqual(response.status_code, 200)
            res_data = response.json()
            self.assertEqual(res_data["status"], "success")
            self.assertIn("WEEKLY_12345.json", res_data["deleted"])
            self.assertIn("WEEKLY_67890.json", res_data["deleted"])
            self.assertNotIn("daily_11111.json", res_data["deleted"])
            
            # Verify they are deleted from disk
            self.assertFalse(os.path.exists("cache/WEEKLY_12345.json"))
            self.assertFalse(os.path.exists("cache/WEEKLY_67890.json"))
            self.assertTrue(os.path.exists("cache/daily_11111.json"))
            self.assertTrue(os.path.exists("cache/test_other.json"))
            
        finally:
            # Restore directories
            if os.path.exists("cache"):
                # Rename back to test_cache_temp so teardown removes it
                os.rename("cache", self.test_cache_dir)
            if has_real_cache and os.path.exists("cache_backup_temp"):
                os.rename("cache_backup_temp", "cache")

if __name__ == "__main__":
    unittest.main()
