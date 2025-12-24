"""
AOTA XML File Parser

Parses AOTA (Asteroid Occultation Timing Analysis) XML files to extract
event timing data for inclusion in occultation reports.

AOTA files contain:
- D_UTC and R_UTC times (disappearance and reappearance)
- Multiple sub-events with IsNonEvent flag
- Camera and measurement information
"""

import xml.etree.ElementTree as ET
import re


class AOTAEvent:
    """Represents a single event result from AOTA analysis"""
    
    def __init__(self):
        self.is_non_event = True
        self.d_frame = -1
        self.r_frame = -1
        self.d_utc = None  # Raw string
        self.r_utc = None  # Raw string
        
        # Parsed time components with original string format
        self.d_hours = None
        self.d_minutes = None
        self.d_seconds = None
        self.d_seconds_str = None  # Original string representation preserving precision
        self.d_error = None
        self.d_error_str = None  # Original string representation preserving precision
        
        self.r_hours = None
        self.r_minutes = None
        self.r_seconds = None
        self.r_seconds_str = None  # Original string representation preserving precision
        self.r_error = None
        self.r_error_str = None  # Original string representation preserving precision
    
    def parse_time(self, time_str, is_disappearance=True):
        """Parse time string in format 'HH MM SS.S ± E.E'
        
        Args:
            time_str: Time string like "10 44 45.2 ± 0.4"
            is_disappearance: True for D time, False for R time
            
        Returns:
            bool: True if parsing succeeded
        """
        if not time_str or time_str == '-1':
            return False
        
        try:
            # Pattern: HH MM SS.S ± E.E
            # Allow for variations in spacing and decimal points
            pattern = r'(\d+)\s+(\d+)\s+([\d.]+)\s*[±]\s*([\d.]+)'
            match = re.match(pattern, time_str.strip())
            
            if match:
                hours = int(match.group(1))
                minutes = int(match.group(2))
                seconds_str = match.group(3)  # Keep original string
                error_str = match.group(4)  # Keep original string
                seconds = float(seconds_str)
                error = float(error_str)
                
                if is_disappearance:
                    self.d_hours = hours
                    self.d_minutes = minutes
                    self.d_seconds = seconds
                    self.d_seconds_str = seconds_str  # Preserve original precision
                    self.d_error = error
                    self.d_error_str = error_str  # Preserve original precision
                else:
                    self.r_hours = hours
                    self.r_minutes = minutes
                    self.r_seconds = seconds
                    self.r_seconds_str = seconds_str  # Preserve original precision
                    self.r_error = error
                    self.r_error_str = error_str  # Preserve original precision
                
                return True
        except Exception as ex:
            print(f"Error parsing time '{time_str}': {ex}")
        
        return False
    
    def is_valid_event(self):
        """Check if this is a valid event with timing data"""
        return (not self.is_non_event and 
                self.d_hours is not None and 
                self.r_hours is not None)
    
    def __str__(self):
        """String representation for display in selection dialog"""
        if self.is_non_event:
            return "Non-event"
        
        if self.d_hours is not None and self.r_hours is not None:
            # Use original string representations to preserve precision
            d_time = f"{self.d_hours:02d}:{self.d_minutes:02d}:{self.d_seconds_str}"
            r_time = f"{self.r_hours:02d}:{self.r_minutes:02d}:{self.r_seconds_str}"
            duration = (self.r_hours * 3600 + self.r_minutes * 60 + self.r_seconds) - \
                      (self.d_hours * 3600 + self.d_minutes * 60 + self.d_seconds)
            return f"D: {d_time} (±{self.d_error_str}s) | R: {r_time} (±{self.r_error_str}s) | Duration: {duration:.1f}s"
        
        return "Event (incomplete data)"


class AOTACameraResult:
    """Camera and measurement information from AOTA"""
    
    def __init__(self):
        self.camera_type = None
        self.measuring_tool = None
        self.video_system = None
        self.frames_integrated = 0
        self.measurements_binned = 1
        self.measured_at_field_level = False
        self.timescale_from_measuring_tool = True
        self.camera_delays_known = False


class AOTAResult:
    """Complete AOTA analysis results"""
    
    def __init__(self):
        self.is_miss = False
        self.are_results_available = False
        self.aota_version = None
        self.camera_result = AOTACameraResult()
        self.events = []  # List of AOTAEvent objects
    
    def get_valid_events(self):
        """Get list of valid events (non-events excluded)"""
        return [e for e in self.events if e.is_valid_event()]
    
    def has_multiple_valid_events(self):
        """Check if there are multiple valid events requiring user selection"""
        return len(self.get_valid_events()) > 1
    
    def get_single_valid_event(self):
        """Get the single valid event, or None if zero or multiple"""
        valid = self.get_valid_events()
        return valid[0] if len(valid) == 1 else None


def parse_aota_file(file_path):
    """Parse an AOTA XML file
    
    Args:
        file_path: Path to .aota.xml file
        
    Returns:
        AOTAResult: Parsed AOTA data, or None if parsing failed
    """
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        result = AOTAResult()
        
        # Parse top-level elements
        is_miss = root.find('IsMiss')
        if is_miss is not None:
            result.is_miss = is_miss.text.lower() == 'true'
        
        are_results = root.find('AreResultsAvailable')
        if are_results is not None:
            result.are_results_available = are_results.text.lower() == 'true'
        
        version = root.find('AOTAVersion')
        if version is not None:
            result.aota_version = version.text
        
        # Parse CameraResult
        camera_elem = root.find('CameraResult')
        if camera_elem is not None:
            camera = result.camera_result
            
            for field_name, attr_name in [
                ('CameraType', 'camera_type'),
                ('MeasuringTool', 'measuring_tool'),
                ('VideoSystem', 'video_system')
            ]:
                elem = camera_elem.find(field_name)
                if elem is not None:
                    setattr(camera, attr_name, elem.text)
            
            frames_int = camera_elem.find('FramesIntegrated')
            if frames_int is not None:
                try:
                    camera.frames_integrated = int(frames_int.text)
                except:
                    pass
            
            meas_binned = camera_elem.find('MeasurementsBinned')
            if meas_binned is not None:
                try:
                    camera.measurements_binned = int(meas_binned.text)
                except:
                    pass
            
            for field_name, attr_name in [
                ('MeasuredAtFieldLevel', 'measured_at_field_level'),
                ('TimeScaleFromMeasuringTool', 'timescale_from_measuring_tool'),
                ('CameraDelaysKnownToAOTA', 'camera_delays_known')
            ]:
                elem = camera_elem.find(field_name)
                if elem is not None:
                    setattr(camera, attr_name, elem.text.lower() == 'true')
        
        # Parse EventResults
        # The structure has EventResults as a container with multiple EventResults children
        event_results_container = root.find('EventResults')
        if event_results_container is not None:
            for event_elem in event_results_container.findall('EventResults'):
                event = AOTAEvent()
                
                # Parse IsNonEvent
                is_non = event_elem.find('IsNonEvent')
                if is_non is not None:
                    event.is_non_event = is_non.text.lower() == 'true'
                
                # Parse frame numbers
                d_frame = event_elem.find('D_Frame')
                if d_frame is not None:
                    try:
                        event.d_frame = int(d_frame.text)
                    except:
                        pass
                
                r_frame = event_elem.find('R_Frame')
                if r_frame is not None:
                    try:
                        event.r_frame = int(r_frame.text)
                    except:
                        pass
                
                # Parse UTC times
                d_utc = event_elem.find('D_UTC')
                if d_utc is not None:
                    event.d_utc = d_utc.text
                    event.parse_time(d_utc.text, is_disappearance=True)
                
                r_utc = event_elem.find('R_UTC')
                if r_utc is not None:
                    event.r_utc = r_utc.text
                    event.parse_time(r_utc.text, is_disappearance=False)
                
                result.events.append(event)
        
        print(f"Successfully parsed AOTA file: {file_path}")
        print(f"  Version: {result.aota_version}")
        print(f"  Camera: {result.camera_result.camera_type}")
        print(f"  Measuring Tool: {result.camera_result.measuring_tool}")
        print(f"  Total events: {len(result.events)}")
        print(f"  Valid events: {len(result.get_valid_events())}")
        
        return result
        
    except Exception as ex:
        print(f"Error parsing AOTA file '{file_path}': {ex}")
        import traceback
        traceback.print_exc()
        return None


def format_aota_time_component(hours=None, minutes=None, seconds=None, seconds_str=None):
    """Format time component for Excel cell
    
    Args:
        hours: Hour value (int)
        minutes: Minute value (int)
        seconds: Second value (float) - not used if seconds_str provided
        seconds_str: Original string representation of seconds (preserves precision)
        
    Returns:
        str: Formatted string or empty string if None
    """
    if hours is not None:
        return str(hours)
    elif minutes is not None:
        return str(minutes)
    elif seconds_str is not None:
        # Use original string to preserve precision
        return seconds_str
    elif seconds is not None:
        # Fallback if string not available
        return f"{seconds:.1f}"
    return ""


def format_aota_error(error, error_str=None):
    """Format error value for Excel cell
    
    Args:
        error: Error value (float) - not used if error_str provided
        error_str: Original string representation of error (preserves precision)
        
    Returns:
        str: Formatted string or empty string if None
    """
    if error_str is not None:
        # Use original string to preserve precision
        return error_str
    elif error is not None:
        # Fallback if string not available
        return f"{error:.1f}"
    return ""
