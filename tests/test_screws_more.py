"""Cone, extended and oval tip set screws, flanged button head and Phillips sheet metal screws:
spot checks against McMaster-Carr and the cited standards, BOM text, and geometry that fits inside the length."""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'SRFastener'))
import fastener_core as fc  # noqa: E402

CAT = fc.load_catalog()
NEW = ('SSN-M', 'SSN-I', 'SSE-M', 'SSE-I', 'SSO-I', 'SBF-M', 'STP-I', 'STP-M')


def fam(code):
    return fc.family(CAT, code)


def row(code, size):
    return fc.size_row(fam(code), size)


def test_new_families_listed():
    codes = {f['code'] for f in CAT['families']}
    assert set(NEW) <= codes


def test_mcmaster_spot_checks():
    # cone tip: McMaster 92785A433 1/4-20 x 1/4 has a 118 deg cone, 92785A435 x 3/8 has 90 deg; drive 1/8
    r = row('SSN-I', '1/4')
    assert r['dims']['angle_by_length']['0.25'] == 118 and r['dims']['angle_by_length']['0.375'] == 90
    assert r['dims']['s'] == 0.125
    # metric cone: ISO 4027 dt M6 = 1.5, socket 3; McMaster M6 x 6 is 120 deg (short socket 2.0, ISO t min)
    m = row('SSN-M', 'M6')
    assert m['dims']['tip_d'] == 1.5 and m['dims']['s'] == 3.0 and 't_by_length' not in m['dims']
    # extended tip: McMaster #10-32 tip 0.127 x 0.049 (Holo-Krome half dog P, Q max 0.127, 0.049)
    e = row('SSE-I', '#10-32')
    assert e['dims']['dp'] == 0.127 and e['dims']['z_by_length']['0.5'] == 0.049
    # metric extended: M6 x 8 short tip 1.75, M6 x 10 long tip 3.25 (ISO 4028 z max), dp 4
    em = row('SSE-M', 'M6')
    assert em['dims']['z_by_length']['8'] == 1.75 and em['dims']['z_by_length']['10'] == 3.25
    assert 't' not in em['dims']
    # oval: Holo-Krome Table 13 R #6 = 0.104
    assert row('SSO-I', '#6')['dims']['R'] == 0.104
    # flanged button: McMaster M5 11.8 flange, 8.8 head, 2.75 high; ISO 7380-2 c 1.0, s 3, t 1.56
    f = row('SBF-M', 'M5')['dims']
    assert (f['dc'], f['dk'], f['k'], f['c'], f['s']) == (11.8, 8.8, 2.75, 1.0, 3.0) and 't' not in f
    # sheet metal: McMaster No. 8 0.322 x 0.115, 15 threads per inch; B18.6.3 recess M 0.175
    s = row('STP-I', '#8')
    assert (s['dims']['dk'], s['dims']['k'], s['tpi'], s['dims']['m']) == (0.322, 0.115, 15, 0.175)
    assert fc.finishes_for(CAT, fam('STP-I'), row('STP-I', '#4'))[:2] == ['SS', 'SS-BO']
    sm = row('STP-M', 'M4.2')
    assert (sm['dims']['dk'], sm['dims']['k'], sm['pitch'], sm['dims']['tip']) == (8.2, 3.1, 1.4, 3.7)


def test_lengths_are_mcmaster_stock():
    assert row('SSN-M', 'M5')['lengths'] == [5.0, 6.0, 8.0, 10.0, 12.0, 30.0]
    assert row('SBF-M', 'M10')['lengths'] == [12.0, 16.0, 35.0, 40.0]
    assert row('STP-M', 'M2.2')['lengths'] == [6.5, 9.5, 13.0, 16.0]
    assert 0.125 in row('SSN-I', '#2')['lengths']


def test_bom_text():
    assert fc.part_number(fam('SSN-I'), row('SSN-I', '1/4'), 0.5, 'SS') == 'SSN-1/4-20 x 0.5 18-8 SS'
    assert fc.part_number(fam('SBF-M'), row('SBF-M', 'M5'), 10, 'SS') == 'SBF-M5-0.8 x 10 18-8 SS'
    assert fc.part_number(fam('STP-I'), row('STP-I', '#8'), 0.5, 'SS-BO') == 'STP-8-15 x 0.5 18-8 SS-BO'
    assert fc.part_number(fam('STP-M'), row('STP-M', 'M2.9'), 9.5, 'SS') == 'STP-M2.9-1.1 x 9.5 18-8 SS'
    d = fc.description(CAT, fam('STP-I'), row('STP-I', '#8'), 0.5, 'SS')
    assert d == 'Phillips Rounded Head Sheet Metal Screw, #8-15, 18-8 Stainless Steel'
    assert fc.thread_spec(fam('STP-M'), row('STP-M', 'M4.2')) is None
    for code in NEW:
        for r in fam(code)['sizes']:
            assert fc.finishes_for(CAT, fam(code), r)[:2] == ['SS', 'SS-BO']


def test_geometry_fits_every_length():
    for code in NEW:
        f = fam(code)
        for r in f['sizes']:
            for L in r['lengths']:
                g = fc.geometry(f, r, L)
                assert g['L'] > 0
                if f['head'] == 'set':
                    # socket plus point stays inside the screw
                    assert g['key_depth'] + g['point_h'] < g['L'], (code, r['size'], L)
                    assert 0 <= g['point_r'] < g['r']
                if g.get('point') == 'tapping':
                    assert g['point_h'] < g['L'], (code, r['size'], L)
                if f['head'] == 'flbutton':
                    assert g['flange_r'] > g['head_r'] > g['r'] and g['key_depth'] < g['head_h']
                    # the crown passes through the head edge at the flange top or above
                    edge_z = g['dome_zc'] + math.sqrt(g['dome_r'] ** 2 - g['head_r'] ** 2)
                    assert edge_z >= g['flange_t'] - 1e-9 and abs(g['dome_zc'] + g['dome_r'] - g['head_h']) < 1e-9


def test_point_shapes():
    g = fc.geometry(fam('SSN-I'), row('SSN-I', '1/4'), 0.5)
    # 90 deg cone from the thread root (0.25 - 1.082532/20) to a point: height = root radius
    assert g['cone_angle'] == 90 and abs(g['point_h'] - (0.25 - 1.082532 / 20) * 2.54 / 2) < 1e-12
    g = fc.geometry(fam('SSE-M'), row('SSE-M', 'M6'), 10)
    assert abs(g['dog_z'] - 0.325) < 1e-12 and abs(g['point_r'] - 0.2) < 1e-12
    assert abs(g['point_h'] - (0.325 + (6 - 1.082532) / 20 - 0.2)) < 1e-12
    g = fc.geometry(fam('SSO-I'), row('SSO-I', '#6'), 0.25)
    R, r = g['oval_R'], g['r']
    assert abs(g['point_h'] - (R - math.sqrt(R * R - r * r))) < 1e-12


def test_short_set_screw_sockets_clear_the_point():
    """The hex pocket stops short of the point. Depth is not a published spec."""
    for code, size, L in [('SSN-I', '#2', 0.125), ('SSN-I', '#6', 0.1875), ('SSN-I', '5/16', 0.375),
                          ('SSN-I', '5/16-24', 0.375), ('SSN-I', '3/8', 0.375), ('SSN-I', '3/8-24', 0.375),
                          ('SSE-I', '#2', 0.125), ('SSE-I', '3/8', 0.375), ('SSE-I', '3/8-24', 0.375),
                          ('SSE-I', '1/2', 0.625), ('SSO-I', '#6', 0.1875)]:
        r = row(code, size)
        assert L in r['lengths'], (code, size, L)
        g = fc.geometry(fam(code), r, L)
        assert g['key_depth'] > 0 and g['key_depth'] + g['point_h'] < g['L'], (code, size, L)
        assert abs(g['key'] - fc.to_cm(fam(code), r['dims']['s'])) < 1e-9
