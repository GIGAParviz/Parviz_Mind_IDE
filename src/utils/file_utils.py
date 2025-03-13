"""
Utility functions for file operations
"""

import os
import re

def validate_file_path(file_path):
    """
    Validates and sanitizes a file path to ensure it's a valid path
    
    Args:
        file_path (str): The file path to validate
        
    Returns:
        str or None: The sanitized file path if valid, None otherwise
    """
    if not file_path:
        return None
        
    # Remove any non-path content that might be mixed in with instructions
    # Look for patterns like "D:/path/to/file" or "D:\\path\\to\\file"
    path_pattern = r'([a-zA-Z]:[/\\][^:\n"*?<>|]+)'
    match = re.search(path_pattern, file_path)
    
    if match:
        potential_path = match.group(1)
        # Normalize path separators
        normalized_path = os.path.normpath(potential_path)
        
        # Check if the directory exists
        dir_path = os.path.dirname(normalized_path)
        if os.path.exists(dir_path):
            return normalized_path
            
    return None

def ensure_directory_exists(file_path):
    """
    Ensures that the directory for the given file path exists
    
    Args:
        file_path (str): The file path
        
    Returns:
        bool: True if the directory exists or was created, False otherwise
    """
    try:
        directory = os.path.dirname(file_path)
        if not os.path.exists(directory):
            os.makedirs(directory)
        return True
    except Exception:
        return False