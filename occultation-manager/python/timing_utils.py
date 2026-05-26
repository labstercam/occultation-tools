"""
Timing correction utilities for the report workflow.

Provides helpers for building, validating, and interpreting the
``timing_data`` dict that flows from the §5 Timing section of
ComprehensiveReportDialog through the report generators and into
VizierExportDialog.

IronPython 3.4 compatible (no pathlib, no typing, no numpy).
"""


# ---------------------------------------------------------------------------
# timing_data schema
# ---------------------------------------------------------------------------
#
# timing_data = {
#     'timing_method':          str   -- 'NTP' | 'GPS_dumb' | 'other'
#     'camera_delay_ms':        float -- NTP only: per_line_delay*Y + line_0_delay
#     'camera_delay_y_line':    int   -- NTP only: sensor Y line used
#     'calib_run_id':           str   -- NTP only: UUID of matched calibration run
#     'ntp_offset_ms':          float -- NTP only: best_offset*1000 from NTP analysis
#     'camera_delay_applied':   bool  -- NTP only: True = already applied in Tangra
#     'ntp_applied':            bool  -- NTP only: True = NTP offset applied in Tangra
#     'net_correction_s':       float -- seconds to add to D/R times and .dat start
#                                        (0.0 when all corrections already applied)
#     'lc_timestamps_corrected': bool|None
#                                        True  = both applied (no OM adjustment needed)
#                                        False = at least one not applied (adjust D/R)
#                                        None  = GPS_dumb / other (unknown state)
# }
#
# Sign convention:
#   net_correction_s < 0 -> event happened earlier than the raw timestamp indicates
#                           (add to D/R, i.e. subtract the magnitude from the raw time)
#   camera_delay: raw_timestamp = true_event_time + delay  =>  subtract delay
#                 (positive camera_delay: timestamp is late, event happened earlier)
#   ntp_offset:   true_UTC      = PC_time + best_offset    =>  add offset
#                 (positive ntp_offset: PC clock is slow, timestamps are early)
#   net = -camera_delay + ntp_offset  (confirmed: Tangra entry = camera_delay - ntp_offset)
# ---------------------------------------------------------------------------


def build_timing_data(timing_method,
                      camera_delay_ms=0.0,
                      camera_delay_y_line=None,
                      calib_run_id=None,
                      ntp_offset_ms=0.0,
                      camera_delay_applied=None,
                      ntp_applied=None):
    """Build and return a fully-computed timing_data dict.

    Args:
        timing_method:        str  -- 'NTP', 'GPS_dumb', or 'other'
        camera_delay_ms:      float -- calculated camera acquisition delay (ms)
        camera_delay_y_line:  int or None -- Y line used for calculation
        calib_run_id:         str or None -- UUID of the matched calibration run
        ntp_offset_ms:        float -- NTP offset in ms (from best_offset * 1000)
        camera_delay_applied: bool or None -- user declaration in §5
        ntp_applied:          bool or None -- user declaration in §5

    Returns:
        dict conforming to the timing_data schema.
    """
    if timing_method not in ('NTP', 'GPS_dumb', 'other'):
        raise ValueError("timing_method must be 'NTP', 'GPS_dumb', or 'other', got: %r" % timing_method)

    if timing_method == 'NTP':
        net_s = compute_net_correction_s(
            camera_delay_ms=camera_delay_ms,
            ntp_offset_ms=ntp_offset_ms,
            camera_delay_applied=camera_delay_applied,
            ntp_applied=ntp_applied,
        )
        if camera_delay_applied is True and ntp_applied is True:
            lc_corrected = True
        elif camera_delay_applied is False or ntp_applied is False:
            lc_corrected = False
        else:
            lc_corrected = None

        return {
            'timing_method': 'NTP',
            'camera_delay_ms': float(camera_delay_ms or 0.0),
            'camera_delay_y_line': camera_delay_y_line,
            'calib_run_id': calib_run_id,
            'ntp_offset_ms': float(ntp_offset_ms or 0.0),
            'camera_delay_applied': camera_delay_applied,
            'ntp_applied': ntp_applied,
            'net_correction_s': net_s,
            'lc_timestamps_corrected': lc_corrected,
        }
    else:
        # GPS_dumb and other: no corrections applied by OM
        return {
            'timing_method': timing_method,
            'camera_delay_ms': 0.0,
            'camera_delay_y_line': None,
            'calib_run_id': None,
            'ntp_offset_ms': 0.0,
            'camera_delay_applied': None,
            'ntp_applied': None,
            'net_correction_s': 0.0,
            'lc_timestamps_corrected': None,
        }


def compute_net_correction_s(camera_delay_ms, ntp_offset_ms,
                              camera_delay_applied, ntp_applied):
    """Return the net timing correction in seconds for NTP-method recordings.

    Only corrections that have NOT been applied are included in the net value.

    Args:
        camera_delay_ms:      float -- camera acquisition delay in ms
        ntp_offset_ms:        float -- NTP clock offset in ms
        camera_delay_applied: bool or None -- True = already applied; False/None = not applied
        ntp_applied:          bool or None -- True = already applied; False/None = not applied

    Returns:
        float -- net correction in seconds to add to raw D/R timestamps
    """
    net_ms = 0.0
    if camera_delay_applied is not True:
        net_ms -= float(camera_delay_ms or 0.0)   # positive delay → timestamp is late → subtract
    if ntp_applied is not True:
        net_ms += float(ntp_offset_ms or 0.0)     # positive offset → PC clock slow (behind UTC) → add
    return net_ms / 1000.0


def apply_correction_to_dr(d_seconds, r_seconds, timing_data):
    """Apply the net timing correction to raw D and R time values.

    Only applies when lc_timestamps_corrected is explicitly False (i.e.
    timing_method is NTP and the user declared corrections were not applied).

    Args:
        d_seconds:   float or None -- disappearance time (seconds past midnight)
        r_seconds:   float or None -- reappearance time (seconds past midnight)
        timing_data: dict or None  -- from build_timing_data(); None = no-op

    Returns:
        tuple (corrected_d, corrected_r) -- same types as inputs; None passes through.
    """
    if timing_data is None or timing_data.get('lc_timestamps_corrected') is not False:
        return d_seconds, r_seconds

    correction_s = timing_data.get('net_correction_s', 0.0) or 0.0
    if correction_s == 0.0:
        return d_seconds, r_seconds

    corrected_d = (d_seconds + correction_s) if d_seconds is not None else None
    corrected_r = (r_seconds + correction_s) if r_seconds is not None else None
    return corrected_d, corrected_r


def seconds_to_hms(total_seconds):
    """Convert a seconds-past-midnight float to (hours, minutes, seconds_float).

    Handles wraparound at 86400 s (midnight crossing).

    Returns:
        tuple (int hours, int minutes, float seconds)
    """
    total_seconds = total_seconds % 86400.0
    h = int(total_seconds // 3600)
    remaining = total_seconds - h * 3600
    m = int(remaining // 60)
    s = remaining - m * 60
    return h, m, s
