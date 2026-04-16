"""
IronPython 3.4 smoke test for vizier_export.py
Run with: ipy _test_vizier_export_ipy.py
Then paste the console output back to GitHub Copilot.
"""

import sys
sys.path.insert(0, r'c:\Users\AstroPC\Git\occultation-tools\occultation-manager\python')

from vizier_export import (
    parse_star_id,
    decimal_degrees_to_dms,
    compute_median_step,
    insert_dropped_readings,
    compute_trim_window,
    build_date_line,
    build_star_line,
    build_location_line,
    build_object_line,
    build_values_line,
    generate_dat_filename,
    to_seconds,
)
from vizier_export import _is_neg_zero

from datetime import datetime, timedelta

passed = 0
failed = 0

def chk(name, got, expected):
    global passed, failed
    if got == expected:
        print('PASS  ' + name)
        passed += 1
    else:
        print('FAIL  %s\n      got:      %r\n      expected:  %r' % (name, got, expected))
        failed += 1

def chk_true(name, expr):
    global passed, failed
    if expr:
        print('PASS  ' + name)
        passed += 1
    else:
        print('FAIL  %s  (expression was False)' % name)
        failed += 1

def chk_false(name, expr):
    global passed, failed
    if not expr:
        print('PASS  ' + name)
        passed += 1
    else:
        print('FAIL  %s  (expression was True)' % name)
        failed += 1

print('=== parse_star_id ===')
chk('ucac4', parse_star_id('UCAC4 361-199861')['ucac4'], '361-199861')
chk('ucac4_other_fields_empty', parse_star_id('UCAC4 361-199861')['tycho2'], '')
chk('tycho2', parse_star_id('TYC 1234-5678-1')['tycho2'], '1234-5678-1')
chk('hipparcos', parse_star_id('HIP 12345')['hipparcos'], '12345')
chk('gaia_ucac4_empty', parse_star_id('Gaia DR3 999912345')['ucac4'], '')
chk('gaia_tycho2_empty', parse_star_id('Gaia DR3 999912345')['tycho2'], '')
chk('gaia_hip_empty', parse_star_id('Gaia DR3 999912345')['hipparcos'], '')
chk('empty_string', parse_star_id('')['ucac4'], '')

print('')
print('=== decimal_degrees_to_dms ===')
d, m, s = decimal_degrees_to_dms(-37.8136)
chk('lat_neg_deg', d, '-37')
chk('lat_neg_min', m, '48')
print('      sec (informational): ' + s)
d2, m2, s2 = decimal_degrees_to_dms(144.9167)
chk('lon_pos_deg', d2, '+144')
chk('lon_pos_min', m2, '55')
print('      sec (informational): ' + s2)
d3, m3, s3 = decimal_degrees_to_dms(0.0)
chk('zero_sign', d3, '+0')

print('')
print('=== _is_neg_zero ===')
chk_true('neg_zero', _is_neg_zero(-0.0))
chk_false('pos_zero', _is_neg_zero(0.0))
chk_false('positive', _is_neg_zero(1.0))
chk_false('negative', _is_neg_zero(-1.0))

print('')
print('=== to_seconds ===')
dt = datetime(1900, 1, 1, 14, 30, 42, 500000)
chk('to_seconds', to_seconds(dt), 14 * 3600 + 30 * 60 + 42.5)

print('')
print('=== compute_median_step ===')
base = datetime(1900, 1, 1, 10, 0, 0)
times_even = [base + timedelta(seconds=i * 0.5) for i in range(10)]
chk('median_step_0.5', compute_median_step(times_even), 0.5)
times_none = [base]
chk('median_step_single', compute_median_step(times_none), None)
chk('median_step_empty', compute_median_step([]), None)

print('')
print('=== insert_dropped_readings ===')
# 4 real frames; gap between index 1 and 2 spans 3 steps -> 2 dropped readings
base2 = datetime(1900, 1, 1, 10, 0, 0)
step = 0.5
frames_in  = [1,   2,   5,   6  ]
times_in   = [base2 + timedelta(seconds=i * step) for i in [0, 1, 4, 5]]
values_in  = [100.0, 95.0, 90.0, 85.0]
ef, et, ev = insert_dropped_readings(frames_in, times_in, values_in, step)
chk('dropped_total_len', len(ef), 6)           # 4 real + 2 synthetic
chk('dropped_ev2_neg_zero', _is_neg_zero(ev[2]), True)
chk('dropped_ev3_neg_zero', _is_neg_zero(ev[3]), True)
chk('real_after_drop', ev[4], 90.0)
chk('real_last', ev[5], 85.0)
print('      expanded frames: ' + str(ef))

print('')
print('=== compute_trim_window ===')
base3 = datetime(1900, 1, 1, 14, 30, 0)
times3 = [base3 + timedelta(seconds=i * 0.12) for i in range(600)]   # 72 s of data
d_s = to_seconds(base3 + timedelta(seconds=30))
r_s = to_seconds(base3 + timedelta(seconds=38))  # 8 s event
li, ri = compute_trim_window(times3, d_time_s=d_s, r_time_s=r_s, event_duration_s=8.0)
duration = to_seconds(times3[ri]) - to_seconds(times3[li])
print('      trim idx %d..%d, duration=%.2f s' % (li, ri, duration))
chk_true('trim_duration_enough', duration >= 55.9)   # 2 * max(15, 8+20) = 56: allow 0.1s rounding

print('')
print('=== build_date_line ===')
dt_d = datetime(1900, 1, 1, 14, 30, 42, 340000)
chk('date_line',
    build_date_line('2025-12-23', dt_d, 35.21, 294),
    'Date: 2025-12-23 14:30:42.34: 35.21: 294')

print('')
print('=== build_star_line ===')
chk('star_ucac4_tycho2',
    build_star_line('', '1234-5678-1', '361-199861'),
    'Star: 0: 0: 0: 0: 1234-5678-1: 361-199861')
chk('star_defaults',
    build_star_line(),
    'Star: 0: 0: 0: 0: 0-0-1: 0-0')
chk('star_hipparcos',
    build_star_line('12345', '', ''),
    'Star: 12345: 0: 0: 0: 0-0-1: 0-0')

print('')
print('=== build_location_line ===')
loc = build_location_line(-37.8136, 144.9167, 50, 'Test Observer')
print('      ' + loc)
chk_true('location_lon_sign', loc.startswith('Observer: +144:'))
chk_true('location_has_lat', ': -37:' in loc)
chk_true('location_name', loc.endswith(': Test Observer'))

print('')
print('=== build_object_line ===')
chk('object_line',
    build_object_line(778, '2001 PA3'),
    'Object: Asteroid: 778: 2001 PA3')

print('')
print('=== build_values_line ===')
# Dropped reading in middle
vals_mixed = [100.0, 95.0, -0.0, 90.0]
vl = build_values_line(vals_mixed)
print('      ' + vl)
# Max=100 -> scale=9524/100=95.24; 100->9524, 95->9048, 90->8572
chk('values_max_9524', vl.split(':')[1], '9524')
chk('values_dropped_field', vl.split(':')[3], ' ')
# No dropped readings
vl2 = build_values_line([9524.0, 9000.0])
chk('values_no_drop', vl2, 'Values:9524:9000')

print('')
print('=== generate_dat_filename ===')
dt_f = datetime(1900, 1, 1, 14, 30, 42, 340000)
fname = generate_dat_filename(778, dt_f, '2025-12-23')
print('      ' + fname)
chk('dat_filename', fname, '(778)_20251223_143042_34.dat')

fname2 = generate_dat_filename('2001', datetime(1900, 1, 1, 0, 0, 0, 0), '2025-1-3')
print('      ' + fname2)
chk('dat_filename_midnight', fname2, '(2001)_20250103_000000_00.dat')

print('')
print('=' * 40)
print('Results: %d passed, %d failed' % (passed, failed))
if failed == 0:
    print('ALL TESTS PASSED')
else:
    print('SOME TESTS FAILED')
