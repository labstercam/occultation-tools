import os
import json
import shutil

class ConfigManager:
    """Manages all configuration and settings with persistent storage"""
    
    CONFIG_FILENAME = 'occultation_config.json'
    
    def __init__(self, config_folder=None):
        # Detect installation directory
        self.script_dir = self._detect_script_directory()
        self.install_root = self._detect_install_root()
        
        # Default configuration values
        self.default_config = {
            # User credentials
            'owc_user_email': 'your_owc_email',
            'owc_user_password': 'your_owc_password',
            
            # File names and retention
            'my_occultations_file': 'occultations.json',
            'my_latest_occultations_file': 'occultations_latest.json',
            'days_to_retain_events': 14,  # Number of days to retain events (1-400)
            
            # Recording parameters
            'base_duration': 60,
            'goto_lead_time': 240,
            'mag_for_40ms_exposure': 12.0,
            'default_gain': 450,
            'sync_mount': False,
            'display_utc': True,
            'output_debug_logs': False,
            
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
            'line_delay_calibrations': [],  # List of GPS line delay calibration runs
            
            # Report generation preferences
            'last_report_type': 'north_america',  # 'north_america' or 'trans_tasman'
            'last_report_folder': '',  # Parent folder of last AOTA/Tangra folder
            'recordings_folder': '',  # Default root folder for recordings
            
            # API configuration
            #'host': 'https://www.occultwatcher.net:443',
            'host': 'https://www.occultwatcher.net',
            'url_path': '/api2/v1/events/details-list',
            'apiKey': 'Go to https://cloud.occultwatcher.net/user-profile User Permssions to verify your email and get an API key',
            'URL_OCCELMNT_ENDPOINT_PATH': '/api2/v1/owc/event/my/%s/occelmnts',

            # Night mode
            'night_mode': False,
            
            # Warning dialogs
            'show_report_warning': True  # Show report generation warning dialog
        }
        
        # Set config folder
        if config_folder:
            self.config_folder = os.path.normpath(config_folder)
        else:
            # Use fixed data/config folder for config storage
            try:
                self.config_folder = os.path.normpath(self.get_config_folder())
                if not os.path.exists(self.config_folder):
                    os.makedirs(self.config_folder, exist_ok=True)
            except:
                self.config_folder = os.path.normpath(os.getcwd())
        
        # Initialize configuration
        self.config = self.default_config.copy()
        
        # Check if this is first startup (no config file exists)
        config_exists = os.path.exists(self.get_config_path())
        
        self.load_config()
        
        # Ensure required folders exist
        self._create_folder_structure()

        # Seed template working copies from master templates
        self._seed_template_working_copies()
        
        # Change to working directory
        try:
            os.chdir(self.get_data_root())
        except:
            print(f"Warning: Could not change to directory {self.get_data_root()}")
    
    def _detect_script_directory(self):
        """Detect the directory where the script is located"""
        try:
            # Try __file__ first (works in most Python environments)
            script_path = os.path.abspath(__file__)
            return os.path.normpath(os.path.dirname(script_path))
        except:
            pass
        
        try:
            # Try sys.argv[0] as fallback
            import sys
            if sys.argv and sys.argv[0]:
                return os.path.normpath(os.path.dirname(os.path.abspath(sys.argv[0])))
        except:
            pass
        
        # Last resort: use current working directory
        return os.path.normpath(os.getcwd())

    def _detect_install_root(self):
        """Detect install root from script location."""
        try:
            return os.path.normpath(os.path.dirname(self.script_dir))
        except:
            return os.path.normpath(os.getcwd())

    # Fixed path model
    def get_install_root(self):
        return os.path.normpath(self.install_root)

    def get_data_root(self):
        return os.path.normpath(os.path.join(self.get_install_root(), 'data'))

    def get_config_folder(self):
        return os.path.normpath(os.path.join(self.get_data_root(), 'config'))

    def get_events_folder(self):
        return os.path.normpath(os.path.join(self.get_data_root(), 'events'))

    def get_templates_folder(self):
        return os.path.normpath(os.path.join(self.get_data_root(), 'templates'))

    def get_sequences_folder(self):
        return os.path.normpath(os.path.join(self.get_data_root(), 'sequences'))

    def get_reports_folder(self):
        return os.path.normpath(os.path.join(self.get_data_root(), 'reports'))

    def get_resources_root(self):
        return os.path.normpath(os.path.join(self.get_install_root(), 'resources'))

    def get_templates_master_root(self):
        return os.path.normpath(os.path.join(self.get_resources_root(), 'templates_master'))

    def get_templates_master_sequencer_folder(self):
        return os.path.normpath(os.path.join(self.get_templates_master_root(), 'sequencer'))

    def get_templates_master_reports_folder(self):
        return os.path.normpath(os.path.join(self.get_templates_master_root(), 'reports'))
    
    def _create_folder_structure(self):
        """Create fixed folder structure"""
        try:
            folders_to_create = [
                self.get_data_root(),
                self.get_config_folder(),
                self.get_events_folder(),
                self.get_templates_folder(),
                self.get_sequences_folder(),
                self.get_reports_folder(),
                self.get_templates_master_root(),
                self.get_templates_master_sequencer_folder(),
                self.get_templates_master_reports_folder()
            ]
            
            for folder in folders_to_create:
                if folder and not os.path.exists(folder):
                    os.makedirs(folder, exist_ok=True)
                    print(f"Created folder: {folder}")
        except Exception as e:
            print(f"Warning: Could not create folder structure: {e}")

    def _seed_template_working_copies(self):
        """Copy missing template working copies from master templates."""
        try:
            master_folder = self.get_templates_master_sequencer_folder()
            working_folder = self.get_templates_folder()

            if not os.path.exists(master_folder):
                return

            for filename in os.listdir(master_folder):
                lower = filename.lower()
                if not (lower.endswith('.txt') or lower.endswith('.scs')):
                    continue

                source_path = os.path.join(master_folder, filename)
                target_path = os.path.join(working_folder, filename)

                if os.path.isfile(source_path) and not os.path.exists(target_path):
                    shutil.copy2(source_path, target_path)
                    print(f"Seeded template: {filename}")
        except Exception as e:
            print(f"Warning: Could not seed template working copies: {e}")
    
    def get_config_path(self):
        """Get the full path to the configuration file"""
        return os.path.join(self.config_folder, self.CONFIG_FILENAME)
    
    def load_config(self):
        """Load configuration from file"""
        config_path = self.get_config_path()
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
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
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)
            
            print(f"Configuration saved to: {config_path}")
            return True
        except Exception as e:
            print(f"Error saving configuration: {e}")
            return False
    
    def reset_to_defaults(self):
        """Reset configuration to default values"""
        self.config = self.default_config.copy()
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
        # Legacy accessor retained temporarily for callers not yet migrated.
        return self.get_data_root()
    
    def set_file_folder(self, folder):
        # Legacy no-op in fixed path model.
        print("set_file_folder ignored: fixed path model is enabled")
    
    def get_occultations_file(self):
        return self.config['my_occultations_file']
    
    def set_occultations_file(self, filename):
        self.config['my_occultations_file'] = filename
    
    def get_latest_occultations_file(self):
        return self.config['my_latest_occultations_file']
    
    def set_latest_occultations_file(self, filename):
        self.config['my_latest_occultations_file'] = filename
    
    def get_sequence_path(self):
        # Legacy accessor retained temporarily for callers not yet migrated.
        return self.get_sequences_folder()
    
    def set_sequence_path(self, path):
        # Legacy no-op in fixed path model.
        print("set_sequence_path ignored: fixed path model is enabled")
    
    def get_days_to_retain_events(self):
        return self.config.get('days_to_retain_events', 14)
    
    def set_days_to_retain_events(self, days):
        self.config['days_to_retain_events'] = int(days)
    
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
    
    def get_default_gain(self):
        return self.config.get('default_gain', 450)
    
    def set_default_gain(self, gain):
        self.config['default_gain'] = int(gain)

    def get_sync_mount(self):
        return self.config['sync_mount']

    def set_sync_mount(self, enabled):
        self.config['sync_mount'] = enabled

    def get_display_utc(self):
        return self.config['display_utc']

    def set_display_utc(self, enabled):
        self.config['display_utc'] = enabled

    def get_output_debug_logs(self):
        return self.config.get('output_debug_logs', False)

    def set_output_debug_logs(self, enabled):
        self.config['output_debug_logs'] = bool(enabled)

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

    # ------------------------------------------------------------------
    # v2 API URL helpers (OW-ApiKey header auth — no key in URL)
    # The existing get_full_url() / get_occelmnt_url() are unchanged.
    # ------------------------------------------------------------------

    def get_base_url(self):
        """Return the events-list URL without an apikey query parameter.

        Used with get_owc_events_v2() which passes the key as an HTTP header.
        """
        return self.config['host'] + self.config['url_path']

    def get_occelmnt_base_url(self):
        """Return the occelmnt URL template without an apikey query parameter.

        Call as  config.get_occelmnt_base_url() % event_id
        Used with get_owc_events_v2().
        """
        return self.config['host'] + self.config['URL_OCCELMNT_ENDPOINT_PATH']

    def get_report_observation_url(self):
        """Return the POST endpoint for submitting an observation report to OWC."""
        return self.config['host'] + '/api2/v1/owc/report-observation'

    def get_event_by_id_url(self, event_id):
        """Return the GET endpoint for fetching a single OWC event by its ID.

        Used to retrieve station IDs (see Task 2 of owc_api_v2_plan.md).
        """
        return self.config['host'] + '/api2/v1/events/' + str(event_id)

    def get_full_file_path(self, filename):
        """Get full path for a file in the configured folder"""
        return os.path.join(self.get_events_folder(), filename)
    
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
            folder = self.get_data_root()
            if not os.path.exists(folder):
                os.makedirs(folder, exist_ok=True)
        except Exception as e:
            errors.append(f"Cannot access/create file folder: {e}")
        
        try:
            seq_path = self.get_sequences_folder()
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
        
        # Check retention days
        retention_days = self.config.get('days_to_retain_events', 14)
        if retention_days < 1 or retention_days > 400:
            errors.append("Days to retain events must be between 1 and 400")

        if not isinstance(self.config['sync_mount'], bool):
            errors.append("Sync mount must be a boolean value")    

        if not isinstance(self.config['display_utc'], bool):
            errors.append("Display UTC must be a boolean value")    

        if not isinstance(self.config.get('output_debug_logs', False), bool):
            errors.append("Output debug logs must be a boolean value")
                

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
    
    def add_camera(self, name, detector, report_type, timing, timing_device, occult4_method='b', occult4_time='a', other_info=''):
        """Add a new camera configuration"""
        import uuid
        cameras = self.get_cameras()
        camera = {
            'id': str(uuid.uuid4()),
            'name': name,
            'detector': detector,
            'report_type': report_type,
            'timing': timing,
            'timing_device': timing_device,
            'occult4_method': occult4_method,
            'occult4_time': occult4_time,
            'other_info': other_info
        }
        cameras.append(camera)
        self.config['cameras'] = cameras
        
        # Set as active if it's the first one
        if len(cameras) == 1:
            self.config['active_camera_id'] = camera['id']
        
        return camera['id']
    
    def update_camera(self, camera_id, name, detector, report_type, timing, timing_device, occult4_method='b', occult4_time='a', other_info=''):
        """Update an existing camera configuration"""
        cameras = self.get_cameras()
        for camera in cameras:
            if camera.get('id') == camera_id:
                camera['name'] = name
                camera['detector'] = detector
                camera['report_type'] = report_type
                camera['timing'] = timing
                camera['timing_device'] = timing_device
                camera['occult4_method'] = occult4_method
                camera['occult4_time'] = occult4_time
                camera['other_info'] = other_info
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

    # ========== Line Delay Calibration Management ==========
    #
    # Each calibration run dict contains:
    #   id              - UUID string (auto-generated)
    #   camera_id       - Foreign key to the cameras list
    #   label           - User-assigned letter string, e.g. 'A', 'B', 'C'
    #   run_datetime    - ISO-8601 UTC string of when the run was recorded
    #   camera_name     - Camera model name string
    #   pc_name         - Computer name string
    #   camera_area     - Frame size string, e.g. '816x822' (binned pixels)
    #   binning         - Binning string, e.g. '1', '2'
    #   tilt            - ROI Y offset integer (unbinned pixels)
    #   pan             - ROI X offset integer (unbinned pixels)
    #   colour_space    - e.g. 'RAW16'
    #   file_format     - e.g. 'ADV'
    #   exposure_ms     - Exposure in ms (float)
    #   gain            - Gain value (float)
    #   per_line_delay  - ms/line to 3 dp (float)
    #   line_0_delay    - ms (float)
    #   measurement_method - 'GPS' (GPS flash calibration) or 'FPS' (approximate via frame rate)
    #   shutter_type    - 'Rolling' or 'Global'
    #   notes           - Optional free-text string

    def get_line_delay_calibrations(self, camera_id=None):
        """Return all line delay calibration runs, optionally filtered by camera_id."""
        runs = self.config.get('line_delay_calibrations', [])
        if camera_id is not None:
            runs = [r for r in runs if r.get('camera_id') == camera_id]
        return runs

    def get_line_delay_calibration_by_id(self, run_id):
        """Return a single calibration run by its UUID, or None."""
        for run in self.config.get('line_delay_calibrations', []):
            if run.get('id') == run_id:
                return run
        return None

    def add_line_delay_calibration(self, run_dict):
        """Append a new calibration run and save config.

        run_dict must contain at minimum: camera_id, label, per_line_delay,
        line_0_delay.  A UUID 'id' is generated automatically if not present.
        Returns the run id.
        """
        import uuid
        runs = self.config.get('line_delay_calibrations', [])
        if 'id' not in run_dict or not run_dict['id']:
            run_dict = dict(run_dict)  # avoid mutating caller's dict
            run_dict['id'] = str(uuid.uuid4())
        runs.append(run_dict)
        self.config['line_delay_calibrations'] = runs
        self.save_config()
        return run_dict['id']

    def update_line_delay_calibration(self, run_id, updates):
        """Patch fields on an existing calibration run and save config.

        Only the keys present in 'updates' are changed; the 'id' and
        'camera_id' keys are protected and cannot be overwritten.
        Returns True if the run was found and updated, False otherwise.
        """
        runs = self.config.get('line_delay_calibrations', [])
        for run in runs:
            if run.get('id') == run_id:
                for key, value in updates.items():
                    if key not in ('id', 'camera_id'):
                        run[key] = value
                self.config['line_delay_calibrations'] = runs
                self.save_config()
                return True
        return False

    def delete_line_delay_calibration(self, run_id):
        """Remove a calibration run by id and save config.

        Returns True if the run was found and deleted, False otherwise.
        """
        runs = self.config.get('line_delay_calibrations', [])
        original_count = len(runs)
        runs = [r for r in runs if r.get('id') != run_id]
        if len(runs) == original_count:
            return False
        self.config['line_delay_calibrations'] = runs
        self.save_config()
        return True

    def set_active_camera(self, camera_id):
        """Set the active camera"""
        if self.get_camera_by_id(camera_id):
            self.config['active_camera_id'] = camera_id
            return True
        return False
    
    # Report generation preferences
    def get_last_report_type(self):
        """Get the last used report type"""
        return self.config.get('last_report_type', 'north_america')
    
    def set_last_report_type(self, report_type):
        """Set the last used report type"""
        self.config['last_report_type'] = report_type
        self.save_config()
    
    def get_last_report_folder(self):
        """Get the parent folder of last selected AOTA/Tangra folder"""
        return self.config.get('last_report_folder', '')
    
    def set_last_report_folder(self, folder_path):
        """Set the parent folder of last selected AOTA/Tangra folder"""
        self.config['last_report_folder'] = os.path.normpath(folder_path) if folder_path else ''
        self.save_config()
    
    def get_recordings_folder(self):
        """Get the default root folder for recordings"""
        return self.config.get('recordings_folder', '')
    
    def set_recordings_folder(self, folder_path):
        """Set the default root folder for recordings"""
        self.config['recordings_folder'] = os.path.normpath(folder_path) if folder_path else ''
        self.save_config()
    
    # Warning dialogs
    def get_show_report_warning(self):
        """Get whether to show report generation warning dialog"""
        return self.config.get('show_report_warning', True)
    
    def set_show_report_warning(self, show):
        """Set whether to show report generation warning dialog"""
        self.config['show_report_warning'] = bool(show)
        self.save_config()
