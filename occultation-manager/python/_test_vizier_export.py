"""Quick smoke test for vizier_export.py"""
import sys
sys.path.insert(0, '.')
from vizier_export import (
    parse_star_id, decimal_degrees_to_dms, _is_neg_zero,
    build_star_line, build_values_line, build_date_line,
    generate_dat_filename, build_location_line, build_object_line,
    compute_median_step, insert_dropped_readings, compute_trim_window,
)
from datetime import datetime

errors = []

def chk(name, expr, expected):
    if expr != expected:
        errors.append('%s: got %r expected %r' % (name, expr, expected))
    else:
        print('OK  ' + name)


# parse_star_id
chk('ucac4', parse_star_id('UCAC4 361-199861')['ucac4'], '361-199861')
chk('tycho2', parse_star_id('TYC 1234-5678-1')['tycho2'], '1234-5678-1')
chk('hipparcos', parse_star_id('HIP 12345')['hipparcos'], '12345')
chk('gaia_empty', parse_star_id('Gaia DR3 12345')['ucac4'], '')

# decimal_degrees_to_dms
d, m, s = decimal_degrees_to_dms(-37.8136)
chk('dms_sign', d, '-37')
chk('dms_min', m, '48')
print('    sec=%s' % s)

# _is_neg_zero
chk('neg_zero_true', _is_neg_zero(-0.0), True)
chk('neg_zero_false', _is_neg_zero(0.0), False)
chk('neg_zero_pos', _is_neg_zero(1.0), False)

# build_star_line
chk('star_line', build_star_line('', '1234-5678-1', '361-199861'),
    'Star: 0: 0: 0: 0: 1234-5678-1: 361-199861')
chk('star_line_defaults', build_star_line(),
    'Star: 0: 0: 0: 0: 0-0-1: 0-0')

# build_values_line
vals = [100.0, 95.0, -0.0, 90.0]
line = build_values_line(vals)
chk('values_line', line, 'Values:9524:9048: :8572')  # 9524*0.95=9047.8->9048, 9524*0.9=8571.6->8572
print('    (actual values line: %s)' % line)

# No-scaling check: max is already 9524
chk('values_scaled_max', build_values_line([9524.0, 9000.0]), 'Values:9524:9000')

# build_date_line
dt = datetime(1900, 1, 1, 14, 30, 42, 340000)
chk('date_line', build_date_line('2025-12-23', dt, 35.21, 294),
    'Date: 2025-12-23 14:30:42.34: 35.21: 294')

# build_location_line  (spot check format)
loc = build_location_line(-37.8136, 144.9167, 50, 'Test Observer')
print('    location_line: %s' % loc)
assert loc.startswith('Observer: +144:'), 'location format wrong'
print('OK  build_location_line')

# build_object_line
chk('object_line', build_object_line(778, '2001 PA3'),
    'Object: Asteroid: 778: 2001 PA3')

# generate_dat_filename
dt2 = datetime(1900, 1, 1, 14, 30, 42, 340000)
fname = generate_dat_filename(778, dt2, '2025-12-23')
print('    filename: %s' % fname)
chk('dat_filename', fname, '(778)_20251223_143042_34.dat')

# compute_median_step
from datetime import timedelta
base = datetime(1900, 1, 1, 10, 0, 0)
times = [base + timedelta(seconds=i * 0.5) for i in range(10)]
step = compute_median_step(times)
chk('median_step', step, 0.5)

# insert_dropped_readings
frames = [1, 2, 5, 6]  # gap between 2 and 5 = 2 dropped frames
base_t = datetime(1900, 1, 1, 10, 0, 0)
times2 = [base_t + timedelta(seconds=i * 0.5) for i in [0, 1, 4, 5]]
values2 = [100.0, 95.0, 90.0, 85.0]
ef, et, ev = insert_dropped_readings(frames, times2, values2, 0.5)
chk('dropped_count', len(ef), 6)  # 4 real + 2 synthetic
chk('dropped_neg_zero', _is_neg_zero(ev[2]), True)
chk('dropped_neg_zero2', _is_neg_zero(ev[3]), True)
chk('real_after_drop', ev[4], 90.0)

if errors:
    print('\nFAILED:')
    for e in errors:
        print('  FAIL: ' + e)
    sys.exit(1)
else:
    print('\nALL TESTS PASSED')
