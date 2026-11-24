"""Builds one screw as a temporary B-Rep body (Fusion API). Numbers come from fastener_core.geometry()."""
import math

import adsk.core
import adsk.fusion

from . import fastener_core as fc

_EPS = 0.0005  # cm; lets the socket cutter break through the top face cleanly
_TIP_R = 0.0005  # cm; pointed tips end in a 0.01 mm flat so the cone stays a valid solid


def _p(x, y, z):
    return adsk.core.Point3D.create(x, y, z)


def _cyl(tbm, z0, r0, z1, r1):
    return tbm.createCylinderOrCone(_p(0, 0, z0), r0, _p(0, 0, z1), r1)


def _hex_prism(tbm, across_flats, z0, z1):
    """Hexagonal prism on the z axis: three slabs of width `across_flats` at 0/60/120 deg, intersected."""
    h = z1 - z0
    centre = _p(0, 0, (z0 + z1) / 2.0)
    body = None
    for k in range(3):
        a = math.radians(60.0 * k)
        length_dir = adsk.core.Vector3D.create(math.cos(a), math.sin(a), 0)
        width_dir = adsk.core.Vector3D.create(-math.sin(a), math.cos(a), 0)
        box = adsk.core.OrientedBoundingBox3D.create(centre, length_dir, width_dir, across_flats * 4.0, across_flats, h)
        slab = tbm.createBox(box)
        if body is None:
            body = slab
        else:
            tbm.booleanOperation(body, slab, adsk.fusion.BooleanTypes.IntersectionBooleanType)
    return body


def _cut_socket(tbm, body, key, depth, z_top):
    cutter = _hex_prism(tbm, key, z_top - depth, z_top + _EPS)
    tbm.booleanOperation(body, cutter, adsk.fusion.BooleanTypes.DifferenceBooleanType)


def _box(tbm, cx, cy, cz, lx, ly, lz, angle_deg=0.0):
    a = math.radians(angle_deg)
    length_dir = adsk.core.Vector3D.create(math.cos(a), math.sin(a), 0)
    width_dir = adsk.core.Vector3D.create(-math.sin(a), math.cos(a), 0)
    return tbm.createBox(adsk.core.OrientedBoundingBox3D.create(_p(cx, cy, cz), length_dir, width_dir, lx, ly, lz))


def _dome_head(tbm, g):
    """Domed head (button or pan): sphere from fastener_core.dome() clipped to the head cylinder."""
    body = tbm.createSphere(_p(0, 0, g['dome_zc']), g['dome_r'])
    tbm.booleanOperation(body, _cyl(tbm, 0.0, g['head_r'], g['head_h'] + _EPS, g['head_r']),
                         adsk.fusion.BooleanTypes.IntersectionBooleanType)
    return body


def _cut_slot(tbm, body, width, depth, z_top, span):
    cutter = _box(tbm, 0, 0, z_top - depth / 2.0 + _EPS / 2.0, span, width, depth + _EPS)
    tbm.booleanOperation(body, cutter, adsk.fusion.BooleanTypes.DifferenceBooleanType)


def _cut_cross(tbm, body, m, depth, z_top):
    """Cross recess, simplified: two crossed slots m long (ISO 7045 'm', recess diameter at the top) and
    m/5 wide, cut to the mean gauge penetration depth. The true ISO 4757 wing shape is not modeled."""
    for ang in (0.0, 90.0):
        cutter = _box(tbm, 0, 0, z_top - depth / 2.0 + _EPS / 2.0, m, m / 5.0, depth + _EPS, ang)
        tbm.booleanOperation(body, cutter, adsk.fusion.BooleanTypes.DifferenceBooleanType)


def build_body(fam, row, length):
    """Return a TemporaryBRepManager body for the screw, seat plane at z=0 (see fastener_core.geometry)."""
    tbm = adsk.fusion.TemporaryBRepManager.get()
    g = fc.geometry(fam, row, length)
    r, L = g['r'], g['L']
    union = adsk.fusion.BooleanTypes.UnionBooleanType
    head = g['head']
    if head == 'cap':
        body = _cyl(tbm, 0.0, g['head_r'], g['head_h'], g['head_r'])
        tbm.booleanOperation(body, _cyl(tbm, 0.0, r, -L, r), union)
        _cut_socket(tbm, body, g['key'], g['key_depth'], g['head_h'])
    elif head == 'button':
        body = _dome_head(tbm, g)
        tbm.booleanOperation(body, _cyl(tbm, 0.0, r, -L, r), union)
        _cut_socket(tbm, body, g['key'], g['key_depth'], g['head_h'])
    elif head == 'flbutton':
        body = _cyl(tbm, 0.0, g['flange_r'], g['flange_t'], g['flange_r'])
        crown = tbm.createSphere(_p(0, 0, g['dome_zc']), g['dome_r'])
        tbm.booleanOperation(crown, _cyl(tbm, g['flange_t'] - _EPS, g['head_r'], g['head_h'] + _EPS, g['head_r']),
                             adsk.fusion.BooleanTypes.IntersectionBooleanType)
        tbm.booleanOperation(body, crown, union)
        tbm.booleanOperation(body, _cyl(tbm, 0.0, r, -L, r), union)
        _cut_socket(tbm, body, g['key'], g['key_depth'], g['head_h'])
    elif head == 'pan':
        if g.get('flat_top'):
            body = _cyl(tbm, 0.0, g['head_r'], g['head_h'], g['head_r'])
        else:
            body = _dome_head(tbm, g)
        if g.get('point') == 'tapping':
            tip = -L + g['point_h']
            tbm.booleanOperation(body, _cyl(tbm, 0.0, r, tip, r), union)
            tbm.booleanOperation(body, _cyl(tbm, tip, r, -L, _TIP_R), union)
        else:
            tbm.booleanOperation(body, _cyl(tbm, 0.0, r, -L, r), union)
        _cut_cross(tbm, body, g['recess_m'], g['recess_depth'], g['head_h'])
    elif head == 'cheese':
        body = _cyl(tbm, 0.0, g['head_r'], g['head_h'], g['head_r'])
        tbm.booleanOperation(body, _cyl(tbm, 0.0, r, -L, r), union)
        _cut_slot(tbm, body, g['slot_w'], g['slot_depth'], g['head_h'], g['head_r'] * 2.0 + 0.1)
    elif head == 'flat':
        body = _cyl(tbm, 0.0, g['head_r'], -g['cone_h'], r)
        tbm.booleanOperation(body, _cyl(tbm, -g['cone_h'], r, -L, r), union)
        _cut_socket(tbm, body, g['key'], g['key_depth'], 0.0)
    elif head == 'hex':
        body = _hex_prism(tbm, g['across_flats'], 0.0, g['head_h'])
        tbm.booleanOperation(body, _cyl(tbm, 0.0, r, -L, r), union)
    elif head == 'set':
        tip = -L + g['point_h']
        body = _cyl(tbm, 0.0, r, tip, r)
        if g.get('point') == 'dog':
            z0 = -L + g['dog_z']
            tbm.booleanOperation(body, _cyl(tbm, tip, g['root_r'], z0, g['point_r']), union)
            tbm.booleanOperation(body, _cyl(tbm, z0, g['point_r'], -L, g['point_r']), union)
        elif g.get('point') == 'oval':
            ball = tbm.createSphere(_p(0, 0, -L + g['oval_R']), g['oval_R'])
            tbm.booleanOperation(ball, _cyl(tbm, -L - _EPS, r, tip + _EPS, r), adsk.fusion.BooleanTypes.IntersectionBooleanType)
            tbm.booleanOperation(body, ball, union)
        elif g['point_h'] > 0:
            top_r = g['root_r'] if g.get('point') == 'cone' else r
            tbm.booleanOperation(body, _cyl(tbm, tip, top_r, -L, max(g['point_r'], _TIP_R)), union)
        if g.get('point') == 'cup':
            cup = _cyl(tbm, -L - _EPS, g['cup_r'], -L + g['cup_depth'], 0.0)
            tbm.booleanOperation(body, cup, adsk.fusion.BooleanTypes.DifferenceBooleanType)
        _cut_socket(tbm, body, g['key'], g['key_depth'], 0.0)
    else:
        raise ValueError(head)
    return body


def build_part_body(fam, row):
    """Nut or washer as one temporary BRep body. z=0 is the seat face, body goes +z (see fastener_core.part_geometry).
    Simplified where the catalog has no dimension: nylon insert drawn as part of the hex, flange serrations and
    lock-washer teeth not drawn, split-washer gap = thickness and flat (not helical), cap-nut dome a half sphere,
    wing-nut wings a flat plate."""
    tbm = adsk.fusion.TemporaryBRepManager.get()
    g = fc.part_geometry(fam, row)
    diff = adsk.fusion.BooleanTypes.DifferenceBooleanType
    union = adsk.fusion.BooleanTypes.UnionBooleanType
    inter = adsk.fusion.BooleanTypes.IntersectionBooleanType
    bore_top = g['height'] + _EPS
    if g['kind'] == 'nut' and g['shape'] == 'square':
        s = g['across_flats']
        body = _box(tbm, 0, 0, g['height'] / 2.0, s, s, g['height'])
    elif g['kind'] == 'nut' and g['shape'] == 'cap':
        body = _hex_prism(tbm, g['across_flats'], 0.0, g['hex_h'])
        dome = tbm.createSphere(_p(0, 0, g['hex_h']), g['dome_r'])
        tbm.booleanOperation(dome, _cyl(tbm, g['hex_h'] - _EPS, g['dome_r'], g['height'], g['dome_r']), inter)
        tbm.booleanOperation(body, dome, union)
        bore_top = g['bore_depth']
    elif g['kind'] == 'nut' and g['shape'] == 'wing':
        body = _cyl(tbm, 0.0, g['base_r'], g['base_h'], g['base_r'])
        tbm.booleanOperation(body, _box(tbm, 0, 0, g['height'] / 2.0, g['wing_w'], g['wing_t'], g['height']), union)
    elif g['kind'] == 'nut':
        body = _hex_prism(tbm, g['across_flats'], 0.0, g['height'])
        if g['shape'] == 'flange':
            tbm.booleanOperation(body, _cyl(tbm, 0.0, g['flange_r'], g['flange_t'], g['flange_r']), union)
    else:
        body = _cyl(tbm, 0.0, g['outer_r'], g['height'], g['outer_r'])
    tbm.booleanOperation(body, _cyl(tbm, -_EPS, g['bore_r'], bore_top, g['bore_r']), diff)
    if g.get('gap'):
        span = g['outer_r'] - g['bore_r'] + 2 * _EPS
        cx = (g['outer_r'] + g['bore_r']) / 2.0
        tbm.booleanOperation(body, _box(tbm, cx, 0, g['height'] / 2.0, span, g['gap'], g['height'] + 2 * _EPS), diff)
    return body, g


# Not a published shank length. Standoff clinch length is not in the bulletin, so this only
# gives the joint a round edge at the published clinch diameter C.
_SEAT = 0.01  # cm


def _union_profile(tbm, pts):
    """Solid of revolution from (z, r) points. A point at the same z only steps the radius."""
    union = adsk.fusion.BooleanTypes.UnionBooleanType
    body = None
    z0, r0 = pts[0]
    for z1, r1 in pts[1:]:
        if abs(z1 - z0) < 1e-9:
            z0, r0 = z1, r1
            continue
        seg = _cyl(tbm, z0, max(r0, 1e-5), z1, max(r1, 1e-5))
        if body is None:
            body = seg
        else:
            tbm.booleanOperation(body, seg, union)
        z0, r0 = z1, r1
    return body


def build_press_body(fam, row, length):
    """Press-in part. z=0 is the install face (see fastener_core.press_geometry).
    A flush stud is the measured head profile revolved to the length code.
    A floating nut keeps the catalog body and leaves the bulletin float gap around the captive nut.
    Returns one body, or a list of bodies when the captive nut is separate."""
    tbm = adsk.fusion.TemporaryBRepManager.get()
    g = fc.press_geometry(fam, row, length)
    union = adsk.fusion.BooleanTypes.UnionBooleanType
    diff = adsk.fusion.BooleanTypes.DifferenceBooleanType
    if g['shape'] == 'clinch-nut':
        body = _cyl(tbm, 0.0, g['head_r'], g['head_h'], g['head_r'])
        tbm.booleanOperation(body, _cyl(tbm, 0.0, g['shank_r'], -g['shank_l'], g['shank_r']), union)
        tbm.booleanOperation(body, _cyl(tbm, -g['shank_l'] - _EPS, g['bore_r'], g['head_h'] + _EPS, g['bore_r']), diff)
    elif g['shape'] == 'floating':
        retainer = _cyl(tbm, 0.0, g['head_r'], g['head_h'], g['head_r'])
        tbm.booleanOperation(retainer, _cyl(tbm, 0.0, g['shank_r'], -g['shank_l'], g['shank_r']), union)
        tbm.booleanOperation(retainer, _cyl(tbm, -_EPS, g['bore_r'], -g['shank_l'] - _EPS, g['bore_r']), diff)
        # Widen only the body so the captive nut has 0.38 mm radial clearance. The shank hole stays the thread minor.
        tbm.booleanOperation(retainer, _cyl(tbm, -_EPS, g['retainer_bore_r'], g['head_h'] + _EPS, g['retainer_bore_r']), diff)
        nut = _cyl(tbm, 0.0, g['nut_r'], g['head_h'], g['nut_r'])
        tbm.booleanOperation(nut, _cyl(tbm, -_EPS, g['bore_r'], g['head_h'] + _EPS, g['bore_r']), diff)
        return [retainer, nut]
    elif g['shape'] == 'stud':
        body = _union_profile(tbm, fc.stud_profile(fam, row, length))
        # Tip recess: 60 deg from the axis (120 deg included), opening radius 0.075 x major.
        depth = g['tip_recess_r'] / math.sqrt(3.0)
        recess = _cyl(tbm, -g['L'] - _EPS, g['tip_recess_r'], -g['L'] + depth, _TIP_R)
        tbm.booleanOperation(body, recess, diff)
    elif g['shape'] == 'standoff':
        body = _hex_prism(tbm, g['across'], -g['L'], 0.0)
        tbm.booleanOperation(body, _cyl(tbm, 0.0, g['seat_r'], -_SEAT, g['seat_r']), union)
        if g.get('blind'):
            tbm.booleanOperation(body, _cyl(tbm, -g['L'] - _EPS, g['bore_r'], -g['L'] + g['blind'], g['bore_r']), diff)
        else:
            tbm.booleanOperation(body, _cyl(tbm, -g['L'] - _EPS, g['bore_r'], _EPS, g['bore_r']), diff)
    else:
        raise ValueError(g['shape'])
    return body
