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


def nominal(row):
    """Nominal size without the thread series, e.g. '#10' for both '#10' (UNC) and '#10-32' (UNF)."""
    return row.get('nominal', row['size'])


def thread_label(fam, row):
    if fam['system'] == 'inch':
        return '%s-%d %s' % (nominal(row), row['tpi'], row.get('series', 'UNC'))
    return '%s x %g' % (row['size'], row['pitch'])


def finishes_for(cat, fam, row):
    """Finish keys offered for this size: the family's list, with ALLOY-BO only where a maker sells it."""
    out = []
    for k in fam.get('finishes', list(cat['finishes'])):
        if k == 'ALLOY-BO' and 'ALLOY-BO' not in row.get('grade', {}):
            continue
        out.append(k)
    return out


def part_number(fam, row, length, finish_key):
    """Daniel's BOM code: 'SSH-M3-0.5 x 10 18-8 SS', 'SSH-1/4-20 x 1.5 18-8 SS-BO', 'SSH-4-40 x 0.25 18-8 SS'."""
    if fam['system'] == 'inch':
        body = '%s-%d x %s' % (nominal(row).lstrip('#'), row['tpi'], ('%.4f' % length).rstrip('0').rstrip('.'))
    else:
        body = '%s-%g x %s' % (row['size'], row['pitch'], fmt_mm(length))
    return '%s-%s %s' % (fam['code'].rsplit('-', 1)[0], body, _FIN_CODE.get(finish_key, finish_key))


_FIN_CODE = {'SS': '18-8 SS', 'SS-BO': '18-8 SS-BO', 'ALLOY-BO': 'ALLOY-BO'}


def grade(row, finish_key):
    """Strength grade for this finish if the catalog gives one, e.g. 'class 12.9' or 'ASTM A574'."""
    return row.get('grade', {}).get(finish_key)


def description(cat, fam, row, length, finish_key):
    """'Socket head cap screw, ISO 4762, M3 x 0.5 x 10 mm, 18-8 stainless steel'
    (alloy adds the grade: '..., alloy steel, black oxide, class 12.9')."""
    unit_len = length_label(fam, length)
    text = '%s, %s, %s x %s, %s' % (fam['name'], fam['standard'], thread_label(fam, row), unit_len,
                                    finish(cat, finish_key)['name'].lower())
    g = grade(row, finish_key)
    return text + (', ' + g if g else '')


def component_name(fam, row, length, finish_key):
    return part_number(fam, row, length, finish_key)


def bom_fields(cat, fam, row, length, finish_key):
    if finish_key not in finishes_for(cat, fam, row):
        raise ValueError('%s %s is not sold in %s' % (fam['code'], row['size'], finish_key))
    f = finish(cat, finish_key)
    g = grade(row, finish_key)
    material = cat.get('alloy_materials', {}).get(g, f['material']) if g else f['material']
    return {
        'part_number': part_number(fam, row, length, finish_key),
        'description': description(cat, fam, row, length, finish_key),
        'material': material,
        'appearance': f['appearance'],
        'finish': f['name'],
        'grade': g or '',
        'vendor_pn': 'TBD',
        'standard': fam['standard'],
        'source': fam['source'],
    }


def thread_length(fam, row, length):
    """Threaded length measured from the tip, in catalog units (mm or in); equals the shank length when the
    screw is threaded to the head. Rules come from the catalog 'thread' block (see tools/build_catalog.py)."""
    shank = length
    t = row.get('thread')
    if not t:
        return shank
    if 'lg' in t:
        lg = t['lg'].get('%g' % length)
        return shank if lg is None else length - lg
    if 'partial_from' in t and length >= t['partial_from'] - 1e-9:
        return min(t['b'], shank)
    if 'partial_from_over' in t and length > t['partial_from_over'] + 1e-9:
        return min(t['b'], shank)
    return shank


def key_depth(row, length):
    """Socket depth for this length: set screws use a shallower socket at their shortest lengths."""
    dims = row['dims']
    tbl = dims.get('t_by_length', {})
    if '%g' % length in tbl:
        return tbl['%g' % length]
    if 'short_max' in dims and length <= dims['short_max'] + 1e-9:
        return dims['t_short']
    return dims['t']


def to_cm(fam, value):
    return value * (MM_PER_IN if fam['system'] == 'inch' else 1.0) / 10.0


def geometry(fam, row, length):
    """All numbers in cm. z=0 is the seat plane:
    cap/button/pan/cheese/hex: bearing face under the head (head goes +z, shank -z, length under head).
    flat: top of the head (whole screw goes -z, overall length).
    set: top face (screw goes -z).
    thread_len: threaded length from the tip (cm)."""
    c = lambda v: to_cm(fam, v)  # noqa: E731
    dims = row['dims']
    g = {'head': fam['head'], 'drive': fam.get('drive', 'hex'), 'r': c(row['d']) / 2.0, 'L': c(length),
         'thread_len': c(thread_length(fam, row, length))}
    if fam['head'] in ('cap', 'button'):
        g.update(head_r=c(dims['dk']) / 2.0, head_h=c(dims['k']), key=c(dims['s']), key_depth=c(key_depth(row, length)))
        g['shank'] = (0.0, -g['L'])
        if fam['head'] == 'button':
            g['dome_r'], g['dome_zc'] = dome(g['head_r'], g['head_h'], rf=c(dims['rf']) if 'rf' in dims else None,
                                             side=c(dims['side']) if 'side' in dims else 0.0)
    elif fam['head'] == 'pan':
        g.update(head_r=c(dims['dk']) / 2.0, head_h=c(dims['k']), recess_m=c(dims['m']), recess_depth=c(dims['pen']),
                 recess_no=dims['recess'])
        g['dome_r'], g['dome_zc'] = dome(g['head_r'], g['head_h'], rf=c(dims['rf']))
        g['shank'] = (0.0, -g['L'])
    elif fam['head'] == 'cheese':
        g.update(head_r=c(dims['dk']) / 2.0, head_h=c(dims['k']), slot_w=c(dims['n']), slot_depth=c(dims['t']))
        g['shank'] = (0.0, -g['L'])
    elif fam['head'] == 'flat':
        half = math.radians(fam['angle'] / 2.0)
        head_r = c(dims['dk']) / 2.0
        cone_h = (head_r - g['r']) / math.tan(half)
        g.update(head_r=head_r, cone_h=cone_h, head_h=c(dims['k']), key=c(dims['s']), key_depth=c(key_depth(row, length)))
        g['shank'] = (-cone_h, -g['L'])
        g['thread_len'] = min(g['thread_len'], g['L'] - cone_h)
    elif fam['head'] == 'hex':
        g.update(across_flats=c(dims['s']), head_h=c(dims['k']))
        g['shank'] = (0.0, -g['L'])
    elif fam['head'] == 'set':
        g.update(key=c(dims['s']), key_depth=c(key_depth(row, length)), point_r=c(dims['dp']) / 2.0)
        g['point_h'] = max(g['r'] - g['point_r'], 0.0)  # 45 deg chamfer down to the point diameter
        g['point'] = fam.get('point', 'flat')
        if g['point'] == 'cup':
            # The standards give only the cup diameter dz; the cup recess is drawn as a 118 deg cone with a
            # rim 0.1 x dz wide (shape not dimensioned in ISO 4029 / ASME B18.3, so simplified).
            g['cup_r'] = g['point_r'] * 0.8
            g['cup_depth'] = g['cup_r'] / math.tan(math.radians(59.0))
        g['shank'] = (0.0, -g['L'])
    else:
        raise ValueError(fam['head'])
    return g


def button_sphere(head_r, head_h):
    """Sphere radius and centre height for a dome through the head edge (r=head_r, z=0) and apex (0, head_h)."""
    radius = (head_r ** 2 + head_h ** 2) / (2.0 * head_h)
    return radius, head_h - radius


def dome(head_r, head_h, rf=None, side=0.0):
    """Sphere (radius, centre z) for a domed head with its apex at head_h.
    side: cylindrical side height at the head edge (ASME B18.3 button 'S'); the dome passes through (head_r, side).
    rf: crown radius from the standard (ISO 7380-1, ISO 7045). If rf is too small to reach the head edge
    within the head height (manufacturer's contour), the dome through the edge at z=0 is used instead."""
    radius, zc = button_sphere(head_r, head_h - side)
    zc += side
    if rf is not None and rf > radius:
        radius, zc = rf, head_h - rf
    return radius, zc


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
    """'M3x0.5' -> 'M3', '1/4-20 UNC' -> '1/4', '#10-24 UNC' or '10-24 UNC' -> '#10', '10-32 UNF' -> '#10-32';
    None if not in this family."""
    d = (designation or '').strip()
    if fam['system'] == 'metric':
        head = d.split('x')[0].strip()
        for row in fam['sizes']:
            if row['size'] == head:
                return head
        return None
    parts = d.split()[0].split('-') if d else []
    if len(parts) < 2:
        return None
    nom = parts[0].lstrip('#')
    try:
        tpi = int(parts[1])
    except ValueError:
        return None
    for row in fam['sizes']:
        if nominal(row).lstrip('#') == nom and row['tpi'] == tpi:
            return row['size']
    return None


def thread_spec(fam, row):
    """Fusion thread-type name and designation for a cosmetic thread."""
    if fam['system'] == 'inch':
        # Fusion lists numbered sizes without the '#', e.g. '6-32 UNC'
        return ('ANSI Unified Screw Threads',
                '%s-%d %s' % (nominal(row).lstrip('#'), row['tpi'], row.get('series', 'UNC')), '3A')
    return 'ISO Metric profile', 'M%gx%g' % (row['d'], row['pitch']), '6g'
