"""Daniel's fixes of 2026-11-17: sizing order, compatibility warnings, stack edits, materials, and BOM text with
capitalized nouns, no standards and no dimensions."""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'SRFastener'))
import fastener_core as fc  # noqa: E402

CAT = fc.load_catalog()
ALL = CAT['families'] + CAT['parts']


def fam(code):
    return fc.family(CAT, code)


def ref(code, size):
    return fc.thread_ref(fam(code), fc.size_row(fam(code), size))


def test_descriptions_have_no_dimensions_or_standards():
    for f in ALL:
        assert not fc.contains_standard(f['name']), f['name']
        for w in re.split(r'[ -]', f['name'].replace(',', '')):
            assert w[:1].isupper(), (f['code'], f['name'])
        for row in f['sizes']:
            L = row['lengths'][0] if fc.kind(f) == 'screw' else None
            for fk in fc.finishes_for(CAT, f, row):
                b = fc.bom_fields(CAT, f, row, L, fk)
                d = b['description']
                assert d == '%s, %s, %s' % (f['name'], fc.desc_thread(f, row), CAT['finishes'][fk]['name']), d
                assert not fc.contains_standard(d), d
                assert not re.search(r'\bmm\b|"|\bID\b|\bOD\b|thick|wide|high', d), d
                assert not fc.contains_standard(b['material']) and 'AISI' not in b['material'], b['material']


def test_material_names_are_plain():
    names = {k: v['material'] for k, v in CAT['finishes'].items()}
    assert names['SS'] == 'Stainless Steel' and names['SS-BO'] == 'Stainless Steel Black Oxide'
    assert names['ZN'] == 'Zinc Plated' and names['STL'] == 'Plain Steel'
    assert names['GR8'] == 'Grade 8 Steel' and names['CL10.9'] == 'Class 10.9 Steel'


def test_part_numbers_carry_the_dimensions():
    nut = fc.bom_fields(CAT, fam('NHX-M'), fc.size_row(fam('NHX-M'), 'M6'), None, 'SS')
    assert nut['part_number'] == 'NHX-M6-1 18-8 SS'  # screw diameter and thread only
    w = fam('WGP-M')
    assert fc.part_number(w, fc.size_row(w, 'M6'), None, 'ZN') == 'WGP-M6 x 12 ZN'  # ISO 7089 M6 OD 12
    wi = fam('WUS-I')
    assert fc.part_number(wi, fc.size_row(wi, '1/4'), None, 'SS') == 'WUS-1/4 x 0.75 18-8 SS'
    assert fc.part_number(fam('SSH-M'), fc.size_row(fam('SSH-M'), 'M4'), 12, 'CL10.9') == 'SSH-M4-0.7 x 12 CL10.9'


def test_new_materials_by_system():
    for f in ALL:
        offered = set(f['finishes'])
        if f['system'] == 'metric':
            assert 'GR8' not in offered, f['code']
        else:
            assert not {'CL10.9', 'CL10'} & offered, f['code']
        assert f['finishes'][:2] == ['SS', 'SS-BO']
    assert 'GR8' in fam('HHB-I')['finishes'] and 'GR8' in fam('NHX-I')['finishes']
    assert 'CL10.9' in fam('HHB-M')['finishes'] and 'CL10' in fam('NHX-M')['finishes']
    assert 'GR8' not in fam('SSH-I')['finishes']  # socket head screws are not sold as Grade 8
    assert 'ZN' in fam('WSA-I')['finishes'] and 'STL' in fam('WSA-I')['finishes']


def test_screw_sizes_from_hole():
    assert fc.size_for(CAT, fam('SSH-M'), hole_thread='M6x1') == 'M6'
    assert fc.size_for(CAT, fam('SSH-M'), hole_diameter_cm=0.66) == 'M6'  # 6.6 mm clearance hole
    assert fc.size_for(CAT, fam('SSH-I'), hole_thread='10-32 UNF') == '#10-32'


def test_nuts_size_from_screw_first_then_hole():
    m6 = ref('SSH-M', 'M6')
    # the bug Daniel saw: an M4-ish hole picked an M4 nut for an M6 screw
    assert fc.size_for(CAT, fam('NHX-M'), screw_ref=m6, hole_diameter_cm=0.45) == 'M6'
    assert fc.size_for(CAT, fam('WGP-M'), screw_ref=m6, hole_diameter_cm=0.45) == 'M6'
    # no screw: from the hole (thread if tapped, else diameter)
    assert fc.size_for(CAT, fam('NHX-M'), hole_diameter_cm=0.45) == 'M4'
    assert fc.size_for(CAT, fam('NNL-I'), hole_thread='1/4-20 UNC') == '1/4'
    # fine thread screw needs the fine thread nut
    assert fc.size_for(CAT, fam('NNL-I'), screw_ref=ref('SSH-I', '#10-32')) == '#10-32'
    # never from another nut or washer: the dialog takes the screw ref only from a screw
    src = open(os.path.join(ROOT, 'SRFastener', 'SRFastener.py'), encoding='utf-8').read()
    body = src[src.index('def _screw_ref('):src.index('def _hole_note(')]
    assert 'h.screw' in body and "'nut'" not in body and "'washer'" not in body


def test_compat_warnings():
    screw = fc.item(CAT, 'SSH-M', 'M4', 'SS', 12)
    nut = fc.item(CAT, 'NHX-I', '#8', 'SS-BO')  # Daniel's screenshot: M4 screw with a 8-32 black oxide nut
    w = fc.compat_warnings(CAT, [screw, nut])
    assert any('different size or thread' in x for x in w) and any('mixed materials' in x for x in w)
    ok = [screw, fc.item(CAT, 'NHX-M', 'M4', 'SS'), fc.item(CAT, 'WGP-M', 'M4', 'SS')]
    assert fc.compat_warnings(CAT, ok) == []
    assert any('tapped hole' in x for x in fc.compat_warnings(CAT, [screw], 'M5x0.8'))
    assert fc.compat_warnings(CAT, [screw], 'M4x0.7') == []
    # Class 10 nut is the mate of a Class 10.9 screw: no material warning
    b = fc.item(CAT, 'HHB-M', 'M6', 'CL10.9', 20)
    assert fc.compat_warnings(CAT, [b, fc.item(CAT, 'NHX-M', 'M6', 'CL10')]) == []
    # no screw, tapped hole: a nut of another thread is flagged
    assert fc.compat_warnings(CAT, [fc.item(CAT, 'NHX-M', 'M5', 'SS')], 'M6x1')


def test_matching_finish():
    nut = fam('NHX-M')
    assert fc.matching_finish(CAT, nut, fc.size_row(nut, 'M6'), 'CL10.9') == 'CL10'
    assert fc.matching_finish(CAT, nut, fc.size_row(nut, 'M6'), 'ALLOY-BO') is None
    assert fc.matching_finish(CAT, nut, fc.size_row(nut, 'M6'), 'SS-BO') == 'SS-BO'


def test_ref_from_designation():
    assert fc.ref_from_designation('M6x1')['pitch'] == 1.0
    assert fc.ref_from_designation('1/4-20 UNC')['tpi'] == 20
    assert fc.ref_from_designation('10-32 UNF')['nominal'] == '10'
    assert fc.ref_from_designation('') is None


def test_stack_edits():
    st = []
    fc.stack_add(st, {'kind': 'washer'}, 1)
    fc.stack_add(st, {'kind': 'nut'}, 2)
    fc.stack_add(st, {'kind': 'washer', 'side': 'far'}, 3)
    assert fc.stack_move(st, 2, -1) == 1 and st[1]['uid'] == 3
    assert fc.stack_remove(st)['uid'] == 3  # nothing highlighted: newest goes first
    assert fc.stack_remove(st, 0)['uid'] == 1  # highlighted row goes
    assert [r['uid'] for r in st] == [2]
    assert fc.stack_move(st, 0, -1) == 0
    assert fc.stack_remove([]) is None


def test_dialog_has_stack_controls():
    src = open(os.path.join(ROOT, 'SRFastener', 'SRFastener.py'), encoding='utf-8').read()
    for needle in ("addTableCommandInput('stk_tbl'", "'stk_add'", "'stk_del'", "'stk_up'", "'stk_dn'",
                   "addBoolValueInput('auto', 'Match size to first hole', True, '', True)", 'fp.place_stack(',
                   '_material_prompt(', 'YesNoCancelButtonType', 'maximumVisibleRows'):
        assert needle in src, needle
    assert "f['standard']" not in src


def _func_src(src, name):
    m = re.search(r'^def %s\(.*?(?=^\S|\Z)' % name, src, re.S | re.M)
    assert m, name
    return m.group(0)


def test_dialog_live_test_fixes():
    """Bugs found driving the dialog live in Fusion on 2026-11-17."""
    src = open(os.path.join(ROOT, 'SRFastener', 'SRFastener.py'), encoding='utf-8').read()
    place = open(os.path.join(ROOT, 'SRFastener', 'fastener_place.py'), encoding='utf-8').read()
    # a table dropdown must not rebuild (delete) its own row inside its change handler: Fusion crashed
    row = _func_src(src, '_stack_row_changed')
    assert not re.search(r'(?<!_later)_refresh_stack\(', row) and '_later_refresh_stack()' in row
    assert 'fireCustomEvent(REFRESH_EVENT' in src and '_drop_refresh_event()' in _func_src(src, 'stop')
    # the + / - / Up / Down toolbar buttons hide with the table
    assert 'btn.isVisible = on' in _func_src(src, '_refresh_stack')
    # warnings still show while the stack is off
    assert '_show_warnings(inputs)\n        return' in _func_src(src, '_refresh_stack')
    # Fusion rejects minimumVisibleRows > maximumVisibleRows, so the order depends on growing or shrinking
    assert "('maximumVisibleRows', 'minimumVisibleRows') if n >=" in _func_src(src, '_resize_stack')
    # preview parts are not "already in the hole"
    assert '_is_preview(occ)' in _func_src(place, 'hardware_at')
    assert _func_src(place, 'make_component').count('_mark_preview(occ)') == 2
    assert 'fp.PREVIEW = True' in src
    # tapped Hole features expose tappedHoleInfo
    assert "'tappedHoleInfo'" in _func_src(place, '_hole_feature_thread')


def test_screw_vs_plain_hole_size():
    screw = fc.item(CAT, 'SSH-M', 'M6', 'SS', 12)
    assert any('bigger than the 4.50 mm hole' in w for w in fc.compat_warnings(CAT, [screw], None, 0.45))
    assert fc.compat_warnings(CAT, [screw], None, 0.66) == []
    # picked counterbore or countersink edges are wide, so a big hole is not flagged
    assert fc.compat_warnings(CAT, [screw], None, 1.2) == []
    # a tapped hole is judged by its thread, not its drill size
    assert fc.compat_warnings(CAT, [screw], 'M6x1', 0.50) == []
