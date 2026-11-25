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


KINDS = (('screw', 'Screws'), ('nut', 'Nuts'), ('washer', 'Washers'), ('press-in', 'Press-in'))


def kind(fam):
    return fam.get('kind', 'screw')


def families(cat, system=None, kind_=None):
    """Screw families by default. kind_='nut' or 'washer' lists cat['parts']; kind_='press-in' lists cat['press_in']."""
    if kind_ in (None, 'screw'):
        pool = cat['families']
    elif kind_ == 'press-in':
        pool = cat.get('press_in', [])
    else:
        pool = [p for p in cat.get('parts', []) if p['kind'] == kind_]
    return [f for f in pool if system in (None, f['system'])]


def family(cat, code):
    for f in cat['families'] + cat.get('parts', []) + cat.get('press_in', []):
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
    (16) while the saved setting is a float (16.0), so match by value, not by text. Shank codes are strings
    ('0', '00') and are matched as text so '00' is not read as 0."""
    if length is None:
        return None
    for L in row['lengths']:
        if isinstance(L, str):
            if str(length) == L:
                return L
            continue
        try:
            if abs(float(L) - float(length)) < 1e-9:
                return str(L)
        except (TypeError, ValueError):
            continue
    return None


def length_label(fam, length):
    if fam.get('length_kind') == 'shank':
        return 'shank %s' % length
    return (fmt_in(length) + '"') if fam['system'] == 'inch' else (fmt_mm(length) + ' mm')


def nominal(row):
    """Nominal size without the thread series, e.g. '#10' for both '#10' (UNC) and '#10-32' (UNF)."""
    return row.get('nominal', row['size'])


def thread_label(fam, row):
    if row.get('menu'):
        return row['menu']
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


def _pem_token(row, length):
    """Catalog length or shank code for a PEM designation, as text ('12', '00')."""
    key = length_key(row, length)
    if key is None:
        raise KeyError(length)
    for L in row['lengths']:
        if isinstance(L, str) and L == key:
            return L
    number = float(key)
    if number == int(number):
        return str(int(number))
    return '%g' % number


def part_number(fam, row, length, finish_key):
    """Daniel's BOM code. All dimensions live here, never in the description.
    Press-in parts use the PEM designation (FHS-M5-12, S-M3-1ZI) instead of the shop finish code.
    Screws: 'SSH-M3-0.5 x 10 18-8 SS', 'SSH-1/4-20 x 1.5 18-8 SS-BO', 'SSH-4-40 x 0.25 18-8 SS'.
    Nuts: screw diameter and thread only: 'NHX-M5-0.8 18-8 SS', 'NHX-1/4-20 ZN'.
    Washers: screw size and outside diameter: 'WGP-M5 x 10 18-8 SS', 'WSA-1/4 x 0.734 18-8 SS'."""
    if kind(fam) == 'press-in':
        return '%s-%s-%s%s' % (fam['code'], row['thread_code'], _pem_token(row, length), fam.get('pem_suffix', ''))
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
    Washers: the screw size only ('M4', '#10', '1/4'). Press-in uses the thread only, never the hole or length."""
    if kind(fam) == 'press-in':
        thread_name = 'M3' if row.get('thread_code') == '3.5M3' else row.get('thread_code', row['size'])
        return '%s x %g' % (thread_name, row['pitch'])
    if kind(fam) == 'washer':
        return row['size'] if fam['system'] == 'metric' else nominal(row)
    if fam['system'] == 'inch':
        return '%s-%d' % (nominal(row), row['tpi'])
    return '%s x %g' % (row['size'], row['pitch'])


def finish_desc_name(fin):
    """Words at the end of the part description. Grade and class finishes use the short form
    ('GR-8 Steel', 'CL-10.9 Steel', 'CL-10 Steel'); everything else uses the finish name."""
    return fin.get('desc_name', fin['name'])


def description(cat, fam, row, length, finish_key):
    """'Socket Head Screw, M4 x 0.7, 18-8 Stainless Steel'. Never a dimension (length, OD, thickness live in the
    part number) and never a standard. Grade and class use the short form: 'Hex Head Bolt, 1/4-20, GR-8 Steel'."""
    return '%s, %s, %s' % (fam['name'], desc_thread(fam, row), finish_desc_name(finish(cat, finish_key)))


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


def part_geometry(fam, row, length=None):
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
    # A length a supplier sells fully threaded, past the product standard's length table.
    if any(abs(float(x) - float(length)) < 1e-9 for x in t.get('full_to_head', ())):
        return shank
    if 'lg' in t:
        lg = t['lg'].get('%g' % length)
        return shank if lg is None else length - lg
    if 'partial_from' in t and length >= t['partial_from'] - 1e-9:
        return min(t['b'], shank)
    if 'partial_from_over' in t and length > t['partial_from_over'] + 1e-9:
        return min(t['b'], shank)
    return shank


def key_depth(row, length, point_h=0.0):
    """How deep the hex looks. Not a spec, and not used in a part number or description.

    The across-flats size stays dims['s']. A headed screw gets half its head height, so the
    hex stops inside the head. A set screw gets half the metal above the point (point_h is
    in the same units as length), so the hex does not come out the tip."""
    k = row['dims'].get('k')
    if k:
        return 0.5 * k
    room = length - point_h
    return 0.5 * room if room > 0 else 0.0


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
        g['key'] = c(dims['s'])
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
        room = g['L'] - g['point_h']
        g['key_depth'] = 0.5 * room if room > 0 else 0.0
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


def material_items(items):
    """Parts a material check may look at. Press-in hardware is left out, as the new part or as a part already
    in the hole."""
    return [i for i in items if i.get('kind') != 'press-in']


def material_mismatch(cat, items):
    """Items whose material differs from the screw's (or, with no screw, from the first item's).
    Press-in parts are ignored on both sides of the comparison."""
    items = material_items(items)
    if not items:
        return []
    ref = next((i for i in items if i['kind'] == 'screw'), items[0])
    g = match_group(cat, ref['finish'])
    return [i for i in items if match_group(cat, i['finish']) != g]


def should_ask_material(cat, existing, new):
    """True when the material-match prompt should open. A press-in part never causes the prompt."""
    new = material_items(new)
    if not new:
        return False
    return bool(material_mismatch(cat, list(existing) + new))


def match_finishes(cat, items, target):
    """Finish keys after a Yes on the material prompt. Press-in finishes are not changed.
    Returns (items, labels left as picked because that finish is not sold)."""
    out, kept = [], []
    for it in items:
        it = dict(it)
        if it.get('kind') == 'press-in':
            out.append(it)
            continue
        k = matching_finish(cat, it['fam'], it['row'], target)
        if k:
            it['finish'] = k
        else:
            kept.append(item_label(cat, it))
        out.append(it)
    return out, kept


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
                why = ('inch and metric' if i['fam']['system'] != screw['fam']['system']
                       else 'different size or thread')
                out.append('%s does not fit %s (%s)' % (item_label(cat, i), item_label(cat, screw), why))
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


# ---------- PEM press-in (one hole, one sheet) ----------

def _at(dims, key, length):
    """A dimension that is either one number or a map keyed by length or shank code."""
    value = dims[key]
    if not isinstance(value, dict):
        return value
    token = None if length is None else str(length)
    if token in value:
        return value[token]
    for k, val in value.items():
        try:
            if abs(float(k) - float(length)) < 1e-9:
                return val
        except (TypeError, ValueError):
            continue
    raise KeyError('%s at %s' % (key, length))


def mount_spec(fam, row, length):
    """Hole size, tolerance and minimum sheet (mm) plus the edge and hardness limits, with the citation."""
    dims = row['dims']
    spec = {
        'hole': float(_at(dims, 'hole', length)),
        'hole_plus': float(_at(dims, 'hole_plus', length)),
        'hole_minus': float(_at(dims, 'hole_minus', length)),
        'min_sheet': float(_at(dims, 'min_sheet', length)),
        'edge': float(_at(dims, 'edge', length)),
        'max_hrb': float(dims['max_hrb']),
        'max_hb': float(dims['max_hb']),
        'citation': row['citation'],
    }
    if 'max_sheet' in dims:
        spec['max_sheet'] = float(dims['max_sheet'])
    return spec


def mount_text(fam, row, length):
    """The three mounting notes for the dialog and for user parameters. Not the BOM description."""
    spec = mount_spec(fam, row, length)
    lines = ['Mounting hole %g mm +%g/-%g mm.' % (spec['hole'], spec['hole_plus'], spec['hole_minus']),
             'Minimum sheet %g mm.' % spec['min_sheet']]
    if 'max_sheet' in spec:
        lines.append('Maximum sheet %g mm.' % spec['max_sheet'])
    lines.append(spec['citation'])
    return '\n'.join(lines)


def parameter_values(fam, row, length):
    """(name suffix, value in mm, comment) for the design user parameters. Not BOM columns."""
    spec = mount_spec(fam, row, length)
    cite = spec['citation']
    return (
        ('hole', spec['hole'], 'PEM mounting hole size (mm). ' + cite),
        ('hole_plus', spec['hole_plus'], 'PEM hole plus tolerance (mm). ' + cite),
        ('hole_minus', spec['hole_minus'], 'PEM hole minus tolerance (mm). ' + cite),
        ('min_sheet', spec['min_sheet'], 'PEM minimum sheet thickness (mm). ' + cite),
    )


def press_warnings(spec, hole_mm=None, sheet_mm=None, edge_mm=None, hardness_hrb=None):
    """Warnings for one press-in part. Pass None for a check the design did not measure."""
    out = []
    if hole_mm is not None:
        lo = spec['hole'] - spec['hole_minus']
        hi = spec['hole'] + spec['hole_plus']
        if hole_mm < lo - 1e-6 or hole_mm > hi + 1e-6:
            out.append('Mounting hole %.3f mm is off the PEM hole %.3f mm +%g/-%g.'
                       % (hole_mm, spec['hole'], spec['hole_plus'], spec['hole_minus']))
    if sheet_mm is not None and sheet_mm < spec['min_sheet'] - 1e-6:
        out.append('Sheet %.3f mm is thinner than the PEM minimum %.3f mm.' % (sheet_mm, spec['min_sheet']))
    if sheet_mm is not None and spec.get('max_sheet') is not None and sheet_mm > spec['max_sheet'] + 1e-6:
        out.append('Sheet %.3f mm is thicker than the PEM maximum %.3f mm.' % (sheet_mm, spec['max_sheet']))
    if edge_mm is not None and edge_mm < spec['edge'] - 1e-6:
        out.append('Centerline-to-edge %.3f mm is under the PEM minimum %.3f mm.' % (edge_mm, spec['edge']))
    if hardness_hrb is not None and hardness_hrb > spec['max_hrb'] + 1e-6:
        out.append('Sheet hardness HRB %g is harder than the PEM maximum HRB %g (HB %g).'
                   % (hardness_hrb, spec['max_hrb'], spec['max_hb']))
    return out


def press_size_for(fam, hole_diameter_cm):
    """Size whose published hole window contains this hole, or None."""
    if not hole_diameter_cm:
        return None
    mm = hole_diameter_cm * 10.0
    for row in fam['sizes']:
        spec = mount_spec(fam, row, row['lengths'][0])
        if spec['hole'] - spec['hole_minus'] - 1e-6 <= mm <= spec['hole'] + spec['hole_plus'] + 1e-6:
            return row['size']
    return None


def press_geometry(fam, row, length):
    """Installed press-in body, centimetres. z=0 is the install face.
    Nuts and floating nuts: head sits on the face (+z), shank goes into the sheet (-z).
    Studs and standoffs: the head is flush at z=0 and the body goes into the sheet (-z).
    A flush stud's head is the STEP profile: thickness H/10, full-round edge, collar, undercut,
    then the plain barrel. Catalog S is the maximum unthreaded length, not the barrel start."""
    dims = row['dims']

    def c(v):
        return float(v) / 10.0

    g = {'shape': fam['shape'], 'kind': 'press-in'}
    if fam['shape'] == 'clinch-nut':
        g.update(head_r=c(_at(dims, 'E', length)) / 2.0,
                 head_h=c(_at(dims, 'T', length)),
                 shank_r=c(_at(dims, 'C', length)) / 2.0,
                 shank_l=c(_at(dims, 'A', length)),
                 bore_r=c(row['d']) / 2.0)
    elif fam['shape'] == 'floating':
        # Outer envelope stays the catalog body. The captive nut is the STEP body diameter.
        # The radial gap is the bulletin float: 0.38 mm from center, 0.76 mm total.
        height_key = 'T2' if 'T2' in dims else 'T1'
        minor = row['d'] - 1.082532 * row['pitch']
        nut_r = c(dims['nut_dia']) / 2.0
        float_r = c(dims['float_radial'])
        g.update(head_r=c(dims['E']) / 2.0,
                 head_h=c(_at(dims, height_key, length)),
                 shank_r=c(_at(dims, 'C', length)) / 2.0,
                 shank_l=c(_at(dims, 'A', length)),
                 barrel_r=c(dims['D']) / 2.0,
                 nut_r=nut_r,
                 float_r=float_r,
                 float_total=c(dims['float_total']),
                 retainer_bore_r=nut_r + float_r,
                 bore_r=c(minor) / 2.0)
    elif fam['shape'] == 'stud':
        # The length code is the shank under the head. The head thickness sits beyond it,
        # so the solid is longer than the length code by the head.
        length_cm = c(float(length))
        head_h = c(_at(dims, 'head_thk', length))
        overall = length_cm + head_h
        barrel = c(_at(dims, 'barrel_start', length))
        g.update(r=c(row['d']) / 2.0, L=overall, head_r=c(_at(dims, 'H', length)) / 2.0,
                 head_h=head_h, edge_r=c(_at(dims, 'edge_r', length)),
                 face_r=c(_at(dims, 'face_dia', length)) / 2.0,
                 collar_r=c(_at(dims, 'collar_dia', length)) / 2.0,
                 collar_l=c(_at(dims, 'collar_len', length)),
                 neck_l=c(_at(dims, 'neck_len', length)),
                 undercut_r=c(_at(dims, 'undercut_min_dia', length)) / 2.0,
                 undercut_l=c(_at(dims, 'undercut_len', length)),
                 barrel_start=barrel, s_max=c(_at(dims, 'S', length)),
                 # Plain length is the measured barrel start. It is under S max, which the datasheet
                 # states as a maximum, so the cosmetic thread may start there.
                 unthread=barrel, thread_len=max(overall - barrel, 0.0),
                 tip_recess_r=c(row['d'] * 0.075),
                 shank=(0.0, -overall))
    elif fam['shape'] == 'standoff':
        length_cm = c(float(length))
        sheet = dims['min_sheet']
        if isinstance(sheet, dict):
            sheet = min(float(v) for v in sheet.values())
        g.update(across=c(_at(dims, 'H', length)), L=length_cm, bore_r=c(row['d']) / 2.0,
                 clinch_r=c(_at(dims, 'C', length)) / 2.0, clinch_l=c(float(sheet)))
        if 'F' in dims:
            g['blind'] = c(_at(dims, 'F', length))
    else:
        raise ValueError(fam['shape'])
    return g


def stud_profile(fam, row, length):
    """Revolve points (z, r) in cm for a flush stud. z=0 is the flush face; z decreases toward the tip.
    The head edge is a full round. The undercut flanks are 63.43 deg from the axis (slope 2) with a
    round root sized so the groove length and minimum diameter match the STEP."""
    g = press_geometry(fam, row, length)
    pts = []
    steps = 16
    for i in range(steps + 1):
        ang = math.pi / 2.0 - i * math.pi / steps
        z = -g['head_h'] / 2.0 + g['edge_r'] * math.sin(ang)
        rad = g['face_r'] + g['edge_r'] * math.cos(ang)
        pts.append((z, rad))
    z = -g['head_h']
    pts.append((z, g['collar_r']))
    z -= g['collar_l']
    pts.append((z, g['collar_r']))
    z -= g['neck_l']
    pts.append((z, g['r']))
    s0 = -z * 10.0  # mm from the flush face, positive toward the tip
    # undercut in mm, then converted
    r_maj = g['r'] * 10.0
    r_min = g['undercut_r'] * 10.0
    U = g['undercut_l'] * 10.0
    h = r_maj - r_min
    rf = (U - h) / (math.sqrt(5.0) - 1.0)
    sc = s0 + U / 2.0
    rc = r_min + rf
    root = math.sqrt(5.0)
    # Left tangent point: center minus Rf along the flank normal (2, 1)/sqrt(5).
    st = sc - rf * 2.0 / root
    rt = rc - rf / root
    pts.append((-st / 10.0, rt / 10.0))
    a_left = math.atan2(-1.0, -2.0)
    a_right = math.atan2(-1.0, 2.0)
    arc_n = 8
    for i in range(1, arc_n):
        ang = a_left + (a_right - a_left) * i / arc_n
        ss = sc + rf * math.cos(ang)
        rr = rc + rf * math.sin(ang)
        pts.append((-ss / 10.0, rr / 10.0))
    pts.append((-(s0 + U - (st - s0)) / 10.0, rt / 10.0))
    z = -(s0 + U) / 10.0
    pts.append((z, g['r']))
    pts.append((-g['L'], g['r']))
    return pts


# What the +/- stack may add on a PEM. Internal threads take one mating screw.
# Thru standoffs take a screw on each end. Blind standoffs take one screw on the
# open end, no longer than F. Studs take nuts and washers on the threaded end.
_PEM_SCREW = ('S', 'SS', 'CLS', 'CLSS', 'AS', 'LAS', 'SO', 'SOS', 'BSO', 'BSOS')
_PEM_STUD = ('FH', 'FHS', 'FH4')


def mate_thread(fam, row):
    """Thread a mating part must match. A press-in size key such as 3.5M3 is still an M3 thread."""
    if kind(fam) == 'press-in':
        return {'system': 'metric', 'nominal': 'M%g' % float(row['d']), 'pitch': float(row['pitch']),
                'tpi': None, 'label': desc_thread(fam, row)}
    return thread_ref(fam, row)


def press_stack_kinds(fam):
    """Catalog kinds the stack may add on this PEM, in dropdown order."""
    if kind(fam) != 'press-in':
        return ()
    if fam['code'] in _PEM_SCREW:
        return ('screw',)
    if fam['code'] in _PEM_STUD:
        return ('nut', 'washer')
    return ()


def press_stack_sides(fam):
    """'near' is the install face. 'far' is the other end (stud thread, or the open end of a standoff)."""
    if kind(fam) != 'press-in':
        return ()
    if fam['code'] in ('SO', 'SOS'):
        return ('near', 'far')
    if fam['code'] in ('BSO', 'BSOS', 'FH', 'FHS', 'FH4'):
        return ('far',)
    if fam['code'] in _PEM_SCREW:
        return ('near',)
    return ()


def press_thread_depth(fam, row, length):
    """Blind full-thread depth F in mm, or None when the mating screw is not limited by a blind hole."""
    if fam.get('code') not in ('BSO', 'BSOS'):
        return None
    return float(_at(row['dims'], 'F', length))


def fitting_screw_length(pem_fam, pem_row, pem_length, screw_row):
    """A catalog screw length that fits this PEM. Blind holes use the longest length that stays within F."""
    lengths = [L for L in screw_row['lengths'] if not isinstance(L, str)]
    if not lengths:
        return screw_row['lengths'][0]
    limit = press_thread_depth(pem_fam, pem_row, pem_length)
    if limit is None:
        return lengths[0]
    fit = [L for L in lengths if float(L) <= float(limit) + 1e-9]
    return fit[-1] if fit else lengths[0]


def press_stack_issues(cat, pem, mates):
    """(index, reason) for mates that cannot stack on this PEM. An empty list means every mate is allowed.
    Thread size and pitch must match. A washer matches the diameter only, the same as the rest of the tool."""
    fam, row = pem['fam'], pem['row']
    kinds = press_stack_kinds(fam)
    sides = press_stack_sides(fam)
    limit = press_thread_depth(fam, row, pem.get('length'))
    seen = set()
    out = []
    pref = mate_thread(fam, row)
    for i, mate in enumerate(mates):
        side = mate.get('side') or 'near'
        mk = mate.get('kind')
        if mk not in kinds:
            if kinds == ('screw',):
                out.append((i, 'only a mating screw stacks on this PEM'))
            else:
                out.append((i, 'only a nut or washer stacks on this stud'))
            continue
        if side not in sides:
            out.append((i, 'that end does not take a stacked part'))
            continue
        if not same_thread(pref, mate_thread(mate['fam'], mate['row'])):
            out.append((i, 'thread does not match'))
            continue
        if mk == 'screw':
            if side in seen:
                out.append((i, 'only one screw on that end'))
                continue
            seen.add(side)
            if limit is not None:
                length = mate.get('length')
                if length is None or float(length) > float(limit) + 1e-9:
                    out.append((i, 'screw is longer than the blind thread depth'))
    return out


def press_mate_places(pem, mates):
    """Where each allowed mate sits. offset_cm and distance_cm are centimetres.
    end 'out': on the install face, this far out from that face.
    end 'tip': at the far end of the standoff body (distance_cm from the install face).
    end 'sheet-far': on the far face of the sheet; offset_cm stacks the nut or washer outward."""
    fam, row, length = pem['fam'], pem['row'], pem.get('length')
    bad = {i for i, _ in press_stack_issues(None, pem, mates)}
    g = press_geometry(fam, row, length)
    out_base = g.get('head_h', 0.0) if fam['shape'] in ('clinch-nut', 'floating') else 0.0
    far_at = 0.0
    places = []
    for i, mate in enumerate(mates):
        if i in bad:
            continue
        side = mate.get('side') or 'near'
        if side == 'near':
            places.append({'index': i, 'end': 'out', 'offset_cm': out_base})
        elif fam['code'] in _PEM_STUD:
            places.append({'index': i, 'end': 'sheet-far', 'offset_cm': far_at})
            if mate['kind'] in ('nut', 'washer'):
                far_at += part_geometry(mate['fam'], mate['row'])['thickness']
        else:
            places.append({'index': i, 'end': 'tip', 'distance_cm': g['L']})
    return places
