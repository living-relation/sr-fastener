import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'SRFastener'))
import fastener_core as fc  # noqa: E402

CAT = fc.load_catalog()


def test_every_family_has_both_finishes():
    assert set(CAT['finishes']) >= {'SS', 'SS-BO'}


def test_part_numbers():
    shcs = fc.family(CAT, 'SSH-M')
    assert fc.part_number(shcs, fc.size_row(shcs, 'M3'), 10, 'SS') == 'SSH-M3-0.5 x 10 18-8 SS'
    inch = fc.family(CAT, 'SSH-I')
    assert fc.part_number(inch, fc.size_row(inch, '1/4'), 1.5, 'SS-BO') == 'SSH-1/4-20 x 1.5 18-8 SS-BO'
    assert fc.part_number(inch, fc.size_row(inch, '#4'), 0.25, 'SS') == 'SSH-4-40 x 0.25 18-8 SS'


def test_description_and_bom():
    fam = fc.family(CAT, 'SBH-M')
    bom = fc.bom_fields(CAT, fam, fc.size_row(fam, 'M4'), 12, 'SS-BO')
    assert bom['description'] == 'Button head socket cap screw, ISO 7380-1, M4 x 0.7 x 12 mm, 18-8 stainless steel, black oxide'
    assert bom['material'] == 'Stainless Steel AISI 304'
    assert bom['part_number'] == 'SBH-M4-0.7 x 12 18-8 SS-BO'
    assert bom['appearance'] == 'Coating - Black Oxide'
    ss = fc.bom_fields(CAT, fam, fc.size_row(fam, 'M4'), 12, 'SS')
    assert ss['material'] == 'Stainless Steel AISI 304' and ss['part_number'].endswith(' 18-8 SS')


def test_fmt_in():
    assert fc.fmt_in(0.25) == '1/4'
    assert fc.fmt_in(1.0) == '1'
    assert fc.fmt_in(1.25) == '1-1/4'
    assert fc.fmt_in(0.1875) == '3/16'


def test_flat_head_cone_matches_standard_head_height():
    # ISO 10642 and ASME B18.3 head heights equal (dk - d) / 2 / tan(half angle) within 0.002 in / 0.05 mm.
    for code, tol in (('SFH-M', 0.05), ('SFH-I', 0.002)):
        fam = fc.family(CAT, code)
        half = math.radians(fam['angle'] / 2)
        for row in fam['sizes']:
            k = (row['dims']['dk'] - row['d']) / 2 / math.tan(half)
            assert abs(k - row['dims']['k']) <= tol, (code, row['size'], k, row['dims']['k'])


def test_geometry_units():
    fam = fc.family(CAT, 'SSH-M')
    g = fc.geometry(fam, fc.size_row(fam, 'M3'), 10)
    assert math.isclose(g['r'], 0.15) and math.isclose(g['L'], 1.0) and math.isclose(g['head_r'], 0.275)
    inch = fc.family(CAT, 'SSH-I')
    g = fc.geometry(inch, fc.size_row(inch, '1/4'), 1.0)
    assert math.isclose(g['L'], 2.54) and math.isclose(g['r'], 0.3175)


def test_set_screw_point():
    fam = fc.family(CAT, 'SSF-M')
    g = fc.geometry(fam, fc.size_row(fam, 'M8'), 10)
    assert math.isclose(g['point_r'], 0.275) and math.isclose(g['point_h'], 0.125)


def test_button_sphere_passes_through_edge_and_apex():
    r, zc = fc.button_sphere(0.285, 0.165)
    assert math.isclose(math.hypot(0.285, 0 - zc), r)
    assert math.isclose(zc + r, 0.165)


def test_suggest_size():
    fam = fc.family(CAT, 'SSH-M')
    assert fc.suggest_size(CAT, fam, 0.34) == 'M3'    # 3.4 mm clearance hole
    assert fc.suggest_size(CAT, fam, 0.25) == 'M2.5'  # clearance fit wins over the M3 tap drill
    assert fc.suggest_size(CAT, fam, 0.42) == 'M4'    # 4.2 mm close-fit hole
    assert fc.suggest_size(CAT, fam, 0.68) == 'M6'
    assert fc.suggest_size(CAT, fam, 0.66) == 'M6'
    assert fc.suggest_size(CAT, fam, 5.0) is None


def test_thread_spec():
    fam = fc.family(CAT, 'SSH-I')
    assert fc.thread_spec(fam, fc.size_row(fam, '#10'))[1] == '10-24 UNC'
    m = fc.family(CAT, 'SSH-M')
    assert fc.thread_spec(m, fc.size_row(m, 'M2.5'))[1] == 'M2.5x0.45'


def test_size_from_designation():
    m = fc.family(CAT, 'SSH-M')
    assert fc.size_from_designation(m, 'M3x0.5') == 'M3'
    assert fc.size_from_designation(m, 'M2.5x0.45') == 'M2.5'
    i = fc.family(CAT, 'SSH-I')
    assert fc.size_from_designation(i, '1/4-20 UNC') == '1/4'
    assert fc.size_from_designation(i, '#10-24 UNC') == '#10'
    assert fc.size_from_designation(i, '7/16-14 UNC') is None
