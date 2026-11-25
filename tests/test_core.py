import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'SRFastener'))
import fastener_core as fc  # noqa: E402

CAT = fc.load_catalog()


def test_finishes():
    assert set(CAT['finishes']) == {'SS', 'SS-BO', 'ALLOY-BO', 'STL', 'ZN', 'GR8', 'CL10.9', 'CL10',
                                    'PEM-ZI', 'PEM-SS', 'PEM-4SS'}
    for fam in CAT['families']:
        for row in fam['sizes']:
            # Daniel's rule: every size in 18-8 SS and 18-8 SS-BO, whatever McMaster stocks
            assert {'SS', 'SS-BO'} <= set(fc.finishes_for(CAT, fam, row)), (fam['code'], row['size'])
    alloy = CAT['finishes']['ALLOY-BO']
    assert alloy['appearance'] == 'Coating - Black Oxide'
    for fam in CAT['families']:
        for row in fam['sizes']:
            for g in row.get('grade', {}).values():
                assert g in CAT['alloy_materials'], (fam['code'], g)
    assert alloy['made_up_code'] is True


def test_part_numbers():
    shcs = fc.family(CAT, 'SSH-M')
    assert fc.part_number(shcs, fc.size_row(shcs, 'M3'), 10, 'SS') == 'SSH-M3-0.5 x 10 18-8 SS'
    inch = fc.family(CAT, 'SSH-I')
    assert fc.part_number(inch, fc.size_row(inch, '1/4'), 1.5, 'SS-BO') == 'SSH-1/4-20 x 1.5 18-8 SS-BO'
    assert fc.part_number(inch, fc.size_row(inch, '#4'), 0.25, 'SS') == 'SSH-4-40 x 0.25 18-8 SS'


def test_description_and_bom():
    fam = fc.family(CAT, 'SBH-M')
    bom = fc.bom_fields(CAT, fam, fc.size_row(fam, 'M4'), 12, 'SS-BO')
    assert bom['description'] == 'Button Head Hex-Drive Screw, M4 x 0.7, 18-8 Stainless Steel Black Oxide'
    assert bom['material'] == 'Stainless Steel Black Oxide' and bom['base_material'] == 'Stainless Steel AISI 304'
    assert bom['part_number'] == 'SBH-M4-0.7 x 12 18-8 SS-BO'
    assert bom['appearance'] == 'Coating - Black Oxide'
    ss = fc.bom_fields(CAT, fam, fc.size_row(fam, 'M4'), 12, 'SS')
    assert ss['material'] == 'Stainless Steel' and ss['part_number'].endswith(' 18-8 SS')
    assert ss['description'] == 'Button Head Hex-Drive Screw, M4 x 0.7, 18-8 Stainless Steel'


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


def test_socket_is_a_look_and_stays_inside():
    """Hex across the flats stays the sourced size. Depth is half the head, or half the metal above a point."""
    fam = fc.family(CAT, 'SSH-M')
    row = fc.size_row(fam, 'M5')
    g = fc.geometry(fam, row, 16)
    assert abs(g['key'] - row['dims']['s'] / 10.0) < 1e-9
    assert abs(g['key_depth'] - 0.5 * g['head_h']) < 1e-9 and g['key_depth'] < g['head_h']
    m = fc.family(CAT, 'SSF-M')
    row = fc.size_row(m, 'M3')
    g = fc.geometry(m, row, 4)
    assert abs(g['key'] - row['dims']['s'] / 10.0) < 1e-9
    assert g['point_h'] < g['L'] and abs(g['key_depth'] - 0.5 * (g['L'] - g['point_h'])) < 1e-9
    desc = fc.description(CAT, fam, fc.size_row(fam, 'M5'), 16, 'SS')
    assert 'depth' not in desc.lower()
    pn = fc.part_number(fam, fc.size_row(fam, 'M5'), 16, 'SS')
    assert pn.startswith('SSH-') and 'depth' not in pn.lower()


def test_same_type_shares_one_smart_code_and_pem_uses_pem_numbers():
    """Inch and metric of one McMaster type share the shop code. Press-in parts use the PEM designation."""
    groups = {}
    for fam in CAT['families']:
        stem = fam['code'].rsplit('-', 1)[0]
        groups.setdefault(fam['mcmaster'], set()).add(stem)
        row = fam['sizes'][0]
        pn = fc.part_number(fam, row, row['lengths'][0], 'SS')
        assert pn.startswith(stem + '-')
    for fam in CAT['parts']:
        stem = fam['code'].rsplit('-', 1)[0]
        groups.setdefault(fam['mcmaster'], set()).add(stem)
        pn = fc.part_number(fam, fam['sizes'][0], None, 'SS')
        assert pn.startswith(stem + '-')
    for name, stems in groups.items():
        assert len(stems) == 1, (name, stems)
    for fam in CAT['press_in']:
        row = fam['sizes'][0]
        pn = fc.part_number(fam, row, row['lengths'][0], fam['finishes'][0])
        assert pn.startswith(fam['code'] + '-') and '18-8' not in pn


def test_dome_uses_crown_radius_or_side_height():
    r, zc = fc.dome(0.285, 0.165, rf=0.35)       # ISO 7380-1 M3, rf mid 3.5 mm
    assert math.isclose(r, 0.35) and math.isclose(zc + r, 0.165)
    side_z = zc + math.sqrt(r * r - 0.285 ** 2)  # dome height at the head edge
    assert 0 < side_z < 0.165
    r, zc = fc.dome(1.05, 0.66, rf=1.085)         # M12: rf cannot reach the edge, so the edge dome is used
    assert math.isclose(math.hypot(1.05, zc), r, rel_tol=1e-9)
    r, zc = fc.dome(0.2185, 0.132, side=0.031)    # B18.3 1/4 button: passes through (A/2, S)
    assert math.isclose(math.hypot(0.2185, 0.031 - zc), r) and math.isclose(zc + r, 0.132)


def test_alloy_black_oxide_bom():
    fam = fc.family(CAT, 'SSH-M')
    bom = fc.bom_fields(CAT, fam, fc.size_row(fam, 'M5'), 16, 'ALLOY-BO')
    assert bom['part_number'] == 'SSH-M5-0.8 x 16 ALLOY-BO'
    assert bom['description'] == 'Socket Head Screw, M5 x 0.8, Alloy Steel Black Oxide'
    assert bom['material'] == 'Alloy Steel Black Oxide' and bom['grade'] == 'Class 12.9'
    assert bom['base_material'] == 'Steel AISI 4142 400 QT'
    s = fc.family(CAT, 'SSF-M')
    assert fc.bom_fields(CAT, s, fc.size_row(s, 'M6'), 8, 'ALLOY-BO')['base_material'] == 'Steel AISI 4142 475 QT'
    lh = fc.family(CAT, 'SLH-M')
    assert fc.bom_fields(CAT, lh, fc.size_row(lh, 'M6'), 16, 'ALLOY-BO')['base_material'] == 'Steel AISI 4340 350A QT'
    inch = fc.family(CAT, 'SBH-I')
    bom = fc.bom_fields(CAT, inch, fc.size_row(inch, '#10-32'), 0.5, 'ALLOY-BO')
    assert bom['part_number'] == 'SBH-10-32 x 0.5 ALLOY-BO' and bom['grade'] == ''  # ASTM F835 is a standard
    assert bom['description'] == 'Button Head Hex-Drive Screw, #10-32, Alloy Steel Black Oxide'


def test_alloy_not_offered_where_makers_do_not_sell_it():
    no = {'HHB-M': None, 'SPH-M': None, 'SCH-M': None,
          'SFH-M': ['M20'], 'SFH-I': ['#2'], 'SLH-I': ['#4', '#6']}
    for code, sizes in no.items():
        fam = fc.family(CAT, code)
        for row in fam['sizes']:
            if sizes is None or fc.nominal(row) in sizes:
                assert 'ALLOY-BO' not in fc.finishes_for(CAT, fam, row), (code, row['size'])
                try:
                    fc.bom_fields(CAT, fam, row, row['lengths'][0], 'ALLOY-BO')
                    raise AssertionError('alloy allowed for %s %s' % (code, row['size']))
                except ValueError:
                    pass
    assert fc.grade(fc.size_row(fc.family(CAT, 'SBH-M'), 'M16'), 'ALLOY-BO') == 'class 10.9'
    assert fc.grade(fc.size_row(fc.family(CAT, 'SLH-M'), 'M6'), 'ALLOY-BO') == 'class 10.9'
    assert fc.grade(fc.size_row(fc.family(CAT, 'HHB-I'), '1/2'), 'ALLOY-BO') == 'SAE J429 Grade 8'


def test_thread_lengths():
    m = fc.family(CAT, 'SSH-M')
    assert fc.thread_length(m, fc.size_row(m, 'M3'), 20) == 20     # threaded to the head (ISO 4762 shaded)
    assert fc.thread_length(m, fc.size_row(m, 'M3'), 25) == 18     # b ref from 25 mm
    assert fc.thread_length(m, fc.size_row(m, 'M6'), 30) == 30 and fc.thread_length(m, fc.size_row(m, 'M6'), 35) == 24
    i = fc.family(CAT, 'SSH-I')
    assert math.isclose(fc.thread_length(i, fc.size_row(i, '1/4'), 2.0), 1.0)   # Holo-Krome Table 2: LG 1.00
    assert fc.thread_length(i, fc.size_row(i, '1/4'), 1.25) == 1.25
    f = fc.family(CAT, 'SFH-I')
    assert math.isclose(fc.thread_length(f, fc.size_row(f, '#10'), 2.0), 0.88)  # Table 9: LGH 1.12 from head top
    h = fc.family(CAT, 'HHB-I')
    assert fc.thread_length(h, fc.size_row(h, '1/4'), 0.75) == 0.75 and fc.thread_length(h, fc.size_row(h, '1/4'), 1.5) == 0.75
    p = fc.family(CAT, 'SPH-M')
    assert fc.thread_length(p, fc.size_row(p, 'M5'), 40) == 40 and fc.thread_length(p, fc.size_row(p, 'M5'), 45) == 38


def test_pan_and_cheese_offered():
    offered = {f['code'] for f in CAT['families']}
    assert {'SPH-M', 'SCH-M'} <= offered and not CAT['pending_approval']


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
    assert fc.thread_spec(fam, fc.size_row(fam, '#10-32'))[1] == '10-32 UNF'
    m = fc.family(CAT, 'SSH-M')
    assert fc.thread_spec(m, fc.size_row(m, 'M2.5'))[1] == 'M2.5x0.45'


def test_size_from_designation():
    m = fc.family(CAT, 'SSH-M')
    assert fc.size_from_designation(m, 'M3x0.5') == 'M3'
    assert fc.size_from_designation(m, 'M2.5x0.45') == 'M2.5'
    i = fc.family(CAT, 'SSH-I')
    assert fc.size_from_designation(i, '1/4-20 UNC') == '1/4'
    assert fc.size_from_designation(i, '#10-24 UNC') == '#10'
    assert fc.size_from_designation(i, '10-24 UNC') == '#10'
    assert fc.size_from_designation(i, '10-32 UNF') == '#10-32'
    assert fc.size_from_designation(i, '7/16-14 UNC') is None


def test_cup_point_geometry():
    fam = fc.family(CAT, 'SSC-M')
    g = fc.geometry(fam, fc.size_row(fam, 'M6'), 10)
    assert g['point'] == 'cup'
    assert abs(g['point_r'] - 0.15) < 1e-9          # dz 3.0 mm
    assert 0 < g['cup_r'] < g['point_r'] and 0 < g['cup_depth'] < g['L'] - g['key_depth']
    flat = fc.family(CAT, 'SSF-M')
    assert fc.geometry(flat, fc.size_row(flat, 'M6'), 10)['point'] == 'flat'


def test_names_follow_mcmaster():
    for fam in CAT['families']:
        code = fam['code'].rsplit('-', 1)[0]
        assert fam['mcmaster'] and fam['mcmaster_url'].startswith('https://www.mcmaster.com/')
        words = fam['mcmaster'].lower()
        if code.startswith('SS') and fam['head'] == 'set':
            assert words.startswith({'F': 'flat-tip', 'C': 'cup-tip', 'N': 'cone-tip', 'E': 'extended-tip',
                                     'O': 'oval-tip'}[code[2]])
        elif code == 'HHB':  # Daniel's name for McMaster's Hex Head Screws
            assert words == 'hex head screws' and fam['name'].startswith('Hex Head Bolt')
        elif code == 'SBF':  # button head, flanged
            assert words == 'flanged button head hex-drive screws'
        elif code == 'STP':  # sheet metal tapping screw, pan (rounded) head
            assert words == 'phillips rounded head screws for sheet metal'
        else:
            assert code[0] == 'S' and code[2] == 'H'


def test_remembered_length_matches_int_catalog_lengths():
    # the dialog saves 16.0; the catalog lists 16 -- the reopened dialog must land on 16 mm, not the first length
    fam = fc.family(CAT, 'SSH-M')
    row = fc.size_row(fam, 'M5')
    assert 16 in row['lengths'] and isinstance(row['lengths'][0], int)
    assert fc.length_key(row, 16.0) == '16'
    assert fc.length_key(row, 16) == '16'
    assert fc.length_key(row, 17.0) is None and fc.length_key(row, None) is None
    inch = fc.family(CAT, 'SSH-I')
    r = fc.size_row(inch, '1/4')
    assert fc.length_key(r, 0.5) == str([L for L in r['lengths'] if abs(L - 0.5) < 1e-9][0])
    src = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'SRFastener',
                            'SRFastener.py'), encoding='utf-8').read()
    assert 'fc.length_key(row, _st.length)' in src


def test_refresh_keeps_remembered_length_when_not_a_screw():
    # Switching to (or opening on) a nut/washer must not wipe the last screw length.
    src = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'SRFastener',
                            'SRFastener.py'), encoding='utf-8').read()
    start = src.index('def _refresh(')
    end = src.index('def _bom_preview(')
    body = src[start:end]
    assert 'if screw:' in body
    assert 'fc.length_key(row, _st.length)' in body
    assert '_st.length = None' not in body


def test_bom_fields_never_use_vendor_numbers():
    """Screws, nuts and washers use the shop smart scheme. Press-in parts use the PEM designation,
    and the BOM description stays the type line (hole notes are not in it)."""
    for fam in CAT['families'] + CAT.get('parts', []) + CAT.get('press_in', []):
        for row in fam['sizes']:
            if fc.kind(fam) == 'press-in':
                Ls = [row['lengths'][0], row['lengths'][-1]]
            elif fc.kind(fam) != 'screw':
                Ls = [None]
            else:
                Ls = [row['lengths'][0], row['lengths'][-1]]
            for L in Ls:
                for fk in fc.finishes_for(CAT, fam, row):
                    bom = fc.bom_fields(CAT, fam, row, L, fk)
                    pn = bom['part_number']
                    assert pn == fc.part_number(fam, row, L, fk)
                    assert pn == fc.component_name(fam, row, L, fk)
                    assert not fc.contains_vendor_number(pn), (fam['code'], row['size'], pn)
                    assert not fc.contains_vendor_number(bom['description'])
                    assert not fc.contains_standard(bom['description'])
                    if fc.kind(fam) == 'press-in':
                        assert 'Mounting hole' not in bom['description']
                        assert 'Minimum sheet' not in bom['description']
                        assert pn.startswith(fam['code'] + '-')
                    else:
                        assert pn.startswith(fam['code'].rsplit('-', 1)[0] + '-')
                        assert pn.endswith(' ' + CAT['finishes'][fk]['code'])
