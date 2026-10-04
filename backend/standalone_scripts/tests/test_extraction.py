import unittest
import os
import sys

# Add parent dir to path to import extract_schedule
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from extract_schedule import parse_excel_schedule

class TestExtraction(unittest.TestCase):
    def test_hierarchy_extraction(self):
        # We assume this file exists in the root for our test
        test_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../Makindu_AHP_B1_B2_Programme_from_15-Sep-2026.xlsx'))
        
        if not os.path.exists(test_file):
            self.skipTest(f"Test file not found: {test_file}")
            
        hierarchy = parse_excel_schedule(test_file)
        
        # Basic validation
        self.assertGreater(len(hierarchy), 0, "Should extract at least one root task")
        
        # Check first root node
        first_node = hierarchy[0]
        self.assertIn("name", first_node)
        self.assertIn("start_date", first_node)
        self.assertIn("finish_date", first_node)
        self.assertIn("children", first_node)
        
        # Verify nesting (dynamic depths)
        if first_node["children"]:
            child = first_node["children"][0]
            self.assertIn("name", child)
            # If the child has children, that means we successfully extracted depth >= 3
            if child["children"]:
                grandchild = child["children"][0]
                self.assertIn("name", grandchild)

if __name__ == '__main__':
    unittest.main()
