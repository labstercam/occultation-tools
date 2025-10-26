import os
import json

class ConfigManager:
    """Manages all configuration and settings with persistent storage"""
    
    CONFIG_FILENAME = 'occultation_config.json'
    
    def __init__(self, config_folder=None):
        # Default configuration values
        self.default_config = {
            # User credentials
            'owc_user_email': 'your_owc_email',
            'owc_user_password': 'your_owc_password',
            
            # File paths
            'my_file_folder': os.path.normpath(r'C:\Users\AstroPC\Documents\SharpCap'),
            'my_occultations_file': 'occultations.json',
            'my_latest_occultations_file': 'occultations_latest.json',
            'sequence_path': '',  # Will be set to my_file_folder if empty
            
            # Recording parameters
            'base_duration': 60,
            'goto_lead_time': 240,
            'mag_for_40ms_exposure': 12.0,
            'sync_mount': True,
            'display_utc': True,
            
            # API configuration
            'host': 'https://www.occultwatcher.net:443',
            'url_path': '/api2/v1/events/details-list',
            'apiKey': 'Go to https://cloud.occultwatcher.net/user-profile User Permssions to verify your email and get an API key',
            'URL_OCCELMNT_ENDPOINT_PATH': '/api2/v1/owc/event/my/%s/occelmnts',

            # Night mode
            'night_mode': False
        }
        
        # Set config folder
        if config_folder:
            self.config_folder = os.path.normpath(config_folder)
        else:
            # Use default folder or current directory if not accessible
            try:
                self.config_folder = os.path.normpath(self.default_config['my_file_folder'])
                if not os.path.exists(self.config_folder):
                    os.makedirs(self.config_folder, exist_ok=True)
            except:
                self.config_folder = os.path.normpath(os.getcwd())
        
        # Initialize configuration
        self.config = self.default_config.copy()
        self.load_config()
        
        # Set sequence_path to my_file_folder if empty
        if not self.config['sequence_path']:
            self.config['sequence_path'] = self.config['my_file_folder']
            
        # Ensure all paths use proper separators
        self._normalize_paths()
        
        # Change to working directory
        try:
            os.chdir(self.get_file_folder())
        except:
            print(f"Warning: Could not change to directory {self.get_file_folder()}")
    
    def _normalize_paths(self):
        """Normalize all path configurations"""
        path_keys = ['my_file_folder', 'sequence_path']
        for key in path_keys:
            if key in self.config and self.config[key]:
                self.config[key] = os.path.normpath(self.config[key])
    
    def get_config_path(self):
        """Get the full path to the configuration file"""
        return os.path.join(self.config_folder, self.CONFIG_FILENAME)
    
    def load_config(self):
        """Load configuration from file"""
        config_path = self.get_config_path()
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    saved_config = json.load(f)
                
                # Update current config with saved values
                for key, value in saved_config.items():
                    if key in self.default_config:
                        self.config[key] = value
                
                print(f"Configuration loaded from: {config_path}")
            else:
                print(f"No configuration file found. Using defaults.")
                self.save_config()  # Save defaults
        except Exception as e:
            print(f"Error loading configuration: {e}")
            print("Using default configuration")
    
    def save_config(self):
        """Save current configuration to file"""
        config_path = self.get_config_path()
        try:
            # Ensure config directory exists
            os.makedirs(self.config_folder, exist_ok=True)
            
            with open(config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            
            print(f"Configuration saved to: {config_path}")
            return True
        except Exception as e:
            print(f"Error saving configuration: {e}")
            return False
    
    def reset_to_defaults(self):
        """Reset configuration to default values"""
        self.config = self.default_config.copy()
        self._normalize_paths()
        return self.save_config()
    
    # User credentials
    def get_owc_email(self):
        return self.config['owc_user_email']
    
    def set_owc_email(self, email):
        self.config['owc_user_email'] = email
    
    def get_owc_password(self):
        return self.config['owc_user_password']
    
    def set_owc_password(self, password):
        self.config['owc_user_password'] = password
    
    # File paths
    def get_file_folder(self):
        return os.path.normpath(self.config['my_file_folder'])
    
    def set_file_folder(self, folder):
        self.config['my_file_folder'] = os.path.normpath(folder)
    
    def get_occultations_file(self):
        return self.config['my_occultations_file']
    
    def set_occultations_file(self, filename):
        self.config['my_occultations_file'] = filename
    
    def get_latest_occultations_file(self):
        return self.config['my_latest_occultations_file']
    
    def set_latest_occultations_file(self, filename):
        self.config['my_latest_occultations_file'] = filename
    
    def get_sequence_path(self):
        return os.path.normpath(self.config['sequence_path'])
    
    def set_sequence_path(self, path):
        self.config['sequence_path'] = os.path.normpath(path)
    
    # Recording parameters
    def get_base_duration(self):
        return self.config['base_duration']
    
    def set_base_duration(self, duration):
        self.config['base_duration'] = int(duration)
    
    def get_goto_lead_time(self):
        return self.config['goto_lead_time']
    
    def set_goto_lead_time(self, time):
        self.config['goto_lead_time'] = int(time)
    
    def get_mag_for_40ms_exposure(self):
        return self.config['mag_for_40ms_exposure']
    
    def set_mag_for_40ms_exposure(self, magnitude):
        self.config['mag_for_40ms_exposure'] = float(magnitude)

    def get_sync_mount(self):
        return self.config['sync_mount']

    def set_sync_mount(self, enabled):
        self.config['sync_mount'] = enabled

    def get_display_utc(self):
        return self.config['display_utc']

    def set_display_utc(self, enabled):
        self.config['display_utc'] = enabled

    # API configuration
    def get_host(self):
        return self.config['host']
    
    def set_host(self, host):
        self.config['host'] = host
    
    def get_api_key(self):
        return self.config['apiKey']
    
    def set_api_key(self, key):
        self.config['apiKey'] = key
    
    def get_full_url(self):
        """Get the complete API URL with key"""
        import binascii
        base_url = self.config['host'] + self.config['url_path']
        sep = '&' if '?' in base_url else '?'
        #return base_url + sep + 'apikey=%s' % binascii.unhexlify(self.config['apiKey'].encode()).decode('ascii')
        return base_url + sep + 'apikey=%s' % self.config['apiKey']
    
    def get_occelmnt_url(self):
        """Get the complete occelmnt URL with key"""
        import binascii
        base_url = self.config['host'] + self.config['URL_OCCELMNT_ENDPOINT_PATH']
        sep = '&' if '?' in base_url else '?'
        #return base_url + sep + 'apikey=%s' % binascii.unhexlify(self.config['apiKey'].encode()).decode('ascii')
        return base_url + sep + 'apikey=%s' % self.config['apiKey']
    
    def get_full_file_path(self, filename):
        """Get full path for a file in the configured folder"""
        return os.path.join(self.get_file_folder(), filename)
    
    def validate_config(self):
        """Validate current configuration"""
        errors = []
        
        # Check required fields
        if not self.config['owc_user_email']:
            errors.append("OWC email is required")
        
        if not self.config['owc_user_password']:
            errors.append("OWC password is required")
        
        # Check paths exist or can be created
        try:
            folder = self.get_file_folder()
            if not os.path.exists(folder):
                os.makedirs(folder, exist_ok=True)
        except Exception as e:
            errors.append(f"Cannot access/create file folder: {e}")
        
        try:
            seq_path = self.get_sequence_path()
            if not os.path.exists(seq_path):
                os.makedirs(seq_path, exist_ok=True)
        except Exception as e:
            errors.append(f"Cannot access/create sequence path: {e}")
        
        # Check numeric values
        if self.config['base_duration'] <= 0:
            errors.append("Base duration must be positive")
        
        if self.config['goto_lead_time'] <= 0:
            errors.append("GOTO lead time must be positive")
        
        if self.config['mag_for_40ms_exposure'] <= 0:
            errors.append("Magnitude for 40ms exposure must be positive")

        if not isinstance(self.config['sync_mount'], bool):
            errors.append("Sync mount must be a boolean value")    

        if not isinstance(self.config['display_utc'], bool):
            errors.append("Display UTC must be a boolean value")    
                

        return errors

    def get_night_mode(self):
        """Get night mode setting"""
        return self.config.get('night_mode', False)
    
    def set_night_mode(self, enabled):
        """Set night mode setting"""
        self.config['night_mode'] = enabled