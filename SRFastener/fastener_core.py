"""Pure logic for SR Fastener: catalog, names, BOM fields, and head/shank geometry numbers.

No adsk imports here, so it runs under plain pytest.
Fusion's internal length unit is the centimetre; `geometry()` returns cm.
"""
import json
import math
import os
import re
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
CATALOG_PATH = os.path.join(HERE, 'data', 'catalog.json')
MM_PER_IN = 25.4


def load_catalog(path=CATALOG_PATH):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


KINDS = (('screw', 'Screws'), ('nut', 'Nuts'), ('washer', 'Washers'))


def kind(fam):
    return fam.get('kind', 'screw')


def families(cat, system=None, kind_=None):
    """Screw families by default; kind_='nut' or 'washer' lists those from cat['parts']."""
    pool = cat['families'] if kind_ in (None, 'screw') else [p for p in cat.get('parts', []) if p['kind'] == kind_]
    return [f for f in pool if system in (None, f['system'])]


def family(cat, code):
    for f in cat['families'] + cat.get('parts', []):
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


def length_key(row, length):
    """Dialog list key (str of the catalog value) for a remembered length, or None. Catalog lengths can be ints
    (16) while the saved setting is a float (16.0), so match by value, not by text."""
    if length is None:
        return None
    for L in row['lengths']:
        if abs(float(L) - float(length)) < 1e-9:
            return str(L)
    return None


def length_label(fam, length):
    return (fmt_in(length) + '"') if fam['system'] == 'inch' else (fmt_mm(length) + ' mm')


def nominal(row):
    """Nominal size without the thread series, e.g. '#10' for both '#10' (UNC) and '#10-32' (UNF)."""
    return row.get('nominal', row['size'])


def thread_label(fam, row):
    if kind(fam) == 'washer':
        return ('%s screw' % nominal(row)) if fam['system'] == 'inch' else row['size']
    if fam.get('thread_form') == 'tapping':  # sheet metal screw: threads per inch or ISO 1478 pitch
        if fam['system'] == 'inch':
            return '%s-%d tapping thread' % (nominal(row), row['tpi'])
        return '%s x %g tapping thread' % (row['size'], row['pitch'])
    if fam['system'] == 'inch':
        return '%s-%d %s' % (nominal(row), row['tpi'], row.get('series', 'UNC'))
    return '%s x %g' % (row['size'], row['pitch'])


def finishes_for(cat, fam, row):
    """Finish keys offered for this size: the family's list, with ALLOY-BO only where a maker sells it."""
    if 'finishes' in row:  # nuts and washers: per size, black oxide only where McMaster stocks it
        return list(row['finishes'])
    out = []
    for k in fam.get('finishes', list(cat['finishes'])):
        if k == 'ALLOY-BO' and 'ALLOY-BO' not in row.get('grade', {}):
            continue
        out.append(k)
    return out


def _num(x):
    return ('%.4f' % x).rstrip('0').rstrip('.')


def washer_od(fam, row):
    """Washer outside diameter in catalog units (mm or in)."""
    return row['dims']['d2']


def part_number(fam, row, length, finish_key):
    """Daniel's BOM code. All dimensions live here, never in the description.
    Screws: 'SSH-M3-0.5 x 10 18-8 SS', 'SSH-1/4-20 x 1.5 18-8 SS-BO', 'SSH-4-40 x 0.25 18-8 SS'.
    Nuts: screw diameter and thread only: 'NHX-M5-0.8 18-8 SS', 'NHX-1/4-20 ZN'.
    Washers: screw size and outside diameter: 'WGP-M5 x 10 18-8 SS', 'WSA-1/4 x 0.734 18-8 SS'."""
    code = fam['code'].rsplit('-', 1)[0]
    fin = _FIN_CODE.get(finish_key, finish_key)
    if kind(fam) == 'washer':
        if fam['system'] == 'inch':
            body = '%s x %s' % (nominal(row).lstrip('#'), _num(washer_od(fam, row)))
        else:
            body = '%s x %g' % (row['size'], washer_od(fam, row))
        return '%s-%s %s' % (code, body, fin)
    if kind(fam) == 'nut':
        if fam['system'] == 'inch':
            body = '%s-%d' % (nominal(row).lstrip('#'), row['tpi'])
        else:
            body = '%s-%g' % (row['size'], row['pitch'])
        return '%s-%s %s' % (code, body, fin)
    if fam['system'] == 'inch':
        body = '%s-%d x %s' % (nominal(row).lstrip('#'), row['tpi'], _num(length))
    else:
        body = '%s-%g x %s' % (row['size'], row['pitch'], fmt_mm(length))
    return '%s-%s %s' % (code, body, fin)


_FIN_CODE = {'SS': '18-8 SS', 'SS-BO': '18-8 SS-BO', 'ALLOY-BO': 'ALLOY-BO', 'STL': 'STL', 'ZN': 'ZN', 'GR8': 'GR8',
             'CL10.9': 'CL10.9', 'CL10': 'CL10'}

# McMaster-style catalog numbers (e.g. 94758A, 90313A108) and vendor names must never
# appear in the Fusion part number, component name or description.
_VENDOR_PN = re.compile(r'\b(?:McMaster|Fastenal)\b|\b\d{5,6}[A-Z]\d{0,6}\b', re.I)

# Standards and material acronyms that must never show in a description, type name or material name.
STANDARD_WORDS = re.compile(r'\b(?:ISO|DIN|ASME|ANSI|ASTM|SAE J\d+|IFI|AISI|JIS|EN \d+)\b')


def contains_vendor_number(text):
    """True if text looks like, or contains, a McMaster or other vendor part number."""
    return bool(_VENDOR_PN.search(text or ''))


def contains_standard(text):
    return bool(STANDARD_WORDS.search(text or ''))


def _reject_vendor(label, text):
    if contains_vendor_number(text):
        raise ValueError('%s must use the shop smart part number scheme, not a vendor number: %s' % (label, text))


def grade(row, finish_key):
    """Raw strength grade from the catalog for this finish, e.g. 'class 12.9' or 'ASTM A574' (internal: picks the
    Fusion base material). Use grade_label() for anything shown to people."""
    return row.get('grade', {}).get(finish_key)


def grade_label(g):
    """Grade text with no standard names: 'class 12.9' -> 'Class 12.9', 'SAE J429 Grade 8' -> 'Grade 8',
    'ASTM A574' -> '' (that is a standard, not a grade name)."""
    if not g:
        return ''
    m = re.search(r'(?i)\b(class|grade)\s+([0-9.]+[A-Z]?)\b', g)
    return ('%s %s' % (m.group(1).capitalize(), m.group(2))) if m else ''


def desc_thread(fam, row):
    """Screw size and thread for a description, no standard or series words: 'M4 x 0.7', '1/4-20', '#10-32'.
    Washers: the screw size only ('M4', '#10', '1/4')."""
    if kind(fam) == 'washer':
        return row['size'] if fam['system'] == 'metric' else nominal(row)
    if fam['system'] == 'inch':
        return '%s-%d' % (nominal(row), row['tpi'])
    return '%s x %g' % (row['size'], row['pitch'])


def description(cat, fam, row, length, finish_key):
    """'Socket Head Screw, M4 x 0.7, 18-8 Stainless Steel'. Never a dimension (length, OD, thickness live in the
    part number) and never a standard."""
    return '%s, %s, %s' % (fam['name'], desc_thread(fam, row), finish(cat, finish_key)['name'])


def part_description(cat, fam, row, finish_key):
    return description(cat, fam, row, None, finish_key)


def component_name(fam, row, length, finish_key):
    return part_number(fam, row, length, finish_key)


def base_material(cat, fam, row, finish_key):
    """Fusion library material the physical properties come from (alloy picks by grade)."""
    g = grade(row, finish_key)
    f = finish(cat, finish_key)
    if g and finish_key == 'ALLOY-BO':
        return cat.get('alloy_materials', {}).get(g, f['base'])
    return f['base']


def bom_fields(cat, fam, row, length, finish_key):
    if finish_key not in finishes_for(cat, fam, row):
        raise ValueError('%s %s is not sold in %s' % (fam['code'], row['size'], finish_key))
    f = finish(cat, finish_key)
    pn = part_number(fam, row, length, finish_key)
    desc = description(cat, fam, row, length, finish_key)
    _reject_vendor('part number', pn)
    _reject_vendor('component name', component_name(fam, row, length, finish_key))
    _reject_vendor('description', desc)
    return {
        'part_number': pn,
        'description': desc,
        'material': f['material'],
        'base_material': base_material(cat, fam, row, finish_key),
        'appearance': f['appearance'],
        'finish': f['name'],
        'finish_key': finish_key,
        'grade': grade_label(grade(row, finish_key)),
    }


def part_geometry(fam, row):
    """Nuts and washers, in cm. z=0 is the face that sits on the part (or on the washer/nut below);
    the body goes +z. bore_r: nut bore = nominal diameter (threads cosmetic), washer bore = ID."""
    c = lambda v: to_cm(fam, v)  # noqa: E731
    d = row['dims']
    g = {'kind': kind(fam), 'shape': fam['shape']}
    if kind(fam) == 'nut':
        g.update(bore_r=c(row['d']) / 2.0, height=c(d['m']))
        if d.get('s'):
            g['across_flats'] = c(d['s'])
        if fam['shape'] == 'flange':
            g.update(flange_r=c(d['dc']) / 2.0, flange_t=c(d['c']))
        elif fam['shape'] == 'cap':
            # hex up to height - s/2, then a half-sphere dome of radius s/2; blind bore to the thread depth
            g.update(dome_r=g['across_flats'] / 2.0, bore_depth=c(d['dp']))
            g['hex_h'] = g['height'] - g['dome_r']
        elif fam['shape'] == 'wing':
            # McMaster gives overall width, height and base dia only; base height and wing thickness are drawn
            # as height/2 and base dia/4 (shape only, not dimensioned)
            g.update(wing_w=c(d['w']), base_r=c(d['db']) / 2.0)
            g.update(base_h=g['height'] / 2.0, wing_t=c(d['db']) / 4.0)
    else:
        g.update(bore_r=c(d['d1']) / 2.0, outer_r=c(d['d2']) / 2.0, height=c(d['t']))
        if fam['shape'] == 'split':
            g['gap'] = g['height']  # slot width drawn equal to the thickness (not dimensioned in the standards)
    g['thickness'] = g['height']
    return g


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
    if fam['head'] == 'flbutton':
        # flange disc dc x c on the seat, then a dome (crown rf) from the head diameter dk at z=c up to k
        g.update(head_r=c(dims['dk']) / 2.0, head_h=c(dims['k']), flange_r=c(dims['dc']) / 2.0, flange_t=c(dims['c']),
                 key=c(dims['s']), key_depth=c(key_depth(row, length)))
        g['dome_r'], zc = dome(g['head_r'], g['head_h'] - g['flange_t'], rf=c(dims['rf']))
        g['dome_zc'] = zc + g['flange_t']
        g['shank'] = (0.0, -g['L'])
    elif fam['head'] in ('cap', 'button'):
        g.update(head_r=c(dims['dk']) / 2.0, head_h=c(dims['k']), key=c(dims['s']), key_depth=c(key_depth(row, length)))
        g['shank'] = (0.0, -g['L'])
        if fam['head'] == 'button':
            g['dome_r'], g['dome_zc'] = dome(g['head_r'], g['head_h'], rf=c(dims['rf']) if 'rf' in dims else None,
                                             side=c(dims['side']) if 'side' in dims else 0.0)
    elif fam['head'] == 'pan':
        g.update(head_r=c(dims['dk']) / 2.0, head_h=c(dims['k']), recess_m=c(dims['m']), recess_depth=c(dims['pen']),
                 recess_no=dims['recess'])
        if dims.get('flat_top'):  # ASME B18.6.3 pan head: flat top (the small corner radius is not drawn)
            g['flat_top'] = True
        else:
            g['dome_r'], g['dome_zc'] = dome(g['head_r'], g['head_h'], rf=c(dims['rf']))
        g['shank'] = (0.0, -g['L'])
        if fam.get('thread_form') == 'tapping':
            # pointed tip: ISO 7049 Type C point length y; inch Type A/AB point length is not in the sources,
            # so it is drawn one diameter long (shape only)
            g['point_h'] = c(dims['tip']) if 'tip' in dims else 2.0 * g['r']
            g['point_r'] = 0.0
            g['point'] = 'tapping'
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
        g['point'] = fam.get('point', 'flat')
        g.update(key=c(dims['s']), key_depth=c(key_depth(row, length)))
        lk = '%g' % length
        # cone and dog points start at the thread root (ISO 4027/4028: the point angle applies below the root
        # diameter); root = basic minor diameter d - 1.082532 P (ISO 68-1 / ASME B1.1)
        pitch = row['pitch'] if 'pitch' in row else 1.0 / row['tpi']
        g['root_r'] = c(row['d'] - 1.082532 * pitch) / 2.0
        if g['point'] == 'cone':
            # cone to the tip diameter (ISO 4027 dt; inch cone drawn to a point); included angle per length
            angle = dims.get('angle_by_length', {}).get(lk, 90)
            g['point_r'] = c(dims.get('tip_d', 0.0)) / 2.0
            g['point_h'] = (g['root_r'] - g['point_r']) / math.tan(math.radians(angle / 2.0))
            g['cone_angle'] = angle
        elif g['point'] == 'dog':
            # extended (dog) tip: cylinder dp x z, joined to the thread by a 45 deg chamfer
            g['point_r'] = c(dims['dp']) / 2.0
            g['dog_z'] = c(dims['z_by_length'][lk])
            g['point_h'] = g['dog_z'] + (g['root_r'] - g['point_r'])
        elif g['point'] == 'oval':
            # oval tip: sphere of radius R (Holo-Krome Table 13) meeting the thread diameter
            g['oval_R'] = c(dims['R'])
            g['point_r'] = 0.0
            g['point_h'] = g['oval_R'] - math.sqrt(g['oval_R'] ** 2 - g['r'] ** 2)
        else:
            g['point_r'] = c(dims['dp']) / 2.0
            g['point_h'] = max(g['r'] - g['point_r'], 0.0)  # 45 deg chamfer down to the point diameter
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
        if nominal(row).lstrip('#') == nom and row.get('tpi', tpi) == tpi:
            return row['size']
    return None


def thread_spec(fam, row):
    """Fusion thread-type name and designation for a cosmetic thread; None for tapping screws (Fusion has no
    sheet metal screw thread, so they get no cosmetic thread)."""
    if fam.get('thread_form') == 'tapping':
        return None
    if fam['system'] == 'inch':
        # Fusion lists numbered sizes without the '#', e.g. '6-32 UNC'
        return ('ANSI Unified Screw Threads',
                '%s-%d %s' % (nominal(row).lstrip('#'), row['tpi'], row.get('series', 'UNC')), '3A')
    return 'ISO Metric profile', 'M%gx%g' % (row['d'], row['pitch']), '6g'


# ---------- matching and compatibility (Daniel 2026-11-17) ----------
# Screws size from the hole (its thread if tapped, else its diameter). Nuts and washers size from the screw's
# diameter and thread first (a screw in the stack, or already in that hole), and only from the hole when there is
# no screw. They never size from other nuts or washers.

def _nom_key(system, nom):
    nom = str(nom).strip()
    return nom if system == 'metric' else nom.lstrip('#')


def thread_ref(fam, row):
    """Size and thread of a screw, nut or washer row: {'system', 'nominal', 'pitch' or 'tpi' (None for washers),
    'label'}."""
    ref = {'system': fam['system'], 'nominal': _nom_key(fam['system'], nominal(row) if fam['system'] == 'inch'
                                                         else row['size']), 'pitch': None, 'tpi': None}
    if kind(fam) != 'washer':
        if fam['system'] == 'inch':
            ref['tpi'] = row['tpi']
        else:
            ref['pitch'] = row['pitch']
    ref['label'] = desc_thread(fam, row)
    return ref


_METRIC_DES = re.compile(r'^\s*M\s*(\d+(?:\.\d+)?)\s*(?:[xX\u00d7]\s*(\d+(?:\.\d+)?))?')
_INCH_DES = re.compile(r'^\s*#?\s*(\d+/\d+|\d+(?:\.\d+)?)\s*-\s*(\d+)')


def ref_from_designation(designation):
    """Fusion thread designation of a tapped hole -> ref. 'M6x1' -> M6 pitch 1; '1/4-20 UNC' -> 1/4 20 tpi;
    '10-32 UNF' -> 10 32 tpi. None if it cannot be read."""
    d = (designation or '').strip()
    m = _METRIC_DES.match(d)
    if m:
        return {'system': 'metric', 'nominal': 'M%g' % float(m.group(1)),
                'pitch': float(m.group(2)) if m.group(2) else None, 'tpi': None, 'label': d}
    m = _INCH_DES.match(d)
    if m:
        return {'system': 'inch', 'nominal': m.group(1), 'pitch': None, 'tpi': int(m.group(2)), 'label': d}
    return None


def same_thread(a, b):
    """True when two refs are the same diameter and thread. A washer ref (no thread) only checks the diameter."""
    if a is None or b is None:
        return True
    if a['system'] != b['system'] or a['nominal'] != b['nominal']:
        return False
    if a['system'] == 'metric':
        return a['pitch'] is None or b['pitch'] is None or abs(a['pitch'] - b['pitch']) < 1e-6
    return a['tpi'] is None or b['tpi'] is None or a['tpi'] == b['tpi']


def row_for_ref(fam, ref):
    """Size key in `fam` matching ref's diameter and thread (washers: diameter only), or None."""
    if ref is None or fam['system'] != ref['system']:
        return None
    for row in fam['sizes']:
        if same_thread(thread_ref(fam, row), ref):
            return row['size']
    return None


def size_for(cat, fam, screw_ref=None, hole_thread=None, hole_diameter_cm=None):
    """Size key for `fam` following Daniel's order. screw_ref: thread_ref of the screw in the stack or in the hole.
    hole_thread: the hole's thread designation if tapped. Returns None when nothing fits."""
    if kind(fam) != 'screw' and screw_ref is not None:
        return row_for_ref(fam, screw_ref)
    if hole_thread:
        ref = ref_from_designation(hole_thread)
        size = row_for_ref(fam, ref)
        if size or ref is not None:
            return size
    if hole_diameter_cm:
        return suggest_size(cat, fam, hole_diameter_cm)
    return None


def match_group(cat, finish_key):
    f = cat['finishes'].get(finish_key, {})
    return f.get('match', finish_key)


def matching_finish(cat, fam, row, finish_key):
    """finish_key if this size is sold in it, else a finish of the same material group (Class 10 for a Class
    10.9 screw), else None."""
    offered = finishes_for(cat, fam, row)
    if finish_key in offered:
        return finish_key
    g = match_group(cat, finish_key)
    for k in offered:
        if match_group(cat, k) == g:
            return k
    return None


def item(cat, code, size, finish_key, length=None):
    """A stack item dict from catalog keys."""
    fam = family(cat, code)
    return {'fam': fam, 'row': size_row(fam, size), 'finish': finish_key, 'length': length, 'kind': kind(fam)}


def item_label(cat, it):
    return '%s %s (%s)' % (it['fam']['name'], desc_thread(it['fam'], it['row']), finish(cat, it['finish'])['name'])


def material_mismatch(cat, items):
    """Items whose material differs from the screw's (or, with no screw, from the first item's)."""
    if not items:
        return []
    ref = next((i for i in items if i['kind'] == 'screw'), items[0])
    g = match_group(cat, ref['finish'])
    return [i for i in items if match_group(cat, i['finish']) != g]


def _hole_text(fam, hole_diameter_cm):
    if fam['system'] == 'inch':
        return '%.3f in' % (hole_diameter_cm / 2.54)
    return '%.2f mm' % (hole_diameter_cm * 10)


def compat_warnings(cat, items, hole_thread=None, hole_diameter_cm=None):
    """Plain-language warnings for hardware that does not go together: a nut or washer whose size or thread does
    not match the screw, a screw (or, with no screw, a nut) that does not match a tapped hole, a screw bigger than
    a plain hole, and mixed materials. items: stack items (new and already placed) on one hole."""
    out = []
    screw = next((i for i in items if i['kind'] == 'screw'), None)
    hole_ref = ref_from_designation(hole_thread) if hole_thread else None
    if screw is not None:
        sref = thread_ref(screw['fam'], screw['row'])
        if hole_ref is None and hole_diameter_cm and screw['row'].get('d'):
            ratio = hole_diameter_cm / to_cm(screw['fam'], screw['row']['d'])
            if ratio < 0.98:
                out.append('%s is bigger than the %s hole, which is not tapped'
                           % (item_label(cat, screw), _hole_text(screw['fam'], hole_diameter_cm)))
        if hole_ref is not None and not same_thread(sref, hole_ref):
            out.append('%s does not fit the tapped hole (%s)' % (item_label(cat, screw), hole_thread))
        for i in items:
            if i is screw or i['kind'] == 'screw':
                continue
            if not same_thread(thread_ref(i['fam'], i['row']), sref):
                out.append('%s does not fit %s (different size or thread)' % (item_label(cat, i), item_label(cat, screw)))
        for i in items:
            if i['kind'] == 'screw' and i is not screw:
                out.append('two screws in one hole: %s and %s' % (item_label(cat, screw), item_label(cat, i)))
    elif hole_ref is not None:
        for i in items:
            if not same_thread(thread_ref(i['fam'], i['row']), hole_ref):
                out.append('%s does not fit the tapped hole (%s)' % (item_label(cat, i), hole_thread))
    odd = material_mismatch(cat, items)
    if odd:
        ref = next((i for i in items if i['kind'] == 'screw'), items[0])
        out.append('mixed materials: %s vs %s' % (finish(cat, ref['finish'])['name'],
                                                  ', '.join(sorted({finish(cat, i['finish'])['name'] for i in odd}))))
    return out


# ---------- stack list edits (pure, so they are unit-tested) ----------

def stack_add(stack, row, uid):
    """Append a row (dict) tagged with its add order; returns the new row's index."""
    row = dict(row)
    row['uid'] = uid
    stack.append(row)
    return len(stack) - 1


def stack_remove(stack, selected=None):
    """'-' button: remove the highlighted row, or the most recently added one when none is highlighted.
    Returns the removed row, or None if the stack is empty."""
    if not stack:
        return None
    if selected is None or not (0 <= selected < len(stack)):
        selected = max(range(len(stack)), key=lambda i: stack[i].get('uid', 0))
    return stack.pop(selected)


def stack_move(stack, selected, step):
    """Move the highlighted row up (step -1) or down (+1). Returns its new index (unchanged at the ends)."""
    if selected is None or not (0 <= selected < len(stack)):
        return selected
    j = selected + step
    if 0 <= j < len(stack):
        stack[selected], stack[j] = stack[j], stack[selected]
        return j
    return selected
