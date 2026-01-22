import os
from datetime import datetime

class TemplateManager:
    """Handles template file operations"""
    
    def __init__(self, config):
        self.config = config
    
    @staticmethod
    def find_template_files(template_folder=None):
        """Find all template files in the specified folder"""
        template_files = []
        try:
            if os.path.exists(template_folder):
                for file in os.listdir(template_folder):
                    if file.lower().endswith('.txt') and 'template' in file.lower():
                        template_files.append(file)
            template_files.sort()
        except Exception as e:
            print(f"Error finding template files: {e}")
        
        return template_files, template_folder
    
    @staticmethod
    def get_template_info(template_path):
        """Get template file information"""
        try:
            size = os.path.getsize(template_path)
            mtime = datetime.fromtimestamp(os.path.getmtime(template_path))
            return size, mtime
        except:
            return 0, datetime.min
    
    @staticmethod
    def load_template(template_path, config=None):
        """Load template content from file"""
        try:
            if template_path and os.path.exists(template_path):
                with open(template_path, 'r') as f:
                    return f.read()
            else:
                return None
        except Exception as e:
            print(f"Error loading template: {e}")
            return None