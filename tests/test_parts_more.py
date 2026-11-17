"""More nuts and washers: catalog rows spot-checked against the McMaster-Carr 18-8 listings read 2026-11-16
(see docs/SOURCES.md for the URLs), plus finishes, BOM text and geometry for the new shapes."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'SRFastener'))
import fastener_core as fc  # noqa: E402

CAT = fc.load_catalog()


def fam(code):
    return fc.family(CAT, code)


def row(code, size):
    return fc.size_row(fam(code), size)


def d(code, size):
    return row(code, size)['dims']


def close(a, b, tol=1e-4):
    return abs(a - b) < tol


def test_inch_flange_nuts_mcmaster():
    assert d('NFL-I', '1/4') == {'s': 0.5, 'm': 0.3125, 'dc': 0.625, 'c': 0.09}  # 94758A028
    assert d('NFL-I', '#10-32') == {'s': 0.375, 'm': 0.3125, 'dc': 0.5, 'c': 0.06}  # 94758A105
    assert close(d('NSF-I', '3/8')['m'], 11 / 32) and d('NSF-I', '3/8')['dc'] == 0.75  # 93776A461
    assert '1/2-20' not in [r['size'] for r in fam('NSF-I')['sizes']]


def test_top_lock_and_thin_nylon():
    assert d('NTL-M', 'M8') == {'s': 13.0, 'm': 6.4}  # 90045A115
    assert close(d('NTL-I', '3/8-24')['m'], 21 / 64)  # 90045A461
    assert close(d('NTN-I', '#8')['m'], 11 / 64)  # 90101A009
    assert fc.finishes_for(CAT, fam('NTN-I'), row('NTN-I', '#8')) == ['SS', 'SS-BO']
    assert fc.finishes_for(CAT, fam('NTN-I'), row('NTN-I', '3/8-24')) == ['SS', 'SS-BO']  # 90101A124
    assert fc.finishes_for(CAT, fam('NTN-I'), row('NTN-I', '1/4-28')) == ['SS', 'SS-BO']


def test_coupling_nuts():
    assert d('NCP-M', 'M6') == {'s': 10.0, 'm': 18.0}  # 93590A106, DIN 6334
    assert d('NCP-M', 'M20') == {'s': 30.0, 'm': 60.0}
    assert fc.finishes_for(CAT, fam('NCP-M'), row('NCP-M', 'M16')) == ['SS', 'SS-BO']
    assert d('NCP-I', '1/4') == {'s': 0.375, 'm': 0.875}  # 90268A029 product page: width 3/8, length 7/8


def test_cap_wing_square():
    assert d('NCA-M', 'M8') == {'s': 13.0, 'm': 15.0, 'dp': 10.7}  # 94000A039
    assert close(d('NCA-I', '1/4')['m'], 15 / 32) and d('NCA-I', '1/4')['dp'] == 0.25  # 91855A520
    assert fc.finishes_for(CAT, fam('NCA-I'), row('NCA-I', '1/4-28')) == ['SS', 'SS-BO']
    assert d('NWG-M', 'M6') == {'s': None, 'm': 12.7, 'w': 26.3, 'db': 13.0}  # 94545A230, DIN 315
    assert d('NWG-I', '1/4')['w'] == 1.125  # 92001A321
    assert d('NSQ-M', 'M10') == {'s': 17.0, 'm': 8.0}  # 90225A104
    assert close(d('NSQ-I', '1/2')['s'], 13 / 16) and close(d('NSQ-I', '1/2')['m'], 7 / 16)  # 94785A427


def test_new_washers():
    assert d('WTK-M', 'M8') == {'d1': 8.4, 'd2': 21.0, 't': 4.0}  # 97310A132, DIN 7349
    assert d('WTE-I', '1/4') == {'d1': 0.256, 'd2': 0.510, 't': 0.0255}  # 95584A207
    assert d('WTI-I', '#10') == {'d1': 0.195, 'd2': 0.381, 't': 0.021}  # 91757A107
    assert fc.finishes_for(CAT, fam('WTE-I'), row('WTE-I', '1/2')) == ['SS', 'SS-BO']
    assert d('WOV-I', '1/4') == {'d1': 0.281, 'd2': 1.25, 't': 0.05}  # 90313A108


def test_bom_text():
    f = fam('NWG-M')
    assert fc.part_number(f, row('NWG-M', 'M6'), None, 'SS') == 'NWG-M6-1 18-8 SS'
    assert fc.description(CAT, f, row('NWG-M', 'M6'), None, 'SS').startswith(
        'Wing nut, McMaster 94545A, M6 x 1, 26.3 mm wide x 12.7 mm high, 13 mm base')
    assert fc.part_number(fam('NCA-I'), row('NCA-I', '#10-32'), None, 'SS-BO') == 'NCA-10-32 18-8 SS-BO'


def test_new_shape_geometry():
    g = fc.part_geometry(fam('NCA-M'), row('NCA-M', 'M8'))
    assert close(g['dome_r'], 0.65) and close(g['hex_h'], 1.5 - 0.65) and close(g['bore_depth'], 1.07)
    assert g['bore_depth'] < g['height']
    w = fc.part_geometry(fam('NWG-M'), row('NWG-M', 'M6'))
    assert close(w['wing_w'], 2.63) and close(w['base_r'], 0.65) and close(w['thickness'], 1.27)
    s = fc.part_geometry(fam('NSQ-M'), row('NSQ-M', 'M6'))
    assert close(s['across_flats'], 1.0) and close(s['height'], 0.5)
