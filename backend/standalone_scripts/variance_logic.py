import os
import json
from datetime import datetime, timedelta

SNAPSHOTS_FILE = os.path.join(os.path.dirname(__file__), 'weekly_snapshots.json')
SCHEDULES_DIR = os.path.join(os.path.dirname(__file__), '..', 'extracted_schedules')
LOCKED_WEEKS_FILE = os.path.join(os.path.dirname(__file__), 'locked_weeks.json')

def get_cumulative_progress(component, up_to_week):
    if not os.path.exists(SNAPSHOTS_FILE):
        return {}
    with open(SNAPSHOTS_FILE, 'r') as f:
        try:
            snapshots = json.load(f)
        except json.JSONDecodeError:
            return {}
            
    cumulative = {}
    for snap in snapshots:
        if snap['component'] == component and snap['week_number'] < up_to_week:
            for task in snap.get('tasks', []):
                name = task['task_name']
                path = task.get('path', '')
                key = f"{path}::{name}" if path else name
                pct = task['percentage']
                if key not in cumulative or pct > cumulative[key]:
                    cumulative[key] = pct
    return cumulative

def get_locked_weeks():
    if not os.path.exists(LOCKED_WEEKS_FILE):
        return []
    with open(LOCKED_WEEKS_FILE, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def lock_week(week_number):
    locks = get_locked_weeks()
    if week_number not in locks:
        locks.append(week_number)
        with open(LOCKED_WEEKS_FILE, 'w') as f:
            json.dump(locks, f)
    return locks

def load_schedule(component_name):
    """Loads the JSON schedule for a given component."""
    filepath = os.path.join(SCHEDULES_DIR, f"{component_name}.json")
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Schedule for {component_name} not found at {filepath}")
    with open(filepath, 'r') as f:
        return json.load(f)

def find_task_in_hierarchy(tasks, target_name, target_path, current_path=""):
    """Recursively searches for a task by name and path in the hierarchical schedule."""
    for task in tasks:
        if task['name'].strip() == target_name.strip() and (current_path or "") == (target_path or ""):
            return task
        if task.get('children'):
            new_path = f"{current_path} > {task['name']}" if current_path else task['name']
            found = find_task_in_hierarchy(task['children'], target_name, target_path, new_path)
            if found:
                return found
    return None

def calculate_variance_days(start_date_str, finish_date_str, report_date_str, percentage):
    """
    Calculates the variance in days based on specific reporting rules:
    - If 100% complete, check against finish date.
    - If started early (report < start), days ahead = start - report.
    - If ongoing within timeline (start <= report <= finish), variance = 0 (On track).
    - If ongoing but late (report > finish), days behind = finish - report.
    """
    start = datetime.strptime(start_date_str, '%Y-%m-%d')
    finish = datetime.strptime(finish_date_str, '%Y-%m-%d')
    report = datetime.strptime(report_date_str, '%Y-%m-%d')
    
    if percentage >= 100:
        if report < finish:
            # Finished earlier than the planned finish date
            return (finish - report).days
        else:
            # report >= finish: We know it was done by the reporting date, but don't know exactly when. Show Completed.
            return "Completed"
    
    if percentage > 0:
        if report < start:
            return (start - report).days
        elif report > finish:
            return (finish - report).days
        else:
            return 0
    
    return 0

def save_weekly_snapshot(week_number, report_date_str, component, tasks, notes, source_id=None):
    """
    Calculates variance, creates a snapshot record, and saves it to the JSON datastore.
    """
    # 1. Load the corresponding schedule
    schedule_file_name = source_id if source_id else component
    schedule = load_schedule(schedule_file_name)
    
    task_records = []

    for t in tasks:
        task_name = t['task_name']
        percentage = t['percentage']
        
        task_path = t.get('path', '')
        # 2. Find the task
        task = find_task_in_hierarchy(schedule, task_name, task_path)
        if not task:
            continue
            
        start = task.get('start_date')
        finish = task.get('finish_date')
        
        if not start or not finish:
            continue
            
        # 3. Calculate Variance
        variance_days = calculate_variance_days(start, finish, report_date_str, percentage)
        
        task_records.append({
            "task_name": task_name,
            "percentage": percentage,
            "path": t.get('path', ''),
            "planned_date": finish, # Keeping finish date as a reference
            "variance_days": variance_days
        })

    # 4. Create record
    record = {
        "week_number": week_number,
        "report_date": report_date_str,
        "component": component,
        "tasks": task_records,
        "notes": notes,
        "timestamp": datetime.now().isoformat()
    }
    
    # 5. Save to Datastore
    snapshots = []
    if os.path.exists(SNAPSHOTS_FILE):
        with open(SNAPSHOTS_FILE, 'r') as f:
            try:
                snapshots = json.load(f)
            except json.JSONDecodeError:
                snapshots = []
                
    # Check if we are updating an existing entry for this week + component
    updated = False
    for i, snap in enumerate(snapshots):
        if snap['week_number'] == week_number and snap['component'] == component:
            snapshots[i] = record
            updated = True
            break
            
    if not updated:
        snapshots.append(record)
        
    with open(SNAPSHOTS_FILE, 'w') as f:
        json.dump(snapshots, f, indent=2)
        
    return record

def get_snapshots_for_week(week_number):
    """Retrieves all snapshot records for a specific week."""
    if not os.path.exists(SNAPSHOTS_FILE):
        return []
    with open(SNAPSHOTS_FILE, 'r') as f:
        try:
            snapshots = json.load(f)
            return [s for s in snapshots if s['week_number'] == week_number]
        except json.JSONDecodeError:
            return []
