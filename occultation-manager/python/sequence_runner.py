import os
import time
from datetime import datetime

class SequenceRunner:
    """Handles running SharpCap sequences"""
    
    def __init__(self, config):
        self.config = config
        self.running = False
        self.current_sequence = None
    
    def run_sequences(self, events, status_callback=None):
        """Run sequences for events in order of GOTO time"""
        if self.running:
            if status_callback:
                status_callback("Sequence runner already running")
            return False
        
        # Filter and sort future events by GOTO time
        now = datetime.utcnow()
        future_events = [e for e in events if e.goto_time and e.goto_time > now]
        future_events.sort(key=lambda x: x.goto_time)
        
        if not future_events:
            if status_callback:
                status_callback("No future events to run")
            return False
        
        self.running = True
        
        try:
            for i, event in enumerate(future_events):
                # Check if event is still in the future before each run
                current_time = datetime.utcnow()
                if event.goto_time <= current_time:
                    if status_callback:
                        status_callback(f"Skipping {event.event_name} - past GOTO time")
                    continue
                
                if status_callback:
                    status_callback(f"Running sequence {i+1}/{len(future_events)}: {event.event_name}")
                
                self.current_sequence = event
                
                # Create sequence file path
                start_time = datetime.strptime(event.start_time_str, '%Y-%m-%dT%H:%M:%S')
                clean_name = "".join(c for c in event.name if c.isalnum() or c in ('(',')',' ', '-', '_')).rstrip()
                seq_name = start_time.strftime('%Y%m%d') + ' ' + clean_name + '.seq'
                sequence_file_path = os.path.join(self.config.get_sequence_path(), seq_name)
                
                # Run the sequence
                success = self.run_single_sequence(sequence_file_path, event, status_callback)
                
                if not success:
                    if status_callback:
                        status_callback(f"Failed to run sequence for {event.event_name}")
                
                # Wait a moment between sequences
                time.sleep(1)
            
            if status_callback:
                status_callback("All sequences completed")
            
        except Exception as e:
            if status_callback:
                status_callback(f"Error running sequences: {e}")
        finally:
            self.running = False
            self.current_sequence = None
        
        return True
    
    def run_single_sequence(self, sequence_file_path, event, status_callback=None):
        """Run a single sequence file with error trapping"""
        try:
            if not os.path.exists(sequence_file_path):
                if status_callback:
                    status_callback(f"Sequence file not found: {sequence_file_path}")
                return False
            
            # Try to connect to SharpCap
            try:
                import clr
                clr.AddReference(r"C:\Program Files\SharpCap 4.1\SharpCap.exe")
                from SharpCap import *
                
                # Run the sequence
                if status_callback:
                    status_callback(f"Starting SharpCap sequence: {os.path.basename(sequence_file_path)}")
                
                # Execute the sequence file
                SharpCap.SequenceEngine.RunSequenceFile(sequence_file_path)
                
                if status_callback:
                    status_callback(f"Sequence started successfully for {event.event_name}")
                
                return True
                
            except Exception as sc_error:
                if status_callback:
                    status_callback(f"SharpCap error for {event.event_name}: {sc_error}")
                print(f"SharpCap error: {sc_error}")
                return False
        
        except Exception as e:
            if status_callback:
                status_callback(f"Fatal error running sequence for {event.event_name}: {e}")
            print(f"Fatal sequence error: {e}")
            return False
    
    def stop_sequences(self):
        """Stop running sequences"""
        self.running = False