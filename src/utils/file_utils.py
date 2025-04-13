import os
import re

def validate_file_path(file_path):
    if not file_path:
        return None
        
    path_pattern = r'([a-zA-Z]:[/\\][^:\n"*?<>|]+)'
    match = re.search(path_pattern, file_path)
    
    if match:
        potential_path = match.group(1)
        normalized_path = os.path.normpath(potential_path)
        
        dir_path = os.path.dirname(normalized_path)
        if os.path.exists(dir_path):
            return normalized_path
            
    return None

def ensure_directory_exists(file_path):
    try:
        directory = os.path.dirname(file_path)
        if not os.path.exists(directory):
            os.makedirs(directory)
        return True
    except Exception:
        return False
