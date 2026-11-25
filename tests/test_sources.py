"""Spot checks: catalog values against the cited standard or maker table (one row per table at least).

Each expected value below was read from the source named in the comment on 2026-11-16.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'SRFastener'))
import fastener_core as fc  # noqa: E402

CAT = fc.load_catalog()


def dims(code, size):
    return fc.size_row(_fam(code), size)['dims']


def _fam(code):
    pools = [CAT['families'], CAT.get('pending_approval', []), CAT.get('parts', []), CAT.get('press_in', [])]
    for pool in pools:
        for f in pool:
            if f['code'] == code:
                return f
    raise KeyError(code)


def lengths(code, size):
    r = fc.size_row(_fam(code), size)['lengths']
    return r[0], r[-1]


def test_iso4762():  # ISO 4762:2004 Table 1 (dk max plain, k max, s nom). Socket depth is not stored.
    assert dims('SSH-M', 'M3') == {'dk': 5.5, 'k': 3.0, 's': 2.5}
    assert dims('SSH-M', 'M8') == {'dk': 13.0, 'k': 8.0, 's': 6.0}
    assert dims('SSH-M', 'M12') == {'dk': 18.0, 'k': 12.0, 's': 10.0}
    assert lengths('SSH-M', 'M4') == (6, 40) and lengths('SSH-M', 'M10') == (16, 100)


def test_iso7380():  # ISO 7380-1:2011 and :2022 Table 1
    d = dims('SBH-M', 'M16')
    assert (d['dk'], d['k'], d['s']) == (28.0, 8.8, 10.0) and 14.5 <= d['rf'] <= 15.3
    d = dims('SBH-M', 'M5')
    assert (d['dk'], d['k'], d['s']) == (9.5, 2.75, 3.0) and 5.25 <= d['rf'] <= 5.75
    # M3 lengths 4 and 5 are on the WASI ISO 7380-1 length grid (step before M5 at 4 mm, before M6 at 5 mm).
    # ISO 7380-1:2011 starts M3 at 6 mm. M4 is unchanged and still starts at 8 mm.
    assert lengths('SBH-M', 'M3') == (4, 30) and lengths('SBH-M', 'M4') == (8, 40)
    assert lengths('SBH-M', 'M16') == (25, 90)
    row = fc.size_row(_fam('SBH-M'), 'M3')
    assert row['lengths'][:3] == [4, 5, 6]
    assert fc.thread_length(_fam('SBH-M'), row, 4) == 4


def test_iso10642():  # ISO 10642:2004 Table 1 (dk theoretical max, k max, s nom). Socket depth is not stored.
    assert dims('SFH-M', 'M6') == {'dk': 13.44, 'k': 3.72, 's': 4.0}
    assert dims('SFH-M', 'M20') == {'dk': 40.32, 'k': 10.16, 's': 12.0}
    assert fc.family(CAT, 'SFH-M')['angle'] == 90.0
    assert lengths('SFH-M', 'M12') == (20, 100)
    # M3 x 5 is not in ISO 10642:2004 Table 1. Aspen sells that length as ISO 10642, full thread.
    assert lengths('SFH-M', 'M3') == (5, 30)
    assert fc.thread_length(_fam('SFH-M'), fc.size_row(_fam('SFH-M'), 'M3'), 5) == 5


def test_din7984():  # Brighton-Best DIN 7984; Fastener Network agrees on dk, k, s. Socket depth is not stored.
    assert dims('SLH-M', 'M4') == {'dk': 7.0, 'k': 2.8, 's': 2.5}
    assert dims('SLH-M', 'M8') == {'dk': 13.0, 'k': 5.0, 's': 5.0}
    assert dims('SLH-M', 'M16') == {'dk': 24.0, 'k': 9.0, 's': 12.0}


def test_iso4017():  # ISO 4017:2022 Table 1 (s nom = max, k nom)
    assert dims('HHB-M', 'M3') == {'s': 5.5, 'k': 2.0}
    assert dims('HHB-M', 'M8') == {'s': 13.0, 'k': 5.3}
    assert dims('HHB-M', 'M16') == {'s': 24.0, 'k': 10.0}


def test_iso4026():  # ISO 4026:2003 Table 1 (dp max, s nom). Socket depth is not stored.
    d = dims('SSF-M', 'M10')
    assert (d['dp'], d['s']) == (7.0, 5.0) and 't' not in d
    d = dims('SSF-M', 'M3')
    assert (d['dp'], d['s']) == (2.0, 1.5)
    assert lengths('SSF-M', 'M3') == (3, 16) and lengths('SSF-M', 'M12') == (12, 60)


def test_iso4032_and_10511_and_din127_m2():
    # ISO 4032:1999 Table 1 style 1, s max and m max. M3 and M4 match DIN 934 and are not repeated.
    assert dims('NHR-M', 'M2') == {'s': 4.0, 'm': 1.6}
    assert dims('NHR-M', 'M5') == {'s': 8.0, 'm': 4.7}
    assert dims('NHR-M', 'M10') == {'s': 16.0, 'm': 8.4}
    assert dims('NHR-M', 'M12') == {'s': 18.0, 'm': 10.8}
    assert dims('NHR-M', 'M20') == {'s': 30.0, 'm': 18.0}
    assert 'M3' not in [r['size'] for r in _fam('NHR-M')['sizes']]
    # ISO 10511:2012 Table 1, s max and h max (stored as the overall height).
    assert dims('NTN-M', 'M3') == {'s': 5.5, 'm': 3.9}
    assert dims('NTN-M', 'M6') == {'s': 10.0, 'm': 6.0}
    assert dims('NTN-M', 'M8') == {'s': 13.0, 'm': 6.76}
    assert dims('NTN-M', 'M10') == {'s': 16.0, 'm': 8.56}
    assert dims('NTN-M', 'M12') == {'s': 18.0, 'm': 10.23}
    # Brighton-Best DIN 127 B M2: d1 max 2.4, d2 max 4.4, thickness middle of 0.4 to 0.6.
    assert dims('WSL-M', 'M2') == {'d1': 2.4, 'd2': 4.4, 't': 0.5}


def test_no_separate_standoff_type():
    """Female-female hex standoffs are a new type. Daniel: no new types, only new sizes."""
    codes = {f['code'] for f in CAT['families'] + CAT.get('parts', []) + CAT.get('press_in', [])}
    assert 'HFF-M' not in codes
    assert all(f.get('kind') != 'standoff' for f in CAT.get('parts', []))
    # The sizes and the PEM numbers from the last pass stay.
    assert 35 in fc.size_row(_fam('SPH-M'), 'M3')['lengths']
    assert 5 in fc.size_row(_fam('SFH-M'), 'M3')['lengths']
    fhs = _fam('FHS')
    assert fc.part_number(fhs, fc.size_row(fhs, 'M3'), 8, 'PEM-SS') == 'FHS-M3-8'
    so = _fam('SO')
    assert fc.part_number(so, fc.size_row(so, 'M3'), 6, 'PEM-ZI') == 'SO-M3-6ZI'


def test_iso7045():  # pending approval, not offered
     # ISO 7045:2011 Table 1 (dk max, k max, rf ref, recess no., m ref, type H penetration mean)
    d = dims('SPH-M', 'M4')
    assert (d['dk'], d['k'], d['rf'], d['recess'], d['m']) == (8.0, 3.1, 6.5, 2, 4.4)
    assert abs(d['pen'] - (2.4 + 1.9) / 2) < 1e-9
    assert lengths('SPH-M', 'M5') == (6, 45)
    # M3 x 35 is not in the ISO 7045 length table. 3FParts sells that length fully threaded.
    assert lengths('SPH-M', 'M3') == (4, 35)
    m3 = fc.size_row(_fam('SPH-M'), 'M3')
    assert 35 in m3['lengths'] and fc.thread_length(_fam('SPH-M'), m3, 35) == 35
    assert fc.thread_length(_fam('SPH-M'), m3, 30) == 25


def test_iso1207():  # ISO 1207:2011 Table 1 (dk max, k max, n nom, t min)
    assert dims('SCH-M', 'M3') == {'dk': 5.5, 'k': 2.0, 'n': 0.8, 't': 0.85}
    assert dims('SCH-M', 'M10') == {'dk': 16.0, 'k': 6.0, 'n': 2.5, 't': 2.4}
    assert lengths('SCH-M', 'M8') == (10, 80)


def test_holo_krome_inch():  # Holo-Krome product standards (A max, H max, J nom). Socket depth is not stored.
    assert dims('SSH-I', '1/4') == {'dk': 0.375, 'k': 0.25, 's': 0.188}
    assert dims('SBH-I', '#10') == {'dk': 0.361, 'k': 0.101, 's': 0.125, 'side': 0.02}
    assert dims('SFH-I', '3/8') == {'dk': 0.781, 'k': 0.234, 's': 0.219}
    assert dims('SLH-I', '5/16') == {'dk': 0.437, 'k': 0.158, 's': 0.156}
    assert fc.family(CAT, 'SFH-I')['angle'] == 82.0
    assert lengths('SBH-I', '1/4')[1] == 1.0 and lengths('SBH-I', '1/2')[1] == 2.0  # max standard lengths


def test_inch_set_screw():  # Holo-Krome Table 13: J nom, flat point C2 max. Socket depth is not stored.
    d = dims('SSF-I', '#10')
    assert (d['s'], d['dp']) == (0.094, 0.102) and 't' not in d
    d = dims('SSF-I', '1/2')
    assert (d['s'], d['dp']) == (0.250, 0.291)


def test_inch_hex():  # Brighton-Best / ASME B18.2.1: F max, H max, LT
    assert dims('HHB-I', '1/4') == {'s': 0.438, 'k': 0.163}
    assert dims('HHB-I', '1/2') == {'s': 0.750, 'k': 0.323}
    assert fc.size_row(fc.family(CAT, 'HHB-I'), '3/8')['thread']['b'] == 1.0


def test_unf_rows_share_head_data():
    for code in ('SSH-I', 'SBH-I', 'SFH-I', 'SLH-I', 'SSF-I'):
        fam = fc.family(CAT, code)
        unc = {r['nominal']: r for r in fam['sizes'] if r['series'] == 'UNC'}
        for r in fam['sizes']:
            if r['series'] == 'UNF':
                assert r['dims'] == unc[r['nominal']]['dims'] and r['tpi'] > unc[r['nominal']]['tpi']


def test_iso4029_cup():
    d = dims('SSC-M', 'M6')
    assert (d['s'], d['dp']) == (3.0, 3.0) and 't' not in d
    assert dims('SSC-M', 'M8')['dp'] == 5.0 and dims('SSC-M', 'M12')['dp'] == 8.0
    assert lengths('SSC-M', 'M3') == (3, 16) and lengths('SSC-M', 'M12') == (12, 60)


def test_holo_krome_cup_inch():
    assert dims('SSC-I', '#10')['dp'] == 0.095 and dims('SSC-I', '3/8')['dp'] == 0.187
    assert 't_by_length' not in dims('SSC-I', '1/4')
