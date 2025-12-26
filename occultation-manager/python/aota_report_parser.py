"""
AOTA Report Parser
Parses AOTA_Report.txt files to extract event timing and SNR data.
Compatible with IronPython 2.7 (uses standard library only).
"""

import re


def parse_aota_report(file_path):
    """
    Parse an AOTA_Report.txt file.
    
    Parameters:
        file_path: Path to the AOTA_Report.txt file
        
    Returns:
        Dictionary with structure:
        {
            'events': [
                {
                    'event_number': 1,
                    'd_time_utc': '10 44 45.2',  # H M S.s format
                    'd_uncertainty': 0.4,
                    'r_time_utc': '10 44 47.2',
                    'r_uncertainty': 0.5,
                    'snr_ave': 4.5
                },
                ...
            ],
            'camera': 'ADVS - corrected',
            'frames_integrated': 0,
            'video_system': 'ADVS or AAV',
            'measurement_tool': 'Tangra'
        }
    """
    try:
        with open(file_path, 'r') as f:
            content = f.read()
    except (IOError, OSError) as e:
        print(f"Error reading AOTA Report file: {e}")
        return None
    
    result = {
        'events': [],
        'camera': None,
        'frames_integrated': None,
        'video_system': None,
        'measurement_tool': None
    }
    
    # Split content by event sections
    event_sections = re.split(r'Event #(\d+)', content)
    
    # First element is header, then alternating event numbers and content
    # Check if we have at least one event
    if len(event_sections) < 3:
        # No events found
        return result
    
    for i in range(1, len(event_sections), 2):
        if i + 1 >= len(event_sections):
            break  # Safety check
        event_num = int(event_sections[i])
        event_content = event_sections[i + 1]
        
        event_data = {
            'event_number': event_num,
            'd_time_utc': None,
            'd_uncertainty': None,
            'r_time_utc': None,
            'r_uncertainty': None,
            'snr_ave': None
        }
        
        # Extract D time from "Event time in UTC" section
        d_match = re.search(r'D:\s+(\d+\s+\d+\s+[\d.]+)\s*±\s*([\d.]+)', event_content)
        if d_match:
            event_data['d_time_utc'] = d_match.group(1)
            event_data['d_uncertainty'] = float(d_match.group(2))
        
        # Extract R time from "Event time in UTC" section
        r_match = re.search(r'R:\s+(\d+\s+\d+\s+[\d.]+)\s*±\s*([\d.]+)', event_content)
        if r_match:
            event_data['r_time_utc'] = r_match.group(1)
            event_data['r_uncertainty'] = float(r_match.group(2))
        
        # Extract SNR average from "SN at event locations" section
        snr_match = re.search(r'Ave:\s*([\d.]+)', event_content)
        if snr_match:
            event_data['snr_ave'] = float(snr_match.group(1))
        
        result['events'].append(event_data)
    
    # Extract camera details (from anywhere in file)
    camera_match = re.search(r'Camera\s*:\s*(.+)', content)
    if camera_match:
        result['camera'] = camera_match.group(1).strip()
    
    frames_match = re.search(r'Frames integrated\s*:\s*(\d+)', content)
    if frames_match:
        result['frames_integrated'] = int(frames_match.group(1))
    
    video_match = re.search(r'Video system\s*:\s*(.+)', content)
    if video_match:
        result['video_system'] = video_match.group(1).strip()
    
    measurement_match = re.search(r'Measurement tool\s*:\s*(.+)', content)
    if measurement_match:
        result['measurement_tool'] = measurement_match.group(1).strip()
    
    return result


def format_time_for_excel(time_str):
    """
    Convert AOTA time format (H M S.s) to separate hours, minutes, seconds.
    
    Parameters:
        time_str: Time string in format "10 44 45.2"
        
    Returns:
        Dictionary with 'hours', 'minutes', 'seconds' as strings
    """
    if not time_str:
        return {'hours': '', 'minutes': '', 'seconds': ''}
    
    parts = time_str.split()
    return {
        'hours': parts[0] if len(parts) > 0 else '',
        'minutes': parts[1] if len(parts) > 1 else '',
        'seconds': parts[2] if len(parts) > 2 else ''
    }


def get_event_summary(aota_report_data, event_index=0):
    """
    Get timing and SNR data for a specific event.
    
    Parameters:
        aota_report_data: Dictionary returned from parse_aota_report()
        event_index: Index of the event to extract (0-based)
        
    Returns:
        Dictionary with formatted timing data:
        {
            'd_hours': '10',
            'd_minutes': '44',
            'd_seconds': '45.2',
            'r_hours': '10',
            'r_minutes': '44',
            'r_seconds': '47.2',
            'snr': 4.5
        }
    """
    if not aota_report_data or not aota_report_data['events']:
        return None
    
    if event_index >= len(aota_report_data['events']):
        event_index = 0
    
    event = aota_report_data['events'][event_index]
    
    d_time = format_time_for_excel(event['d_time_utc'])
    r_time = format_time_for_excel(event['r_time_utc'])
    
    return {
        'd_hours': d_time['hours'],
        'd_minutes': d_time['minutes'],
        'd_seconds': d_time['seconds'],
        'd_uncertainty': event.get('d_uncertainty'),
        'r_hours': r_time['hours'],
        'r_minutes': r_time['minutes'],
        'r_seconds': r_time['seconds'],
        'r_uncertainty': event.get('r_uncertainty'),
        'snr': event.get('snr_ave')  # Use .get() to safely handle missing SNR
    }
