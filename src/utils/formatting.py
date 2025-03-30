def format_bytes(size: int) -> str:
    """Format bytes to human readable string"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} TB"

def format_object_ref(obj_ref: str) -> str:
    """Format object reference for display"""
    # Remove hash ID if present
    if '@' in obj_ref:
        obj_ref = obj_ref.split('@')[0]
    return obj_ref.strip()

def format_task_name(task_name: str) -> str:
    """Format task name for display"""
    # Remove common prefixes and suffixes
    prefixes = ['task', 'Task', 'TASK']
    suffixes = ['Task', 'TASK']
    
    for prefix in prefixes:
        if task_name.startswith(prefix):
            task_name = task_name[len(prefix):]
            
    for suffix in suffixes:
        if task_name.endswith(suffix):
            task_name = task_name[:-len(suffix)]
            
    return task_name.strip()

def format_device_name(device: str) -> str:
    """Format device name for display"""
    # Convert common device names to more readable format
    device_map = {
        'CPU': 'CPU',
        'GPU': 'GPU',
        'FPGA': 'FPGA',
        'ACCELERATOR': 'Accelerator'
    }
    return device_map.get(device, device)
