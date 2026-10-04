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
                pct = task['percentage']
                if name not in cumulative or pct > cumulative[name]:
                    cumulative[name] = pct
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

def find_task_in_hierarchy(tasks, target_name):
    """Recursively searches for a task by name in the hierarchical schedule."""
    for task in tasks:
        if task['name'].strip() == target_name.strip():
            return task
        if task.get('children'):
            found = find_task_in_hierarchy(task['children'], target_name)
            if found:
                return found
    return None

def calculate_planned_date(start_date_str, finish_date_str, percentage):
    """
    Interpolates the planned date based on start date, finish date, and % complete.
    If 100%, it returns finish_date. If 50%, it returns the midway date.
    """
    if percentage >= 100:
        return datetime.strptime(finish_date_str, '%Y-%m-%d')
    if percentage <= 0:
        return datetime.strptime(start_date_str, '%Y-%m-%d')
        
    start = datetime.strptime(start_date_str, '%Y-%m-%d')
    finish = datetime.strptime(finish_date_str, '%Y-%m-%d')
    
    total_days = (finish - start).days
    days_to_add = total_days * (percentage / 100.0)
    
    return start + timedelta(days=days_to_add)

def calculate_variance(planned_date, report_date_str):
    """
    Calculates the variance in days.
    Variance = Planned Date - Report Date
    Positive means ahead of schedule. Negative means behind schedule.
    """
    report_date = datetime.strptime(report_date_str, '%Y-%m-%d')
    variance = (planned_date - report_date).days
    return variance

def save_weekly_snapshot(week_number, report_date_str, component, tasks, notes):
    """
    Calculates variance, creates a snapshot record, and saves it to the JSON datastore.
    """
    # 1. Load the corresponding schedule
    schedule = load_schedule(component)
    
    task_records = []
    total_variance = 0
    valid_tasks = 0

    for t in tasks:
        task_name = t['task_name']
        percentage = t['percentage']
        
        # 2. Find the task
        task = find_task_in_hierarchy(schedule, task_name)
        if not task:
            continue
            
        start = task.get('start_date')
        finish = task.get('finish_date')
        
        if not start or not finish:
            continue
            
        # 3. Calculate Planned Date & Variance
        planned_date = calculate_planned_date(start, finish, percentage)
        variance_days = calculate_variance(planned_date, report_date_str)
        
        task_records.append({
            "task_name": task_name,
            "percentage": percentage,
            "path": t.get('path', ''),
            "planned_date": planned_date.strftime('%Y-%m-%d'),
            "variance_days": variance_days
        })
        
        total_variance += variance_days
        valid_tasks += 1

    overall_variance = round(total_variance / valid_tasks) if valid_tasks > 0 else 0
    
    # 4. Create record
    record = {
        "week_number": week_number,
        "report_date": report_date_str,
        "component": component,
        "tasks": task_records,
        "variance_days": overall_variance,
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
