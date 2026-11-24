"""PEM press-in parts: citations, mounting notes, warnings, and no placeholder values.

Expected numbers were read from the PEM datasheets (CL, FH, SO, ALA) and the matching
catalog.pemnet.com item pages. See tools/pem_press.py and data/pem_sources.md.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'SRFastener'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tools'))
import fastener_core as fc  # noqa: E402
import pem_press  # noqa: E402

CAT = fc.load_catalog()
_BAD = ('tbd', 'n/a', 'placeholder', 'todo', 'unknown')


def fam(code):
    return fc.family(CAT, code)


def row(code, size):
    return fc.size_row(fam(code), size)


def press_parts():
    return CAT['press_in']


def _walk(value, path):
    if value is None:
        raise AssertionError('null at %s' % path)
    if isinstance(value, str):
        low = value.strip().lower()
        if low in _BAD or low.startswith('tbd'):
            raise AssertionError('placeholder %r at %s' % (value, path))
    elif isinstance(value, dict):
        for k, v in value.items():
            _walk(v, '%s.%s' % (path, k))
    elif isinstance(value, (list, tuple)):
        for i, v in enumerate(value):
            _walk(v, '%s[%s]' % (path, i))


def test_no_placeholder_dimensions():
    assert press_parts(), 'no press-in parts in the catalog'
    for part in press_parts():
        _walk(part, part['code'])
        for size in part['sizes']:
            for length in size['lengths']:
                spec = fc.mount_spec(part, size, length)
                for key in ('hole', 'hole_plus', 'hole_minus', 'min_sheet'):
                    assert isinstance(spec[key], float), (part['code'], size['size'], length, key)
                    assert spec[key] >= 0
                assert spec['citation']
                assert 'http' in spec['citation']


def test_mount_notes_are_not_in_the_bom_description():
    part = fam('FHS')
    size = row('FHS', 'M5')
    text = fc.mount_text(part, size, 12)
    assert 'Mounting hole 5 mm +0.08/-0 mm.' in text
    assert 'Minimum sheet 1 mm.' in text
    assert 'pemnet.com' in text
    bom = fc.bom_fields(CAT, part, size, 12, 'PEM-SS')
    assert bom['part_number'] == 'FHS-M5-12'
    assert bom['description'] == 'Flush-Head Stud, M5 x 0.8, Stainless Steel'
    assert 'Mounting hole' not in bom['description']
    assert 'Minimum sheet' not in bom['description']
    names = [item[0] for item in fc.parameter_values(part, size, 12)]
    assert names == ['hole', 'hole_plus', 'hole_minus', 'min_sheet']


def test_each_family_places_warns_and_bom():
    """One real part per family: PEM number, plain description, and the four warnings."""
    samples = (
        ('S', 'M4', '1', 'S-M4-1ZI', 'Self-Clinching Nut, M4 x 0.7, Zinc Plated Steel', 5.41, 1.0, 6.9, 80),
        ('CLS', 'M4', '2', 'CLS-M4-2', 'Self-Clinching Nut, M4 x 0.7, Stainless Steel', 5.41, 1.4, 6.9, 70),
        ('SS', 'M5', '0', 'SS-M5-0ZI', 'Self-Clinching Nut, M5 x 0.8, Zinc Plated Steel', 6.35, 0.8, 7.1, 80),
        ('CLSS', 'M5', '1', 'CLSS-M5-1', 'Self-Clinching Nut, M5 x 0.8, Stainless Steel', 6.35, 1.0, 7.1, 70),
        ('FH', 'M5', 12, 'FH-M5-12ZI', 'Flush-Head Stud, M5 x 0.8, Zinc Plated Steel', 5.0, 1.0, 7.2, 80),
        ('FHS', 'M5', 12, 'FHS-M5-12', 'Flush-Head Stud, M5 x 0.8, Stainless Steel', 5.0, 1.0, 7.2, 70),
        ('FH4', 'M5', 12, 'FH4-M5-12', 'Flush-Head Stud, M5 x 0.8, Hardened Stainless Steel', 5.0, 1.0, 7.2, 92),
        ('SO', 'M3', 8, 'SO-M3-8ZI', 'Thru-Hole Standoff, M3 x 0.5, Zinc Plated Steel', 4.22, 1.0, 6.0, 80),
        ('SOS', 'M5', 25, 'SOS-M5-25', 'Thru-Hole Standoff, M5 x 0.8, Stainless Steel', 7.14, 1.27, 8.0, 70),
        ('BSO', 'M3', 6, 'BSO-M3-6ZI', 'Blind Standoff, M3 x 0.5, Zinc Plated Steel', 4.22, 1.0, 6.0, 80),
        ('BSOS', 'M4', 12, 'BSOS-M4-12', 'Blind Standoff, M4 x 0.7, Stainless Steel', 7.14, 1.27, 8.0, 70),
        ('AS', 'M4', '2', 'AS-M4-2ZI', 'Floating Nut, M4 x 0.7, Zinc Plated Steel', 9.35, 1.38, 8.64, 70),
        ('LAS', 'M6', '2', 'LAS-M6-2MD', 'Locking Floating Nut, M6 x 1, Zinc Plated Steel', 13.08, 1.38, 10.67, 70),
    )
    for code, size, length, pn, desc, hole, sheet, edge, hrb in samples:
        part = fam(code)
        size_row = row(code, size)
        bom = fc.bom_fields(CAT, part, size_row, length, part['finishes'][0])
        assert bom['part_number'] == pn, (code, bom['part_number'])
        assert bom['description'] == desc
        spec = fc.mount_spec(part, size_row, length)
        assert spec['hole'] == hole and spec['min_sheet'] == sheet and spec['edge'] == edge
        assert fc.press_warnings(spec, hole, sheet, edge, hrb) == []
        assert any('off the PEM hole' in w for w in fc.press_warnings(spec, hole - 0.2, None, None, None))
        assert any('thinner' in w for w in fc.press_warnings(spec, None, sheet - 0.2, None, None))
        assert any('Centerline-to-edge' in w for w in fc.press_warnings(spec, None, None, edge - 0.1, None))
        assert any('harder' in w for w in fc.press_warnings(spec, None, None, None, hrb + 1))
        g = fc.press_geometry(part, size_row, length)
        assert g['kind'] == 'press-in' and g['shape'] == part['shape']


def test_fhs_m5_edge_from_the_bulletin():
    """FH datasheet page 5: M5 minimum centerline-to-edge is 7.2 mm. 7.1 warns, 7.2 does not."""
    part, size = fam('FHS'), row('FHS', 'M5')
    spec = fc.mount_spec(part, size, 12)
    assert spec['edge'] == 7.2
    assert spec['hole'] == 5.0 and spec['hole_plus'] == 0.08 and spec['hole_minus'] == 0.0
    assert spec['min_sheet'] == 1.0
    low = fc.press_warnings(spec, 5.0, 1.0, 7.1, 70)
    assert len(low) == 1 and '7.100 mm is under the PEM minimum 7.200 mm' in low[0]
    assert fc.press_warnings(spec, 5.0, 1.0, 7.2, 70) == []
    assert fc.press_warnings(spec, 5.08, 1.0, 7.2, 70) == []
    assert any('off the PEM hole' in w for w in fc.press_warnings(spec, 5.09, None, None, None))


def test_fh4_sheet_range_and_nut_shanks():
    spec = fc.mount_spec(fam('FH4'), row('FH4', 'M4'), 6)
    assert spec['min_sheet'] == 1.0 and spec['max_sheet'] == 2.4
    assert any('thicker' in w for w in fc.press_warnings(spec, None, 2.5, None, None))
    assert fc.press_warnings(spec, None, 2.4, None, None) == []
    m6 = row('S', 'M6')
    assert m6['lengths'] == ['00', '0', '1', '2']
    assert fc.part_number(fam('S'), m6, '00', 'PEM-ZI') == 'S-M6-00ZI'
    assert fc.mount_spec(fam('S'), m6, '00')['min_sheet'] == 0.92
    assert fc.mount_spec(fam('S'), m6, '2')['min_sheet'] == 2.29
    assert 'M5' not in [s['size'] for s in fam('S')['sizes']]
    assert [s['size'] for s in fam('SS')['sizes']] == ['M5']


def test_coverage_matches_the_datasheets():
    assert [s['size'] for s in fam('S')['sizes']] == ['M2.5', 'M3', 'M3.5', 'M4', 'M6', 'M8', 'M10']
    assert [s['size'] for s in fam('CLS')['sizes']] == [s['size'] for s in fam('S')['sizes']]
    assert [s['size'] for s in fam('FH')['sizes']] == ['M2.5', 'M3', 'M3.5', 'M4', 'M5', 'M6', 'M8']
    assert row('FH', 'M5')['lengths'] == [8, 10, 12, 15, 18, 20, 25, 30, 35]
    assert row('FH', 'M2.5')['lengths'] == [6, 8, 10, 12, 15, 18]
    assert row('FH', 'M8')['lengths'] == [12, 15, 18, 20, 25, 30, 35]
    assert [s['size'] for s in fam('FH4')['sizes']] == ['M3', 'M4', 'M5', 'M6']
    assert row('FH4', 'M6')['lengths'] == [10, 12, 15, 18, 20, 25, 30, 35]
    assert [s['size'] for s in fam('SO')['sizes']] == ['M3', '3.5M3', 'M3.5', 'M4', 'M5']
    assert row('SO', 'M3')['lengths'] == [3, 4, 6, 8, 10, 12, 14, 16, 18]
    assert row('SO', 'M5')['lengths'] == [3, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 25]
    assert row('BSO', 'M3')['lengths'] == [6, 8, 10, 12, 14, 16, 18, 20, 22, 25]
    assert row('BSO', 'M3')['dims']['F']['6'] == 3.2
    assert row('BSO', 'M3')['dims']['F']['12'] == 5.0
    assert row('BSO', 'M3')['dims']['F']['25'] == 9.5
    assert row('AS', 'M6')['lengths'] == ['2']
    assert row('LAS', 'M3')['lengths'] == ['1', '2']
    # Spot-check one published envelope per shape.
    assert row('CLSS', 'M5')['dims']['C'] == 6.33
    assert row('CLSS', 'M5')['dims']['E'] == 8.64
    assert row('CLSS', 'M5')['dims']['T'] == 2.0
    assert row('FHS', 'M5')['dims']['H'] == 6.5
    assert row('FHS', 'M5')['dims']['S'] == 2.7
    assert row('SOS', 'M3')['dims']['H'] == 4.8
    assert row('SOS', 'M3')['dims']['C'] == 4.2
    g = fc.press_geometry(fam('FHS'), row('FHS', 'M5'), 12)
    assert abs(g['L'] - 1.2) < 1e-9 and abs(g['r'] - 0.25) < 1e-9
    assert abs(g['head_r'] - 0.325) < 1e-9
    assert abs(g['head_h'] * 10 - 0.65) < 1e-9


def test_stud_head_matches_the_step_profile():
    """Head thickness is H/10. The plain barrel starts before S max, and S is left as that maximum."""
    for code in ('FH', 'FHS'):
        for size, H, S, barrel in (
            ('M2.5', 4.1, 1.95, 1.300), ('M3', 4.6, 2.1, 1.400), ('M3.5', 5.3, 2.25, 1.500),
            ('M4', 5.9, 2.4, 1.600), ('M5', 6.5, 2.7, 1.800), ('M6', 8.2, 3.0, 2.000),
            ('M8', 9.6, 3.7, 2.467),
        ):
            dims = row(code, size)['dims']
            assert dims['S'] == S
            assert abs(dims['head_thk'] - H / 10.0) < 0.001
            assert abs(dims['edge_r'] - dims['head_thk'] / 2.0) < 1e-9
            assert dims['barrel_start'] <= dims['S']
            assert dims['barrel_start'] == barrel
    for code in ('FH4',):
        assert 'M8' not in [s['size'] for s in fam(code)['sizes']]
        assert row('FH4', 'M5')['dims']['head_thk'] == row('FH', 'M5')['dims']['head_thk']
    part, size = fam('FHS'), row('FHS', 'M5')
    pts = fc.stud_profile(part, size, 12)
    assert abs(pts[0][0]) < 1e-9
    assert abs(max(r for _z, r in pts) * 20 - 6.5) < 1e-6
    assert abs(pts[-1][0] * 10 + 12) < 1e-6
    g = fc.press_geometry(part, size, 12)
    assert g['unthread'] <= g['s_max'] + 1e-9
    under = [r for z, r in pts if -g['barrel_start'] - 0.02 < z < -g['head_h'] - g['collar_l'] - g['neck_l']]
    assert under and min(under) <= g['undercut_r'] + 1e-4


def test_floating_nut_float_follows_the_bulletin():
    """0.76 mm is the total travel. Body E, C, A, T and D stay the catalog numbers."""
    for code, height_key, height in (('AS', 'T1', 4.32), ('LAS', 'T2', 6.86)):
        dims = row(code, 'M5')['dims']
        assert dims['float_total'] == 0.76 and dims['float_radial'] == 0.38
        assert dims['E'] == 11.94 and dims['C'] == 10.29 and dims['D'] == 10.29
        assert dims['A']['1'] == 0.97 and dims[height_key] == height
        g = fc.press_geometry(fam(code), row(code, 'M5'), '1')
        gap = (g['retainer_bore_r'] - g['nut_r']) * 20
        assert abs(gap - 0.76) < 1e-9
        assert abs(g['head_r'] * 20 - 11.94) < 1e-9
        assert abs(g['shank_r'] * 20 - 10.29) < 1e-9
    # The STEP gaps are not the model. M3 is under 0.76 and M6 is over it.
    assert row('AS', 'M3')['dims']['nut_dia'] == 5.978
    assert row('AS', 'M6')['dims']['float_total'] == 0.76


def test_standoff_keeps_the_datasheet_hex_and_minimum_blind_depth():
    """SO-3 and SO-4 draw a full-length hex. F on SO-4 is a minimum, so the hole is cut to F."""
    so = fc.press_geometry(fam('SO'), row('SO', 'M3'), 16)
    assert abs(so['across'] * 10 - 4.8) < 1e-9
    assert abs(so['L'] * 10 - 16) < 1e-9
    assert so['L'] * 10 > 0.50
    assert row('SO', 'M4')['dims']['B'] == 4.8
    assert row('SO', 'M5')['pitch'] == 0.8
    bso = fc.press_geometry(fam('BSO'), row('BSO', 'M3'), 6)
    assert abs(bso['blind'] * 10 - row('BSO', 'M3')['dims']['F']['6']) < 1e-9
    assert bso['blind'] * 10 >= 3.2
    assert abs(fc.press_geometry(fam('BSOS'), row('BSOS', 'M4'), 16)['blind'] * 10 - 6.5) < 1e-9


_SCREW_PEM = ('S', 'SS', 'CLS', 'CLSS', 'SO', 'SOS', 'BSO', 'BSOS', 'AS', 'LAS')
_STUD_PEM = ('FH', 'FHS', 'FH4')


def _pem(code, size, length):
    return fc.item(CAT, code, size, fam(code)['finishes'][0], length)


def _screw(size, length):
    return fc.item(CAT, 'SSH-M', size, 'SS', length)


def _nut(size):
    return fc.item(CAT, 'NHX-M', size, 'ZN')


def _washer(size):
    return fc.item(CAT, 'WGP-M', size, 'SS')


def _msgs(pem, mates):
    return [m for _, m in fc.press_stack_issues(CAT, pem, mates)]


def test_material_check_skips_pem():
    """PEM is ignored as the new part and as the part already in the hole."""
    pem = _pem('S', 'M4', '1')
    screw = _screw('M4', 12)
    zinc = _nut('M4')
    assert pem['finish'] == 'PEM-ZI'
    assert fc.match_group(CAT, 'PEM-ZI') != fc.match_group(CAT, 'SS')
    assert fc.material_mismatch(CAT, [pem, screw]) == []
    assert fc.material_mismatch(CAT, [screw, pem]) == []
    assert fc.material_mismatch(CAT, [pem]) == []
    odd = fc.material_mismatch(CAT, [pem, screw, zinc])
    assert odd == [zinc]
    assert fc.should_ask_material(CAT, [pem], [screw]) is False
    assert fc.should_ask_material(CAT, [screw], [pem]) is False
    assert fc.should_ask_material(CAT, [screw], [pem, zinc]) is True
    switched, kept = fc.match_finishes(CAT, [pem, zinc], 'SS')
    assert switched[0]['finish'] == 'PEM-ZI'
    assert switched[1]['finish'] == 'SS'
    assert kept == []
    src = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'SRFastener',
                            'SRFastener.py'), encoding='utf-8').read()
    start = src.index('def _material_prompt(')
    body = src[start:src.index('\n# ---------- event handlers')]
    assert 'should_ask_material(' in body and 'match_finishes(' in body


def test_each_pem_family_stacks_only_its_mate():
    codes = {p['code'] for p in press_parts()}
    assert codes == set(_SCREW_PEM + _STUD_PEM)
    for code in _SCREW_PEM:
        part = fam(code)
        assert fc.press_stack_kinds(part) == ('screw',)
        assert 'nut' not in fc.press_stack_kinds(part)
        assert 'washer' not in fc.press_stack_kinds(part)
    for code in _STUD_PEM:
        part = fam(code)
        assert fc.press_stack_kinds(part) == ('nut', 'washer')
    assert fc.press_stack_sides(fam('SO')) == ('near', 'far')
    assert fc.press_stack_sides(fam('SOS')) == ('near', 'far')
    for code in ('BSO', 'BSOS', 'FH', 'FHS', 'FH4'):
        assert fc.press_stack_sides(fam(code)) == ('far',)
    for code in ('S', 'SS', 'CLS', 'CLSS', 'AS', 'LAS'):
        assert fc.press_stack_sides(fam(code)) == ('near',)


def test_pem_stack_accepts_the_same_thread_only():
    nut = _pem('CLS', 'M4', '1')
    ok = _screw('M4', 10)
    ok['side'] = 'near'
    assert _msgs(nut, [ok]) == []
    wrong = _screw('M5', 10)
    wrong['side'] = 'near'
    assert any('thread does not match' in m for m in _msgs(nut, [wrong]))
    # Same nominal, different pitch, is still a mismatch.
    off_pitch = _screw('M4', 10)
    off_pitch['side'] = 'near'
    off_pitch['row'] = dict(off_pitch['row'])
    off_pitch['row']['pitch'] = 0.5
    assert any('thread does not match' in m for m in _msgs(nut, [off_pitch]))
    stud = _pem('FHS', 'M5', 12)
    good_nut = _nut('M5')
    good_nut['side'] = 'far'
    washer = _washer('M5')
    washer['side'] = 'far'
    assert _msgs(stud, [washer, good_nut]) == []
    bad_nut = _nut('M4')
    bad_nut['side'] = 'far'
    assert any('thread does not match' in m for m in _msgs(stud, [bad_nut]))
    bad_washer = _washer('M4')
    bad_washer['side'] = 'far'
    assert any('thread does not match' in m for m in _msgs(stud, [bad_washer]))
    # A thick-wall standoff is still an M3 thread.
    thick = _pem('SO', '3.5M3', 8)
    m3 = _screw('M3', 6)
    m3['side'] = 'near'
    assert _msgs(thick, [m3]) == []
    m35 = _screw('M3.5', 8) if any(r['size'] == 'M3.5' for r in fam('SSH-M')['sizes']) else None
    if m35 is None:
        m35 = _screw('M4', 8)
    m35['side'] = 'near'
    assert any('thread does not match' in m for m in _msgs(thick, [m35]))


def test_pem_stack_ends_and_blind_depth():
    clinch = _pem('S', 'M4', '1')
    screw = _screw('M4', 10)
    screw['side'] = 'far'
    assert any('end' in m for m in _msgs(clinch, [screw]))
    screw['side'] = 'near'
    other = _nut('M4')
    other['side'] = 'near'
    assert any('screw' in m for m in _msgs(clinch, [other]))
    so = _pem('SO', 'M4', 10)
    near, far = _screw('M4', 8), _screw('M4', 8)
    near['side'], far['side'] = 'near', 'far'
    assert _msgs(so, [near, far]) == []
    extra = _screw('M4', 8)
    extra['side'] = 'near'
    assert any('one screw' in m for m in _msgs(so, [near, extra]))
    blind = _pem('BSO', 'M4', 16)
    assert fc.press_thread_depth(blind['fam'], blind['row'], 16) == 6.5
    short = _screw('M4', 6)
    short['side'] = 'far'
    long = _screw('M4', 8)
    long['side'] = 'far'
    assert _msgs(blind, [short]) == []
    assert any('blind thread' in m for m in _msgs(blind, [long]))
    short['side'] = 'near'
    assert any('end' in m for m in _msgs(blind, [short]))
    stud = _pem('FH', 'M4', 12)
    on_head = _nut('M4')
    on_head['side'] = 'near'
    assert any('end' in m for m in _msgs(stud, [on_head]))
    on_thread = _nut('M4')
    on_thread['side'] = 'far'
    assert _msgs(stud, [on_thread]) == []
    # Where the accepted parts sit.
    placed = fc.press_mate_places(clinch, [dict(screw, side='near')])
    assert placed[0]['end'] == 'out'
    assert abs(placed[0]['offset_cm'] - fc.press_geometry(clinch['fam'], clinch['row'], '1')['head_h']) < 1e-9
    ends = fc.press_mate_places(so, [near, far])
    assert [p['end'] for p in ends] == ['out', 'tip']
    assert ends[0]['offset_cm'] == 0
    assert abs(ends[1]['distance_cm'] - 1.0) < 1e-9
    washer = _washer('M4')
    washer['side'] = 'far'
    nut = _nut('M4')
    nut['side'] = 'far'
    stack = fc.press_mate_places(stud, [washer, nut])
    assert [p['end'] for p in stack] == ['sheet-far', 'sheet-far']
    assert stack[0]['offset_cm'] == 0
    assert abs(stack[1]['offset_cm'] - fc.part_geometry(washer['fam'], washer['row'])['thickness']) < 1e-9


def test_sources_cover_every_press_family():
    for part in press_parts():
        assert part['source'].startswith('https://')
        assert part['citation']
        for key in part['sources']['dims']:
            assert CAT['sources'][key].startswith('https://')
    # The omitted list is reasons, not placeholder rows.
    assert pem_press.OMITTED
    for title, reason in pem_press.OMITTED:
        assert title and reason
        assert 'tbd' not in reason.lower()
