import os
from datetime import datetime
from templates import TemplateManager

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
            'name': occ.name,
            'station_name': occ.station_name,
            # Add simple local time strings
            'event_time_local': occ.event_time_local,
            'start_time_local': occ.start_time_local,
            'goto_time_local': occ.goto_time_local            
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
                'goto_time_local': ''
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
            # Add local time template variables
            event_time_local=occ_dict.get('event_time_local', ''),
            start_time_local=occ_dict.get('start_time_local', ''),
            goto_time_local=occ_dict.get('goto_time_local', '') 
        )
        
        with open(full_seq_path, 'w') as f:
            f.write(report)
        
        return True
        
    except Exception as e:
        print(f"Error creating sequence: {e}")
        return False

