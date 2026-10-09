import os
import sys
import json

# Ensure we can import the standalone scripts
sys.path.append(os.path.join(os.path.dirname(__file__), 'standalone_scripts'))

from variance_logic import save_weekly_snapshot, get_cumulative_progress, load_schedule
import variance_logic

def run_test():
    # Clear out files
    with open(variance_logic.SNAPSHOTS_FILE, 'w') as f:
        json.dump([], f)
    with open(variance_logic.LOCKED_WEEKS_FILE, 'w') as f:
        json.dump([], f)

    print("--- Test Started ---")
    source_id = "Makindu_AHP_B1_B2_Programme_from_15-Sep-2026"
    
    # 1. Fill B1 week 44
    print("Saving B1 Week 44 snapshot...")
    save_weekly_snapshot(
        week_number=44,
        report_date_str="2026-09-27",
        component="Block_B1",
        tasks=[
            {"task_name": "Fixing of steel Reinforcement", "percentage": 100.0, "path": "SECOND FLOOR > Columns & Lift Walls"},
            {"task_name": "Masonry Blocks walls installation", "percentage": 30.0, "path": "SECOND FLOOR"}
        ],
        notes="B1 Week 44 notes",
        source_id=source_id
    )

    # 2. Fill B2 week 44 (Different tasks)
    print("Saving B2 Week 44 snapshot...")
    save_weekly_snapshot(
        week_number=44,
        report_date_str="2026-09-27",
        component="Block_B2",
        tasks=[
            {"task_name": "Casting", "percentage": 50.0, "path": "SECOND FLOOR > Columns & Lift Walls"}
        ],
        notes="B2 Week 44 notes",
        source_id=source_id
    )

    # 3. "Lock" week 44
    print("Locking week 44...")
    with open(variance_logic.LOCKED_WEEKS_FILE, 'w') as f:
        json.dump([44], f)

    # 4. Open Week 45 for B1 and see if cumulative progress is correct
    print("\nFetching cumulative progress for B1 up to week 45...")
    b1_cum = get_cumulative_progress("Block_B1", 45)
    print(f"B1 Cumulative Progress: {b1_cum}")
    assert b1_cum.get("SECOND FLOOR > Columns & Lift Walls::Fixing of steel Reinforcement") == 100.0, "B1 missing 100% task"
    assert b1_cum.get("SECOND FLOOR::Masonry Blocks walls installation") == 30.0, "B1 missing 30% task"

    # 5. Open Week 45 for B2 and see if cumulative progress is separated
    print("Fetching cumulative progress for B2 up to week 45...")
    b2_cum = get_cumulative_progress("Block_B2", 45)
    print(f"B2 Cumulative Progress: {b2_cum}")
    assert b2_cum.get("SECOND FLOOR > Columns & Lift Walls::Casting") == 50.0, "B2 missing 50% task"
    assert "SECOND FLOOR > Columns & Lift Walls::Fixing of steel Reinforcement" not in b2_cum, "B2 incorrectly contains B1's task!"

    # 6. Fill B1 week 45 (Update 30% to 70%)
    print("\nSaving B1 Week 45 snapshot (Updating 30% to 70%)...")
    save_weekly_snapshot(
        week_number=45,
        report_date_str="2026-10-04",
        component="Block_B1",
        tasks=[
            # 100% task is not sent by frontend unless modified, but wait, frontend sends everything in selectedTasks!
            {"task_name": "Fixing of steel Reinforcement", "percentage": 100.0, "path": "SECOND FLOOR > Columns & Lift Walls"},
            {"task_name": "Masonry Blocks walls installation", "percentage": 70.0, "path": "SECOND FLOOR"}
        ],
        notes="B1 Week 45 notes",
        source_id=source_id
    )

    # 7. Check Week 46 for B1
    print("Fetching cumulative progress for B1 up to week 46...")
    b1_cum_46 = get_cumulative_progress("Block_B1", 46)
    print(f"B1 Cumulative Progress (Week 46): {b1_cum_46}")
    assert b1_cum_46.get("SECOND FLOOR::Masonry Blocks walls installation") == 70.0, "B1 failed to update task to 70%"

    print("\n--- Testing Variance Days Logic ---")
    from variance_logic import calculate_variance_days
    
    # Case 1: 100% complete, report date >= finish date -> "Completed"
    v1 = calculate_variance_days("2026-09-01", "2026-09-10", "2026-09-12", 100)
    assert v1 == "Completed", f"Expected 'Completed', got {v1}"
    print("Case 1 Passed: 100% complete after finish date returns 'Completed'")

    # Case 1b: 100% complete, report date == finish date -> "Completed"
    v1b = calculate_variance_days("2026-09-01", "2026-09-10", "2026-09-10", 100)
    assert v1b == "Completed", f"Expected 'Completed', got {v1b}"
    print("Case 1b Passed: 100% complete exactly on finish date returns 'Completed'")

    # Case 2: 100% complete, report date < finish date -> Days Ahead
    v2 = calculate_variance_days("2026-09-01", "2026-09-10", "2026-09-08", 100)
    assert v2 == 2, f"Expected 2, got {v2}"
    print("Case 2 Passed: 100% complete before finish date calculates Days Ahead correctly (2 days)")

    # Case 3: >0% complete, report date < start date -> Days Ahead
    v3 = calculate_variance_days("2026-09-05", "2026-09-10", "2026-09-03", 50)
    assert v3 == 2, f"Expected 2, got {v3}"
    print("Case 3 Passed: Started early calculates Days Ahead correctly (2 days)")

    # Case 4: >0% complete, start <= report <= finish -> On track (0)
    v4 = calculate_variance_days("2026-09-01", "2026-09-10", "2026-09-05", 50)
    assert v4 == 0, f"Expected 0, got {v4}"
    print("Case 4 Passed: Ongoing task within timeline is On Track (0 variance)")

    # Case 5: >0% complete, report date > finish date -> Days Behind (Negative)
    v5 = calculate_variance_days("2026-09-01", "2026-09-10", "2026-09-12", 50)
    assert v5 == -2, f"Expected -2, got {v5}"
    print("Case 5 Passed: Ongoing task past deadline calculates Days Behind correctly (-2 days)")

    # Case 6: 0% complete, should be 0 variance
    v6 = calculate_variance_days("2026-09-01", "2026-09-10", "2026-09-12", 0)
    assert v6 == 0, f"Expected 0, got {v6}"
    print("Case 6 Passed: Not started task returns 0 variance by default")

    # 8. Update B2 week 45 Casting to 90%
    print("\nSaving B2 Week 45 snapshot (Updating Casting from 50% to 90%)...")
    b2_w45_record = save_weekly_snapshot(
        week_number=45,
        report_date_str="2026-10-04",
        component="Block_B2",
        tasks=[
            {"task_name": "Casting", "percentage": 90.0, "path": "SECOND FLOOR > Columns & Lift Walls"}
        ],
        notes="B2 Week 45 notes",
        source_id=source_id
    )
    for t in b2_w45_record['tasks']:
        print(f"--> Saved Task: {t['task_name']} | Path: {t['path']} | %: {t['percentage']} | Variance: {t['variance_days']} days")

    print("\n--- ALL TESTS PASSED! Logic is working flawlessly! ---")

if __name__ == "__main__":
    run_test()
