"""
frame_acquisition_delay_test.py
===============================

SharpCap IronPython script that measures the delay between the moment the
script requests a frame and the timestamp carried in the frame's own metadata
(args.Frame.Info.EndTimeStamp).

Usage (from SharpCap's IronPython console):
    execfile(r"<path-to-this-file>")

Requirements:
    - A camera is connected AND live preview is running (SharpCap must be
      streaming frames before the script is started).

Steps performed:
    1. Print and store the current UTC timestamp (millisecond precision).
    2. Trigger capture of a single frame via SharpCap.CaptureSingleFrame().
    3. Print the frame's metadata timestamp, store it, and print the elapsed
       time since the frame was requested.
    4. Repeat until NUM_FRAMES valid frames have been measured (the first
       SKIP_FRAMES frames are discarded to absorb capture start-up delay).
    5. Print a table: frame number, timestamps, and the acquisition delay
       with the nominal exposure time subtracted.
    6. Print mean, SD (sample), min and max of the corrected delays.

Notes:
    - The camera's FrameCaptured event is used to obtain the frame (the same
      mechanism used by led_line_delay_calibration.py / pc_performance_testing.py).
    - Info.EndTimeStamp is the UTC time at which the camera finished the
      exposure, timestamped by SharpCap from the PC clock.
    - Three values are reported:
        * "Raw (ms)"     : frame metadata time minus request time (includes
                           the exposure time).
        * "Delay (ms)"   : Raw minus the nominal exposure time = time from the
                           request to the start of the accepted exposure. In a
                           TRUE triggered (still) capture this is the frame
                           acquisition / pipeline latency (~tens of ms). In
                           continuous/video mode it is instead the wait for the
                           current exposure to finish (~exposure - SETTLE_S).
        * "Arrival (ms)" : high-resolution elapsed time (Stopwatch) from the
                           request until the frame reached the handler, which
                           isolates the software/USB pipeline latency.
    - A MODE VERDICT is printed at the end: if the mean delay is small the run
      was triggered/still (delay = acquisition latency); if large it was
      continuous/video mode and the delay is NOT the acquisition latency. Set
      the boundary via TRIGGER_LATENCY_THRESHOLD_MS.
    - The nominal exposure is read from the camera
      (Controls.Exposure.ExposureMs); set EXPOSURE_MS_OVERRIDE to force a value.
    - The camera settle pause (SETTLE_S) is taken BEFORE the request timestamp
      is stamped, so settling can never inflate the measured delay.
    - Frame-selection guards (both default True):
        * IGNORE_PRE_REQUEST_FRAMES : skip frames whose end time predates the
          request.
        * REQUIRE_FRESH_FRAME       : skip frames already exposing when the
          request was made. In live/video mode (used at short exposures) frames
          stream continuously, so CaptureSingleFrame() cannot force a fresh
          exposure and the next frame is grabbed "in flight". This guard waits
          for a frame whose exposure began at/after the request; the exposure
          start is estimated as EndTimeStamp - exposure.
    - TRIGGER_CAPTURE = True issues an explicit single-frame capture each
      iteration. NOTE: SharpCap.CaptureSingleFrame() saves a frame to the
      current output target, so a file will be written per iteration. Set it
      to False to fall back to grabbing the next live frame (no disk writes).
"""

import time
import clr

clr.AddReference("System")
clr.AddReference("System.Windows.Forms")

from System import DateTime
from System.Diagnostics import Stopwatch
from System.Windows.Forms import Application

# SharpCap global is injected by the SharpCap IronPython console.
try:
    _ = SharpCap
except NameError:
    SharpCap = None

# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------
NUM_FRAMES = 10            # number of *valid* frames to measure
SKIP_FRAMES = 1            # initial frames to discard (capture start-up delay)
FRAME_TIMEOUT_S = 5.0      # abandon a request after this many seconds
TRIGGER_CAPTURE = True     # True -> call SharpCap.CaptureSingleFrame() per frame
SETTLE_S = 0.2           # camera settle pause; applied BEFORE the request stamp (excluded from delay)
EXPOSURE_MS_OVERRIDE = None  # e.g. 40.0 to force the nominal exposure; None = read camera
IGNORE_PRE_REQUEST_FRAMES = True  # True -> only accept frames captured at/after the request stamp
REQUIRE_FRESH_FRAME = True    # True -> skip frames already exposing at request time (no in-flight grab)
TRIGGER_LATENCY_THRESHOLD_MS = 100.0  # mean delay above this => continuous/video mode, not a real trigger


class FrameDelayProbe(object):
    """Collects the timestamp of the next frame received after a request."""

    def __init__(self):
        self.waiting = False
        self.request_dt = None       # request timestamp for the current measurement
        self.exposure_ms = None      # nominal exposure, used to estimate exposure start
        self.frame_time = None       # .NET DateTime (UTC) end-of-exposure timestamp
        self.arrival_ms = None       # Stopwatch value when the frame arrived
        self.skipped_prerequest = 0  # frames captured entirely before the request
        self.skipped_inflight = 0    # frames already exposing when requested
        self._stopwatch = Stopwatch()
        self._stopwatch.Start()

    def on_frame(self, sender, args):
        if not self.waiting:
            return
        try:
            end_stamp = args.Frame.Info.EndTimeStamp

            # Estimate when this frame's exposure began (EndTimeStamp - exposure).
            start_stamp = None
            if self.exposure_ms is not None:
                start_stamp = end_stamp.AddMilliseconds(-float(self.exposure_ms))

            if self.request_dt is not None and end_stamp < self.request_dt:
                # Frame was captured entirely before the request.
                if IGNORE_PRE_REQUEST_FRAMES:
                    self.skipped_prerequest += 1
                    return
            elif (start_stamp is not None and self.request_dt is not None
                    and start_stamp < self.request_dt):
                # Camera was already mid-exposure -> frame grabbed "in flight".
                # Wait for a frame whose exposure starts at/after the request.
                if REQUIRE_FRESH_FRAME:
                    self.skipped_inflight += 1
                    return

            # Publish arrival_ms BEFORE frame_time so any reader that sees
            # frame_time set is guaranteed to see arrival_ms set too.
            self.arrival_ms = self._stopwatch.Elapsed.TotalMilliseconds
            self.frame_time = end_stamp
            self.waiting = False
        except Exception as ex:
            print("  Frame handler error: {0}".format(ex))

    def begin_request(self, request_dt):
        """Arm the probe to accept the next frame captured at/after request_dt.

        Pass request_dt=None to accept any frame (used for the warm-up probe).
        """
        self.request_dt = request_dt
        self.frame_time = None
        self.arrival_ms = None
        self.skipped_prerequest = 0
        self.skipped_inflight = 0
        self._stopwatch.Restart()
        self.waiting = True


def fmt(dt):
    """Format a .NET DateTime to millisecond precision (SharpCap times are UTC)."""
    return dt.ToString("yyyy-MM-dd HH:mm:ss.fff")


def num(value, width=8, decimals=3):
    """Fixed-width numeric format for an optional float (None prints as 'n/a').

    Guards the console output against a transient None (see the handler race
    note) so the script can never crash with 'NoneType.__format__'.
    """
    if value is None:
        return "{0:>{1}}".format("n/a", width)
    return "{0:>{1}.{2}f}".format(value, width, decimals)


def stats(values):
    """Return (mean, sample_sd, minimum, maximum) for a list of floats."""
    n = len(values)
    mean = sum(values) / float(n)
    sd = 0.0
    if n > 1:
        sd = (sum((v - mean) ** 2 for v in values) / float(n - 1)) ** 0.5
    return mean, sd, min(values), max(values)


def get_exposure_ms(camera):
    """Return the nominal exposure time in milliseconds.

    Reads the camera's exposure control (Controls.Exposure.ExposureMs). Falls
    back to Settings.Exposure.Value (microseconds) if that is unavailable, and
    finally to EXPOSURE_MS_OVERRIDE / 0.0.
    """
    if EXPOSURE_MS_OVERRIDE is not None:
        return float(EXPOSURE_MS_OVERRIDE)
    try:
        return float(camera.Controls.Exposure.ExposureMs)
    except Exception:
        pass
    try:
        return float(camera.Settings.Exposure.Value) / 1000.0
    except Exception:
        pass
    print("WARNING: could not read exposure time - assuming 0 ms.")
    return 0.0


def main():
    if SharpCap is None:
        print("ERROR: SharpCap not available.")
        print("Run this script from SharpCap's IronPython console.")
        return

    camera = SharpCap.SelectedCamera
    if camera is None:
        print("ERROR: No camera selected.")
        print("Connect a camera and start live preview, then run the script again.")
        return

    probe = FrameDelayProbe()
    camera.FrameCaptured += probe.on_frame

    # Warm-up: confirm frames are actually arriving before measuring.
    print("Waiting for live frames...")
    probe.begin_request(None)
    deadline = DateTime.UtcNow.AddSeconds(FRAME_TIMEOUT_S)
    # Wait on 'waiting' (cleared LAST by the handler) so every frame field is
    # populated by the time the loop exits.
    while probe.waiting and DateTime.UtcNow < deadline:
        time.sleep(0.01)
        Application.DoEvents()

    if probe.frame_time is None:
        camera.FrameCaptured -= probe.on_frame
        print("ERROR: No frames received. Start SharpCap live preview and retry.")
        return

    print("Frames detected.")

    exposure_ms = get_exposure_ms(camera)
    probe.exposure_ms = exposure_ms
    print("Nominal exposure: {0:.3f} ms (subtracted from each delay)".format(exposure_ms))
    print("Ignore pre-request frames: {0}".format(IGNORE_PRE_REQUEST_FRAMES))
    print("Require fresh frame: {0}".format(REQUIRE_FRESH_FRAME))
    print("")

    can_trigger = TRIGGER_CAPTURE and hasattr(SharpCap, "CaptureSingleFrame")
    if TRIGGER_CAPTURE and not can_trigger:
        print("WARNING: SharpCap.CaptureSingleFrame() is not available;")
        print("         falling back to taking the next live frame.")
        print("")

    rows = []   # (no, request_dt, frame_dt, raw_ms, delay_ms, arrival_ms)
    inflight_total = 0
    prereq_total = 0

    try:
        total = NUM_FRAMES + SKIP_FRAMES
        for i in range(1, total + 1):
            # Let the camera settle from the previous capture BEFORE the request
            # timestamp is stamped, so SETTLE_S never falls inside the measured
            # request -> frame window (it sits outside the measurement).
            if i > 1:
                time.sleep(SETTLE_S)

            # --- Step 1 & 2: stamp the request time, then trigger a frame ---
            request_dt = DateTime.UtcNow
            probe.begin_request(request_dt)
            print("[{0:2d}] Request time : {1}".format(i, fmt(request_dt)))

            if can_trigger:
                try:
                    SharpCap.CaptureSingleFrame()
                except Exception as ex:
                    print("      CaptureSingleFrame call failed: {0}".format(ex))

            # --- Step 3: wait for the frame to arrive ---
            # Allow at least 3 frame times so long exposures still get a fresh
            # frame (video mode streams back-to-back frames).
            frame_timeout = max(FRAME_TIMEOUT_S, exposure_ms / 1000.0 * 3.0)
            deadline = DateTime.UtcNow.AddSeconds(frame_timeout)
            # Wait on 'waiting' (cleared LAST by the handler) so frame_time and
            # arrival_ms are both populated once the loop exits.
            while probe.waiting and DateTime.UtcNow < deadline:
                time.sleep(0.005)
                Application.DoEvents()

            inflight_total += probe.skipped_inflight
            prereq_total += probe.skipped_prerequest

            if probe.frame_time is None:
                print("      No frame within {0:.1f}s - skipped ({1} in-flight, {2} pre-request ignored)".format(
                    frame_timeout, probe.skipped_inflight, probe.skipped_prerequest))
                probe.waiting = False
                continue

            frame_dt = probe.frame_time
            raw_ms = (frame_dt - request_dt).TotalMilliseconds
            delay_ms = raw_ms - exposure_ms
            arrival_ms = probe.arrival_ms

            if abs(raw_ms) > 60000.0:
                print("      WARNING: delay is large - frame time base may")
                print("               differ from UTC (local vs UTC).")

            # Discard the first SKIP_FRAMES frames (capture start-up delay).
            if i <= SKIP_FRAMES:
                print("[{0:2d}] Ignored    : {1}  (raw {2:8.3f} ms) - start-up frame".format(
                    i, fmt(frame_dt), raw_ms))
                continue

            print("[{0:2d}] Frame ts     : {1}  (raw {2} ms, delay {3} ms, arrival {4} ms)".format(
                i, fmt(frame_dt), num(raw_ms, 8), num(delay_ms, 8), num(arrival_ms, 8)))
            rows.append((i, request_dt, frame_dt, raw_ms, delay_ms, arrival_ms))
    finally:
        try:
            camera.FrameCaptured -= probe.on_frame
        except Exception:
            pass

    if not rows:
        print("")
        print("No frames measured - nothing to report.")
        return

    # --- Step 5: results table ---
    print("")
    print("(first {0} frame(s) ignored; exposure {1:.3f} ms subtracted from each delay)".format(
        SKIP_FRAMES, exposure_ms))
    print("=" * 89)
    print("{0:>3}  {1:<23}  {2:<23}  {3:>10}  {4:>10}  {5:>10}".format(
        "No", "Request time (UTC)", "Frame time (UTC)", "Raw (ms)", "Delay (ms)", "Arrival (ms)"))
    print("-" * 89)
    for no, req, frm, raw, dly, arr in rows:
        print("{0:>3}  {1:<23}  {2:<23}  {3}  {4}  {5}".format(
            no, fmt(req), fmt(frm), num(raw, 10), num(dly, 10), num(arr, 10)))
    print("=" * 89)

    # --- Step 6: statistics (on the exposure-corrected delays) ---
    delays = [r[4] for r in rows]
    arrivals = [r[5] for r in rows if r[5] is not None]

    mean, sd, lo, hi = stats(delays)
    print("")
    print("Frame acquisition delay (frame ts - request - exposure), n = {0}".format(len(delays)))
    print("  Exposure subtracted : {0:9.3f} ms".format(exposure_ms))
    print("  Mean   : {0:9.3f} ms".format(mean))
    print("  StdDev : {0:9.3f} ms".format(sd))
    print("  Min    : {0:9.3f} ms".format(lo))
    print("  Max    : {0:9.3f} ms".format(hi))

    if arrivals:
        amean, asd, alo, ahi = stats(arrivals)
        print("")
        print("Arrival latency (request -> handler), n = {0}".format(len(arrivals)))
        print("  Mean   : {0:9.3f} ms".format(amean))
        print("  StdDev : {0:9.3f} ms".format(asd))
        print("  Min    : {0:9.3f} ms".format(alo))
        print("  Max    : {0:9.3f} ms".format(ahi))

    # --- Mode verdict -------------------------------------------------------
    # A true triggered exposure starts within a few ms of the request (still
    # mode). If it only starts much later, the camera was streaming frames
    # continuously (video mode) and the delay is the wait for the current
    # exposure to finish, NOT the acquisition latency.
    print("")
    if mean <= TRIGGER_LATENCY_THRESHOLD_MS:
        print("Mode: TRIGGERED / STILL  ->  the delay above IS the acquisition latency")
        print("  (a fresh exposure began ~{0:.1f} ms after each request).".format(mean))
    else:
        print("Mode: CONTINUOUS / VIDEO  ->  the delay above is NOT the acquisition latency")
        print("  The camera was already exposing and could not start a fresh exposure")
        print("  on request. The ~{0:.0f} ms delay is the wait for the current".format(mean))
        print("  exposure to finish (~exposure - SETTLE_S). To measure the true")
        print("  (~tens of ms) acquisition latency, capture in still / triggered mode")
        print("  (e.g. stop live view so single-frame capture is honoured).")

    if inflight_total > 0 or prereq_total > 0:
        print("")
        print("Frame selection: {0} in-flight and {1} pre-request frame(s) were skipped.".format(
            inflight_total, prereq_total))
        if inflight_total > 0:
            print("  In-flight frames mean the camera was already exposing when the")
            print("  request was made (typical of live/video mode, where")
            print("  CaptureSingleFrame() cannot force a fresh exposure). The delays")
            print("  above are measured to the start of the next FRESH exposure.")

    print("")
    print("Done.")


main()
