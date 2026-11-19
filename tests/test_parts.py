"""Nuts and washers: catalog values against McMaster-Carr 18-8 listings and the standards/maker sheets
(read 2026-11-16, see docs/SOURCES.md), plus part numbers, descriptions, finishes and geometry."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'SRFastener'))
import fastener_core as fc  # noqa: E402

CAT = fc.load_catalog()


def row(code, size):
    return fc.size_row(fc.family(CAT, code), size)


def d(code, size):
    return row(code, size)['dims']


def test_kinds_listed_separately():
    screws = fc.families(CAT)
    assert all(fc.kind(f) == 'screw' for f in screws)
    nuts = {f['code'] for f in fc.families(CAT, kind_='nut')}
    washers = {f['code'] for f in fc.families(CAT, kind_='washer')}
    assert nuts == {'NHX-M', 'NTH-M', 'NNL-M', 'NFL-M', 'NSF-M', 'NHX-I', 'NTH-I', 'NNL-I',
                    'NFL-I', 'NSF-I', 'NTL-M', 'NTL-I', 'NTN-I', 'NCP-M', 'NCP-I', 'NCA-M', 'NCA-I',
                    'NWG-M', 'NWG-I', 'NSQ-M', 'NSQ-I'}
    assert washers == {'WGP-M', 'WOV-M', 'WSL-M', 'WTE-M', 'WTI-M', 'WSA-I', 'WUS-I', 'WSL-I',
                       'WTK-M', 'WTE-I', 'WTI-I', 'WOV-I'}


def test_mcmaster_names():
    names = {p['code']: p['mcmaster'] for p in CAT['parts']}
    assert names['NHX-M'] == names['NHX-I'] == 'Hex Nuts'
    assert names['NTH-M'] == 'Thin-Profile Hex Nuts'
    assert names['NNL-I'] == 'Nylon-Insert Locknuts'
    assert names['NSF-M'] == 'Serrated Flange Nuts'
    assert names['WGP-M'] == 'General Purpose Washers'
    assert names['WSL-I'] == 'Split Lock Washers'
    for p in CAT['parts']:
        assert p['mcmaster_url'].startswith('https://'), p['code']


def test_hex_nut_din934_mcmaster():  # McMaster 18-8 metric hex nuts (DIN 934): width, height
    assert d('NHX-M', 'M3') == {'s': 5.5, 'm': 2.4}
    assert d('NHX-M', 'M5') == {'s': 8.0, 'm': 4.0}
    assert d('NHX-M', 'M10') == {'s': 17.0, 'm': 8.0}
    assert d('NHX-M', 'M20') == {'s': 30.0, 'm': 16.0}


def test_hex_nut_inch_mcmaster():  # McMaster 18-8 hex nuts: 4-40 1/4 x 3/32, 1/4-20 7/16 x 7/32, 1/2-13 3/4 x 7/16
    assert d('NHX-I', '#4') == {'s': 0.25, 'm': round(3 / 32, 4)}
    assert d('NHX-I', '1/4') == {'s': round(7 / 16, 4), 'm': round(7 / 32, 4)}
    assert d('NHX-I', '1/2') == {'s': 0.75, 'm': round(7 / 16, 4)}
    assert row('NHX-I', '#10-32')['tpi'] == 32


def test_thin_nut():  # McMaster DIN 439 B / ISO 4035: M6 10 x 3.2, M12 19 x 6; 3/8 9/16 x 7/32
    assert d('NTH-M', 'M6') == {'s': 10.0, 'm': 3.2}
    assert d('NTH-M', 'M12') == {'s': 19.0, 'm': 6.0}
    assert d('NTH-I', '3/8') == {'s': round(9 / 16, 4), 'm': round(7 / 32, 4)}


def test_nylon_locknut():  # McMaster and Brighton-Best DIN 985: M8 13 x 8, M10 17 x 10; 1/4-20 7/16 x 5/16
    assert d('NNL-M', 'M8') == {'s': 13.0, 'm': 8.0}
    assert d('NNL-M', 'M10') == {'s': 17.0, 'm': 10.0}
    assert d('NNL-I', '1/4') == {'s': round(7 / 16, 4), 'm': round(5 / 16, 4)}
    assert d('NNL-I', '#8') == {'s': round(11 / 32, 4), 'm': round(15 / 64, 4)}


def test_flange_nuts():  # ISO 4161 Table 1 M8: s 13, m 8, dc 17.9, c 1.2; McMaster M3 5.5/4/8/1
    assert d('NFL-M', 'M8') == {'s': 13.0, 'm': 8.0, 'dc': 17.9, 'c': 1.2}
    assert d('NSF-M', 'M12') == {'s': 18.0, 'm': 12.0, 'dc': 26.0, 'c': 1.8}
    assert d('NFL-M', 'M3') == {'s': 5.5, 'm': 4.0, 'dc': 8.0, 'c': 1.0}
    assert d('NSF-M', 'M4')['m'] == 4.65


def test_washers_metric():  # ISO 7089 M6 6.4/12/1.6; ISO 7093-1 M8 8.4/24/2; McMaster split M5 5.4/9.2/1.1-1.3
    assert d('WGP-M', 'M6') == {'d1': 6.4, 'd2': 12.0, 't': 1.6}
    assert d('WOV-M', 'M8') == {'d1': 8.4, 'd2': 24.0, 't': 2.0}
    assert d('WSL-M', 'M5') == {'d1': 5.4, 'd2': 9.2, 't': 1.2}
    assert d('WTE-M', 'M4') == {'d1': 4.3, 'd2': 8.0, 't': 0.5}  # DIN 6797 A, s 0.4-0.6
    assert d('WTI-M', 'M10') == {'d1': 10.5, 'd2': 18.0, 't': 0.9}


def test_washers_inch():  # McMaster SAE 1/4 .281/.625; USS 1/4 .312/.750; split #10 .200/.334/.047
    assert d('WSA-I', '1/4') == {'d1': 0.281, 'd2': 0.625, 't': 0.065}
    assert d('WUS-I', '1/4') == {'d1': 0.312, 'd2': 0.750, 't': 0.065}
    assert d('WSL-I', '#10') == {'d1': 0.200, 'd2': 0.334, 't': 0.047}


def test_black_oxide_only_where_stocked():
    fin = lambda c, s: fc.finishes_for(CAT, fc.family(CAT, c), row(c, s))  # noqa: E731
    assert fin('NHX-M', 'M6')[:2] == ['SS', 'SS-BO']
    # Daniel's rule: every nut and washer size in 18-8 SS and 18-8 SS-BO, even where McMaster has no black oxide
    assert fin('NHX-M', 'M8')[:2] == ['SS', 'SS-BO']
    assert fin('NHX-I', '#4-48')[:2] == ['SS', 'SS-BO']
    assert fin('WSL-M', 'M4')[:2] == ['SS', 'SS-BO']
    for p in CAT['parts']:
        assert p['finishes'][:2] == ['SS', 'SS-BO'], p['code']
        for r in p['sizes']:
            assert r['finishes'][:2] == ['SS', 'SS-BO'], (p['code'], r['size'])


def test_part_numbers_and_descriptions():
    def bom(code, size, fin='SS'):
        f = fc.family(CAT, code)
        return fc.bom_fields(CAT, f, fc.size_row(f, size), None, fin)
    assert bom('NHX-M', 'M5')['part_number'] == 'NHX-M5-0.8 18-8 SS'
    assert bom('NHX-I', '1/4', 'SS-BO')['part_number'] == 'NHX-1/4-20 18-8 SS-BO'
    assert bom('NNL-I', '#10-32')['part_number'] == 'NNL-10-32 18-8 SS'
    # washers: screw size and OD in the part number (Daniel 2026-11-17); ISO 7089 M5 OD 10, SAE #10 OD 0.438
    assert bom('WGP-M', 'M5')['part_number'] == 'WGP-M5 x 10 18-8 SS'
    assert bom('WSA-I', '#10')['part_number'] == 'WSA-10 x %s 18-8 SS' % fc._num(row('WSA-I', '#10')['dims']['d2'])
    assert bom('NHX-M', 'M5')['description'] == 'Hex Nut, M5 x 0.8, 18-8 Stainless Steel'
    assert bom('WSL-M', 'M6')['description'] == 'Split Lock Washer, M6, 18-8 Stainless Steel'
    assert bom('WSL-M', 'M6')['part_number'] == 'WSL-M6 x 11.8 18-8 SS'
    assert bom('NHX-I', '1/4', 'GR8')['description'] == 'Hex Nut, 1/4-20, GR-8 Steel'
    assert bom('NHX-I', '1/4', 'GR8')['material'] == 'Grade 8 Steel'
    assert bom('NHX-M', 'M6', 'CL10')['description'] == 'Hex Nut, M6 x 1, CL-10 Steel'
    assert bom('NHX-M', 'M6', 'CL10')['material'] == 'Class 10 Steel'
    def screw_bom(code, size, length, fin):
        f = fc.family(CAT, code)
        return fc.bom_fields(CAT, f, fc.size_row(f, size), length, fin)
    hhb = screw_bom('HHB-I', '1/4', 1.0, 'GR8')
    assert hhb['description'] == 'Hex Head Bolt, 1/4-20, GR-8 Steel'
    assert hhb['material'] == 'Grade 8 Steel'
    ssh = screw_bom('SSH-M', 'M6', 20, 'CL10.9')
    assert ssh['description'] == 'Socket Head Screw, M6 x 1, CL-10.9 Steel'
    assert ssh['material'] == 'Class 10.9 Steel'
    assert bom('NHX-M', 'M6', 'CL10')['part_number'] == 'NHX-M6-1 CL10'
    assert bom('NHX-M', 'M8', 'SS-BO')['part_number'] == 'NHX-M8-1.25 18-8 SS-BO'
    try:
        bom('NHX-M', 'M8', 'ALLOY-BO')
        assert False, 'alloy black oxide is not offered on nuts'
    except ValueError:
        pass


def test_geometry():
    g = fc.part_geometry(fc.family(CAT, 'NFL-M'), row('NFL-M', 'M6'))
    assert abs(g['bore_r'] - 0.3) < 1e-9 and abs(g['across_flats'] - 1.0) < 1e-9
    assert abs(g['flange_r'] - 0.71) < 1e-9 and abs(g['thickness'] - 0.6) < 1e-9
    w = fc.part_geometry(fc.family(CAT, 'WSA-I'), row('WSA-I', '1/4'))
    assert abs(w['outer_r'] - 0.625 * 2.54 / 2) < 1e-9 and abs(w['thickness'] - 0.065 * 2.54) < 1e-9
    s = fc.part_geometry(fc.family(CAT, 'WSL-M'), row('WSL-M', 'M8'))
    assert s['gap'] == s['thickness']
    for p in CAT['parts']:
        for r in p['sizes']:
            g = fc.part_geometry(p, r)
            assert g['thickness'] > 0
            if p['kind'] == 'nut' and p['shape'] == 'wing':
                assert g['wing_w'] > 2 * g['base_r'] > 2 * g['bore_r'], (p['code'], r['size'])
            elif p['kind'] == 'nut':  # across flats clears the bore, flange wider than the hex
                assert g['across_flats'] > 2 * g['bore_r'], (p['code'], r['size'])
                if 'flange_r' in g:
                    assert 2 * g['flange_r'] > g['across_flats']
            else:  # washer bore clears the screw, OD wider than the bore
                assert g['outer_r'] > g['bore_r'] >= fc.to_cm(p, r['d']) / 2.0 - 1e-9, (p['code'], r['size'])


def test_designation_and_suggestion():
    assert fc.size_from_designation(fc.family(CAT, 'WSA-I'), '1/4-20 UNC') == '1/4'
    assert fc.size_from_designation(fc.family(CAT, 'NHX-I'), '10-32 UNF') == '#10-32'
    assert fc.suggest_size(CAT, fc.family(CAT, 'WGP-M'), 0.55) == 'M5'
