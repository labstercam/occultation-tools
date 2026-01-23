# SharpCap RunAsync Implementation

## Overview

This document describes the implementation of asynchronous sequence execution in the Occultation Manager using SharpCap's `RunAsync()` API, including the critical threading architecture required for stable operation.

## Problem Statement

### Original Issue: UI Blocking

The initial implementation used `SharpCap.Sequencer.RunSequenceFile()` which **completely blocks** SharpCap's UI thread until the sequence completes. This caused:

- Complete UI freeze - couldn't minimize, close, or interact with SharpCap
- No ability to stop or cancel sequences
- Poor user experience during long-running observations
- No status feedback during execution

### Requirements

1. Non-blocking sequence execution
2. User ability to stop sequences mid-execution
3. Real-time status monitoring
4. Camera settings preservation and restoration
5. Proper error handling and recovery
6. Support for both single and multi-sequence execution

## Solution Architecture

### Key API Methods

```python
# SharpCap.Sequencer API
RunAsync()           # Non-blocking, returns immediately
StopAsync()          # Request stop asynchronously
IsRunning            # Boolean property for monitoring
Status              # Enum: Running, Completed, Failed
FailingStep         # Error information when failed
FailureReason       # Detailed failure message
LoadScriptFile()    # Load sequence from file
AnySteps()          # Check if sequence has steps
```

### Two Implementation Patterns

#### 1. Test Recording (Single Sequence)

**Architecture:**
- UI thread calls `RunAsync()` directly
- Separate monitoring thread polls `IsRunning` status
- Monitor thread marshals callbacks to UI thread via `Invoke()`

**Code Location:** Lines 2383-2660 in `main_gui.py`

**Key Methods:**
- `test_recording_click_async()` - Entry point, saves camera settings
- `_start_sequence_async()` - Calls RunAsync on UI thread
- `_start_sequence_monitor()` - Creates monitor thread
- `_monitor_sequence_execution()` - Background polling loop
- `_on_sequence_completed()` - Completion handler with context awareness

**Flow:**
```
UI Thread: test_recording_click_async()
    ↓
UI Thread: _start_sequence_async()
    ↓
UI Thread: RunAsync() ← Safe, STA thread
    ↓
Background: _monitor_sequence_execution() (polls every 1 second)
    ↓
UI Thread: _on_sequence_completed() (via Invoke)
```

#### 2. Run Sequences (Multiple Sequential Sequences)

**Architecture:**
- Background thread manages sequence loop
- Each `RunAsync()` call marshaled to UI thread
- Background thread polls status between sequences
- No separate monitor thread needed (inline monitoring)

**Code Location:** Lines 1197-1410 in `main_gui.py`

**Key Methods:**
- `run_sequences_click_async()` - Entry point
- `_start_sequences_async()` - Creates background thread
- `run_all_sequences()` - Nested function in background thread
- `_on_sequence_completed()` - Shared completion handler

**Flow:**
```
UI Thread: run_sequences_click_async()
    ↓
Background Thread: run_all_sequences()
    ↓
    For each sequence:
        UI Thread: RunAsync() ← Marshaled via Invoke (CRITICAL!)
        Background: Poll IsRunning
        Background: Check Status
        Background: Sleep between sequences
    ↓
UI Thread: _on_sequence_completed() (via Invoke)
```

## Critical Threading Issue: STA Apartment State

### The Problem

**Error Encountered:**
```
'The calling thread must be STA, because many UI components require this.' 
while running step Auto stretch the display.
```

### Root Cause

SharpCap sequence steps that manipulate UI components (like `DISPLAY STRETCH AUTO`, `SHOW NOTIFICATION`, camera control changes) require the calling thread to have **STA (Single Threaded Apartment)** state.

Python's `threading.Thread` creates threads with **MTA (Multi Threaded Apartment)** state by default, which is incompatible with .NET UI operations.

### Why Test Recording Worked But Run Sequences Failed

| Implementation | RunAsync() Called From | Thread State | Result |
|----------------|------------------------|--------------|--------|
| **Test Recording** | UI thread (line 2623) | STA ✓ | Works |
| **Run Sequences (original)** | Background thread (line 1339) | MTA ✗ | STA Error |

### The Fix

**Original Code (BROKEN):**
```python
# Inside run_all_sequences() background thread
task = self.sharpcap.Sequencer.RunAsync()  # Called from MTA thread - FAILS!
```

**Fixed Code:**
```python
# Inside run_all_sequences() background thread
self.Invoke(lambda: self.sharpcap.Sequencer.RunAsync())  # Marshaled to STA UI thread - WORKS!
```

### Why This Fix Works

1. **`Invoke()`** marshals the call to the UI thread
2. UI thread always has STA apartment state in WinForms applications
3. **`RunAsync()`** executes on STA thread, allowing UI operations
4. **`RunAsync()`** returns immediately (asynchronous), so UI isn't blocked
5. Background thread continues monitoring without STA requirement

### Affected Sequence Operations

**Works from MTA thread:**
- File I/O operations
- Delays (`DELAY` commands)
- Calculations
- Status checks

**Requires STA thread (must use Invoke):**
- `DISPLAY STRETCH AUTO`
- `SHOW NOTIFICATION`
- Camera control UI updates
- Any COM/ActiveX operations
- Display adjustments

## State Management

### Instance Variables

```python
# Line 98-104 in main_gui.py
self._sequence_running = False              # Master flag
self._sequence_monitoring_thread = None     # Monitor thread reference
self._sequence_saved_settings = {}          # Camera settings backup
self._current_sequence_path = None          # Current sequence file(s)
self._sequence_stopped_by_user = False      # Stop request flag
self._sequence_context = None               # 'test_recording' or 'run_sequences'
```

### State Lifecycle

**Starting:**
1. Check `_sequence_running` (prevent concurrent sequences)
2. Save camera settings to `_sequence_saved_settings`
3. Set `_sequence_running = True`
4. Enable Stop button
5. Set context for appropriate messaging
6. Clear `_sequence_stopped_by_user`

**Running:**
1. Monitor thread polls `IsRunning` property
2. Check `_sequence_stopped_by_user` flag each iteration
3. Update UI status via `Invoke()`

**Stopping (User Request):**
1. Set `_sequence_stopped_by_user = True`
2. Call `StopAsync()`
3. Wait briefly for stop to take effect
4. Call `_cleanup_after_sequences_stopped()`
5. Restore camera settings
6. Reset all state variables

**Completion (Natural):**
1. Monitor detects `IsRunning = False`
2. Check `Status` property (Completed/Failed)
3. If not stopped by user, call `_on_sequence_completed()`
4. Restore camera settings
5. Show context-appropriate completion message
6. Reset all state variables

## Camera Settings Preservation

### Save Settings (`_save_camera_settings`)

Captures current state before sequence execution:
- Binning
- Exposure (ExposureMs)
- Gain
- Resolution
- Display levels (Black, Mid, White)

**Protection:** Only saves once - won't overwrite if already saved.

### Restore Settings (`_restore_camera_settings`)

**Challenge:** Camera needs time to stabilize after changes.

**Solution:** Non-blocking stabilization
```python
def _restore_camera_settings():
    # Restore settings immediately
    camera.Controls.Exposure.ExposureMs = saved_exposure
    # ... restore other settings ...
    
    # Background stabilization thread
    def wait_for_stabilization():
        time.sleep(exposure_time * 2)
        # Restore display levels on UI thread
        self.Invoke(lambda: restore_display_levels())
    
    thread = threading.Thread(target=wait_for_stabilization)
    thread.daemon = True
    thread.start()
```

**Why non-blocking:** Allows UI to remain responsive during stabilization period.

## Error Handling Patterns

### Exception Safety

Every error path must clean up state:
```python
try:
    # Sequence execution
except Exception as ex:
    # CRITICAL: Clean up all state variables
    self._sequence_running = False
    self._sequence_stopped_by_user = False
    self.btn_stop_sequence.Enabled = False
    self._sequence_saved_settings = {}
    self._current_sequence_path = None
    self._sequence_context = None  # Added after bug fix
    # Show error to user
    MessageBox.Show(...)
```

### Race Condition Prevention

**Challenge:** Stop button clicked after sequence completes naturally.

**Solution:** Check state before processing
```python
def _on_sequence_completed():
    # Safety check
    if not self._sequence_running:
        print("Already marked as not running, skip")
        return
    # ... proceed with cleanup ...
```

### Monitor Thread Safety

**Challenge:** Exception in monitor thread kills monitoring silently.

**Solution:** Try-except wrapper with UI notification
```python
def _monitor_sequence_execution():
    try:
        # Monitoring loop
    except Exception as ex:
        print(f"Monitor thread error: {ex}")
        try:
            self.Invoke(lambda: self._on_sequence_completed("Error"))
        except:
            print("Could not invoke error handler")
```

## Context-Aware Messaging

Different completion messages based on execution context:

```python
context = self._sequence_context  # 'test_recording' or 'run_sequences'

if context == 'run_sequences':
    MessageBox.Show("All sequences completed successfully!")
else:  # test_recording
    MessageBox.Show("Test recording sequence completed successfully!")
```

## Stop Button Implementation

### Dynamic State Management

```python
# Initially disabled
self.btn_stop_sequence.Enabled = False

# Enable when sequence starts
self._sequence_running = True
self.btn_stop_sequence.Enabled = True

# Disable when complete
self._sequence_running = False
self.btn_stop_sequence.Enabled = False
```

### Confirmation Dialog

```python
def stop_sequence_click(self, sender, e):
    result = MessageBox.Show(
        "Stop the currently running sequence?\n\n" +
        "Camera settings will be restored.",
        "Confirm Stop",
        MessageBoxButtons.YesNo,
        MessageBoxIcon.Warning
    )
    
    if result == DialogResult.Yes:
        # Race condition check
        if not self._sequence_running:
            MessageBox.Show("Sequence already completed")
            return
        self._stop_sequence_async()
```

## Best Practices & Lessons Learned

### 1. Always Marshal RunAsync to UI Thread

**Wrong:**
```python
# From background thread - FAILS with STA error
task = self.sharpcap.Sequencer.RunAsync()
```

**Correct:**
```python
# Marshal to UI thread - WORKS
self.Invoke(lambda: self.sharpcap.Sequencer.RunAsync())
```

### 2. Lambda Closure Captures

**Problem:** Loop variables captured by reference
```python
for i, (seq_path, event_name) in enumerate(sequence_paths):
    # BAD - captures reference to 'i' and 'event_name'
    self.Invoke(lambda: self.update_status(f"Sequence {i}: {event_name}"))
```

**Solution:** Capture values in local scope
```python
for i, (seq_path, event_name) in enumerate(sequence_paths):
    # GOOD - captures values
    idx = i + 1
    total = len(sequence_paths)
    name = event_name
    self.Invoke(lambda: self.update_status(f"Starting sequence {idx}/{total}: {name}"))
```

### 3. Python Threading API (Not .NET)

Use lowercase Python methods:
```python
thread = threading.Thread(target=func)
thread.daemon = True      # Lowercase 'daemon'
thread.start()            # Lowercase 'start()'
if thread.is_alive():     # Lowercase 'is_alive()'
```

### 4. Comprehensive State Cleanup

Every error path must reset **all** state variables:
- `_sequence_running`
- `_sequence_stopped_by_user`
- `_sequence_saved_settings`
- `_current_sequence_path`
- `_sequence_context`
- `btn_stop_sequence.Enabled`

### 5. Non-Blocking Operations

Camera stabilization must not block UI:
```python
# Create background thread for wait operations
stabilization_thread = threading.Thread(target=wait_for_stabilization)
stabilization_thread.daemon = True
stabilization_thread.start()
# UI remains responsive during wait
```

## Testing Scenarios

### Test Coverage

1. **Single sequence (Test Recording)**
   - Normal completion
   - User stop
   - Sequence failure
   - Empty sequence file

2. **Multiple sequences (Run Sequences)**
   - All sequences complete
   - User stop mid-execution
   - Individual sequence failure
   - Mixed success/failure

3. **UI operations in sequences**
   - Display stretch (STA requirement)
   - Show notifications
   - Camera control changes

4. **Concurrent operation prevention**
   - Click Run while already running
   - Multiple stop button clicks
   - Race conditions

5. **Camera settings**
   - Save/restore all controls
   - Stabilization timing
   - Missing controls (old cameras)

## Performance Characteristics

### Polling Intervals

**Test Recording Monitor:**
- Poll every 1 second
- Minimal CPU impact
- Responsive to user stop requests

**Run Sequences:**
- Poll every 1 second during sequence execution
- 2 second delay between sequences
- 0.5 second startup delay per sequence

### Memory Management

- Daemon threads automatically cleaned up on exit
- No thread joining (avoids UI blocking)
- Settings dictionary cleared after use
- Monitor thread naturally exits when `IsRunning = False`

## Future Enhancements

### Potential Improvements

1. **Configurable polling interval** - Allow user to adjust responsiveness vs CPU usage
2. **Progress percentage** - Calculate based on sequence step count
3. **Sequence queue** - Allow adding sequences while running
4. **Parallel sequence execution** - Run multiple cameras simultaneously
5. **Auto-retry on failure** - Configurable retry logic for transient errors
6. **Sequence history log** - Record all executions with timestamps and outcomes

### Known Limitations

1. **No step-level granularity** - Can't stop between individual sequence steps
2. **Display level restoration timing** - Fixed 2x exposure time, not adaptive
3. **No pause capability** - Only stop (can't pause and resume)
4. **Single sequence at a time** - No concurrent sequence support

## Code References

### Key Files

- `main_gui.py` - Main implementation
  - Lines 98-104: State variable initialization
  - Lines 2383-2660: Test Recording async implementation
  - Lines 1197-1410: Run Sequences async implementation
  - Lines 2677-2774: Camera settings save/restore
  - Lines 2825-2904: Sequence monitoring
  - Lines 2906-2970: Completion and cleanup handlers
  - Lines 2972-3046: Stop button implementation

### Dependencies

- `threading` - Python standard library for background threads
- `System.Windows.Forms` - WinForms UI controls (STA by default)
- `SharpCap.Sequencer` - SharpCap automation API
- `time` - Sleep and timing operations

## Conclusion

The RunAsync implementation provides robust, non-blocking sequence execution with proper threading architecture. The critical insight is that **all SharpCap Sequencer API calls must be marshaled to the UI thread (STA)** even when monitoring from a background thread. This ensures compatibility with UI-touching sequence operations while maintaining UI responsiveness.

The dual implementation pattern (Test Recording with separate monitor thread vs Run Sequences with inline monitoring) demonstrates flexibility in async architecture while maintaining consistent state management and error handling principles.

---

*Document created: January 24, 2026*  
*Author: AI Assistant via GitHub Copilot*  
*Version: 1.0*
