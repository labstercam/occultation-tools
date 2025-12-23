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
            'my_file_folder': os.path.normpath(os.path.dirname(__file__)),
            'my_occultations_file': 'occultations.json',
            'my_latest_occultations_file': 'occultations_latest.json',
            'sequence_path': '',  # Will be set to my_file_folder if empty
            
            # Recording parameters
            'base_duration': 60,
            'goto_lead_time': 240,
            'mag_for_40ms_exposure': 12.0,
            'sync_mount': True,
            'display_utc': True,
            
            # Observer information for NA Report Form
            'observer_name': '',
            'observer_email': '',
            'observer_address': '',
            'observer_city': '',
            'observer_state': '',
            'observer_country': '',
            'observer_phone': '',
            'observer_fax': '',
            
            # Telescope information for NA Report Form (legacy - kept for backward compatibility)
            'telescope_aperture': 0,  # mm
            'telescope_focal_length': 0,  # mm
            'telescope_type': 'SCT including Cass and Mak',
            
            # Multiple telescopes and cameras support
            'telescopes': [],  # List of telescope configurations
            'cameras': [],  # List of camera configurations
            'active_telescope_id': None,  # ID of currently selected telescope
            'active_camera_id': None,  # ID of currently selected camera
            
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

    # Observer configuration
    def get_observer_name(self):
        return self.config.get('observer_name', '')
    
    def set_observer_name(self, name):
        self.config['observer_name'] = name
    
    def get_observer_email(self):
        return self.config.get('observer_email', '')
    
    def set_observer_email(self, email):
        self.config['observer_email'] = email
    
    def get_observer_address(self):
        return self.config.get('observer_address', '')
    
    def set_observer_address(self, address):
        self.config['observer_address'] = address
    
    def get_observer_city(self):
        return self.config.get('observer_city', '')
    
    def set_observer_city(self, city):
        self.config['observer_city'] = city
    
    def get_observer_state(self):
        return self.config.get('observer_state', '')
    
    def set_observer_state(self, state):
        self.config['observer_state'] = state
    
    def get_observer_country(self):
        return self.config.get('observer_country', '')
    
    def set_observer_country(self, country):
        self.config['observer_country'] = country
    
    def get_observer_phone(self):
        return self.config.get('observer_phone', '')
    
    def set_observer_phone(self, phone):
        self.config['observer_phone'] = phone
    
    def get_observer_fax(self):
        return self.config.get('observer_fax', '')
    
    def set_observer_fax(self, fax):
        self.config['observer_fax'] = fax
    
    # Telescope configuration
    def get_telescope_aperture(self):
        return self.config.get('telescope_aperture', 0)
    
    def set_telescope_aperture(self, aperture):
        self.config['telescope_aperture'] = int(aperture)
    
    def get_telescope_focal_length(self):
        return self.config.get('telescope_focal_length', 0)
    
    def set_telescope_focal_length(self, focal_length):
        self.config['telescope_focal_length'] = int(focal_length)
    
    def get_telescope_type(self):
        return self.config.get('telescope_type', 'SCT including Cass and Mak')
    
    def set_telescope_type(self, tel_type):
        self.config['telescope_type'] = tel_type

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
    
    # ========== Telescope Management ==========
    
    def get_telescopes(self):
        """Get list of all telescope configurations"""
        return self.config.get('telescopes', [])
    
    def get_telescope_by_id(self, telescope_id):
        """Get a specific telescope by ID"""
        telescopes = self.get_telescopes()
        for telescope in telescopes:
            if telescope.get('id') == telescope_id:
                return telescope
        return None
    
    def get_active_telescope(self):
        """Get the currently active telescope configuration"""
        active_id = self.config.get('active_telescope_id')
        if active_id:
            telescope = self.get_telescope_by_id(active_id)
            if telescope:
                return telescope
        
        # Fallback to legacy single telescope config
        if self.config.get('telescope_aperture', 0) > 0:
            return {
                'id': 'legacy',
                'name': 'Default Telescope',
                'aperture': self.config.get('telescope_aperture', 0),
                'focal_ratio': 0,  # Legacy config doesn't store focal_ratio
                'type': self.config.get('telescope_type', 'SCT including Cass and Mak')
            }
        
        # Return first telescope if available
        telescopes = self.get_telescopes()
        return telescopes[0] if telescopes else None
    
    def add_telescope(self, name, aperture, focal_ratio, tel_type):
        """Add a new telescope configuration"""
        import uuid
        telescopes = self.get_telescopes()
        telescope = {
            'id': str(uuid.uuid4()),
            'name': name,
            'aperture': float(aperture),
            'focal_ratio': float(focal_ratio),
            'type': tel_type
        }
        telescopes.append(telescope)
        self.config['telescopes'] = telescopes
        
        # Set as active if it's the first one
        if len(telescopes) == 1:
            self.config['active_telescope_id'] = telescope['id']
        
        return telescope['id']
    
    def update_telescope(self, telescope_id, name, aperture, focal_ratio, tel_type):
        """Update an existing telescope configuration"""
        telescopes = self.get_telescopes()
        for telescope in telescopes:
            if telescope.get('id') == telescope_id:
                telescope['name'] = name
                telescope['aperture'] = float(aperture)
                telescope['focal_ratio'] = float(focal_ratio)
                telescope['type'] = tel_type
                self.config['telescopes'] = telescopes
                return True
        return False
    
    def delete_telescope(self, telescope_id):
        """Delete a telescope configuration"""
        telescopes = self.get_telescopes()
        telescopes = [t for t in telescopes if t.get('id') != telescope_id]
        self.config['telescopes'] = telescopes
        
        # Clear active if deleting the active telescope
        if self.config.get('active_telescope_id') == telescope_id:
            self.config['active_telescope_id'] = telescopes[0]['id'] if telescopes else None
        
        return True
    
    def set_active_telescope(self, telescope_id):
        """Set the active telescope"""
        if self.get_telescope_by_id(telescope_id):
            self.config['active_telescope_id'] = telescope_id
            return True
        return False
    
    # ========== Camera Management ==========
    
    def get_cameras(self):
        """Get list of all camera configurations"""
        return self.config.get('cameras', [])
    
    def get_camera_by_id(self, camera_id):
        """Get a specific camera by ID"""
        cameras = self.get_cameras()
        for camera in cameras:
            if camera.get('id') == camera_id:
                return camera
        return None
    
    def get_active_camera(self):
        """Get the currently active camera configuration"""
        active_id = self.config.get('active_camera_id')
        if active_id:
            camera = self.get_camera_by_id(active_id)
            if camera:
                return camera
        
        # Return first camera if available
        cameras = self.get_cameras()
        return cameras[0] if cameras else None
    
    def add_camera(self, name, detector, timing, timing_device, other_info='', video_format='SER', exposure_integration='Other'):
        """Add a new camera configuration"""
        import uuid
        cameras = self.get_cameras()
        camera = {
            'id': str(uuid.uuid4()),
            'name': name,
            'detector': detector,
            'timing': timing,
            'timing_device': timing_device,
            'other_info': other_info,
            'video_format': video_format,
            'exposure_integration': exposure_integration
        }
        cameras.append(camera)
        self.config['cameras'] = cameras
        
        # Set as active if it's the first one
        if len(cameras) == 1:
            self.config['active_camera_id'] = camera['id']
        
        return camera['id']
    
    def update_camera(self, camera_id, name, detector, timing, timing_device, other_info='', video_format='SER', exposure_integration='Other'):
        """Update an existing camera configuration"""
        cameras = self.get_cameras()
        for camera in cameras:
            if camera.get('id') == camera_id:
                camera['name'] = name
                camera['detector'] = detector
                camera['timing'] = timing
                camera['timing_device'] = timing_device
                camera['other_info'] = other_info
                camera['video_format'] = video_format
                camera['exposure_integration'] = exposure_integration
                self.config['cameras'] = cameras
                return True
        return False
    
    def delete_camera(self, camera_id):
        """Delete a camera configuration"""
        cameras = self.get_cameras()
        cameras = [c for c in cameras if c.get('id') != camera_id]
        self.config['cameras'] = cameras
        
        # Clear active if deleting the active camera
        if self.config.get('active_camera_id') == camera_id:
            self.config['active_camera_id'] = cameras[0]['id'] if cameras else None
        
        return True
    
    def set_active_camera(self, camera_id):
        """Set the active camera"""
        if self.get_camera_by_id(camera_id):
            self.config['active_camera_id'] = camera_id
            return True
        return False