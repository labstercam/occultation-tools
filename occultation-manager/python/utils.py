import os
from datetime import datetime
from templates import TemplateManager
import urllib.request
import json
import time


def get_location_name_from_coordinates(latitude, longitude, timeout=10):
    """
    Look up nearest city/town for given coordinates using Nominatim (OpenStreetMap)
    Returns formatted location string, or None if lookup fails
    
    For US: "City, ST" (e.g., "Atlanta, GA")
    For others: "City, COUNTRY" (e.g., "Auckland, NZ")
    
    Args:
        latitude: Latitude in decimal degrees
        longitude: Longitude in decimal degrees
        timeout: Request timeout in seconds
    
    Returns:
        str: Formatted location string, or None if lookup fails
    """
    try:
        # Nominatim API - free OpenStreetMap geocoding service
        # Important: Must include User-Agent header as per usage policy
        url = "https://nominatim.openstreetmap.org/reverse?format=json&lat={}&lon={}&zoom=10&addressdetails=1".format(
            latitude, longitude)
        
        request = urllib.request.Request(url)
        request.add_header('User-Agent', 'OccultationManager/1.0 (Astronomical observation tool)')
        
        # Nominatim requires 1 second between requests (rate limit)
        time.sleep(1)
        
        response = urllib.request.urlopen(request, timeout=timeout)
        data = json.loads(response.read().decode('utf-8'))
        
        if 'address' in data:
            address = data['address']
            country_code = address.get('country_code', '').upper()
            
            # Try to get city/town name with preference for main city over suburbs/districts
            # For conurbations, prefer higher-level administrative areas over local districts
            city = None
            
            # Priority 1: Check county/state/region first for major metropolitan areas
            # This handles cases like "Auckland Region" which should become "Auckland"
            for field in ['state', 'county', 'region', 'state_district']:
                if field in address and address[field]:
                    location_name = address[field]
                    # Extract main city name by removing common suffixes
                    for suffix in [' Region', ' County', ' District', ' Metropolitan Area', ' Council']:
                        if location_name.endswith(suffix):
                            location_name = location_name[:-len(suffix)].strip()
                            break
                    # Use this if it's not a generic administrative term
                    if location_name and location_name.lower() not in ['region', 'county', 'district', 'state']:
                        city = location_name
                        break
            
            # Priority 2: Actual 'city' field (only if not found in county/region)
            if not city and 'city' in address and address['city']:
                city = address['city']
            
            # Priority 3: Town
            if not city and 'town' in address and address['town']:
                city = address['town']
            
            # Priority 4: Village/hamlet/municipality (avoid suburb/city_district as they're too local)
            if not city:
                city = (address.get('village') or 
                       address.get('hamlet') or
                       address.get('municipality'))
            
            if not city:
                print("No city/town found in geocoding result")
                return None
            
            # Format based on country
            if country_code == 'US':
                # US format: City, ST
                state_code = address.get('state_code', address.get('state', ''))
                if state_code:
                    # Extract just the state abbreviation if it's in "US-XX" format
                    if '-' in state_code:
                        state_code = state_code.split('-')[1]
                    location_str = "{}, {}".format(city, state_code)
                else:
                    location_str = "{}, USA".format(city)
            else:
                # International format: City, COUNTRY_CODE
                location_str = "{}, {}".format(city, country_code)
            
            print("Location lookup successful: {}".format(location_str))
            return location_str
        
        print("No address data returned from geocoding API")
        return None
        
    except urllib.error.URLError as e:
        print("Network error during location lookup: {}".format(e))
        return None
    except Exception as e:
        print("Error looking up location: {}".format(e))
        return None


def get_elevation_from_coordinates(latitude, longitude, timeout=10):
    """
    Look up elevation for given coordinates using Open-Elevation API
    Returns elevation in meters relative to WGS84 datum, or None if lookup fails
    
    Args:
        latitude: Latitude in decimal degrees
        longitude: Longitude in decimal degrees
        timeout: Request timeout in seconds
    
    Returns:
        float: Elevation in meters, or None if lookup fails
    """
    try:
        # Open-Elevation API - free, no API key required
        url = "https://api.open-elevation.com/api/v1/lookup?locations={},{}".format(latitude, longitude)
        
        request = urllib.request.Request(url)
        request.add_header('User-Agent', 'OccultationManager/1.0')
        
        response = urllib.request.urlopen(request, timeout=timeout)
        data = json.loads(response.read().decode('utf-8'))
        
        if 'results' in data and len(data['results']) > 0:
            elevation = data['results'][0].get('elevation')
            if elevation is not None:
                print("Elevation lookup successful: {} meters at {}, {}".format(elevation, latitude, longitude))
                return float(elevation)
        
        print("No elevation data returned from API")
        return None
        
    except urllib.error.URLError as e:
        print("Network error during elevation lookup: {}".format(e))
        return None
    except Exception as e:
        print("Error looking up elevation: {}".format(e))
        return None


def save_occultation_sequence(occ, template_path="", sequence_path=None, config=None):
    """Format occultation data into readable report and save it"""
    if sequence_path is None:
        sequence_path = config.get_sequence_path()
    
    # Load template
    template_content = TemplateManager.load_template(template_path, config)
    if not template_content:
        print("No template file found!")
        return False
    
    # Handle both OccultationEvent objects and dictionaries
    if hasattr(occ, 'start_time_str'):  # It's an OccultationEvent object
        start_time = datetime.strptime(occ.start_time_str, '%Y-%m-%dT%H:%M:%S')
        clean_name = "".join(c for c in occ.name if c.isalnum() or c in ('(',')',' ', '-', '_')).rstrip()
        seq_name = start_time.strftime('%Y%m%d') + ' ' + clean_name + '.scs'
        
        occ_dict = {
            'object_name': occ.object_name,
            'event_time': occ.event_time,
            'start_time': occ.start_time_str,
            'goto_time': occ.goto_time_str,
            'recording_duration': occ.recording_duration,
            'star_mag': occ.star_mag,
            'comb_mag': occ.comb_mag,
            'mag_drop': occ.mag_drop,
            'event_uncertainty': occ.event_uncertainty,
            'ra': occ.ra,
            'dec': occ.dec,
            'asteroid_name': occ.object_name,
            'exposure': occ.get_exposure_seconds(),  # Use current exposure (custom or calculated)
            'gain': occ.gain_value,  # Use current gain (custom or default)
            'name': occ.name,
            'station_name': occ.station_name,
            # Add simple local time strings
            'event_time_local': occ.event_time_local,
            'start_time_local': occ.start_time_local,
            'goto_time_local': occ.goto_time_local,
            'pre_goto_time_local': occ.pre_goto_time_local           
        }
    else:  # It's a dictionary (legacy format)
        start_time = datetime.strptime(occ['start_time'], '%Y-%m-%dT%H:%M:%S')
        clean_name = "".join(c for c in occ['name'] if c.isalnum() or c in ('(',')',' ', '-', '_')).rstrip()
        seq_name = start_time.strftime('%Y%m%d') + ' ' + clean_name + '.scs'
        occ_dict = occ
        # Add empty local time fields if not present
        if 'event_time_local' not in occ_dict:
            occ_dict.update({
                'event_time_local': '',
                'start_time_local': '',
                'goto_time_local': '',
                'pre_goto_time_local': ''
            })        
    
    try:
        # Ensure directory exists
        if not os.path.exists(sequence_path):
            os.makedirs(sequence_path, exist_ok=True)
        
        full_seq_path = os.path.join(sequence_path, seq_name)
        
        report = template_content.format(
            object_name=occ_dict.get('object_name', ''),
            event_time=occ_dict.get('event_time', ''),
            start_time=occ_dict.get('start_time', ''),
            goto_time=occ_dict.get('goto_time', ''),
            recording_duration=format(occ_dict.get('recording_duration', 0),'.0f'),
            star_mag= format(occ_dict.get('star_mag', 0),'.1f'),
            comb_mag= format(occ_dict.get('comb_mag', 0),'.1f'),
            mag_drop= format(occ_dict.get('mag_drop', 0),'.1f'),
            time_error= format(occ_dict.get('event_uncertainty', 0),'.1f'),
            ra= format(occ_dict.get('ra', 0),'.6f'),
            dec= format(occ_dict.get('dec', 0),'.6f'),
            asteroid_name=occ_dict.get('object_name', ''),
            exposure= format(occ_dict.get('exposure', 0),'.3f'),
            gain=occ_dict.get('gain', 450),
            # Add local time template variables
            event_time_local=occ_dict.get('event_time_local', ''),
            start_time_local=occ_dict.get('start_time_local', ''),
            goto_time_local=occ_dict.get('goto_time_local', ''),
            pre_goto_time_local=occ_dict.get('pre_goto_time_local', '') 
        )
        
        with open(full_seq_path, 'w') as f:
            f.write(report)
        
        return True
        
    except Exception as e:
        print(f"Error creating sequence: {e}")
        return False

