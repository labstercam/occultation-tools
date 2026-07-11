"""
VizieR light curve .dat file export.

Generates PyOTE-compatible 5-line .dat files for submission to the VizieR
asteroid occultation archive.

File format (5 lines):
    Date: {year}-{month}-{day} {HH:MM:SS.ss}: {duration:.2f}: {num_readings}
    Star: {hipparcos}: 0: 0: 0: {Tycho2}: {UCAC4}
    Observer: {+/-longDeg}:{longMin}:{longSec}: {+/-latDeg}:{latMin}:{latSec}: {altitude}: {observer_name}
    Object: Asteroid: {asteroidNumber}: {asteroidName}
    Values:{v1}:{v2}: :{v3}:...

Values are scaled so the maximum = 9524.  Dropped readings (missing frames)
are encoded as empty colon-separated fields (": " between neighbours).

IronPython 3.4 compatible (no pathlib, no typing, no numpy).
"""

import math
import os
from datetime import datetime, timedelta


# ---------------------------------------------------------------------------
# Star catalog ID parsing
# ---------------------------------------------------------------------------

def parse_star_id(star_id):
    """Parse an OWCloud StarName string into VizieR catalog identifiers.

    Handles:
        'UCAC4 361-199861'  -> ucac4='361-199861'
        'TYC 1234-5678-1'   -> tycho2='1234-5678-1'
        'HIP 12345'         -> hipparcos='12345'
        'Gaia DR3 ...'      -> all empty  (must not be placed in hipparcos)
        'J1234567890123456789' -> all empty (raw GAIA ID starting with 'J')
        Anything unrecognised -> all empty

    Returns a dict with keys 'ucac4', 'tycho2', 'hipparcos'; values are
    strings that are empty when not identified.
    """
    result = {'ucac4': '', 'tycho2': '', 'hipparcos': ''}

    if not star_id:
        return result

    star_id = star_id.strip()
    upper = star_id.upper()

    # Check for raw GAIA ID starting with 'J' (e.g., "J1234567890123456789")
    if upper.startswith('J'):
        # Raw GAIA ID - must NOT go into any VizieR field
        return result

    if upper.startswith('UCAC4 ') or upper.startswith('UCAC4-') or upper.startswith('UCAC4_'):
        # e.g. 'UCAC4 361-199861'
        candidate = star_id[6:].strip()
        parts = candidate.split('-')
        if len(parts) == 2 and len(parts[0]) <= 3 and len(parts[1]) <= 6:
            result['ucac4'] = candidate
        return result

    if upper.startswith('TYC ') or upper.startswith('TYC-'):
        # e.g. 'TYC 1234-5678-1' or 'TYC1234-5678-1'
        candidate = star_id[4:].strip()
        # Allow formats with or without a space after TYC
        parts = candidate.split('-')
        if len(parts) == 3:
            result['tycho2'] = '-'.join(parts)
        return result

    # Tycho2 without prefix might look like 'nnnn-nnnnn-1'
    if upper.startswith('TYCHO2 ') or upper.startswith('TYCHO ') or upper.startswith('TYCHO2-'):
        idx = star_id.index(' ') if ' ' in star_id else star_id.index('-')
        candidate = star_id[idx + 1:].strip()
        parts = candidate.split('-')
        if len(parts) == 3:
            result['tycho2'] = '-'.join(parts)
        return result

    if upper.startswith('HIP ') or upper.startswith('HIP-') or upper.startswith('HIPPARCOS '):
        # e.g. 'HIP 12345'
        idx = star_id.index(' ') if ' ' in star_id else star_id.index('-')
        candidate = star_id[idx + 1:].strip()
        if candidate.isdigit():
            result['hipparcos'] = candidate
        return result

    # Gaia identifiers — must NOT go into any VizieR field
    if upper.startswith('GAIA') or upper.startswith('GAI '):
        return result

    # Unknown format — leave empty so user fills in manually
    return result


# ---------------------------------------------------------------------------
# Coordinate conversion
# ---------------------------------------------------------------------------

def decimal_degrees_to_dms(decimal_degrees):
    """Convert decimal degrees to (deg_str, min_str, sec_str).

    deg_str includes a leading '+' or '-' sign.

    Examples:
        144.9167 -> ('+144', '55', '0.12')
        -37.8136 -> ('-37', '48', '49.0')
    """
    negative = decimal_degrees < 0
    d = abs(decimal_degrees)

    degrees = int(d)
    remainder = (d - degrees) * 60.0
    minutes = int(remainder)
    seconds = (remainder - minutes) * 60.0

    # Round seconds to 2 decimal places
    seconds = round(seconds, 2)

    # Handle 60.0 seconds carry
    if seconds >= 60.0:
        seconds -= 60.0
        minutes += 1
    if minutes >= 60:
        minutes -= 60
        degrees += 1

    sign = '-' if negative else '+'
    deg_str = sign + str(degrees)
    min_str = str(minutes)
    # Format seconds to 2 d.p., stripping trailing zeros to avoid float repr noise
    # e.g. 48.96 not 48.960000000000001
    sec_rounded = round(seconds, 2)
    if sec_rounded == int(sec_rounded):
        sec_str = str(int(sec_rounded))
    else:
        sec_str = ('%.2f' % sec_rounded).rstrip('0')

    return deg_str, min_str, sec_str


# ---------------------------------------------------------------------------
# Timestamp helpers
# ---------------------------------------------------------------------------

def to_seconds(dt):
    """Convert a datetime object (or a datetime with date fixed to 1900-01-01) to
    float seconds from midnight.

    Args:
        dt: datetime object.

    Returns:
        float seconds since 00:00:00.
    """
    return dt.hour * 3600.0 + dt.minute * 60.0 + dt.second + dt.microsecond / 1e6


# ---------------------------------------------------------------------------
# Dropped-reading detection and insertion
# ---------------------------------------------------------------------------

def _is_neg_zero(v):
    """Return True if v is negative zero (-0.0)."""
    return v == 0.0 and math.copysign(1.0, v) < 0


def compute_median_step(times):
    """Compute the median inter-frame time step in seconds using pure Python.

    Args:
        times: list of datetime objects (None entries are skipped).

    Returns:
        float: median step in seconds, or None if fewer than 2 valid timestamps.
    """
    valid = [t for t in times if t is not None]
    if len(valid) < 2:
        return None
    deltas = []
    for i in range(1, len(valid)):
        delta = (valid[i] - valid[i - 1]).total_seconds()
        if delta > 0:
            deltas.append(delta)
    if not deltas:
        return None
    deltas.sort()
    n = len(deltas)
    if n % 2 == 1:
        return deltas[n // 2]
    return (deltas[n // 2 - 1] + deltas[n // 2]) / 2.0


def insert_dropped_readings(frames, times, values, time_step_s):
    """Expand a light curve by inserting -0.0 sentinels for dropped/missing frames.

    A gap between consecutive frames is considered a dropped reading when
    the measured time step exceeds 1.8 * time_step_s.  For each such gap,
    the number of dropped readings is estimated as
        round(gap / time_step_s) - 1
    and that many -0.0 sentinels (with synthetic interpolated timestamps and
    frame numbers) are inserted.

    Rows whose timestamp is None are kept as-is without expansion.

    Args:
        frames:      list of int frame numbers.
        times:       list of datetime objects (None for unparseable rows).
        values:      list of float signal values (None for missing).
        time_step_s: float median time step in seconds (from compute_median_step).

    Returns:
        Tuple (exp_frames, exp_times, exp_values) — expanded parallel lists.
    """
    if time_step_s is None or time_step_s <= 0:
        return list(frames), list(times), list(values)

    drop_threshold = 1.8 * time_step_s

    exp_frames = []
    exp_times = []
    exp_values = []

    for i in range(len(frames)):
        exp_frames.append(frames[i])
        exp_times.append(times[i])
        exp_values.append(values[i])

        # Check gap to the next frame
        if i + 1 >= len(frames):
            continue

        t_now = times[i]
        t_next = times[i + 1]

        if t_now is None or t_next is None:
            continue

        gap = (t_next - t_now).total_seconds()

        # Skip if gap is within normal range (including near-zero anomalous gaps)
        if gap <= drop_threshold:
            continue

        # Number of dropped readings between frame i and frame i+1
        n_dropped = int(round(gap / time_step_s)) - 1
        if n_dropped <= 0:
            continue

        # Insert n_dropped synthetic frames
        t_ref = t_now
        f_now = frames[i]
        for k in range(1, n_dropped + 1):
            synthetic_time = t_ref + timedelta(seconds=time_step_s * k)
            # Synthetic frame number (may be fractional in some formats; use int)
            synthetic_frame = f_now + k
            exp_frames.append(synthetic_frame)
            exp_times.append(synthetic_time)
            # -0.0 sentinel marks a dropped reading
            exp_values.append(-0.0)

    return exp_frames, exp_times, exp_values


# ---------------------------------------------------------------------------
# Trim window calculation
# ---------------------------------------------------------------------------

def compute_trim_window(times, d_time_s=None, r_time_s=None,
                        event_time_s=None, event_duration_s=0.0):
    """Compute the default trim window centred on the occultation event.

    The centre is the midpoint of D and R times if both are provided,
    otherwise the midpoint of whichever is given, otherwise the predicted
    event time.

    The half-window is:
        max(15.0, event_duration_s + 20.0)
    seconds on each side, giving a minimum total window of 30 s and ensuring
    the event shape is visible with sufficient baseline on both sides.

    Args:
        times:            list of datetime objects (expanded by insert_dropped_readings).
                          None entries are treated as having no timestamp.
        d_time_s:         float disappearance time in seconds-from-midnight, or None.
        r_time_s:         float reappearance time in seconds-from-midnight, or None.
        event_time_s:     float predicted event time in seconds-from-midnight, or None.
        event_duration_s: float expected event duration in seconds (default 0).

    Returns:
        Tuple (left_idx, right_idx) — inclusive indices into the times list.
        Falls back to (0, len(times)-1) if no anchor time is available.
    """
    n = len(times)
    if n == 0:
        return 0, 0

    # Choose anchor
    if d_time_s is not None and r_time_s is not None:
        centre_s = (d_time_s + r_time_s) / 2.0
    elif d_time_s is not None:
        centre_s = d_time_s
    elif r_time_s is not None:
        centre_s = r_time_s
    elif event_time_s is not None:
        centre_s = event_time_s
    else:
        return 0, n - 1

    half_window = max(15.0, event_duration_s + 20.0)
    window_start = centre_s - half_window
    window_end = centre_s + half_window

    # Scan for nearest indices
    left_idx = 0
    right_idx = n - 1

    for i, t in enumerate(times):
        if t is None:
            continue
        t_s = to_seconds(t)
        if t_s >= window_start:
            left_idx = i
            break

    for i in range(n - 1, -1, -1):
        t = times[i]
        if t is None:
            continue
        t_s = to_seconds(t)
        if t_s <= window_end:
            right_idx = i
            break

    # Never produce an empty window
    if right_idx < left_idx:
        return 0, n - 1

    return left_idx, right_idx


# ---------------------------------------------------------------------------
# .dat file line builders
# ---------------------------------------------------------------------------

def build_date_line(event_date, initial_time_dt, delta_time_s, num_readings):
    """Build the Date: line for the .dat file.

    Args:
        event_date:     str in 'YYYY-M-D' or 'YYYY-MM-DD' format.
        initial_time_dt: datetime of the first reading in the trimmed window.
        delta_time_s:   float duration of the trimmed window in seconds.
        num_readings:   int number of readings (including inserted dropped readings).

    Returns:
        str: Date line, e.g. 'Date: 2025-12-23 14:30:42.34: 35.21: 294'
    """
    # Format timestamp as HH:MM:SS.ss (2 decimal places on seconds)
    h = initial_time_dt.hour
    m = initial_time_dt.minute
    s = initial_time_dt.second + initial_time_dt.microsecond / 1e6
    ts_str = '%02d:%02d:%05.2f' % (h, m, s)

    return 'Date: %s %s: %.2f: %d' % (event_date, ts_str, delta_time_s, num_readings)


def build_star_line(hipparcos='', tycho2='', ucac4=''):
    """Build the Star: line for the .dat file.

    SAO, XZ80Q, and Kepler2 are always '0' (no longer used by modern Occult4/VizieR).
    Empty catalog fields are replaced with the VizieR 'not provided' sentinels:
        hipparcos -> '0'
        tycho2    -> '0-0-1'
        ucac4     -> '0-0'

    Args:
        hipparcos: str Hipparcos catalog number, or '' if not available.
        tycho2:    str Tycho2 designation (e.g. '1234-5678-1'), or ''.
        ucac4:     str UCAC4 designation (e.g. '361-199861'), or ''.

    Returns:
        str: Star line, e.g. 'Star: 0: 0: 0: 0: 1234-5678-1: 361-199861'
    """
    hip = hipparcos if hipparcos else '0'
    tyc = tycho2 if tycho2 else '0-0-1'
    uca = ucac4 if ucac4 else '0-0'
    # SAO, XZ80Q, Kepler2 always 0
    return 'Star: %s: 0: 0: 0: %s: %s' % (hip, tyc, uca)


def build_location_line(lat_decimal, lon_decimal, altitude_m, observer_name):
    """Build the Observer: line for the .dat file.

    Longitude and latitude are expressed as degrees/minutes/seconds with
    a leading sign on the degrees field.

    Args:
        lat_decimal:   float observer latitude in decimal degrees (+N, -S).
        lon_decimal:   float observer longitude in decimal degrees (+E, -W).
        altitude_m:    float or int observer altitude in metres above sea level.
        observer_name: str observer name.

    Returns:
        str: Observer line.
    """
    lon_d, lon_m, lon_s = decimal_degrees_to_dms(lon_decimal)
    lat_d, lat_m, lat_s = decimal_degrees_to_dms(lat_decimal)
    alt = str(int(round(altitude_m)))
    return ('Observer: %s:%s:%s: %s:%s:%s: %s: %s'
            % (lon_d, lon_m, lon_s, lat_d, lat_m, lat_s, alt, observer_name))


def build_object_line(asteroid_number, asteroid_name):
    """Build the Object: line for the .dat file.

    Args:
        asteroid_number: str or int asteroid catalog number (max 6 digits).
        asteroid_name:   str asteroid name (e.g. '2001 PA3').

    Returns:
        str: Object line.
    """
    return 'Object: Asteroid: %s: %s' % (str(asteroid_number), asteroid_name)


def build_values_line(expanded_values):
    """Build the Values: line for the .dat file.

    The values are scaled so that the maximum (ignoring dropped readings)
    equals 9524, matching the PyOTE VizieR format.  Dropped readings
    (-0.0 sentinels) are encoded as empty fields (i.e. ': :' produces
    '  ': ').

    Args:
        expanded_values: list of float signal values; dropped readings are
                         represented as -0.0 (use insert_dropped_readings).

    Returns:
        str: Values line, e.g. 'Values:9524:9487: :8901:...'

    Raises:
        ValueError: If expanded_values contains no valid (non-dropped) readings,
                    or if all valid values are zero.
    """
    valid = [v for v in expanded_values if v is not None and not _is_neg_zero(v)]
    if not valid:
        raise ValueError('No valid signal values to export.')

    max_val = max(valid)
    if max_val <= 0:
        raise ValueError('Maximum signal value is zero or negative; cannot scale.')

    scale_factor = 9524.0 / max_val

    parts = ['Values']
    for v in expanded_values:
        if v is None or _is_neg_zero(v):
            parts.append(' ')   # empty field = dropped reading
        else:
            parts.append(str(int(round(v * scale_factor))))

    return ':'.join(parts)


# ---------------------------------------------------------------------------
# Filename generation
# ---------------------------------------------------------------------------

def generate_dat_filename(asteroid_number, initial_time_dt, event_date):
    """Generate the VizieR .dat filename.

    Format: ({asteroidNumber})_{yyyymmdd}_{HH}{MM}{SS}_{FF}.dat
    where SS and FF are the integer and fractional parts of the seconds.

    Args:
        asteroid_number: str or int asteroid catalog number.
        initial_time_dt: datetime of the first reading in the trimmed window.
        event_date:      str in 'YYYY-M-D' or 'YYYY-MM-DD' format.

    Returns:
        str: filename, e.g. '(778)_20251223_143042_34.dat'
    """
    # Normalise event_date to yyyymmdd. Accept 'YYYY-MM-DD' and 'YYYY-M-D'.
    try:
        parts = str(event_date).split('-')
        d = datetime(int(parts[0]), int(parts[1]), int(parts[2]))
    except (ValueError, IndexError):
        d = datetime(1900, 1, 1)
    date_str = '%04d%02d%02d' % (d.year, d.month, d.day)

    hh = '%02d' % initial_time_dt.hour
    mm_str = '%02d' % initial_time_dt.minute
    total_sec = initial_time_dt.second + initial_time_dt.microsecond / 1e6
    ss_int = '%02d' % int(total_sec)
    # Two-digit fractional seconds (centiseconds)
    centisecs = '%02d' % int(round((total_sec - int(total_sec)) * 100))

    return '(%s)_%s_%s%s%s_%s.dat' % (str(asteroid_number), date_str, hh, mm_str, ss_int, centisecs)


# ---------------------------------------------------------------------------
# Output path resolution
# ---------------------------------------------------------------------------

def get_output_paths(asteroid_number, initial_time_dt, event_date,
                     reports_folder, observation_folder):
    """Return the list of destination file paths for a VizieR .dat export.

    Three copies are written:
        1. %USERPROFILE%\\Documents\\VizieR_lightcurves\\  (PyOTE-compatible location)
        2. OM data/reports/ folder
        3. The observation source folder (where the light curve CSV came from)

    Destination directories are created if they do not exist.

    Args:
        asteroid_number:    str or int.
        initial_time_dt:    datetime of first trimmed reading.
        event_date:         str 'YYYY-MM-DD' or 'YYYY-M-D'.
        reports_folder:     str path to OM data/reports/ folder.
        observation_folder: str path to the folder containing the source light curve.

    Returns:
        List[str]: up to 3 absolute file paths (duplicates suppressed).
    """
    filename = generate_dat_filename(asteroid_number, initial_time_dt, event_date)

    paths = []

    # 1. VizieR_lightcurves in user Documents
    user_profile = os.environ.get('USERPROFILE') or os.environ.get('HOME', '')
    if user_profile:
        vizier_dir = os.path.join(user_profile, 'Documents', 'VizieR_lightcurves')
        paths.append(os.path.join(vizier_dir, filename))

    # 2. OM reports folder
    if reports_folder:
        paths.append(os.path.join(str(reports_folder), filename))

    # 3. Observation source folder
    if observation_folder:
        candidate = os.path.join(str(observation_folder), filename)
        if candidate not in paths:
            paths.append(candidate)

    return paths


# ---------------------------------------------------------------------------
# Core export function
# ---------------------------------------------------------------------------

def export_vizier_dat(output_path,
                      event_date,
                      initial_time_dt,
                      delta_time_s,
                      num_readings,
                      ucac4,
                      tycho2,
                      hipparcos,
                      lat_decimal,
                      lon_decimal,
                      altitude_m,
                      observer_name,
                      asteroid_number,
                      asteroid_name,
                      expanded_values,
                      timing_correction_s=0.0):
    """Write a single VizieR .dat file.

    The output directory is created if it does not already exist.

    Args:
        output_path:        str full path of the file to write.
        event_date:         str 'YYYY-MM-DD' or 'YYYY-M-D' observation date.
        initial_time_dt:    datetime of the first reading in the trimmed window
                            (before timing_correction_s is applied).
        delta_time_s:       float duration of the trimmed window in seconds.
        num_readings:       int total frame count including inserted dropped readings.
        ucac4:              str UCAC4 designation (e.g. '361-199861'), or ''.
        tycho2:             str Tycho2 designation (e.g. '1234-5678-1'), or ''.
        hipparcos:          str Hipparcos number, or ''.
        lat_decimal:        float observer latitude in decimal degrees (+N, -S).
        lon_decimal:        float observer longitude in decimal degrees (+E, -W).
        altitude_m:         float or int observer altitude in metres.
        observer_name:      str observer name.
        asteroid_number:    str or int asteroid catalog number.
        asteroid_name:      str asteroid name.
        expanded_values:    list of float signal values; dropped readings = -0.0.
        timing_correction_s: float net timing correction in seconds, combining
                             NTP offset and camera acquisition delay components
                             that were not applied in the source tool. Subtracted
                             from initial_time_dt to correct the .dat start time.
                             Default 0.0 (no correction).

    Raises:
        ValueError: If expanded_values contains no valid readings.
        IOError:    If the output file cannot be written.
    """
    # Apply timing correction to initial timestamp
    corrected_time = initial_time_dt
    if timing_correction_s != 0.0:
        corrected_time = initial_time_dt - timedelta(seconds=timing_correction_s)

    date_line = build_date_line(event_date, corrected_time, delta_time_s, num_readings)
    star_line = build_star_line(hipparcos, tycho2, ucac4)
    location_line = build_location_line(lat_decimal, lon_decimal, altitude_m, observer_name)
    object_line = build_object_line(asteroid_number, asteroid_name)
    values_line = build_values_line(expanded_values)

    out_dir = os.path.dirname(output_path)
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir)

    with open(output_path, 'w') as f:
        f.write(date_line + '\n')
        f.write(star_line + '\n')
        f.write(location_line + '\n')
        f.write(object_line + '\n')
        f.write(values_line + '\n')


# ---------------------------------------------------------------------------
# High-level convenience function
# ---------------------------------------------------------------------------

def export_all_copies(event_date,
                      initial_time_dt,
                      delta_time_s,
                      num_readings,
                      ucac4,
                      tycho2,
                      hipparcos,
                      lat_decimal,
                      lon_decimal,
                      altitude_m,
                      observer_name,
                      asteroid_number,
                      asteroid_name,
                      expanded_values,
                      reports_folder,
                      observation_folder,
                      timing_correction_s=0.0):
    """Export the VizieR .dat file to all three standard destinations.

    Calls get_output_paths() to determine destinations then calls
    export_vizier_dat() for each.

    Returns:
        List[str]: paths that were successfully written.

    Raises:
        ValueError: If expanded_values contains no valid readings (before any
                    writes are attempted).
    """
    paths = get_output_paths(
        asteroid_number, initial_time_dt, event_date,
        reports_folder, observation_folder
    )

    written = []
    errors = []
    for path in paths:
        try:
            export_vizier_dat(
                output_path=path,
                event_date=event_date,
                initial_time_dt=initial_time_dt,
                delta_time_s=delta_time_s,
                num_readings=num_readings,
                ucac4=ucac4,
                tycho2=tycho2,
                hipparcos=hipparcos,
                lat_decimal=lat_decimal,
                lon_decimal=lon_decimal,
                altitude_m=altitude_m,
                observer_name=observer_name,
                asteroid_number=asteroid_number,
                asteroid_name=asteroid_name,
                expanded_values=expanded_values,
                timing_correction_s=timing_correction_s,
            )
            written.append(path)
        except Exception as exc:
            errors.append((path, str(exc)))

    if errors and not written:
        raise IOError('All export destinations failed: ' + '; '.join(
            '%s: %s' % (p, e) for p, e in errors
        ))

    return written
