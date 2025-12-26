# Test script for SharpCap IronPython - Tangra Light Curve Analysis
# This script tests the light_curves_iron.py functions in SharpCap's IronPython environment
#
# Usage: Run this script in SharpCap's IronPython scripting console

import clr
clr.AddReference('System.Windows.Forms')
clr.AddReference('System.Drawing')

from System.Windows.Forms import OpenFileDialog, MessageBox, MessageBoxButtons, MessageBoxIcon, DialogResult
from System.IO import Path as SystemPath
import sys
import os

# Add the module path if needed
script_dir = SystemPath.GetDirectoryName(__file__)
if script_dir not in sys.path:
    sys.path.append(script_dir)

# Import the IronPython-compatible light curve functions
try:
    import light_curves_iron as lc
    print("Successfully imported light_curves_iron module")
except ImportError as e:
    MessageBox.Show(
        "Failed to import light_curves_iron module.\nError: " + str(e),
        "Import Error",
        MessageBoxButtons.OK,
        MessageBoxIcon.Error
    )
    raise


def format_value(value, decimals=3):
    """Format a numeric value for display"""
    if value is None:
        return "N/A"
    try:
        if isinstance(value, float):
            return "{:.{prec}f}".format(value, prec=decimals)
        else:
            return str(value)
    except:
        return str(value)


def display_results(summary):
    """Display analysis results in a formatted message box"""
    
    # Build the results message
    message = "=== TANGRA LIGHT CURVE ANALYSIS RESULTS ===\n\n"
    
    message += "FILE INFORMATION:\n"
    message += "  File: " + summary['filename_from_tangra'] + "\n\n"
    
    message += "OBSERVATION TIMES:\n"
    message += "  Start Time: " + summary['start_time'] + "\n"
    message += "  End Time: " + summary['end_time'] + "\n\n"
    
    message += "EXPOSURE TIMING (ms):\n"
    message += "  Median (Exposure): " + format_value(summary['tdelta_median'], 3) + " ms\n"
    message += "  Mean: " + format_value(summary['tdelta_mean'], 3) + " ms\n"
    message += "  Std Dev: " + format_value(summary['tdelta_std'], 3) + " ms\n"
    message += "  Min: " + format_value(summary['tdelta_min'], 3) + " ms\n"
    message += "  Max: " + format_value(summary['tdelta_max'], 3) + " ms\n"
    
    # Show calculated exposure times
    message += "\nCALCULATED EXPOSURES:\n"
    message += "  From row count: " + format_value(summary['exposure_from_row_count'], 3) + " ms\n"
    message += "  From frame numbers: " + format_value(summary['exposure_from_frame_no'], 3) + " ms\n"
    
    message += "\nFRAME INFORMATION:\n"
    message += "  First Frame: " + str(summary['first_frame_no']) + "\n"
    message += "  Last Frame: " + str(summary['last_frame_no']) + "\n"
    message += "  Total Frames: " + str(summary['frame_count']) + "\n"
    message += "  Rows in CSV: " + str(summary['no_rows_in_csv']) + "\n"
    
    message += "\nACQUISITION DELAYS:\n"
    message += "  Late frames (>1.9x): " + str(summary['n_late_frames']) + "\n"
    message += "  Delayed frames (>1.1x): " + str(summary['n_delayed_frames']) + "\n"
    message += "  Repeated frames: " + str(summary['n_repeated_frames']) + "\n"
    message += "  Rows with blanks: " + str(summary['n_blank_cells']) + "\n"
    message += "  Missing signal: " + str(summary['no_rows_missing_signal']) + "\n"
    
    # Show percentiles if available
    percentile_keys = [k for k in summary.keys() if k.startswith('tdelta_percentile_')]
    if percentile_keys:
        message += "\nDELAY PERCENTILES (offset from median, ms):\n"
        for key in sorted(percentile_keys):
            percentile_num = key.replace('tdelta_percentile_', '')
            message += "  " + percentile_num + "th: " + format_value(summary[key], 3) + " ms\n"
    
    return message


def test_individual_functions(file_path):
    """Test each function individually and show results"""
    
    print("\n" + "="*60)
    print("TESTING INDIVIDUAL FUNCTIONS")
    print("="*60)
    
    # Test 1: read_tangra_csv_iron
    print("\n1. Testing read_tangra_csv_iron()...")
    try:
        tangra_obj = lc.read_tangra_csv_iron(file_path)
        print("   SUCCESS: File read successfully")
        print("   - Filename from TANGRA: " + tangra_obj['filename_from_tangra'])
        print("   - Light curve rows: " + str(len(tangra_obj['light_curve'])))
        print("   - Apertures found: " + str(len(tangra_obj['apertures'])))
        if tangra_obj['apertures']:
            for i, ap in enumerate(tangra_obj['apertures']):
                print("     Aperture {}: {} at ({}, {})".format(
                    i+1, 
                    ap['Object'], 
                    format_value(ap['StartingX'], 1), 
                    format_value(ap['StartingY'], 1)
                ))
    except Exception as e:
        print("   FAILED: " + str(e))
        return None
    
    # Test 2: analyse_timestamps_iron without percentiles
    print("\n2. Testing analyse_timestamps_iron() without percentiles...")
    try:
        summary_basic = lc.analyse_timestamps_iron(tangra_obj)
        print("   SUCCESS: Timestamp analysis completed")
        print("   - Start time: " + summary_basic['start_time'])
        print("   - End time: " + summary_basic['end_time'])
        print("   - Median exposure: " + format_value(summary_basic['tdelta_median'], 3) + " ms")
        print("   - Frame count: " + str(summary_basic['frame_count']))
    except Exception as e:
        print("   FAILED: " + str(e))
        return None
    
    # Test 3: analyse_timestamps_iron with percentiles
    print("\n3. Testing analyse_timestamps_iron() with percentiles [1, 5, 95, 99]...")
    try:
        summary_percentiles = lc.analyse_timestamps_iron(tangra_obj, percentiles=[1, 5, 95, 99])
        print("   SUCCESS: Timestamp analysis with percentiles completed")
        for key in sorted([k for k in summary_percentiles.keys() if k.startswith('tdelta_percentile_')]):
            percentile_num = key.replace('tdelta_percentile_', '')
            print("   - {}th percentile offset: {} ms".format(
                percentile_num, 
                format_value(summary_percentiles[key], 3)
            ))
    except Exception as e:
        print("   FAILED: " + str(e))
        return None
    
    # Test 4: get_observation_summary convenience function
    print("\n4. Testing get_observation_summary() convenience function...")
    try:
        summary_quick = lc.get_observation_summary(file_path, percentiles=[1, 99])
        print("   SUCCESS: One-step summary completed")
        print("   - This function combines read and analyse in one call")
    except Exception as e:
        print("   FAILED: " + str(e))
        return None
    
    print("\n" + "="*60)
    print("ALL TESTS PASSED!")
    print("="*60)
    
    return summary_percentiles


def main():
    """Main test function"""
    
    print("="*60)
    print("SharpCap IronPython - Tangra Light Curve Analysis Test")
    print("="*60)
    print("")
    print("This script tests the IronPython-compatible light curve")
    print("analysis functions for reading Tangra CSV files.")
    print("")
    
    # Create and configure the file dialog
    dialog = OpenFileDialog()
    dialog.Title = "Select TANGRA CSV Light Curve File"
    dialog.Filter = "CSV files (*.csv)|*.csv|Text files (*.txt)|*.txt|All files (*.*)|*.*"
    dialog.FilterIndex = 1
    dialog.Multiselect = False
    
    # Show the dialog
    result = dialog.ShowDialog()
    
    if result != DialogResult.OK:
        print("File selection cancelled by user.")
        return
    
    file_path = dialog.FileName
    print("Selected file: " + file_path)
    
    if not os.path.exists(file_path):
        MessageBox.Show(
            "Selected file does not exist:\n" + file_path,
            "File Not Found",
            MessageBoxButtons.OK,
            MessageBoxIcon.Error
        )
        return
    
    # Run the tests
    try:
        summary = test_individual_functions(file_path)
        
        if summary is not None:
            # Display results in a message box
            results_text = display_results(summary)
            print("\n" + results_text)
            
            MessageBox.Show(
                results_text,
                "Tangra Light Curve Analysis Results",
                MessageBoxButtons.OK,
                MessageBoxIcon.Information
            )
            
            print("\nTest completed successfully!")
            print("\nKEY INFORMATION FOR EXCEL REPORT:")
            print("  Start Time: " + summary['start_time'])
            print("  End Time: " + summary['end_time'])
            print("  Exposure (ms): " + format_value(summary['tdelta_median'], 3))
            print("  Max Delay (ms): " + format_value(summary['tdelta_max'], 3))
            print("  Std Dev (ms): " + format_value(summary['tdelta_std'], 3))
            
    except Exception as e:
        error_msg = "An error occurred during testing:\n\n" + str(e)
        print("\nERROR: " + error_msg)
        MessageBox.Show(
            error_msg,
            "Test Error",
            MessageBoxButtons.OK,
            MessageBoxIcon.Error
        )


# Run the test
if __name__ == '__main__':
    main()
