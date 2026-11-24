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
    assert 'head_h' not in g


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
