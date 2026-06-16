"""
Reader for PyOTE fit_metrics.txt files.

Supports:
- CSV-style header line starting with "aperture name,"
- Blank lines
- Optional "Source file is <path>" lines

IronPython 3.4 compatible (no pathlib, no typing).
"""

import csv


_NUMERIC_COLUMNS = {
    "time err +/-secs",
    "DNR",
    "FP metric",
    "magDrop",
    "percent drop",
    "duration (secs)",
    "D frame",
    "R frame",
    "B",
    "A",
    "sigmaB",
    "sigmaA",
    "observed drop",
    "FP drop",
    "FP margin",
}


def detect_pyote_metrics(file_path):
    """Return True if file_path is a PyOTE fit_metrics file (header starts with 'aperture name,')."""
    try:
        with open(str(file_path), 'r') as f:
            for line in f:
                stripped = line.strip()
                if stripped:
                    return stripped.lower().startswith('aperture name,')
    except Exception:
        pass
    return False


def read_pyote_fit_metrics(file_path, coerce_types=True):
    """Read a PyOTE fit_metrics.txt file and return a list of dicts, one per event row."""
    rows = []
    header = None
    current_source_file = None

    with open(str(file_path), 'r') as handle:
        for raw_line in handle:
            line = raw_line.strip()

            if not line:
                continue

            if line.startswith("Source file is "):
                current_source_file = line[len("Source file is "):].strip()
                continue

            if line.startswith("aperture name,"):
                header = next(csv.reader([line]))
                continue

            if header is None:
                continue

            parsed = next(csv.reader([line]))
            if not parsed:
                continue

            extra = []
            if len(parsed) < len(header):
                parsed.extend([""] * (len(header) - len(parsed)))
            elif len(parsed) > len(header):
                extra = parsed[len(header):]
                parsed = parsed[:len(header)]
            else:
                extra = []

            record = dict(zip(header, parsed))

            if extra:
                record["_extra_columns"] = extra

            if current_source_file is not None:
                record["source_file"] = current_source_file

            if coerce_types:
                for key in _NUMERIC_COLUMNS:
                    value = record.get(key, "")
                    if value == "":
                        continue
                    try:
                        record[key] = float(value)
                    except ValueError:
                        pass

            rows.append(record)

    return rows


def _parse_bracketed_time(time_str):
    """Parse [HH:MM:SS.ssss] or HH:MM:SS.ssss into (hours_str, minutes_str, seconds_str).

    Returns (None, None, None) on failure.
    """
    if not time_str:
        return None, None, None
    s = time_str.strip().strip('[]')
    parts = s.split(':')
    if len(parts) != 3:
        return None, None, None
    return parts[0], parts[1], parts[2]


def record_to_aota_report_data(record):
    """Convert a PyOTE fit_metrics record to the aota_report_data dict shape used by report generators.

    Field mapping:
      D time           -> d_hours, d_minutes, d_seconds
      R time           -> r_hours, r_minutes, r_seconds
      time err +/-secs -> d_uncertainty, r_uncertainty
      DNR              -> snr
    """
    d_h, d_m, d_s = _parse_bracketed_time(record.get('D time', ''))
    r_h, r_m, r_s = _parse_bracketed_time(record.get('R time', ''))
    uncertainty = record.get('time err +/-secs', None)
    snr = record.get('DNR', None)
    try:
        uncertainty = round(float(uncertainty), 3) if uncertainty is not None else None
    except (TypeError, ValueError):
        pass
    try:
        snr = round(float(snr), 1) if snr is not None else None
    except (TypeError, ValueError):
        pass
    return {
        'd_hours':       d_h if d_h is not None else '',
        'd_minutes':     d_m if d_m is not None else '',
        'd_seconds':     d_s if d_s is not None else '',
        'd_uncertainty': uncertainty,
        'r_hours':       r_h if r_h is not None else '',
        'r_minutes':     r_m if r_m is not None else '',
        'r_seconds':     r_s if r_s is not None else '',
        'r_uncertainty': uncertainty,
        'snr':           snr,
    }


def format_record_display(record):
    """Return a one-line summary of a record suitable for a listbox entry."""
    aperture = record.get('aperture name', 'unknown')
    d_time = record.get('D time', '?')
    r_time = record.get('R time', '?')
    return "{0}  D:{1}  R:{2}".format(aperture, d_time, r_time)
