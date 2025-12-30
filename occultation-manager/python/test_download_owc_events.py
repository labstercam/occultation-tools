"""
Test Script to Download Events from OccultWatcher Cloud
Downloads events using stored configuration and saves raw data to a text file
"""

import os
import sys
import json
import base64
import urllib.request
from datetime import datetime

# Add the module directory to Python path
module_dir = os.path.dirname(os.path.abspath(__file__))
if module_dir not in sys.path:
    sys.path.insert(0, module_dir)

from config import ConfigManager


def download_owc_events(url, username, password):
    """Download events from OW Cloud API"""
    print(f"Connecting to: {url}")
    print(f"Username: {username}")
    
    credentials = f"{username}:{password}"
    encoded_credentials = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
    
    request = urllib.request.Request(url)
    request.add_header("Authorization", f"Basic {encoded_credentials}")
    request.add_header("Content-Type", "application/json")
    
    try:
        response = urllib.request.urlopen(request)
        data = json.loads(response.read().decode('utf-8'))
        print(f"Successfully downloaded {len(data)} events")
        return data
    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code} - {e.reason}")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None


def save_raw_data_to_file(data, filename):
    """Save raw data to a text file with nice formatting"""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("OccultWatcher Cloud - Raw Event Data Export\n")
        f.write(f"Downloaded: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*80 + "\n\n")
        
        if not data:
            f.write("No data downloaded\n")
            return
        
        f.write(f"Total Events: {len(data)}\n\n")
        f.write("="*80 + "\n")
        
        # Write each event with all fields
        for i, event in enumerate(data, 1):
            f.write(f"\nEVENT #{i}\n")
            f.write("-"*80 + "\n")
            
            # Write all top-level fields
            for key, value in sorted(event.items()):
                if key == 'Stations':
                    # Handle stations separately
                    f.write(f"\n{key}: {len(value)} station(s)\n")
                    for j, station in enumerate(value, 1):
                        f.write(f"  Station #{j}:\n")
                        for skey, svalue in sorted(station.items()):
                            f.write(f"    {skey}: {svalue}\n")
                elif isinstance(value, dict):
                    f.write(f"\n{key}:\n")
                    for subkey, subvalue in sorted(value.items()):
                        f.write(f"  {subkey}: {subvalue}\n")
                elif isinstance(value, list):
                    f.write(f"\n{key}: {len(value)} item(s)\n")
                    for item in value:
                        f.write(f"  - {item}\n")
                else:
                    f.write(f"{key}: {value}\n")
            
            f.write("-"*80 + "\n")
        
        # Also save as JSON for easy inspection
        json_filename = filename.replace('.txt', '.json')
        with open(json_filename, 'w', encoding='utf-8') as jf:
            json.dump(data, jf, indent=2)
        
        print(f"\nData saved to:")
        print(f"  Text format: {filename}")
        print(f"  JSON format: {json_filename}")


def main():
    """Main test function"""
    print("="*80)
    print("OccultWatcher Cloud Event Download Test")
    print("="*80)
    print()
    
    # Load configuration
    print("Loading configuration...")
    config = ConfigManager()
    
    # Get credentials
    email = config.get_owc_email()
    password = config.get_owc_password()
    url = config.get_full_url()
    
    print(f"OWC Email: {email}")
    print(f"API URL: {url}")
    print()
    
    # Validate credentials
    if not email or email == 'your_owc_email':
        print("ERROR: OWC email not configured!")
        print("Please set your OccultWatcher Cloud email in the configuration.")
        return
    
    if not password or password == 'your_owc_password':
        print("ERROR: OWC password not configured!")
        print("Please set your OccultWatcher Cloud password in the configuration.")
        return
    
    # Download events
    print("Downloading events from OccultWatcher Cloud...")
    print()
    data = download_owc_events(url, email, password)
    
    if data is None:
        print("Failed to download events")
        return
    
    # Save to file
    output_file = os.path.join(module_dir, 'owc_downloaded_events.txt')
    print()
    print("Saving raw data to file...")
    save_raw_data_to_file(data, output_file)
    
    print()
    print("="*80)
    print("Download complete!")
    print("="*80)
    print()
    print("You can now inspect the downloaded data to see all available fields.")
    print()


if __name__ == '__main__':
    main()
