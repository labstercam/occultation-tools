# light_curve_reader.py
# IronPython 3.4 compatible
#
# Auto-detecting light curve reader for Tangra, PyOTE, R-OTE, and Limovie formats.
# Tangra files are delegated to light_curves_iron.get_observation_summary() unchanged.
# All formats return a dict with the same keys as light_curves_iron.analyse_timestamps_iron().
#
# Supported formats:
#   - Tangra  (delegated to light_curves_iron)
#   - PyOTE   (CSV files with '#' comment header containing 'PyOTE' or 'PyMovie')
#   - R-OTE   (CSV files with '#' comment header; same data layout as PyOTE)
#   - Limovie

import os
from datetime import datetime


def detect_format(filepath):
    """Detect the light curve CSV format by reading the first few lines.

    PyOTE/PyMovie files begin with '#' comment lines before the 'FrameNum'
    header; R-OTE files also use '#' but lack 'PyOTE'/'PyMovie' markers.
    Read up to 20 lines so the PyOTE/PyMovie identifier is found even when
    it appears after the first comment line.

    Returns: 'Tangra', 'Limovie', 'PyOTE', 'R-OTE', or 'unknown'
    """
    try:
        header_lines = []
        with open(filepath, 'r') as f:
            for _ in range(20):
                line = f.readline()
                if not line:
                    break
                header_lines.append(line)

        combined = ''.join(header_lines)
        first_line = header_lines[0] if header_lines else ''

        if 'Tangra' in first_line:
            return 'Tangra'
        elif 'Limovie' in first_line:
            return 'Limovie'
        elif 'PyOTE' in combined or 'PyMovie' in combined:
            return 'PyOTE'
        elif 'R-OTE' in combined or (header_lines and header_lines[0].startswith('#')):
            return 'R-OTE'
        else:
            return 'unknown'
    except Exception:
        return 'unknown'


def _parse_time(time_str):
    """Parse a bracketed time string such as [HH:MM:SS.ffffff] or [HH:MM:SS.ffff].

    Returns a datetime object (date fixed to 1900-01-01), or None if parsing fails.
    """
    if not time_str:
        return None
    time_str = time_str.strip().replace('[', '').replace(']', '')
    try:
        return datetime.strptime(time_str, '%H:%M:%S.%f')
    except ValueError:
        try:
            return datetime.strptime(time_str, '%H:%M:%S')
        except ValueError:
            return None


def _read_rote_data(filepath):
    """Read R-OTE / PyOTE light curve data.

    Header detection key: 'FrameNum'
    Sample data line: 1.00,[17:25:39.3415],2737.8,3897.32,...

    Returns: (frames, times, values) as parallel lists.
    """
    frames = []
    times = []
    values = []

    with open(filepath, 'r') as f:
        lines = f.readlines()

    # Skip '#' comment lines (PyOTE files begin with comment blocks) until 'FrameNum' header
    data_start = -1
    for i, line in enumerate(lines):
        if 'FrameNum' in line:
            data_start = i + 1
            break

    if data_start < 0:
        raise ValueError("R-OTE/PyOTE header 'FrameNum' not found in file: " + filepath)

    for line in lines[data_start:]:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        part = line.split(',')
        if len(part) < 3:
            continue

        try:
            frame = int(float(part[0]))
        except (ValueError, IndexError):
            continue

        t = _parse_time(part[1]) if len(part) > 1 else None

        try:
            val = float(part[2]) if len(part) > 2 and part[2].strip() else None
        except ValueError:
            val = None

        frames.append(frame)
        times.append(t)
        values.append(val)

    return frames, times, values


def _read_limovie_data(filepath):
    """Read Limovie light curve data.

    Header detection key: 'No.'
    Sample data line: 3.5,21381195,21381200,22,27,43.0000,,,,,2737.8,3897.32,...
      part[0]  = frame number
      part[3]  = hours
      part[4]  = minutes
      part[5]  = seconds (decimal)
      part[10] = target star signal

    Returns: (frames, times, values) as parallel lists.
    """
    frames = []
    times = []
    values = []

    with open(filepath, 'r') as f:
        lines = f.readlines()

    # Find the 'No.' header line
    data_start = -1
    for i, line in enumerate(lines):
        if 'No.' in line:
            data_start = i + 1
            break

    if data_start < 0:
        raise ValueError("Limovie header 'No.' not found in file: " + filepath)

    for line in lines[data_start:]:
        line = line.strip()
        if not line:
            continue
        part = line.split(',')

        try:
            frame = int(float(part[0]))
        except (ValueError, IndexError):
            continue

        # Reconstruct bracketed [HH:MM:SS.ssss] from columns 3-5
        # Strip each part to guard against whitespace in some Limovie versions
        t = None
        if len(part) > 5:
            try:
                t = _parse_time('[' + part[3].strip() + ':' + part[4].strip() + ':' + part[5].strip() + ']')
            except (ValueError, IndexError):
                t = None

        # Target star signal is at column index 10
        val = None
        if len(part) > 10:
            try:
                val = float(part[10]) if part[10].strip() else None
            except ValueError:
                val = None

        frames.append(frame)
        times.append(t)
        values.append(val)

    return frames, times, values


# ---------------------------------------------------------------------------
# Statistics helpers — duplicated from light_curves_iron.py so this module
# has no cross-module dependency beyond the standard library.
# ---------------------------------------------------------------------------

def _calculate_median(values):
    if not values:
        return 0.0
    sorted_values = sorted(values)
    n = len(sorted_values)
    if n % 2 == 0:
        return (sorted_values[n // 2 - 1] + sorted_values[n // 2]) / 2.0
    return sorted_values[n // 2]


def _calculate_std(values, mean):
    if not values or len(values) < 2:
        return 0.0
    variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
    return variance ** 0.5


def _calculate_percentile(values, percentile):
    if not values:
        return 0.0
    sorted_values = sorted(values)
    n = len(sorted_values)
    k = (n - 1) * percentile / 100.0
    f = k - int(k)
    idx = int(k)
    if idx >= n - 1:
        return sorted_values[-1]
    return sorted_values[idx] + f * (sorted_values[idx + 1] - sorted_values[idx])


# ---------------------------------------------------------------------------

def _compute_summary(frames, times, values, filepath, source_format, percentiles=None):
    """Compute an observation summary dict from parallel (frames, times, values) lists.

    The returned dict has the same keys as light_curves_iron.analyse_timestamps_iron(),
    plus the additional key 'source_format'.
    """
    filename = os.path.basename(filepath)

    # Only rows with a valid timestamp are used for timing statistics
    valid_rows = [(f, t, v) for f, t, v in zip(frames, times, values) if t is not None]

    if len(valid_rows) < 2:
        raise ValueError(
            'Not enough valid timestamps in light curve'
            ' (need at least 2 rows with parseable times)'
        )

    valid_frames = [r[0] for r in valid_rows]
    valid_times = [r[1] for r in valid_rows]
    valid_values = [r[2] for r in valid_rows]

    # Time deltas in milliseconds
    timediffs = []
    for i in range(1, len(valid_times)):
        delta = valid_times[i] - valid_times[i - 1]
        timediffs.append(delta.total_seconds() * 1000.0)

    if not timediffs:
        raise ValueError('Could not calculate any time differences')

    tdelta_min = min(timediffs)
    tdelta_max = max(timediffs)
    tdelta_mean = sum(timediffs) / len(timediffs)
    tdelta_median = _calculate_median(timediffs)
    tdelta_std = _calculate_std(timediffs, tdelta_mean)

    first_frame_no = valid_frames[0]
    last_frame_no = valid_frames[-1]
    frame_count = last_frame_no - first_frame_no + 1
    no_rows_in_csv = len(frames)

    total_time_sec = (valid_times[-1] - valid_times[0]).total_seconds()
    n_valid = len(valid_times)
    exposure_from_row_count = total_time_sec / (n_valid - 1) * 1000.0 if n_valid > 1 else 0.0
    exposure_from_frame_no = total_time_sec / (frame_count - 1) * 1000.0 if frame_count > 1 else 0.0

    n_late_frames = sum(1 for td in timediffs if td > tdelta_median * 1.9)
    n_delayed_frames = sum(1 for td in timediffs if td > tdelta_median * 1.1)

    # Repeated frames: consecutive rows whose signal values are identical and non-None
    n_repeated_frames = 0
    for i in range(1, len(valid_values)):
        if valid_values[i] is not None and valid_values[i] == valid_values[i - 1]:
            n_repeated_frames += 1

    # Blank cells: rows where the value could not be parsed
    n_blank_cells = sum(1 for v in values if v is None)
    no_rows_missing_signal = n_blank_cells

    start_time = valid_times[0].strftime('%H:%M:%S.%f')[:12]
    end_time = valid_times[-1].strftime('%H:%M:%S.%f')[:12]
    exposure_integration = 'Exposure' if (tdelta_median > 0 and tdelta_std < tdelta_median * 0.1) else 'Integration'

    result = {
        'file_read_from': filepath,
        'filename_from_tangra': filename,   # kept for downstream consumer compatibility
        'source_format': source_format,
        'start_time': start_time,
        'end_time': end_time,
        'tdelta_min': tdelta_min,
        'tdelta_max': tdelta_max,
        'tdelta_median': tdelta_median,
        'tdelta_mean': tdelta_mean,
        'tdelta_std': tdelta_std,
        'first_frame_no': first_frame_no,
        'last_frame_no': last_frame_no,
        'frame_count': frame_count,
        'no_rows_in_csv': no_rows_in_csv,
        'no_rows_missing_signal': no_rows_missing_signal,
        'exposure_from_row_count': exposure_from_row_count,
        'exposure_from_frame_no': exposure_from_frame_no,
        'n_late_frames': n_late_frames,
        'n_delayed_frames': n_delayed_frames,
        'n_repeated_frames': n_repeated_frames,
        'n_blank_cells': n_blank_cells,
        'video_format': '',
        'exposure_integration': exposure_integration,
    }

    if percentiles is not None:
        for p in percentiles:
            result['tdelta_percentile_' + str(p)] = _calculate_percentile(timediffs, p) - tdelta_median

    return result


def read_light_curve(filepath):
    """Read a light curve CSV file and return parallel (frames, times, values) lists.

    Works for Tangra, R-OTE/PyOTE, and Limovie formats.  For Tangra, delegates to
    light_curves_iron.read_tangra_csv_iron() and extracts the three lists from the
    returned dict so the same data structure is returned for all formats.

    Args:
        filepath: Path to the light curve CSV file.

    Returns:
        Tuple (frames, times, values) where:
          frames -- list of int frame numbers
          times  -- list of datetime objects (or None for unparseable rows)
          values -- list of float signal values (or None for missing values)

    Raises:
        ValueError: If the format is not recognised.
    """
    fmt = detect_format(filepath)

    if fmt == 'Tangra':
        import light_curves_iron as lc
        tangra_obj = lc.read_tangra_csv_iron(filepath)
        light_curve = tangra_obj.get('light_curve', [])
        frames = [r.get('frameno') for r in light_curve]
        times = [r.get('time_ut') for r in light_curve]
        # Tangra exports Signal (1) = raw aperture sum (including sky) and
        # Background (1) = total sky background contribution for the aperture.
        # Subtract background to match the background-corrected values that
        # PyOTE/R-OTE export in their own CSV format.
        def _net_signal(r):
            sig = r.get('signal_1')
            bg = r.get('background_1')
            if sig is not None and bg is not None:
                return sig - bg
            return sig
        values = [_net_signal(r) for r in light_curve]
        return frames, times, values

    elif fmt in ('PyOTE', 'R-OTE'):
        return _read_rote_data(filepath)

    elif fmt == 'Limovie':
        return _read_limovie_data(filepath)

    else:
        raise ValueError('Unrecognised light curve format in file: ' + filepath)


def get_observation_summary(filepath, percentiles=None):
    """Auto-detect light curve format and return an observation summary dict.

    For Tangra files, delegates to light_curves_iron.get_observation_summary() and
    injects source_format='Tangra'.  For R-OTE/PyOTE and Limovie, parses the file
    directly and returns a dict with the same key structure.

    Args:
        filepath:   Path to the light curve CSV file.
        percentiles: Optional list of percentile values, e.g. [1, 99].

    Returns:
        Dict with the same keys as light_curves_iron.analyse_timestamps_iron(),
        plus 'source_format' ('Tangra', 'R-OTE', or 'Limovie').

    Raises:
        ValueError: If the format is not recognised or the file cannot be parsed.
    """
    fmt = detect_format(filepath)

    if fmt == 'Tangra':
        import light_curves_iron as lc
        result = lc.get_observation_summary(filepath, percentiles=percentiles)
        result['source_format'] = 'Tangra'
        return result

    elif fmt in ('PyOTE', 'R-OTE'):
        frames, times, values = _read_rote_data(filepath)
        return _compute_summary(frames, times, values, filepath, fmt, percentiles)

    elif fmt == 'Limovie':
        frames, times, values = _read_limovie_data(filepath)
        return _compute_summary(frames, times, values, filepath, 'Limovie', percentiles)

    else:
        raise ValueError('Unrecognised light curve format in file: ' + filepath)
