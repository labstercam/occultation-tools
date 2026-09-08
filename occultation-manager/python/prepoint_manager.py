"""
Prepoint Manager for Occultation Manager
IronPython-compatible implementation of prepoint calculations
Simplified formulas based on spherical trigonometry without AstroPy dependency
"""

import clr
import math
from datetime import datetime, timedelta
from System.Windows.Forms import Form, Label, Button, GroupBox, TextBox, ComboBox, CheckBox
from System.Drawing import Point, Size, Color, Font, FontStyle
from System import Double

class PrepointCalculator:
    """Simplified prepoint calculations using spherical trigonometry"""
    
    def __init__(self, lat, lon, elev=0):
        """
        Initialize with observer coordinates
        
        Args:
            lat: Latitude in degrees (North positive)
            lon: Longitude in degrees (East positive)
            elev: Elevation in meters (optional)
        """
        self.lat = lat
        self.lon = lon
        self.elev = elev
    
    def calculate_sidereal_time(self, utc_time, longitude):
        """
        Calculate Local Sidereal Time (LST) in hours
        Reuses DummyEventGenerator.calculate_sidereal_time()
        
        Args:
            utc_time: datetime object in UTC
            longitude: observer longitude in degrees (East positive)
        
        Returns:
            LST in hours (0-24)
        """
        # Import and use DummyEventGenerator function
        try:
            from dummy_event_generator import DummyEventGenerator
            return DummyEventGenerator.calculate_sidereal_time(utc_time, longitude)
        except ImportError:
            return 'error'

    def saemundsson_refraction(alt_deg):
        """
        Saemundsson formula for atmospheric refraction
        R = 1.02 / tan(h + 10.3/(h + 5.11)) [arcminutes]
        Args:
            alt_deg: True altitude in degrees
        Returns:
            Refraction in degrees
        No correction for temperature or pressure. Assumes 10 C, 1010 hPa
        """
        if alt_deg <= 0:
            return 0.0
        
        # Saemundsson formula (in arcminutes)
        R_corrected_deg = 1.02 / math.tan(math.radians(alt_deg + 10.3/(alt_deg + 5.11)))/60.0
       
        
        # Convert to degrees
        return R_corrected_deg
        
    
    def ra_dec_to_altaz(self, ra_hours, dec_degrees, utc_time):
        """
        Convert RA/Dec to Alt/Az (degrees) using Astrid's fast algorithm
        Reference: https://astrogreg.com/convert_ra_dec_to_alt_az.html
        
        Args:
            ra_hours: RA in hours (0-24)
            dec_degrees: Dec in degrees (-90 to 90)
            utc_time: datetime object in UTC
        
        Returns:
            (alt_deg, az_deg) tuple
        """
        # Convert RA from hours to degrees
        ra_deg = ra_hours * 15.0
        
        # Convert to radians
        ra_rad = math.radians(ra_deg)
        dec_rad = math.radians(dec_degrees)
        lat_rad = math.radians(self.lat)
        lon_rad = math.radians(self.lon)
        
        # Calculate Local Sidereal Time (LST)
        lst_hours = self.calculate_sidereal_time(utc_time, self.lon)
        lst_rad = math.radians(lst_hours * 15.0)
        
        # Calculate Hour Angle (H = LST - RA)
        H = lst_rad - ra_rad
        # Normalize to [-π, π]
        if H < -math.pi:
            H += 2.0 * math.pi
        if H > math.pi:
            H -= 2.0 * math.pi
        
        # Standard formula for altitude (same as Astrid's)
        # alt = asin(sin(lat) * sin(dec) + cos(lat) * cos(dec) * cos(H))
        sin_alt = math.sin(lat_rad) * math.sin(dec_rad) + math.cos(lat_rad) * math.cos(dec_rad) * math.cos(H)
        sin_alt = max(-1.0, min(1.0, sin_alt))
        alt_rad = math.asin(sin_alt)
        
        # Standard formula for azimuth (North-based, 0°=North)
        cos_alt = math.cos(alt_rad)
        if abs(cos_alt) < 1e-10:
            az_rad = 0.0
        else:
            sin_az = -math.sin(H) * math.cos(dec_rad) / cos_alt
            cos_az = (
                math.sin(dec_rad) - math.sin(alt_rad) * math.sin(lat_rad)
            ) / (cos_alt * math.cos(lat_rad))
            az_rad = math.atan2(sin_az, cos_az)
        
        # Convert to degrees
        alt_deg = math.degrees(alt_rad)
        az_deg = math.degrees(az_rad)
        
        # Normalize azimuth to 0-360 (North-based, 0°=North)
        az_deg = (az_deg + 360.0) % 360.0
        
        # Debug logging
        # print("[Astrid Alt/Az Debug] RA={:.4f}h, Dec={:.4f}°".format(ra_hours, dec_degrees))
        # print("[Astrid Alt/Az Debug] LST={:.4f}h, H={:.4f}rad ({:.2f}°)".format(lst_hours, H, math.degrees(H)))
        # print("[Astrid Alt/Az Debug] Calculated: Alt={:.2f}°, Az={:.2f}°".format(alt_deg, az_deg))
        
        # Simplified atmospheric refraction correction
        #alt_deg +=  self.saemundsson_refraction(alt_deg)
        
        return alt_deg, az_deg
    
    def altaz_to_radec(self, alt_deg, az_deg, utc_time):
        """
        Convert Alt/Az back to RA/Dec (hours, degrees)
        Inverse of Astrid's fastRaDecToAltAz algorithm
        
        Args:
            alt_deg: Altitude in degrees (0-90)
            az_deg: Azimuth in degrees (0-360) - North-based (0°=North)
            utc_time: datetime object in UTC
        
        Returns:
            (ra_hours, dec_degrees) tuple
        """
        # Debug logging
        # print("[AltAzToRADec Debug] Input: Alt={:.4f}°, Az={:.4f}°".format(alt_deg, az_deg))
        # print("[AltAzToRADec Debug] Site: lat={:.4f}°, lon={:.4f}°".format(self.lat, self.lon))
        # print("[AltAzToRADec Debug] Time: {}".format(utc_time))
        
        # Convert to radians
        alt_rad = math.radians(alt_deg)
        az_rad_north = math.radians(az_deg)  # North-based azimuth
        lat_rad = math.radians(self.lat)
        
        # Remove simplified atmospheric refraction if applied
        #alt_deg -=  self.saemundsson_refraction(alt_deg)
                
        # Calculate Declination using standard formula with North-based azimuth
        # sin(dec) = sin(alt) * sin(lat) + cos(alt) * cos(lat) * cos(az)
        sin_dec = math.sin(alt_rad) * math.sin(lat_rad) + math.cos(alt_rad) * math.cos(lat_rad) * math.cos(az_rad_north)
        sin_dec = max(-1.0, min(1.0, sin_dec))
        dec_rad = math.asin(sin_dec)
        dec_degrees = math.degrees(dec_rad)
        print("[AltAzToRADec Debug] Calculated Dec: {:.4f}°".format(dec_degrees))
        
        # Calculate Hour Angle using standard formula with North-based azimuth
        # For North-based azimuth (0°=North):
        # cos(H) = (sin(alt) - sin(lat) * sin(dec)) / (cos(lat) * cos(dec))
        # sin(H) = -sin(az) * cos(alt) / cos(dec)
        
        if abs(math.cos(dec_rad)) < 1e-10:
            # Near celestial pole, hour angle is ill-defined
            ha_rad = 0.0
            print("[AltAzToRADec Debug] Near celestial pole, HA=0")
        else:
            # Standard formula for North-based azimuth (0°=North)
            cos_ha = (math.sin(alt_rad) - math.sin(lat_rad) * math.sin(dec_rad)) / (math.cos(lat_rad) * math.cos(dec_rad))
            sin_ha = -math.sin(az_rad_north) * math.cos(alt_rad) / math.cos(dec_rad)  # Negative sign for North-based
            
            # Clamp values to avoid numerical issues
            cos_ha = max(-1.0, min(1.0, cos_ha))
            sin_ha = max(-1.0, min(1.0, sin_ha))
            
            print("[AltAzToRADec Debug] sin(HA)={:.6f}, cos(HA)={:.6f}".format(sin_ha, cos_ha))
            
            # Use atan2 to get correct quadrant and sign
            ha_rad = math.atan2(sin_ha, cos_ha)
        
        ha_hours = math.degrees(ha_rad) / 15.0
        print("[AltAzToRADec Debug] Hour Angle: {:.4f}h ({:.2f}°)".format(ha_hours, ha_hours * 15))
        
        # Calculate RA from LST and HA
        lst_hours = self.calculate_sidereal_time(utc_time, self.lon)
        print("[AltAzToRADec Debug] LST: {:.4f}h".format(lst_hours))
        
        ra_hours = (lst_hours - ha_hours) % 24
        print("[AltAzToRADec Debug] Calculated RA: {:.4f}h".format(ra_hours))
        
        return ra_hours, dec_degrees
    
    def calculate_prepoint(self, target_ra_hours, target_dec_degrees, event_time_utc, prepoint_offset_seconds=10, event_alt=None, event_az=None):
        """
        Calculate prepoint coordinates for telescope pointing without tracking
        
        Args:
            target_ra_hours: Target RA in hours
            target_dec_degrees: Target Dec in degrees
            event_time_utc: Event time (datetime UTC)
            prepoint_offset_seconds: How many seconds before event to prepoint
            event_alt: Optional Altitude from event (if available, more accurate)
            event_az: Optional Azimuth from event (if available, more accurate)
        
        Returns:
            (prepoint_ra_hours, prepoint_dec_degrees, prepoint_time)
        """
        # Debug logging
        print("[Prepoint Debug] Target: RA={:.4f}h, Dec={:.4f}°".format(target_ra_hours, target_dec_degrees))
        print("[Prepoint Debug] Event time: {}".format(event_time_utc))
        print("[Prepoint Debug] Site: lat={:.4f}°, lon={:.4f}°".format(self.lat, self.lon))
        
        # 1. Get target Alt/Az at event time
        try:
            alt_event, az_event = self.ra_dec_to_altaz(target_ra_hours, target_dec_degrees, event_time_utc)
            print("[Prepoint Debug] Calculated Alt/Az at event: Alt={:.4f}°, Az={:.4f}°".format(alt_event, az_event))
        except:
            # Use event Alt/Az from OW Cloud if error
            alt_event = event_alt
            az_event = event_az
            print("[Prepoint Debug] Using event Alt/Az from OW Cloud: Alt={:.4f}°, Az={:.4f}°".format(alt_event, az_event))
        
        # 2. Keep same Alt/Az for prepoint time (drift into position)
        # Prepoint time is BEFORE the event, not from current time
        prepoint_time = event_time_utc - timedelta(seconds=prepoint_offset_seconds)
        print("[Prepoint Debug] Prepoint time: {} ({}s before event)".format(prepoint_time, prepoint_offset_seconds))
        
        # 3. Convert Alt/Az back to RA/DEC at prepoint time
        ra_prepoint, dec_prepoint = self.altaz_to_radec(alt_event, az_event, prepoint_time)
        print("[Prepoint Debug] Prepoint coordinates: RA={:.4f}h, Dec={:.4f}°".format(ra_prepoint, dec_prepoint))
        
        return ra_prepoint, dec_prepoint, prepoint_time
    
    def calculate_drift_info(self, target_ra_hours, target_dec_degrees, event_time_utc, fov_width_deg=1.0, fov_height_deg=1.0, prepoint_offset_seconds=10):
        """
        Calculate drift information for prepoint
        
        Args:
            target_ra_hours, target_dec_degrees: Target coordinates
            event_time_utc: Event time
            fov_width_deg, fov_height_deg: Field of view dimensions
            prepoint_offset_seconds: How many seconds before event to prepoint
        
        Returns:
            Dict with drift time, direction, etc.
        """
        # Calculate Alt/Az at event time
        alt_event, az_event = self.ra_dec_to_altaz(target_ra_hours, target_dec_degrees, event_time_utc)
        
        # Calculate Alt/Az at prepoint time (event time - offset)
        prepoint_time = event_time_utc - timedelta(seconds=prepoint_offset_seconds)
        alt_prepoint, az_prepoint = self.ra_dec_to_altaz(target_ra_hours, target_dec_degrees, prepoint_time)
        
        # Calculate drift rates
        alt_diff = alt_event - alt_prepoint
        az_diff = az_event - az_prepoint
        
        # Estimate time to drift through FOV
        # Simple approximation: drift rate = change per second
        time_diff_seconds = prepoint_offset_seconds
        
        if time_diff_seconds > 0:
            alt_rate = alt_diff / time_diff_seconds  # degrees per second
            az_rate = az_diff / time_diff_seconds   # degrees per second
            
            # Time to drift through FOV (approximate)
            alt_time = fov_height_deg / abs(alt_rate) if abs(alt_rate) > 0 else float('inf')
            az_time = fov_width_deg / abs(az_rate) if abs(az_rate) > 0 else float('inf')
            drift_time_min = min(alt_time, az_time) / 60  # Convert to minutes
        else:
            alt_rate = 0
            az_rate = 0
            drift_time_min = 0
        
        return {
            'alt_event': alt_event,
            'az_event': az_event,
            'alt_prepoint': alt_prepoint,
            'az_prepoint': az_prepoint,
            'alt_diff': alt_diff,
            'az_diff': az_diff,
            'alt_rate_deg_per_sec': alt_rate,
            'az_rate_deg_per_sec': az_rate,
            'drift_time_minutes': drift_time_min,
            'time_to_event_seconds': time_diff_seconds,
            'prepoint_time': prepoint_time
        }


class PrepointMountController:
    """Handle mount operations for prepoint positioning"""
    
    def __init__(self, sharpcap=None):
        self.sharpcap = sharpcap
        self.mount = None
        if sharpcap and hasattr(sharpcap, 'Mounts') and sharpcap.Mounts.SelectedMount:
            self.mount = sharpcap.Mounts.SelectedMount
    
    def is_mount_available(self):
        """Check if mount is connected and available"""
        return self.mount is not None and self.mount.CanGoto
    
    def goto_prepoint(self, alt_deg, az_deg, ra_hours=None, dec_degrees=None):
        """
        Slew mount to prepoint coordinates
        
        Args:
            alt_deg: Altitude in degrees (if using Alt/Az)
            az_deg: Azimuth in degrees (if using Alt/Az)
            ra_hours: RA in hours (if using RA/Dec - preferred)
            dec_degrees: Dec in degrees (if using RA/Dec - preferred)
        
        Returns:
            True if successful, False otherwise
        """
        if not self.is_mount_available():
            return False
        
        try:
            # Disable tracking if mount supports it
            if hasattr(self.mount, 'CanSetTracking') and self.mount.CanSetTracking:
                self.mount.Tracking = False
                # Set tracking rate to Off (no tracking)
                # Assuming TrackingRate enum exists with Off value
                if hasattr(self.mount, 'TrackingRate'):
                    try:
                        # Try to set TrackingRate to None (no tracking)
                        # Use string-based approach to avoid Python keyword issues
                        # SharpCap may have specific enum values like "None", "Sidereal", etc.
                        self.mount.TrackingRate = -1  # Common convention: -1 = None/Off
                    except:
                        # If enum not available, just disable tracking
                        pass
            
            # Prefer RA/Dec if provided (more reliable)
            if ra_hours is not None and dec_degrees is not None:
                print("[Mount Debug] Slew to RA={:.4f}h, Dec={:.4f}°".format(ra_hours, dec_degrees))
                try:
                    # Try SlewToCoordinates if available
                    if hasattr(self.mount, 'SlewToCoordinates'):
                        self.mount.SlewToCoordinates(ra_hours, dec_degrees)
                        print("[Mount Debug] SlewToCoordinates succeeded")
                        return True
                    # Fallback to Alt/Az
                    else:
                        print("[Mount Debug] SlewToCoordinates not available, using Alt/Az")
                except Exception as e:
                    print("[Mount Debug] SlewToCoordinates failed: " + str(e))
                    # Fallback to Alt/Az
            
            # Use Alt/Az (fallback or primary)
            print("[Mount Debug] Slew to Alt={:.1f}°, Az={:.1f}°".format(alt_deg, az_deg))
            
            # Check if mount supports Alt/Az slewing
            if not hasattr(self.mount, 'SlewToAltAz'):
                print("[Mount Debug] Mount does not support Alt/Az slewing")
                return False
            
            try:
                self.mount.SlewToAltAz(alt_deg, az_deg)
                print("[Mount Debug] Alt/Az slew command sent")
                return True
            except Exception as e:
                print("[Mount Debug] Alt/Az slew failed: " + str(e))
                return False
            
        except Exception as e:
            print("Slew failed: " + str(e))
            return False
    
    def get_current_altaz(self):
        """
        Get current mount Alt/Az coordinates
        
        Returns:
            (alt_deg, az_deg) tuple or None if unavailable
        """
        if self.mount:
            try:
                alt = self.mount.Altitude
                az = self.mount.Azimuth
                return alt, az
            except Exception:
                return None, None
        return None, None
    
    def get_tracking_status(self):
        """Get current tracking status"""
        if self.mount and hasattr(self.mount, 'Tracking'):
            return self.mount.Tracking
        return False