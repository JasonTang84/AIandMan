import os
import re
from typing import List
from pathlib import Path

def parse_text_prompts(content: str) -> List[str]:
    """Parse semicolon-separated prompts from text content"""
    # Split by semicolon and clean up
    prompts = [prompt.strip() for prompt in content.split(';')]
    
    # Remove empty prompts and filter out very short ones
    prompts = [prompt for prompt in prompts if len(prompt) > 5]
    
    # Clean up prompts - remove extra whitespace and newlines
    cleaned_prompts = []
    for prompt in prompts:
        # Replace multiple whitespace/newlines with single space
        cleaned_prompt = re.sub(r'\s+', ' ', prompt).strip()
        if cleaned_prompt:
            cleaned_prompts.append(cleaned_prompt)
    
    return cleaned_prompts

def ensure_output_folder(folder_path: str) -> bool:
    """Ensure the output folder exists, create if it doesn't"""
    try:
        Path(folder_path).mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        print(f"Error creating output folder: {str(e)}")
        return False

def validate_image_file(file_path: str) -> bool:
    """Validate if a file is a supported image format"""
    supported_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}
    return Path(file_path).suffix.lower() in supported_extensions

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe saving"""
    # Remove or replace invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Limit length
    if len(filename) > 200:
        name, ext = os.path.splitext(filename)
        filename = name[:190] + ext
    return filename

def get_safe_filename(base_name: str, extension: str, output_folder: str) -> str:
    """Generate a safe, unique filename"""
    base_name = sanitize_filename(base_name)
    filename = f"{base_name}.{extension}"
    filepath = os.path.join(output_folder, filename)
    
    # Add counter if file already exists
    counter = 1
    while os.path.exists(filepath):
        filename = f"{base_name}_{counter}.{extension}"
        filepath = os.path.join(output_folder, filename)
        counter += 1
    
    return filename

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"

def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to specified length with ellipsis"""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."