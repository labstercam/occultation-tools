"""
Test script for AOTA Report Parser
Tests parsing of the example AOTA Report file
"""

import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import aota_report_parser as arp

def test_aota_report_parser():
    """Test the AOTA Report parser with the example file"""
    
    # Find the example file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    example_file = os.path.join(script_dir, '20251107_778_Theobalda_UCAC4_361_199861+Camilleri_AOTA_Report.txt')
    
    if not os.path.exists(example_file):
        print(f"ERROR: Example file not found: {example_file}")
        return False
    
    print(f"Testing with: {os.path.basename(example_file)}")
    print("=" * 60)
    
    # Parse the file
    try:
        result = arp.parse_aota_report(example_file)
        
        print(f"\nParsed {len(result['events'])} event(s)")
        print(f"Camera: {result['camera']}")
        print(f"Frames integrated: {result['frames_integrated']}")
        print(f"Video system: {result['video_system']}")
        print(f"Measurement tool: {result['measurement_tool']}")
        
        # Display each event
        for i, event in enumerate(result['events']):
            print(f"\n--- Event #{event['event_number']} ---")
            print(f"  D time (UTC): {event['d_time_utc']} ± {event['d_uncertainty']}")
            print(f"  R time (UTC): {event['r_time_utc']} ± {event['r_uncertainty']}")
            print(f"  SNR average: {event['snr_ave']}")
            
            # Test formatting for Excel
            summary = arp.get_event_summary(result, i)
            print(f"\n  Excel format:")
            print(f"    D: {summary['d_hours']}h {summary['d_minutes']}m {summary['d_seconds']}s")
            print(f"    R: {summary['r_hours']}h {summary['r_minutes']}m {summary['r_seconds']}s")
            print(f"    SNR: {summary['snr']}")
        
        print("\n" + "=" * 60)
        print("SUCCESS: AOTA Report parser test passed!")
        return True
        
    except Exception as ex:
        import traceback
        print(f"\nERROR: {ex}")
        print(traceback.format_exc())
        return False


if __name__ == '__main__':
    success = test_aota_report_parser()
    sys.exit(0 if success else 1)
