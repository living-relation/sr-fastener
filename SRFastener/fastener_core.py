"""Pure logic for SR Fastener: catalog, names, BOM fields, and head/shank geometry numbers.

No adsk imports here, so it runs under plain pytest.
Fusion's internal length unit is the centimetre; `geometry()` returns cm.
"""
import json
import math
import os
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
CATALOG_PATH = os.path.join(HERE, 'data', 'catalog.json')
MM_PER_IN = 25.4


def load_catalog(path=CATALOG_PATH):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def families(cat, system=None):
    return [f for f in cat['families'] if system in (None, f['system'])]


def family(cat, code):
    for f in cat['families']:
        if f['code'] == code:
            return f
    raise KeyError(code)


def size_row(fam, size):
    for s in fam['sizes']:
        if s['size'] == size:
            return s
    raise KeyError('%s %s' % (fam['code'], size))


def finish(cat, key):
    return cat['finishes'][key]


def fmt_in(x):
    """0.25 -> '1/4', 1.5 -> '1-1/2', 2.0 -> '2' (lengths in inches)."""
    fr = Fraction(x).limit_denominator(64)
    whole, rem = divmod(fr.numerator, fr.denominator)
    if rem == 0:
        return '%d' % whole
    frac = '%d/%d' % (rem, fr.denominator)
    return '%d-%s' % (whole, frac) if whole else frac


def fmt_mm(x):
    return ('%g' % x)


def length_label(fam, length):
    return (fmt_in(length) + '"') if fam['system'] == 'inch' else (fmt_mm(length) + ' mm')


def thread_label(fam, row):
    if fam['system'] == 'inch':
        return '%s-%d' % (row['size'], row['tpi'])
    return '%s x %g' % (row['size'], row['pitch'])


def part_number(fam, row, length, finish_key):
    """Daniel's BOM code: 'SSH-M3-0.5 x 10 18-8 SS', 'SSH-1/4-20 x 1.5 18-8 SS-BO', 'SSH-4-40 x 0.25 18-8 SS'."""
    if fam['system'] == 'inch':
        body = '%s-%d x %s' % (row['size'].lstrip('#'), row['tpi'], ('%.4f' % length).rstrip('0').rstrip('.'))
    else:
        body = '%s-%g x %s' % (row['size'], row['pitch'], fmt_mm(length))
    return '%s-%s %s' % (fam['code'].split('-')[0], body, _FIN_CODE.get(finish_key, finish_key))


_FIN_CODE = {'SS': '18-8 SS', 'SS-BO': '18-8 SS-BO'}


def description(cat, fam, row, length, finish_key):
    """'Socket head cap screw, ISO 4762, M3 x 0.5 x 10 mm, 18-8 stainless steel'."""
    unit_len = length_label(fam, length)
    return '%s, %s, %s x %s, %s' % (fam['name'], fam['standard'], thread_label(fam, row), unit_len,
                                   finish(cat, finish_key)['name'].lower())


def component_name(fam, row, length, finish_key):
    return part_number(fam, row, length, finish_key)


def bom_fields(cat, fam, row, length, finish_key):
    f = finish(cat, finish_key)
    return {
        'part_number': part_number(fam, row, length, finish_key),
        'description': description(cat, fam, row, length, finish_key),
        'material': f['material'],
        'appearance': f['appearance'],
        'finish': f['name'],
        'vendor_pn': 'TBD',
        'standard': fam['standard'],
        'source': fam['source'],
    }


def to_cm(fam, value):
    return value * (MM_PER_IN if fam['system'] == 'inch' else 1.0) / 10.0


def geometry(fam, row, length):
    """All numbers in cm. z=0 is the seat plane:
    cap/button/hex: bearing face under the head (head goes +z, shank -z, length under head).
    flat: top of the head (whole screw goes -z, overall length).
    set: top face (screw goes -z)."""
    c = lambda v: to_cm(fam, v)  # noqa: E731
    dims = row['dims']
    g = {'head': fam['head'], 'r': c(row['d']) / 2.0, 'L': c(length)}
    if fam['head'] in ('cap', 'button'):
        g.update(head_r=c(dims['dk']) / 2.0, head_h=c(dims['k']), key=c(dims['s']), key_depth=c(dims['t']))
        g['shank'] = (0.0, -g['L'])
    elif fam['head'] == 'flat':
        half = math.radians(fam['angle'] / 2.0)
        head_r = c(dims['dk']) / 2.0
        cone_h = (head_r - g['r']) / math.tan(half)
        g.update(head_r=head_r, cone_h=cone_h, head_h=c(dims['k']), key=c(dims['s']), key_depth=c(dims['t']))
        g['shank'] = (-cone_h, -g['L'])
    elif fam['head'] == 'hex':
        g.update(across_flats=c(dims['s']), head_h=c(dims['k']))
        g['shank'] = (0.0, -g['L'])
    elif fam['head'] == 'set':
        g.update(key=c(dims['s']), key_depth=c(dims['t']), point_r=c(dims['dp']) / 2.0)
        g['point_h'] = max(g['r'] - g['point_r'], 0.0)  # 45 deg chamfer down to the flat point
        g['shank'] = (0.0, -g['L'])
    else:
        raise ValueError(fam['head'])
    return g


def button_sphere(head_r, head_h):
    """Sphere radius and centre height for a dome through the head edge (r=head_r, z=0) and apex (0, head_h)."""
    radius = (head_r ** 2 + head_h ** 2) / (2.0 * head_h)
    return radius, head_h - radius


def suggest_size(cat, fam, hole_diameter_cm):
    """Nominal size for a plain (unthreaded) hole: a clearance fit (hole 1.0-1.3 x d, nearest 1.1) wins,
    else a tap-drill fit (0.7-1.0 x d). Threaded holes are read from their thread feature instead."""
    for lo, hi, target in ((1.0, 1.3, 1.1), (0.7, 1.0, 0.85)):
        best = None
        for row in fam['sizes']:
            ratio = hole_diameter_cm / to_cm(fam, row['d'])
            if lo <= ratio <= hi:
                score = abs(ratio - target)
                if best is None or score < best[0]:
                    best = (score, row['size'])
        if best:
            return best[1]
    return None


def size_from_designation(fam, designation):
    """'M3x0.5' -> 'M3', '1/4-20 UNC' -> '1/4', '#10-24 UNC' -> '#10'; None if not in this family."""
    d = (designation or '').strip()
    if fam['system'] == 'metric':
        head = d.split('x')[0].strip()
    else:
        head = d.split('-')[0].strip()
    for row in fam['sizes']:
        if row['size'] == head:
            return head
    return None


def thread_spec(fam, row):
    """Fusion thread-type name and designation for a cosmetic thread."""
    if fam['system'] == 'inch':
        # Fusion lists numbered sizes without the '#', e.g. '6-32 UNC'
        return 'ANSI Unified Screw Threads', '%s-%d UNC' % (row['size'].lstrip('#'), row['tpi']), '3A'
    return 'ISO Metric profile', 'M%gx%g' % (row['d'], row['pitch']), '6g'
