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
    for f in CAT['families'] + CAT.get('pending_approval', []):
        if f['code'] == code:
            return f
    raise KeyError(code)


def lengths(code, size):
    r = fc.size_row(_fam(code), size)['lengths']
    return r[0], r[-1]


def test_iso4762():  # ISO 4762:2004 Table 1 (dk max plain, k max, s nom, t min)
    assert dims('SSH-M', 'M3') == {'dk': 5.5, 'k': 3.0, 's': 2.5, 't': 1.3}
    assert dims('SSH-M', 'M8') == {'dk': 13.0, 'k': 8.0, 's': 6.0, 't': 4.0}
    assert dims('SSH-M', 'M12') == {'dk': 18.0, 'k': 12.0, 's': 10.0, 't': 6.0}
    assert lengths('SSH-M', 'M4') == (6, 40) and lengths('SSH-M', 'M10') == (16, 100)


def test_iso7380():  # ISO 7380-1:2011 and :2022 Table 1
    d = dims('SBH-M', 'M16')
    assert (d['dk'], d['k'], d['s'], d['t']) == (28.0, 8.8, 10.0, 5.2) and 14.5 <= d['rf'] <= 15.3
    d = dims('SBH-M', 'M5')
    assert (d['dk'], d['k'], d['s'], d['t']) == (9.5, 2.75, 3.0, 1.56) and 5.25 <= d['rf'] <= 5.75
    assert lengths('SBH-M', 'M3') == (6, 30) and lengths('SBH-M', 'M16') == (25, 90)


def test_iso10642():  # ISO 10642:2004 Table 1 (dk theoretical max, k max, s nom, t min)
    assert dims('SFH-M', 'M6') == {'dk': 13.44, 'k': 3.72, 's': 4.0, 't': 2.2}
    assert dims('SFH-M', 'M20') == {'dk': 40.32, 'k': 10.16, 's': 12.0, 't': 5.6}
    assert fc.family(CAT, 'SFH-M')['angle'] == 90.0
    assert lengths('SFH-M', 'M12') == (20, 100)


def test_din7984():  # Brighton-Best DIN 7984 data sheet (t min); Fastener Network agrees on dk, k, s
    assert dims('SLH-M', 'M4') == {'dk': 7.0, 'k': 2.8, 's': 2.5, 't': 2.18}
    assert dims('SLH-M', 'M8') == {'dk': 13.0, 'k': 5.0, 's': 5.0, 't': 3.65}
    assert dims('SLH-M', 'M16') == {'dk': 24.0, 'k': 9.0, 's': 12.0, 't': 5.35}


def test_iso4017():  # ISO 4017:2022 Table 1 (s nom = max, k nom)
    assert dims('SHH-M', 'M3') == {'s': 5.5, 'k': 2.0}
    assert dims('SHH-M', 'M8') == {'s': 13.0, 'k': 5.3}
    assert dims('SHH-M', 'M16') == {'s': 24.0, 'k': 10.0}


def test_iso4026():  # ISO 4026:2003 Table 1 (dp max, s nom, t min below / in the shaded area)
    d = dims('SSF-M', 'M10')
    assert (d['dp'], d['s'], d['t'], d['t_short'], d['short_max']) == (7.0, 5.0, 6.0, 4.0, 10)
    d = dims('SSF-M', 'M3')
    assert (d['dp'], d['s'], d['t'], d['t_short']) == (2.0, 1.5, 2.0, 1.2)
    assert lengths('SSF-M', 'M3') == (3, 16) and lengths('SSF-M', 'M12') == (12, 60)


def test_iso7045():  # pending approval, not offered
     # ISO 7045:2011 Table 1 (dk max, k max, rf ref, recess no., m ref, type H penetration mean)
    d = dims('SPH-M', 'M4')
    assert (d['dk'], d['k'], d['rf'], d['recess'], d['m']) == (8.0, 3.1, 6.5, 2, 4.4)
    assert abs(d['pen'] - (2.4 + 1.9) / 2) < 1e-9
    assert lengths('SPH-M', 'M5') == (6, 45)


def test_iso1207():  # ISO 1207:2011 Table 1 (dk max, k max, n nom, t min)
    assert dims('SCH-M', 'M3') == {'dk': 5.5, 'k': 2.0, 'n': 0.8, 't': 0.85}
    assert dims('SCH-M', 'M10') == {'dk': 16.0, 'k': 6.0, 'n': 2.5, 't': 2.4}
    assert lengths('SCH-M', 'M8') == (10, 80)


def test_holo_krome_inch():  # Holo-Krome product standards (A max, H max, J nom, T min)
    assert dims('SSH-I', '1/4') == {'dk': 0.375, 'k': 0.25, 's': 0.188, 't': 0.12}
    assert dims('SBH-I', '#10') == {'dk': 0.361, 'k': 0.101, 's': 0.125, 't': 0.07, 'side': 0.02}
    assert dims('SFH-I', '3/8') == {'dk': 0.781, 'k': 0.234, 's': 0.219, 't': 0.159}
    assert dims('SLH-I', '5/16') == {'dk': 0.437, 'k': 0.158, 's': 0.156, 't': 0.11}
    assert fc.family(CAT, 'SFH-I')['angle'] == 82.0
    assert lengths('SBH-I', '1/4')[1] == 1.0 and lengths('SBH-I', '1/2')[1] == 2.0  # max standard lengths


def test_inch_set_screw():  # Holo-Krome Table 13: J nom, TH min, flat point C2 max
    d = dims('SSF-I', '#10')
    assert (d['s'], d['t'], d['dp']) == (0.094, 0.100, 0.102)
    d = dims('SSF-I', '1/2')
    assert (d['s'], d['t'], d['dp']) == (0.250, 0.250, 0.291)


def test_inch_hex():  # Brighton-Best / ASME B18.2.1: F max, H max, LT
    assert dims('SHH-I', '1/4') == {'s': 0.438, 'k': 0.163}
    assert dims('SHH-I', '1/2') == {'s': 0.750, 'k': 0.323}
    assert fc.size_row(fc.family(CAT, 'SHH-I'), '3/8')['thread']['b'] == 1.0


def test_unf_rows_share_head_data():
    for code in ('SSH-I', 'SBH-I', 'SFH-I', 'SLH-I', 'SSF-I'):
        fam = fc.family(CAT, code)
        unc = {r['nominal']: r for r in fam['sizes'] if r['series'] == 'UNC'}
        for r in fam['sizes']:
            if r['series'] == 'UNF':
                assert r['dims'] == unc[r['nominal']]['dims'] and r['tpi'] > unc[r['nominal']]['tpi']


def test_iso4029_cup():
    d = dims('SSC-M', 'M6')
    assert (d['s'], d['dp'], d['t'], d['t_short']) == (3.0, 3.0, 3.5, 2.0)
    assert dims('SSC-M', 'M8')['dp'] == 5.0 and dims('SSC-M', 'M12')['dp'] == 8.0
    assert lengths('SSC-M', 'M3') == (3, 16) and lengths('SSC-M', 'M12') == (12, 60)


def test_holo_krome_cup_inch():
    assert dims('SSC-I', '#10')['dp'] == 0.095 and dims('SSC-I', '3/8')['dp'] == 0.187
    assert dims('SSC-I', '1/4')['t_by_length'] == {'0.1875': 0.090}
