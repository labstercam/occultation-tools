"""NTP timing analysis computation core — IronPython / CPython compatible.

Provides all data classes, parsing, statistical, and geographic functions needed
to analyse Meinberg NTP loopstats/peerstats files.  Contains no Windows Forms or
clr dependencies so it can be imported by occultation-manager or any other tool.

The GUI shell (analyze_ntp_timing_accuracy.py) imports everything from this module.
"""

import csv
import ipaddress
import json
import math
import os
import re
import socket
import sys
import urllib.request
from datetime import date, datetime, timedelta


MJD_EPOCH = date(1858, 11, 17)
SQRT3 = math.sqrt(3.0)

# Speed of light in single-mode fibre (km/s): c / refractive_index (n ≈ 1.467).
# Used to compute the minimum one-way propagation delay from geographic distance.
_FIBRE_SPEED_KMS = 299792.458 / 1.467   # ≈ 204,354 km/s


class LoopRecord(object):
    def __init__(self, mjd, sec_of_day, offset, freq, jitter):
        self.mjd = mjd
        self.sec_of_day = sec_of_day
        self.offset = offset
        self.freq = freq
        self.jitter = jitter


class PeerRecord(object):
    def __init__(self, mjd, sec_of_day, status, delay, dispersion, jitter, server_address="", offset=0.0):
        self.mjd = mjd
        self.sec_of_day = sec_of_day
        self.status = status
        self.delay = delay
        self.dispersion = dispersion
        self.jitter = jitter
        self.server_address = server_address
        self.offset = offset


class DayOption(object):
    def __init__(self, key, label, loop_path, peer_path, target_mjd, recency_score):
        self.key = key
        self.label = label
        self.loop_path = loop_path
        self.peer_path = peer_path
        self.target_mjd = target_mjd
        self.recency_score = recency_score


class AnalysisResult(object):
    def __init__(
        self,
        option,
        mjds,
        loop_rows_used,
        peer_rows_total,
        peer_rows_used,
        peer_selection_note,
        metrics,
        diagnostics,
        pit_result=None,
    ):
        self.option = option
        self.mjds = mjds
        self.loop_rows_used = loop_rows_used
        self.peer_rows_total = peer_rows_total
        self.peer_rows_used = peer_rows_used
        self.peer_selection_note = peer_selection_note
        self.metrics = metrics
        self.diagnostics = diagnostics
        self.pit_result = pit_result


def mjd_to_date_string(mjd):
    return (MJD_EPOCH + timedelta(days=mjd)).isoformat()


def has_stats_files(folder):
    try:
        children = os.listdir(folder)
    except OSError:
        return False

    for child in children:
        child_path = os.path.join(folder, child)
        if not os.path.isfile(child_path):
            continue
        lower = child.lower()
        if lower.startswith("loopstats") or lower.startswith("peerstats"):
            return True
    return False


def discover_candidate_dirs():
    env = os.environ
    roots = []
    for key in (
        "PROGRAMDATA",
        "ProgramData",
        "ProgramFiles",
        "ProgramFiles(x86)",
        "LOCALAPPDATA",
        "APPDATA",
        "USERPROFILE",
    ):
        value = env.get(key)
        if value:
            roots.append(value)

    known_relatives = [
        os.path.join("NTP", "logs"),
        os.path.join("NTP", "etc"),
        os.path.join("Meinberg", "NTP", "logs"),
        os.path.join("Meinberg", "NTP", "etc"),
    ]

    candidates = []
    seen = set()

    def add_if_log_dir(path):
        normalized = os.path.normcase(os.path.abspath(path))
        if normalized in seen:
            return
        if os.path.isdir(path) and has_stats_files(path):
            seen.add(normalized)
            candidates.append(path)

    for root in roots:
        for relative in known_relatives:
            add_if_log_dir(os.path.join(root, relative))

    explicit = env.get("NTP_LOG_DIR")
    if explicit:
        add_if_log_dir(explicit)

    return candidates


def get_settings_file_path():
    base = (
        os.environ.get("APPDATA")
        or os.environ.get("LOCALAPPDATA")
        or os.environ.get("USERPROFILE")
        or os.path.expanduser("~")
    )
    if not base:
        return os.path.join(os.getcwd(), "ntp_analyzer_settings.json")
    settings_dir = os.path.join(base, "occultation-ntp-installer")
    return os.path.join(settings_dir, "ntp_analyzer_settings.json")


def load_folder_settings():
    path = get_settings_file_path()
    try:
        handle = open(path, "r", encoding="utf-8")
    except IOError:
        return {}

    try:
        data = json.load(handle)
    except Exception:
        return {}
    finally:
        handle.close()

    if not isinstance(data, dict):
        return {}
    return data


def save_folder_settings(log_folder, export_folder, observer_lat="", observer_lon=""):
    path = get_settings_file_path()
    parent = os.path.dirname(path)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent)

    payload = {
        "log_folder": log_folder,
        "export_folder": export_folder,
        "observer_lat": observer_lat,
        "observer_lon": observer_lon,
    }
    handle = open(path, "w", encoding="utf-8")
    try:
        json.dump(payload, handle, indent=2, sort_keys=True)
    finally:
        handle.close()


def extract_tag(name, prefix):
    if not name.lower().startswith(prefix):
        return ""

    remainder = name[len(prefix):]
    if remainder.startswith("."):
        remainder = remainder[1:]

    if not remainder:
        return ""

    match = re.search(r"(\d{8})", remainder)
    if match:
        return match.group(1)

    return remainder


def read_available_mjds(path):
    values = set()
    try:
        handle = open(path, "r")
    except IOError:
        return values

    try:
        for line in handle:
            text = line.strip()
            if not text or text.startswith("#"):
                continue
            parts = text.split()
            if not parts:
                continue
            try:
                values.add(int(parts[0]))
            except ValueError:
                continue
    finally:
        handle.close()

    return values


def build_day_options(folder):
    loop_by_tag = {}
    peer_by_tag = {}

    for child in os.listdir(folder):
        child_path = os.path.join(folder, child)
        if not os.path.isfile(child_path):
            continue

        lower = child.lower()
        if lower.startswith("loopstats"):
            loop_by_tag[extract_tag(lower, "loopstats")] = child_path
        elif lower.startswith("peerstats"):
            peer_by_tag[extract_tag(lower, "peerstats")] = child_path

    options = []
    common_tags = sorted(set(loop_by_tag.keys()).intersection(set(peer_by_tag.keys())))

    for tag in common_tags:
        loop_path = loop_by_tag[tag]
        peer_path = peer_by_tag[tag]

        label_tag = tag if tag else "(unsuffixed files)"
        if tag.isdigit() and len(tag) == 8:
            label_tag = "%s-%s-%s" % (tag[:4], tag[4:6], tag[6:])

        score = max(os.path.getmtime(loop_path), os.path.getmtime(peer_path))
        options.append(
            DayOption(
                key="tag:%s" % tag,
                label="%s  [%s, %s]" % (label_tag, os.path.basename(loop_path), os.path.basename(peer_path)),
                loop_path=loop_path,
                peer_path=peer_path,
                target_mjd=None,
                recency_score=score,
            )
        )

    if "" in loop_by_tag and "" in peer_by_tag:
        loop_path = loop_by_tag[""]
        peer_path = peer_by_tag[""]
        loop_mjds = read_available_mjds(loop_path)
        peer_mjds = read_available_mjds(peer_path)
        common_mjds = sorted(loop_mjds.intersection(peer_mjds))

        base_score = max(os.path.getmtime(loop_path), os.path.getmtime(peer_path))
        for mjd in common_mjds:
            score = base_score + (mjd / 1000000000.0)
            options.append(
                DayOption(
                    key="mjd:%d" % mjd,
                    label="%s (MJD %d)  [%s, %s]"
                    % (mjd_to_date_string(mjd), mjd, os.path.basename(loop_path), os.path.basename(peer_path)),
                    loop_path=loop_path,
                    peer_path=peer_path,
                    target_mjd=mjd,
                    recency_score=score,
                )
            )

    options.sort(key=lambda item: item.recency_score, reverse=True)
    return options


def parse_loopstats(path, target_mjd):
    rows = []
    handle = open(path, "r")
    try:
        for line in handle:
            text = line.strip()
            if not text or text.startswith("#"):
                continue

            parts = text.split()
            if len(parts) < 5:
                continue

            try:
                mjd = int(parts[0])
                sec_of_day = float(parts[1])
                offset = float(parts[2])
                freq = float(parts[3])
                jitter = float(parts[4])
            except ValueError:
                continue

            if target_mjd is not None and mjd != target_mjd:
                continue

            rows.append(LoopRecord(mjd=mjd, sec_of_day=sec_of_day, offset=offset, freq=freq, jitter=jitter))
    finally:
        handle.close()

    return rows


def parse_peerstats(path, target_mjd):
    rows = []
    handle = open(path, "r")
    try:
        for line in handle:
            text = line.strip()
            if not text or text.startswith("#"):
                continue

            parts = text.split()
            if len(parts) < 8:
                continue

            try:
                mjd = int(parts[0])
                sec_of_day = float(parts[1])
                server_address = parts[2]
                peer_offset = float(parts[4])
                delay = float(parts[5])
                dispersion = float(parts[6])
                jitter = float(parts[7])
            except ValueError:
                continue

            if target_mjd is not None and mjd != target_mjd:
                continue

            rows.append(
                PeerRecord(
                    mjd=mjd,
                    sec_of_day=sec_of_day,
                    status=parts[3],
                    delay=delay,
                    dispersion=dispersion,
                    jitter=jitter,
                    server_address=server_address,
                    offset=peer_offset,
                )
            )
    finally:
        handle.close()

    return rows


def parse_status_word(status_text):
    """Parse a peer status word.

    NTP peerstats status is represented as a hex status word in this project
    (for example: "9614"). Treating plain digits as decimal introduces
    false classifications, so parse as hexadecimal by default.
    """
    token = status_text.strip().lower()
    if not token:
        return None

    try:
        if token.startswith("0x"):
            return int(token, 16)
        return int(token, 16)
    except ValueError:
        return None


def is_selected_status(status_text):
    """Return True only for peers currently selected for synchronization.

    Selection code is bits 8..10 of the peer status word:
    - 6: sys.peer
    - 7: pps.peer
    """
    value = parse_status_word(status_text)
    if value is None:
        return False
    select_code = (value & 0x0700) >> 8
    return select_code in (6, 7)


def is_candidate_or_better(status_text):
    """Return True for peers that passed NTP's sanity checks (select code >= 4).

    This includes candidate (4), backup (5), sys.peer (6) and pps.peer (7).
    Codes 0-3 (reject, falseticker, excess, outlier) are excluded.
    These peers carry valid independent offset measurements in peerstats.
    """
    value = parse_status_word(status_text)
    if value is None:
        return False
    select_code = (value & 0x0700) >> 8
    return select_code >= 4


def get_select_code(status_text):
    value = parse_status_word(status_text)
    if value is None:
        return -1
    return (value & 0x0700) >> 8


def select_peer_subset(peer_rows):
    selected_peers = [row for row in peer_rows if is_selected_status(row.status)]
    if selected_peers:
        note = "Selected peers by status flags: %d of %d rows" % (len(selected_peers), len(peer_rows))
        return selected_peers, note
    note = "No selected-peer status rows found; using all peerstats rows"
    return peer_rows, note


def reduce_to_active_timeline(peer_rows):
    """Collapse rows to one active selected peer per timestamp for charting.

    If multiple selected rows exist at the same rounded second, prefer
    pps.peer (7) over sys.peer (6), then lower delay as a stable tie-breaker.
    """
    by_second = {}
    for row in peer_rows:
        key = (row.mjd, int(round(row.sec_of_day)))
        code = get_select_code(row.status)
        priority = 1 if code == 7 else 0
        delay_value = row.delay
        sort_key = (priority, -delay_value)

        current = by_second.get(key)
        if current is None:
            by_second[key] = (sort_key, row)
        else:
            if sort_key > current[0]:
                by_second[key] = (sort_key, row)

    chosen = [entry[1] for key, entry in sorted(by_second.items(), key=lambda item: item[0])]
    return chosen


def compute_peer_diagnostics(peer_subset):
    code_counts = {}
    for row in peer_subset:
        code = get_select_code(row.status)
        code_counts[code] = code_counts.get(code, 0) + 1

    active_rows = reduce_to_active_timeline(peer_subset)
    transitions = 0
    prev_server = None
    for row in active_rows:
        server = row.server_address if hasattr(row, "server_address") else ""
        if prev_server is not None and server != prev_server:
            transitions += 1
        prev_server = server

    return {
        "select_code_counts": code_counts,
        "active_rows": len(active_rows),
        "active_transitions": transitions,
        "active_unique_servers": len(set([(r.server_address if hasattr(r, "server_address") else "") for r in active_rows])),
    }


def to_utc_datetime(mjd, sec_of_day):
    day = MJD_EPOCH + timedelta(days=mjd)
    day_start = datetime(day.year, day.month, day.day)
    return day_start + timedelta(seconds=float(sec_of_day))


def aggregate_peer_timeseries(peer_rows):
    """Aggregate peer measurements by second and server.

    Returns a list of aggregated records grouped by (mjd, second, server).
    This allows per-server visualization when using aggregated data.
    """
    by_second_server = {}
    for row in peer_rows:
        second_key = int(round(row.sec_of_day))
        server = row.server_address if hasattr(row, 'server_address') else ""
        key = (row.mjd, second_key, server)
        if key not in by_second_server:
            by_second_server[key] = [0.0, 0.0, 0.0, 0]
        by_second_server[key][0] += row.jitter
        by_second_server[key][1] += row.dispersion
        by_second_server[key][2] += row.delay
        by_second_server[key][3] += 1

    points = []
    for key in sorted(by_second_server.keys()):
        stats = by_second_server[key]
        count = stats[3]
        points.append(
            {
                "mjd": key[0],
                "sec_of_day": key[1],
                "server_address": key[2],
                "jitter": stats[0] / float(count),
                "dispersion": stats[1] / float(count),
                "delay": stats[2] / float(count),
            }
        )
    return points


def compute_axis_day_bounds(loop_rows, peer_rows):
    if not loop_rows and not peer_rows:
        return None, None

    all_mjds = [row.mjd for row in loop_rows] + [row.mjd for row in peer_rows]
    min_mjd = min(all_mjds)
    max_mjd = max(all_mjds)

    start_day = MJD_EPOCH + timedelta(days=min_mjd)
    end_day = MJD_EPOCH + timedelta(days=max_mjd + 1)
    start = datetime(start_day.year, start_day.month, start_day.day, 0, 0, 0)
    end = datetime(end_day.year, end_day.month, end_day.day, 0, 0, 0)
    return start, end


def mean(values):
    if not values:
        raise RuntimeError("Cannot compute mean of empty data.")
    return float(sum(values)) / float(len(values))


def stdev(values):
    if len(values) < 2:
        return 0.0
    avg = mean(values)
    variance = sum((value - avg) * (value - avg) for value in values) / float(len(values) - 1)
    return math.sqrt(variance)


def format_ms(seconds):
    return "%.6f ms" % (seconds * 1000.0)


def format_us(seconds):
    return "%.3f us" % (seconds * 1000000.0)


def _choose_y_step_ms(span_ms):
    """Return a nice round Y-axis tick interval (in ms) for the given data span."""
    if span_ms <= 0:
        return 1.0
    # Candidate nice intervals in ms
    nice = [
        0.001, 0.002, 0.005,
        0.01, 0.02, 0.05,
        0.1, 0.2, 0.5,
        1.0, 2.0, 5.0,
        10.0, 20.0, 50.0,
        100.0, 200.0, 500.0, 1000.0,
    ]
    for step in nice:
        if span_ms / step <= 7:
            return step
    return nice[-1]


def _format_y_label_ms(value_ms, step):
    """Format a Y-axis tick value (ms) with precision matched to the tick step."""
    if step >= 100.0:
        return "%d ms" % int(round(value_ms))
    elif step >= 10.0:
        return "%d ms" % int(round(value_ms))
    elif step >= 1.0:
        return "%d ms" % int(round(value_ms))
    elif step >= 0.1:
        return "%.1f ms" % value_ms
    elif step >= 0.01:
        return "%.2f ms" % value_ms
    elif step >= 0.001:
        return "%.3f ms" % value_ms
    else:
        return "%.4f ms" % value_ms


def _parse_pit_time_sec(hms_str):
    """Parse an HH:MM:SS string to seconds past midnight UTC. Raises ValueError on bad input."""
    parts = hms_str.strip().split(":")
    if len(parts) != 3:
        raise ValueError("Time must be in HH:MM:SS format (e.g. 14:32:05).")
    try:
        h, m, s = int(parts[0]), int(parts[1]), float(parts[2])
    except ValueError:
        raise ValueError("Time must be in HH:MM:SS format (e.g. 14:32:05).")
    if not (0 <= h < 24 and 0 <= m < 60 and 0.0 <= s < 60.0):
        raise ValueError("Time values out of range (H:0-23, M:0-59, S:0-59).")
    return h * 3600.0 + m * 60.0 + s


def format_pit_section(pit):
    """Format the point-in-time offset accuracy estimate as a list of report lines."""
    query_dt = (MJD_EPOCH + timedelta(days=pit["query_mjd"])).isoformat()
    query_hms = str(timedelta(seconds=int(pit["query_sec"])))
    if pit["gap_after_s"] is not None:
        gap_after_text = "%.1f s  (offset %s)" % (pit["gap_after_s"], format_ms(pit["offset_after"]))
    else:
        gap_after_text = "N/A (end of data)"
    interpolated = pit["gap_after_s"] is not None
    method_text = "Linear interpolation between surrounding loopstats records." if interpolated else "Last loopstats offset used (no later record available)."
    server_text = pit["active_server_at_T"] if pit["active_server_at_T"] else "unknown"
    lines = [
        "Point-in-Time Offset Accuracy Estimate",
        "=" * 80,
        "Query time: %s %s UTC" % (query_dt, query_hms),
        "Active reference server:            %s" % server_text,
        "",
        "Method: %s" % method_text,
        "  Asymmetry (rectangular 95%) and statistical terms (Gaussian k=2) combined in quadrature.",
        "",
        "Best-estimate offset at T:          %s" % format_ms(pit["best_offset"]),
        "  (loopstats freq at T:              %.6f ppm)" % pit["freq_ppm"],
        "  (last loopstats sync:  -%s  offset %s)" % ("%.1f s" % pit["gap_before_s"], format_ms(pit["offset_before"])),
        "  (next loopstats sync:  +%s)" % gap_after_text,
        "",
        "Uncertainty components:",
        "  u_drift (residual between sync records): %s" % format_ms(pit["u_drift"]),
        "  u_asymmetry (b_asym/sqrt(3)):            %s" % format_ms(pit["u_asymmetry"]),
        "    (mean RTT near T: %s, N=%d peer records)" % (format_ms(pit["mean_delay_near_T"]), pit["n_peer_near_T"]),
        "    b_asym (RTT/2): %s%s" % (
            format_ms(pit["b_asym_raw"]),
            ("  ->  tightened to %s  [%s]" % (format_ms(pit["b_asym"]), pit["server_location_note"]))
            if pit.get("b_asym") is not None and pit["b_asym"] < pit["b_asym_raw"]
            else ("  [%s]" % pit["server_location_note"]) if pit.get("server_location_note") else "",
        ),
        "  u_scatter (stdev of loopstats offsets near T): %s" % format_ms(pit["u_scatter"]),
        "",
        "  u_combined (k=1):  %s" % format_ms(pit["u_combined"]),
        "  U_expanded (~95%%): +/- %s  [sqrt((0.95*RTT/2)^2 + (2*u_stat)^2)]" % format_ms(pit["u_expanded"]),
        "",
        "Corrected UTC time = PC time - (%s)" % format_ms(pit["best_offset"]),
        "Accuracy of corrected time: +/- %s (~95%%)" % format_ms(pit["u_expanded"]),
    ]

    # --- Alternative candidate-peer estimate ---
    lines.append("")
    lines.append("Alternative estimate from best candidate peer (min sqrt(u_asym^2 + u_jitter^2)):")
    n_cand = pit.get("n_candidate_peers_near_T", 0)
    alt_exp = pit.get("alt_u_expanded")
    if n_cand == 0:
        lines.append("  No candidate-or-better peers (select code >= 4) found near T.")
    elif alt_exp is None:
        lines.append("  No alternative candidate peers found near T (sys.peer is the only candidate).")
    else:
        is_better = alt_exp < pit["u_expanded"]
        verdict = ("IMPROVEMENT vs sys.peer estimate" if is_better
                   else "no improvement (sys.peer already has lowest uncertainty)")
        lines += [
            "  Server: %-40s  RTT: %s  (record gap from T: %.1f s)" % (
                pit["alt_server"], format_ms(pit["alt_delay"]), pit["alt_gap_s"]),
            "  Offset at poll near T (peerstats):   %s" % format_ms(pit["alt_best_offset"]),
            "  u_asymmetry (alt RTT/2/sqrt(3)):     %s" % format_ms(pit["alt_u_asymmetry"]),
            "  u_scatter   (alt peer jitter):       %s" % format_ms(pit["alt_u_scatter"]),
            "  U_expanded  (~95%%):  +/- %s  -- %s" % (format_ms(alt_exp), verdict),
        ]
        if is_better:
            lines.append(
                "  *** Lower-uncertainty estimate:  offset = %s  +/- %s (~95%%) ***" % (
                    format_ms(pit["alt_best_offset"]), format_ms(alt_exp))
            )
    return lines


def _haversine_km(lat1, lon1, lat2, lon2):
    """Return the great-circle distance in km between two WGS-84 lat/lon points (degrees)."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2.0) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(dlon / 2.0) ** 2)
    return R * 2.0 * math.asin(math.sqrt(max(0.0, min(1.0, a))))


def load_known_servers(json_path):
    """Load a national_utc_ntp_servers.json file and return a flat list of server-location dicts.

    Each dict has keys:
        hostnames       list[str]   canonical NTP hostnames for this authority
        ips             list[str]   pre-resolved IPs (empty until populated at runtime)
        lat             float       latitude of server site (degrees)
        lon             float       longitude of server site (degrees)
        location_note   str         human-readable description, e.g. "PTB, Braunschweig (curated)"

    Entries without a "server_location" key are silently skipped.
    Entries with no "ntp_servers" hostnames are also skipped.
    """
    try:
        handle = open(json_path, "r", encoding="utf-8")
        try:
            data = json.load(handle)
        finally:
            handle.close()
    except Exception:
        return []

    result = []
    for entry in data.get("entries", []):
        loc = entry.get("server_location")
        if not loc:
            continue
        lat = loc.get("lat")
        lon = loc.get("lon")
        if lat is None or lon is None:
            continue
        hostnames = [h.lower() for h in entry.get("ntp_servers", []) if h]
        if not hostnames:
            continue
        authority = entry.get("authority", "")
        city = loc.get("city", "")
        note = "%s%s (curated)" % (
            ("%s, " % authority) if authority else "",
            city if city else "known server",
        )
        result.append({
            "hostnames": hostnames,
            "ips": [],
            "lat": float(lat),
            "lon": float(lon),
            "location_note": note,
        })
    return result


# ---------------------------------------------------------------------------
# Persistent IP-location cache  (resources/ip_location_cache.json)
# ---------------------------------------------------------------------------
# Entries survive across runs and are refreshed after _IP_CACHE_MAX_DAYS days.
# Structure:  { "ip_str": { lat, lon, location_note, source, cached_at } }
# Only the server coordinates are stored; geo_km is observer-dependent and
# recalculated each time from the cached lat/lon.
# ---------------------------------------------------------------------------
_ip_location_cache = {}
_ip_cache_file_path = None
_IP_CACHE_MAX_DAYS = 90


def _load_ip_location_cache(path):
    """Read ip_location_cache.json into memory.  Silent on any error."""
    global _ip_location_cache, _ip_cache_file_path
    _ip_cache_file_path = path
    try:
        handle = open(path, "r", encoding="utf-8")
        try:
            _ip_location_cache = json.load(handle)
        finally:
            handle.close()
    except Exception:
        _ip_location_cache = {}


def _save_ip_location_cache():
    """Write the in-memory cache to disk.  Silent on any error."""
    if not _ip_cache_file_path:
        return
    try:
        handle = open(_ip_cache_file_path, "w", encoding="utf-8")
        try:
            json.dump(_ip_location_cache, handle, indent=2)
        finally:
            handle.close()
    except Exception:
        pass


def _cache_ip_location(ip, lat, lon, location_note, source):
    """Store a resolved IP location in memory and flush to disk."""
    _ip_location_cache[ip] = {
        "lat": lat,
        "lon": lon,
        "location_note": location_note,
        "source": source,
        "cached_at": datetime.utcnow().strftime("%Y-%m-%d"),
    }
    _save_ip_location_cache()


# In-process GeoIP cache so a single analysis run doesn't re-query the same IP.
_geoip_cache = {}


def geolocate_ip(ip):
    """Look up the geographic coordinates of an IP address using ip-api.com.

    Results are cached in-process.  Returns a dict with keys lat, lon, city,
    country, or None on failure (network error, rate-limit, private IP, etc.).
    Timeout is 5 seconds; failure is always silent.
    """
    if ip in _geoip_cache:
        return _geoip_cache[ip]
    result = None
    try:
        url = "http://ip-api.com/json/%s?fields=status,lat,lon,city,country" % ip
        response = urllib.request.urlopen(url, timeout=5)
        data = json.loads(response.read().decode("utf-8"))
        if data.get("status") == "success":
            result = {
                "lat": float(data["lat"]),
                "lon": float(data["lon"]),
                "city": data.get("city", ""),
                "country": data.get("country", ""),
            }
    except Exception:
        pass
    _geoip_cache[ip] = result
    return result


def resolve_server_location(server_ip, known_servers, observer_lat, observer_lon):
    """Attempt to determine d_min (seconds) for an NTP server based on its IP address.

    Lookup order:
      1. Private / loopback / link-local IP  -> d_min = 0 (local network)
      2. Persistent IP location cache (valid for _IP_CACHE_MAX_DAYS days)
      3. Reverse-DNS -> match known_servers by hostname/domain
      4. GeoIP fallback via ip-api.com

    Parameters
    ----------
    server_ip : str
        The IP address (or hostname) from peerstats column 3.
    known_servers : list of dict or None
        Output of load_known_servers().  None disables curated lookup.
    observer_lat : float or None
        Observer latitude in degrees.
    observer_lon : float or None
        Observer longitude in degrees.

    Returns
    -------
    dict with keys:
        d_min_s        float or None   minimum one-way propagation delay (seconds)
        location_note  str             human-readable description of what matched
        geo_km         float or None   geographic distance used (km)
    """
    _no_match = {"d_min_s": None, "location_note": "server location unknown", "geo_km": None}

    if not server_ip:
        return _no_match

    # Step 1: private / loopback / link-local -> local, no propagation uncertainty worth modelling.
    try:
        addr = ipaddress.ip_address(server_ip)
        if addr.is_private or addr.is_loopback or addr.is_link_local:
            return {"d_min_s": 0.0, "location_note": "local network (private IP)", "geo_km": 0.0}
    except ValueError:
        # Not a valid IP literal -- treat as a hostname; fall through.
        pass

    # Step 2: persistent IP location cache (valid for _IP_CACHE_MAX_DAYS days).
    cached = _ip_location_cache.get(server_ip)
    if cached:
        try:
            cached_date = datetime.strptime(cached["cached_at"], "%Y-%m-%d")
            age_days = (datetime.utcnow() - cached_date).days
        except Exception:
            age_days = _IP_CACHE_MAX_DAYS + 1  # treat corrupt date as expired
        if age_days <= _IP_CACHE_MAX_DAYS:
            if observer_lat is not None and observer_lon is not None:
                geo_km = _haversine_km(observer_lat, observer_lon, cached["lat"], cached["lon"])
                d_min_s = geo_km / _FIBRE_SPEED_KMS
                note = "%s, %.0f km" % (cached["location_note"], geo_km)
            else:
                geo_km = None
                d_min_s = None
                note = cached["location_note"]
            return {"d_min_s": d_min_s, "location_note": note, "geo_km": geo_km}

    if observer_lat is None or observer_lon is None:
        return _no_match

    # Step 3: reverse DNS then match against known_servers by hostname/domain.
    rdns_hostname = None
    try:
        rdns_hostname = socket.gethostbyaddr(server_ip)[0].lower()
    except Exception:
        pass

    def _registered_domain(hostname):
        """Return the registered domain (e.g. 'nist.gov') from a hostname string."""
        parts = hostname.rstrip(".").split(".")
        return ".".join(parts[-2:]) if len(parts) >= 2 else hostname

    rdns_domain = _registered_domain(rdns_hostname) if rdns_hostname else None

    # Registered-domain comparison handles sibling hostnames returned by rDNS
    # (e.g. time-a-g.nist.gov reverse-resolves for an entry listing time.nist.gov).
    for entry in (known_servers or []):
        matched = False
        if rdns_hostname:
            for h in entry["hostnames"]:
                if rdns_hostname == h or rdns_hostname.endswith("." + h) or h.endswith("." + rdns_hostname):
                    matched = True
                    break
                if rdns_domain and _registered_domain(h) == rdns_domain:
                    matched = True
                    break
        if matched:
            geo_km = _haversine_km(observer_lat, observer_lon, entry["lat"], entry["lon"])
            d_min_s = geo_km / _FIBRE_SPEED_KMS
            note = entry["location_note"]
            _cache_ip_location(server_ip, entry["lat"], entry["lon"], note, "curated")
            return {
                "d_min_s": d_min_s,
                "location_note": "%s, %.0f km" % (note, geo_km),
                "geo_km": geo_km,
            }

    # Step 4: GeoIP fallback via ip-api.com (in-process cached, silent on failure).
    geo = geolocate_ip(server_ip)
    if geo is not None:
        geo_km = _haversine_km(observer_lat, observer_lon, geo["lat"], geo["lon"])
        d_min_s = geo_km / _FIBRE_SPEED_KMS
        parts = [p for p in [geo.get("city", ""), geo.get("country", "")] if p]
        note = "%s (GeoIP)" % (", ".join(parts) if parts else server_ip)
        _cache_ip_location(server_ip, geo["lat"], geo["lon"], note, "geoip")
        return {"d_min_s": d_min_s, "location_note": "%s, %.0f km" % (note, geo_km), "geo_km": geo_km}

    return _no_match


def estimate_offset_at_time(query_mjd, query_sec, loop_rows, peer_rows, window_seconds=3600.0,
                            known_servers=None, observer_lat=None, observer_lon=None):
    """Estimate the NTP offset and its uncertainty at a specific point in time.

    Parameters
    ----------
    query_mjd : int
        Modified Julian Day of the query time.
    query_sec : float
        Seconds past midnight (UTC) of the query time.
    loop_rows : list of LoopRecord
        All loopstats records available (need not be filtered to one day).
    peer_rows : list of PeerRecord
        All peerstats records available.
    window_seconds : float
        Half-width of the time window used to gather nearby peer samples for
        the network uncertainty estimate (default +-1 hour).
    known_servers : list of dict or None
        Output of load_known_servers().  When provided together with
        observer_lat/lon, enables geographic tightening of b_asym via
        resolve_server_location().  Defaults to None (conservative RTT/2 used).
    observer_lat : float or None
        Observer latitude in decimal degrees.  Required for geographic tightening.
    observer_lon : float or None
        Observer longitude in decimal degrees.  Required for geographic tightening.

    Returns
    -------
    dict with keys:
        query_mjd, query_sec          -- echo of inputs
        best_offset                    -- estimated offset at T (seconds)
        u_drift                        -- uncertainty from clock walk since last sync (s)
        u_asymmetry                    -- network path asymmetry uncertainty (s)
        u_scatter                      -- NTP measurement scatter near T (s)
        u_combined                     -- combined standard uncertainty k=1 (s)
        u_expanded                     -- expanded uncertainty ~95% (s)
        gap_before_s                   -- seconds between T and the last loopstats record
        gap_after_s                    -- seconds between T and the next loopstats record (or None)
        freq_ppm                       -- freq correction in use at T (ppm)
        mean_delay_near_T              -- mean RTT of nearby peer records (s)
        n_peer_near_T                  -- count of peer records used for network estimate
        active_server_at_T             -- server address active at T (str or None)
        b_asym_raw                     -- RTT/2 before any geographic tightening (s)
        b_asym                         -- asymmetry bound used in expansion (s)
        server_location_note           -- description of how server location was resolved
        note                           -- human-readable summary string
    """
    # Convert every loopstats row to a single comparable float: seconds since MJD epoch
    def loop_abs_sec(row):
        return row.mjd * 86400.0 + row.sec_of_day

    def peer_abs_sec(row):
        return row.mjd * 86400.0 + row.sec_of_day

    query_abs = query_mjd * 86400.0 + query_sec

    sorted_loop = sorted(loop_rows, key=loop_abs_sec)
    if not sorted_loop:
        raise RuntimeError("No loopstats rows available for point-in-time estimate.")

    # Find the last loopstats record at or before T ("before"), and the first after T ("after").
    before = None
    after = None
    for row in sorted_loop:
        t = loop_abs_sec(row)
        if t <= query_abs:
            before = row
        elif after is None:
            after = row

    if before is None:
        # T is before all data -- use the earliest record, extrapolating backward
        before = sorted_loop[0]

    # Time gaps
    gap_before_s = query_abs - loop_abs_sec(before)
    gap_after_s = (loop_abs_sec(after) - query_abs) if after is not None else None

    freq_ppm = before.freq
    offset_before = before.offset
    offset_after = after.offset if after is not None else None

    # Best-estimate offset at T:
    #   loopstats freq is the correction NTP is *already applying* to the kernel clock,
    #   not an uncompensated drift.  Projecting it forward double-counts the correction.
    #   When the record on both sides of T is available, linear interpolation between
    #   the two measured offsets is the most accurate estimate.  When only the record
    #   before T is available, use that offset directly (best known value).
    if after is not None:
        total_gap = gap_before_s + gap_after_s
        fraction = gap_before_s / total_gap if total_gap > 0 else 0.0
        best_offset = before.offset + fraction * (after.offset - before.offset)
    else:
        best_offset = before.offset

    # Uncertainty from residual clock drift between the last sync and T.
    #   When interpolating: the jitter at the surrounding records bounds how much the
    #   true offset deviates from a straight line between them.
    #   When extrapolating (no after record): the freq value tells us the rate at which
    #   ntpd was steering the clock; the residual uncertainty grows with the gap.
    if after is not None:
        u_drift = max(before.jitter, after.jitter)
    else:
        freq_drift_bound = abs(freq_ppm * 1e-6 * gap_before_s)
        u_drift = max(freq_drift_bound / SQRT3, before.jitter)

    # Gather peer records within +-window_seconds of T for the network estimate.
    selected_peer_rows, _note = select_peer_subset(peer_rows)
    near_peers = [
        row for row in selected_peer_rows
        if abs(peer_abs_sec(row) - query_abs) <= window_seconds
    ]
    # Fall back to the full selected subset if the window is empty.
    if not near_peers:
        near_peers = selected_peer_rows

    # Determine which server was active at T using the same reduce_to_active_timeline logic.
    active_server_at_T = None
    active_timeline = reduce_to_active_timeline(selected_peer_rows)
    last_active = None
    for row in active_timeline:
        if peer_abs_sec(row) <= query_abs:
            last_active = row
        else:
            break
    if last_active is not None:
        active_server_at_T = last_active.server_address if hasattr(last_active, "server_address") else None

    # Network path asymmetry uncertainty from nearby peers.
    # Use only the active server's records near T if available;
    # fall back to all selected near-peers.
    active_near_peers = [
        row for row in near_peers
        if (row.server_address if hasattr(row, "server_address") else None) == active_server_at_T
    ] if active_server_at_T else []
    network_peers = active_near_peers if active_near_peers else near_peers

    delays_near = [row.delay for row in network_peers]
    mean_delay_near = mean(delays_near) if delays_near else 0.0
    # Hard rectangular bound on one-way path asymmetry: RTT/2 in either direction.
    # Applying k=2 to the rectangular standard uncertainty (RTT/2/sqrt(3)) alone produces
    # an expanded interval ~15% wider than the 100% physical ceiling (RTT/2).  Instead,
    # the rectangular 95% coverage (0.95 * b_asym) and the Gaussian statistical components
    # (drift + scatter, k=2) are combined in quadrature so U_expanded stays within RTT/2.
    b_asym_raw = mean_delay_near / 2.0
    b_asym = b_asym_raw

    # Geographic tightening: if the server location is known, the minimum one-way
    # propagation delay (d_min = geo_distance / v_fibre) is symmetric and cannot
    # be asymmetric.  The true asymmetry bound shrinks to max(RTT/2 - d_min, 0).
    server_loc = resolve_server_location(
        active_server_at_T or "",
        known_servers,
        observer_lat,
        observer_lon,
    )
    d_min_s = server_loc["d_min_s"]
    if d_min_s is not None:
        b_asym = max(b_asym_raw - d_min_s, 0.0)
    server_location_note = server_loc["location_note"]

    u_asymmetry = b_asym / SQRT3               # rectangular standard uncertainty (for u_combined)

    # Scatter: standard deviation of offsets among nearby loopstats records.
    # Use a matching window around T.
    near_loop = [
        row for row in sorted_loop
        if abs(loop_abs_sec(row) - query_abs) <= window_seconds
    ]
    near_offsets = [row.offset for row in near_loop] if near_loop else [before.offset]
    u_scatter = stdev(near_offsets) if len(near_offsets) >= 2 else 0.0

    u_combined = math.sqrt(u_drift * u_drift + u_asymmetry * u_asymmetry + u_scatter * u_scatter)
    # Expanded uncertainty: rectangular asymmetry at 95% of its hard bound, Gaussian
    # statistical terms at k=2, combined in quadrature.
    u_stat = math.sqrt(u_drift * u_drift + u_scatter * u_scatter)
    u_expanded = math.sqrt((0.95 * b_asym) ** 2 + (2.0 * u_stat) ** 2)

    # --- Alternative low-uncertainty estimate from candidate peers ---
    # The loopstats offset is disciplined by the sys.peer only, so u_asymmetry above
    # reflects that peer's RTT.  Other candidate-or-better peers (select codes 4-7)
    # carry their own independently-measured UTC offsets in peerstats column [4].
    # A peer with a smaller combined sqrt(u_asym^2 + u_jitter^2) may give a
    # lower-uncertainty independent estimate.  We use its offset AND delay together
    # (never mixing another peer's delay with the loopstats offset).
    candidate_near = [
        row for row in peer_rows
        if abs(peer_abs_sec(row) - query_abs) <= window_seconds
        and is_candidate_or_better(row.status)
    ]
    alt_candidate_near = [
        row for row in candidate_near
        if (row.server_address if hasattr(row, "server_address") else "") != active_server_at_T
    ] if active_server_at_T else candidate_near

    alt_best_offset = None
    alt_u_asymmetry = None
    alt_u_scatter = None
    alt_u_combined = None
    alt_u_expanded = None
    alt_server = None
    alt_delay = None
    alt_gap_s = None
    n_candidate_peers_near_T = len(set(
        row.server_address for row in candidate_near
        if hasattr(row, "server_address")
    ))

    if alt_candidate_near:
        # For each distinct server keep only the record nearest in time to T.
        by_server = {}
        for row in alt_candidate_near:
            addr = row.server_address if hasattr(row, "server_address") else ""
            gap = abs(peer_abs_sec(row) - query_abs)
            current = by_server.get(addr)
            if current is None or gap < current[0]:
                by_server[addr] = (gap, row)
        # Score each server by combined uncertainty; pick the minimum.
        best_score = None
        for addr, (gap, row) in by_server.items():
            b_a = row.delay / 2.0
            u_a = b_a / SQRT3
            u_s = row.jitter
            score = math.sqrt(u_a * u_a + u_s * u_s)
            if best_score is None or score < best_score:
                best_score = score
                alt_server = addr
                alt_delay = row.delay
                alt_gap_s = gap
                alt_u_asymmetry = u_a
                alt_u_scatter = u_s
                alt_best_offset = row.offset
                alt_u_combined = score
                # Same expansion as sys.peer: 95% rectangular asymmetry + k=2 Gaussian jitter.
                alt_u_expanded = math.sqrt((0.95 * b_a) ** 2 + (2.0 * u_s) ** 2)

    note_parts = [
        "gap_before=%.1fs" % gap_before_s,
        "freq=%.3fppm" % freq_ppm,
        "u_drift=%s" % format_ms(u_drift),
        "u_asymmetry=%s" % format_ms(u_asymmetry),
        "u_scatter=%s" % format_ms(u_scatter),
        "U_expanded(~95%%)=+/-%s" % format_ms(u_expanded),
    ]
    if active_server_at_T:
        note_parts.insert(0, "server=%s" % active_server_at_T)
    if d_min_s is not None and d_min_s > 0.0:
        note_parts.append("b_asym_tightened=%s->%s" % (format_ms(b_asym_raw), format_ms(b_asym)))

    return {
        "query_mjd": query_mjd,
        "query_sec": query_sec,
        "best_offset": best_offset,
        "offset_before": offset_before,
        "offset_after": offset_after,
        "u_drift": u_drift,
        "u_asymmetry": u_asymmetry,
        "u_scatter": u_scatter,
        "u_combined": u_combined,
        "u_expanded": u_expanded,
        "gap_before_s": gap_before_s,
        "gap_after_s": gap_after_s,
        "freq_ppm": freq_ppm,
        "mean_delay_near_T": mean_delay_near,
        "n_peer_near_T": len(network_peers),
        "active_server_at_T": active_server_at_T,
        "b_asym_raw": b_asym_raw,
        "b_asym": b_asym,
        "server_location_note": server_location_note,
        "n_candidate_peers_near_T": n_candidate_peers_near_T,
        "alt_best_offset": alt_best_offset,
        "alt_u_asymmetry": alt_u_asymmetry,
        "alt_u_scatter": alt_u_scatter,
        "alt_u_combined": alt_u_combined,
        "alt_u_expanded": alt_u_expanded,
        "alt_server": alt_server,
        "alt_delay": alt_delay,
        "alt_gap_s": alt_gap_s,
        "note": "; ".join(note_parts),
    }


def analyze(option, loop_rows, peer_rows, known_servers=None, observer_lat=None, observer_lon=None):
    if not loop_rows:
        raise RuntimeError("No usable loopstats rows were found for the selected day.")
    if not peer_rows:
        raise RuntimeError("No usable peerstats rows were found for the selected day.")

    peer_subset, peer_selection_note = select_peer_subset(peer_rows)
    diagnostics = compute_peer_diagnostics(peer_subset)

    offsets = [row.offset for row in loop_rows]
    loop_jitter = [row.jitter for row in loop_rows]
    delays = [row.delay for row in peer_subset]
    dispersions = [row.dispersion for row in peer_subset]
    peer_jitter = [row.jitter for row in peer_subset]

    mean_offset_signed = mean(offsets)
    mean_offset_abs = mean([abs(value) for value in offsets])
    mean_delay = mean(delays)
    mean_half_delay = mean_delay / 2.0
    mean_loop_jitter = mean(loop_jitter)
    mean_dispersion = mean(dispersions)
    mean_peer_jitter = mean(peer_jitter)

    a_uncertainty = math.sqrt(mean_offset_signed * mean_offset_signed + mean_delay * mean_delay)

    b_u_offset = mean_offset_abs / SQRT3
    b_u_delay = mean_half_delay / SQRT3
    b_u_server = 3e-6
    b_u_combined = math.sqrt(b_u_offset * b_u_offset + b_u_delay * b_u_delay + b_u_server * b_u_server)
    b_u_expanded = 2.0 * b_u_combined

    c_bias = mean_offset_signed
    c_u_wander = stdev(offsets)
    c_u_asymmetry = mean_half_delay / SQRT3
    c_u_delay_variation = stdev(delays) / 2.0
    c_u_server = 3e-6 / SQRT3
    c_u_combined = math.sqrt(
        c_u_wander * c_u_wander
        + c_u_asymmetry * c_u_asymmetry
        + c_u_delay_variation * c_u_delay_variation
        + c_u_server * c_u_server
    )
    c_u_expanded = 2.0 * c_u_combined

    d_u_jitter = mean_loop_jitter
    d_u_dispersion = mean_dispersion
    d_u_asymmetry = mean_half_delay / SQRT3
    d_u_server = 3e-6 / SQRT3
    d_u_combined = math.sqrt(
        d_u_jitter * d_u_jitter
        + d_u_dispersion * d_u_dispersion
        + d_u_asymmetry * d_u_asymmetry
        + d_u_server * d_u_server
    )
    d_u_expanded = 2.0 * d_u_combined

    # Offset accuracy to UTC (3 practical variants)
    # Variant E: Minimal (network asymmetry + NTP measurement variation)
    e_u_asymmetry = mean_half_delay / SQRT3
    e_u_measurement = stdev(offsets)
    e_u_combined = math.sqrt(e_u_asymmetry * e_u_asymmetry + e_u_measurement * e_u_measurement)
    e_u_expanded = 2.0 * e_u_combined

    # Variant F: Using NTP's dispersion directly
    f_u_offset = mean_dispersion
    f_u_expanded = 2.0 * f_u_offset

    # Variant G: Conservative (worst-case delay)
    max_delay = max(delays) if delays else mean_delay
    g_u_asymmetry = (max_delay / 2.0) / SQRT3
    g_u_measurement = stdev(offsets)
    g_u_combined = math.sqrt(g_u_asymmetry * g_u_asymmetry + g_u_measurement * g_u_measurement)
    g_u_expanded = 2.0 * g_u_combined

    # Point-in-time estimate: use the last loopstats record as the representative query time.
    # Callers can also call estimate_offset_at_time() directly with any (mjd, sec) pair.
    sorted_loop_for_pit = sorted(loop_rows, key=lambda r: (r.mjd, r.sec_of_day))
    last_loop = sorted_loop_for_pit[-1]
    pit_result = estimate_offset_at_time(last_loop.mjd, last_loop.sec_of_day, loop_rows, peer_rows,
                                         known_servers=known_servers,
                                         observer_lat=observer_lat, observer_lon=observer_lon)

    mjds = sorted(set([row.mjd for row in loop_rows] + [row.mjd for row in peer_rows]))

    metrics = {
        "mean_offset_signed": mean_offset_signed,
        "mean_delay": mean_delay,
        "a_uncertainty": a_uncertainty,
        "b_u_offset": b_u_offset,
        "b_u_delay": b_u_delay,
        "b_u_server": b_u_server,
        "b_u_combined": b_u_combined,
        "b_u_expanded": b_u_expanded,
        "c_bias": c_bias,
        "c_u_wander": c_u_wander,
        "c_u_asymmetry": c_u_asymmetry,
        "c_u_delay_variation": c_u_delay_variation,
        "c_u_server": c_u_server,
        "c_u_combined": c_u_combined,
        "c_u_expanded": c_u_expanded,
        "d_u_jitter": d_u_jitter,
        "d_u_dispersion": d_u_dispersion,
        "d_u_peer_jitter": mean_peer_jitter,
        "d_u_asymmetry": d_u_asymmetry,
        "d_u_server": d_u_server,
        "d_u_combined": d_u_combined,
        "d_u_expanded": d_u_expanded,
        "e_u_asymmetry": e_u_asymmetry,
        "e_u_measurement": e_u_measurement,
        "e_u_combined": e_u_combined,
        "e_u_expanded": e_u_expanded,
        "f_u_offset": f_u_offset,
        "f_u_expanded": f_u_expanded,
        "g_u_asymmetry": g_u_asymmetry,
        "g_u_measurement": g_u_measurement,
        "g_u_combined": g_u_combined,
        "g_u_expanded": g_u_expanded,
    }

    return AnalysisResult(
        option=option,
        mjds=mjds,
        loop_rows_used=len(loop_rows),
        peer_rows_total=len(peer_rows),
        peer_rows_used=len(peer_subset),
        peer_selection_note=peer_selection_note,
        metrics=metrics,
        diagnostics=diagnostics,
        pit_result=pit_result,
    )


def generate_report(result):
    date_text = ", ".join(["%s (MJD %d)" % (mjd_to_date_string(mjd), mjd) for mjd in result.mjds])
    option = result.option
    m = result.metrics
    d = result.diagnostics

    code_counts = d.get("select_code_counts", {})
    code_6 = code_counts.get(6, 0)
    code_7 = code_counts.get(7, 0)
    code_other = 0
    for code_value, count in code_counts.items():
        if code_value not in (6, 7):
            code_other += count

    lines = [
        "NTP Timing Accuracy Report",
        "=" * 80,
        "Dataset: %s" % option.label,
        "Loopstats file: %s" % option.loop_path,
        "Peerstats file: %s" % option.peer_path,
        "Day(s) present in selected data: %s" % date_text,
        "Loopstats rows used: %d" % result.loop_rows_used,
        "Peerstats rows used: %d (%s)" % (result.peer_rows_used, result.peer_selection_note),
        "",
        "Selected Peer Diagnostics",
        "-" * 80,
        "Select code 6 (sys.peer) rows: %d" % code_6,
        "Select code 7 (pps.peer) rows: %d" % code_7,
        "Other select codes in subset: %d" % code_other,
        "Active timeline rows (1 peer per second): %d" % d.get("active_rows", 0),
        "Active source transitions: %d" % d.get("active_transitions", 0),
        "Unique active servers: %d" % d.get("active_unique_servers", 0),
        "",
        "Interpretation A (literal reading)",
        "-" * 80,
        "Mean signed loop offset: %s" % format_ms(m["mean_offset_signed"]),
        "Mean peer delay (RTT): %s" % format_ms(m["mean_delay"]),
        "Quadrature sum: %s" % format_ms(m["a_uncertainty"]),
        "",
        "Interpretation B (metrological)",
        "-" * 80,
        "u_offset = mean(abs(offset))/sqrt(3): %s" % format_ms(m["b_u_offset"]),
        "u_delay = (mean(delay)/2)/sqrt(3): %s" % format_ms(m["b_u_delay"]),
        "u_server (fixed): %s" % format_us(m["b_u_server"]),
        "u_combined (k=1): %s" % format_ms(m["b_u_combined"]),
        "U_expanded (k=2): +/- %s" % format_ms(m["b_u_expanded"]),
        "",
        "Interpretation C (statistical)",
        "-" * 80,
        "Systematic bias (mean signed offset): %s" % format_ms(m["c_bias"]),
        "u_wander = stdev(offset): %s" % format_ms(m["c_u_wander"]),
        "u_asymmetry = (mean(delay)/2)/sqrt(3): %s" % format_ms(m["c_u_asymmetry"]),
        "u_delay_variation = stdev(delay)/2: %s" % format_ms(m["c_u_delay_variation"]),
        "u_server (rectangular): %s" % format_us(m["c_u_server"]),
        "u_combined (k=1): %s" % format_ms(m["c_u_combined"]),
        "U_expanded (k=2): +/- %s" % format_ms(m["c_u_expanded"]),
        "",
        "Interpretation D (NTP native statistics)",
        "-" * 80,
        "u_jitter (loopstats mean jitter): %s" % format_ms(m["d_u_jitter"]),
        "u_dispersion (peerstats mean dispersion): %s" % format_ms(m["d_u_dispersion"]),
        "u_peer_jitter (informational): %s" % format_ms(m["d_u_peer_jitter"]),
        "u_asymmetry = (mean(delay)/2)/sqrt(3): %s" % format_ms(m["d_u_asymmetry"]),
        "u_server (rectangular): %s" % format_us(m["d_u_server"]),
        "u_combined (k=1): %s" % format_ms(m["d_u_combined"]),
        "U_expanded (k=2): +/- %s" % format_ms(m["d_u_expanded"]),
        "",
        "Offset Accuracy to UTC (practical variants)",
        "=" * 80,
        "",
        "Variant E (minimal: network + measurement)",
        "-" * 80,
        "u_asymmetry = (mean(delay)/2)/sqrt(3): %s" % format_ms(m["e_u_asymmetry"]),
        "u_measurement = stdev(offset): %s" % format_ms(m["e_u_measurement"]),
        "u_combined (k=1): %s" % format_ms(m["e_u_combined"]),
        "U_expanded (k=2): +/- %s" % format_ms(m["e_u_expanded"]),
        "",
        "Variant F (using NTP's dispersion directly)",
        "-" * 80,
        "u_offset = mean(dispersion): %s" % format_ms(m["f_u_offset"]),
        "U_expanded (k=2): +/- %s" % format_ms(m["f_u_expanded"]),
        "",
        "Variant G (conservative: worst-case delay)",
        "-" * 80,
        "u_asymmetry = (max(delay)/2)/sqrt(3): %s" % format_ms(m["g_u_asymmetry"]),
        "u_measurement = stdev(offset): %s" % format_ms(m["g_u_measurement"]),
        "u_combined (k=1): %s" % format_ms(m["g_u_combined"]),
        "U_expanded (k=2): +/- %s" % format_ms(m["g_u_expanded"]),
    ]

    return "\r\n".join(lines)


def sanitize_filename_part(value):
    sanitized = re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("_")
    return sanitized or "dataset"


def resolve_export_paths(export_dir, result):
    if not os.path.isdir(export_dir):
        os.makedirs(export_dir)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if result.mjds:
        day_part = sanitize_filename_part(mjd_to_date_string(max(result.mjds)))
    else:
        day_part = "unknown_day"

    base = os.path.join(export_dir, "ntp_accuracy_%s_%s" % (day_part, stamp))
    return base + ".json", base + ".csv"


def export_json(path, result):
    generated_at = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    payload = {
        "generated_at": generated_at,
        "dataset_label": result.option.label,
        "loopstats_file": result.option.loop_path,
        "peerstats_file": result.option.peer_path,
        "mjd_days": result.mjds,
        "iso_days": [mjd_to_date_string(mjd) for mjd in result.mjds],
        "loop_rows_used": result.loop_rows_used,
        "peer_rows_total": result.peer_rows_total,
        "peer_rows_used": result.peer_rows_used,
        "peer_selection_note": result.peer_selection_note,
        "metrics_seconds": result.metrics,
        "diagnostics": result.diagnostics,
    }

    handle = open(path, "w", encoding="utf-8")
    try:
        json.dump(payload, handle, indent=2, sort_keys=True)
    finally:
        handle.close()


def export_csv(path, result):
    generated_at = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    columns = [
        "generated_at",
        "dataset_label",
        "loopstats_file",
        "peerstats_file",
        "mjd_days",
        "iso_days",
        "loop_rows_used",
        "peer_rows_total",
        "peer_rows_used",
        "peer_selection_note",
        "diag_select_code_6",
        "diag_select_code_7",
        "diag_select_code_other",
        "diag_active_rows",
        "diag_active_transitions",
        "diag_active_unique_servers",
    ] + sorted(result.metrics.keys())

    row = {
        "generated_at": generated_at,
        "dataset_label": result.option.label,
        "loopstats_file": result.option.loop_path,
        "peerstats_file": result.option.peer_path,
        "mjd_days": ";".join([str(mjd) for mjd in result.mjds]),
        "iso_days": ";".join([mjd_to_date_string(mjd) for mjd in result.mjds]),
        "loop_rows_used": str(result.loop_rows_used),
        "peer_rows_total": str(result.peer_rows_total),
        "peer_rows_used": str(result.peer_rows_used),
        "peer_selection_note": result.peer_selection_note,
    }

    diag = result.diagnostics or {}
    code_counts = diag.get("select_code_counts", {})
    code_other = 0
    for code_value, count in code_counts.items():
        if code_value not in (6, 7):
            code_other += count

    row["diag_select_code_6"] = str(code_counts.get(6, 0))
    row["diag_select_code_7"] = str(code_counts.get(7, 0))
    row["diag_select_code_other"] = str(code_other)
    row["diag_active_rows"] = str(diag.get("active_rows", 0))
    row["diag_active_transitions"] = str(diag.get("active_transitions", 0))
    row["diag_active_unique_servers"] = str(diag.get("active_unique_servers", 0))

    for key, value in result.metrics.items():
        row[key] = "%.12f" % value

    handle = open(path, "w", newline="", encoding="utf-8")
    try:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerow(row)
    finally:
        handle.close()
