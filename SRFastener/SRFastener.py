"""SR Fastener: pick a screw, nut or washer (type, size, length, material), click hole edges, and it is placed,
joined and BOM-filled. Tick 'Stack nuts/washers' to add any number of nuts and washers on either side of the screw
(or of the hole); one Insert places the whole stack on every picked hole.

Each placed part is a real component with a solid body saved in the design. data/catalog.json is only the size
table the add-in builds new parts from; nobody opens or inserts a library file by hand.
"""
import json
import os
import traceback

import adsk.core
import adsk.fusion

_HERE = os.path.dirname(os.path.abspath(__file__))

from . import fastener_core as fc  # noqa: E402
from . import fastener_place as fp  # noqa: E402
from . import panels as sp  # noqa: E402

CMD_ID = 'srFastenerInsertCmd'
CMD_NAME = 'SR Fastener'
CMD_TIP = ('Insert screws, bolts, nuts and washers at hole edges. Sizes match the hole (screws) or the screw '
           '(nuts and washers). Tick Stack nuts/washers to add any number of nuts and washers on either side; one '
           'Insert places the whole stack on every picked hole. Warns about mismatched size, thread or material.')
SYSTEMS = [('metric', 'Metric'), ('inch', 'Inch')]
SETTINGS_DIR = os.path.join(os.environ.get('APPDATA') or os.path.expanduser('~'), 'SRFastener')
SETTINGS_FILE = os.path.join(SETTINGS_DIR, 'settings.json')
PANELS_FILE = os.path.join(SETTINGS_DIR, 'panels.json')  # where the button goes (see panels.py)

_handlers = []
_last = {}       # the open command and its inputs (live tests drive the dialog through these)
_placed = []    # (workspace id, panel id, created the panel) for every control this add-in added
_cat = None


def _app():
    return adsk.core.Application.get()


def _ui():
    return _app().userInterface


def _load_settings():
    try:
        with open(SETTINGS_FILE, encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def _save_settings(s):
    try:
        os.makedirs(SETTINGS_DIR, exist_ok=True)
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(s, f, indent=1)
    except Exception:
        pass


def _catalog():
    global _cat
    if _cat is None:
        _cat = fc.load_catalog()
    return _cat


# ---------- dialog helpers ----------

def _fill(dd, items, selected):
    """items: [(key, label)]. Keeps `selected` if present, else picks the first."""
    dd.listItems.clear()
    keys = [k for k, _ in items]
    pick = selected if selected in keys else (keys[0] if keys else None)
    for k, label in items:
        dd.listItems.add(label, k == pick)
    return pick


def _sel_key(dd, items):
    if dd.selectedItem is None:
        return None
    label = dd.selectedItem.name
    for k, lab in items:
        if lab == label:
            return k
    return None


class _State:
    def __init__(self):
        self.system = 'metric'
        self.kind = 'screw'
        self.code = None
        self.size = None
        self.length = None
        self.finish = 'SS'
        self.items = {}
        self.stack = []   # [{'side', 'kind', 'code', 'size', 'finish', 'uid'}], each side listed from the part out
        self.uid = 0      # order rows were added (the '-' button removes the newest when none is highlighted)
        self.sel = None   # highlighted stack row
        self.gen = 0      # table rebuild counter (keeps input ids unique)
        self.hole = None

    def family(self):
        return fc.family(_catalog(), self.code)

    def row(self):
        return fc.size_row(self.family(), self.size)

    def is_screw(self):
        return self.kind == 'screw'


_st = _State()


def _family_items(system, kind):
    items = []
    for f in fc.families(_catalog(), system, kind):
        label = ('%s (%s)' % (f['name'], f['code'])) if kind == 'press-in' else f['name']
        items.append((f['code'], label))
    return items


def _size_items(fam):
    return [(r['size'], fc.thread_label(fam, r)) for r in fam['sizes']]


def _length_items(fam, row):
    return [(str(L), fc.length_label(fam, L)) for L in row['lengths']]


def _finish_items(fam, row):
    """Only finishes a maker sells for this type and size (alloy black oxide is not offered everywhere)."""
    cat = _catalog()
    items = []
    for k in fc.finishes_for(cat, fam, row):
        label = cat['finishes'][k]['name']
        g = fc.grade_label(fc.grade(row, k))
        items.append((k, label + (' (%s)' % g if g else '')))
    return items


def _refresh(inputs, level):
    """level: 'system' rebuilds everything below it, 'family' sizes down, 'size' lengths down."""
    if level == 'system':
        _st.items['family'] = _family_items(_st.system, _st.kind)
        _st.code = _fill(inputs.itemById('family'), _st.items['family'], _st.code)
        level = 'family'
    fam = _st.family()
    if level == 'family':
        _st.items['size'] = _size_items(fam)
        _st.size = _fill(inputs.itemById('size'), _st.items['size'], _st.size)
        level = 'size'
    row = _st.row()
    if level == 'size':
        screw = _st.is_screw()
        press = _st.kind == 'press-in'
        inputs.itemById('length').isVisible = screw or press
        inputs.itemById('thread').isVisible = screw or (press and fam.get('shape') == 'stud')
        if screw or press:
            _st.items['length'] = _length_items(fam, row)
            cur = fc.length_key(row, _st.length)
            picked = _fill(inputs.itemById('length'), _st.items['length'], cur)
            if screw:
                _st.length = float(picked)
            else:
                _st.length = picked
            inputs.itemById('length').name = 'Shank' if fam.get('length_kind') == 'shank' else 'Length'
        # Keep the last screw length when the dialog is on a nut or washer so
        # switching back (or reopening on a nut, then choosing Screws) still lands on it.
        _st.items['finish'] = _finish_items(fam, row)
        _st.finish = _fill(inputs.itemById('finish'), _st.items['finish'], _st.finish)
        for iid in ('mount', 'sheet', 'edge', 'hard'):
            box = inputs.itemById(iid)
            if box is not None:
                box.isVisible = press
        stack = inputs.itemById('stack')
        if stack is not None:
            if press and fc.press_stack_kinds(fam) == ('screw',):
                stack.name = 'Stack a mating screw'
            else:
                stack.name = 'Stack nuts/washers'
            help_box = inputs.itemById('stk_help')
            if help_box is not None:
                if press and fc.press_stack_kinds(fam) == ('screw',):
                    if fam['code'] in ('SO', 'SOS'):
                        help_box.text = ('Near and far each take one screw of this thread. '
                                         'Far is the open end away from the sheet.')
                    elif fam['code'] in ('BSO', 'BSOS'):
                        help_box.text = 'One screw on the open end. Its length stays within the blind thread depth.'
                    else:
                        help_box.text = 'One screw of this thread, on the near side, stacked on the nut.'
                elif press:
                    help_box.text = 'Nuts and washers go on the far side, on the stud thread. The thread must match.'
                else:
                    help_box.text = ('Near side = the picked edge (under the screw head). Far side = the other end of '
                                     'the hole. Each side stacks from the part out, top row first.')
                help_box.isVisible = bool(stack.value)
    _bom_preview(inputs)
    _resize_stack(inputs)


def _bom_preview(inputs):
    fam, row = _st.family(), _st.row()
    bom = fc.bom_fields(_catalog(), fam, row, _st.length, _st.finish)
    inputs.itemById('pn').text = bom['part_number']
    inputs.itemById('desc').text = bom['description']
    inputs.itemById('mat').text = bom['material']
    mount = inputs.itemById('mount')
    if mount is not None:
        if _st.kind == 'press-in' and _st.length is not None:
            mount.text = fc.mount_text(fam, row, _st.length)
        else:
            mount.text = ''


def _edges(inputs):
    sel = inputs.itemById('holes')
    return [sel.selection(i).entity for i in range(sel.selectionCount)]


class _Hole:
    """What the dialog knows about the first picked hole."""

    def __init__(self, hole=None, screw=None, existing=()):
        self.hole, self.screw, self.existing = hole, screw, list(existing)

    @property
    def thread(self):
        return self.hole.thread if self.hole else None

    @property
    def dia(self):
        return self.hole.radius * 2.0 if self.hole else None


def _first_hole(inputs):
    edges = _edges(inputs)
    if not edges:
        return _Hole()
    hole = fp.read_hole(edges[0], inputs.itemById('flip').value)
    if hole is None:
        return _Hole()
    design = adsk.fusion.Design.cast(_app().activeProduct)
    existing = fp.existing_items(_catalog(), design, hole)
    screw = next((i for i in existing if i['kind'] == 'screw'), None)
    return _Hole(hole, screw, existing)


def _screw_ref(h):
    """Thread of the screw the nuts and washers must fit: the screw being inserted, else a screw already in the
    first hole. None means size from the hole."""
    if _st.is_screw() and _st.code and _st.size:
        return fc.thread_ref(_st.family(), _st.row())
    if h.screw is not None:
        return fc.thread_ref(h.screw['fam'], h.screw['row'])
    return None


def _hole_note(inputs):
    """Describe the first picked hole, auto-pick sizes (screw from the hole; nuts and washers from the screw first,
    the hole only when there is no screw) and show warnings."""
    box = inputs.itemById('holeinfo')
    edges = _edges(inputs)
    if not edges:
        if _st.kind == 'press-in':
            box.text = ('Pick the hole edge on the install face. Tick the stack box to add the mating screw, '
                        'or a nut and washer on a stud. The thread must match.')
        else:
            box.text = ('Pick circular hole edges on the side the part goes: the top edge (or countersink) for a screw '
                        'or a washer under its head, the bottom edge of a through hole for a nut.')
        _st.hole = _Hole()
        _refresh_stack(inputs)
        return
    try:
        h = _first_hole(inputs)
        _st.hole = h
        fam = _st.family()
        unit = ('%.3f in' % (h.dia / 2.54) if fam['system'] == 'inch' else '%.2f mm' % (h.dia * 10)) if h.dia else '?'
        msg = '%d hole(s). First hole: %s, %s.' % (len(edges), unit,
                                                   ('tapped ' + h.thread) if h.thread else 'not tapped')
        if h.screw is not None:
            msg += ' Already has %s.' % fc.item_label(_catalog(), h.screw)
        if inputs.itemById('auto').value and _st.kind == 'press-in':
            size = fc.press_size_for(fam, h.dia)
            if size and size != _st.size:
                _st.size = size
                _refresh(inputs, 'family')
                msg += ' Size set to %s.' % size
            elif not size:
                msg += ' No PEM size matches this hole; check it.'
            _prefill_sheet(inputs, edges[0])
        elif inputs.itemById('auto').value:
            sref = None if _st.is_screw() else _screw_ref(h)
            size = fc.size_for(_catalog(), fam, sref, h.thread, h.dia)
            if size and size != _st.size:
                _st.size = size
                _refresh(inputs, 'family')
                msg += ' Size set to %s.' % size
            elif not size:
                msg += ' No size in this type fits; check it.'
        box.text = msg
    except Exception as e:
        box.text = 'Could not read that edge: %s' % e
    _refresh_stack(inputs)


# ---------- stack (nuts and washers on either side) ----------

SIDES = [('near', 'Near side'), ('far', 'Far side')]
PARTS = [('nut', 'Nut'), ('washer', 'Washer')]
_KIND_LABEL = {'screw': 'Screw', 'nut': 'Nut', 'washer': 'Washer'}


def _stack_parts():
    """Part kinds the +/- row may be. A PEM offers only the mate its thread can take."""
    if _st.kind == 'press-in' and _st.code:
        kinds = fc.press_stack_kinds(_st.family())
        if kinds:
            return [(k, _KIND_LABEL[k]) for k in kinds]
    return list(PARTS)


def _stack_sides():
    if _st.kind == 'press-in' and _st.code:
        sides = fc.press_stack_sides(_st.family())
        if sides:
            return [(k, n) for k, n in SIDES if k in sides]
    return list(SIDES)


def _stack_ref():
    """Ref the stack rows size from: the PEM thread when the main part is press-in, else the screw (inserted or
    already in the hole), else the hole's thread, else None (rows then size from the hole diameter)."""
    h = getattr(_st, 'hole', None) or _Hole()
    if _st.kind == 'press-in' and _st.code and _st.size:
        return fc.mate_thread(_st.family(), _st.row()), h
    ref = _screw_ref(h)
    if ref is None and h.thread:
        ref = fc.ref_from_designation(h.thread)
    if ref is None and h.hole is None and _st.code and _st.size:
        ref = fc.thread_ref(_st.family(), _st.row())  # nothing picked yet: follow the dialog's size for now
    return ref, h


def _row_size(fam, ref, h):
    if ref is not None:
        return fc.row_for_ref(fam, ref)
    return fc.suggest_size(_catalog(), fam, h.dia) if h.dia else None


def _type_choices(kind, ref, h):
    """[(code, name, size)] of the types of this part that have a size matching the screw (or hole)."""
    out = []
    for f in fc.families(_catalog(), _st.system, kind):
        size = _row_size(f, ref, h)
        if size:
            out.append((f['code'], f['name'], size))
    return out


def _target_finish():
    h = getattr(_st, 'hole', None) or _Hole()
    if _st.is_screw() or h.screw is None:
        return _st.finish
    return h.screw['finish']


def _settle_row(r, ref, h):
    """Fix a row's type, size and material so they fit; returns the type choices."""
    choices = _type_choices(r['kind'], ref, h)
    codes = [c for c, _, _ in choices]
    if r.get('code') not in codes:
        r['code'] = codes[0] if codes else None
    r['size'] = next((sz for c, _, sz in choices if c == r['code']), None)
    if r['code'] and r['size']:
        fam = fc.family(_catalog(), r['code'])
        row = fc.size_row(fam, r['size'])
        offered = fc.finishes_for(_catalog(), fam, row)
        # A PEM finish is not a match target for the screw or nut stacked on it.
        target = _target_finish()
        if _st.kind == 'press-in':
            target = 'SS' if 'SS' in offered else (offered[0] if offered else target)
        if r.get('finish') not in offered:
            r['finish'] = fc.matching_finish(_catalog(), fam, row, target) or offered[0]
        if r['kind'] == 'screw':
            if fc.length_key(row, r.get('length')) is None and _st.kind == 'press-in' and _st.length is not None:
                r['length'] = fc.fitting_screw_length(_st.family(), _st.row(), _st.length, row)
            elif fc.length_key(row, r.get('length')) is None:
                r['length'] = row['lengths'][0]
            else:
                r['length'] = next(L for L in row['lengths'] if fc.length_key(row, L) == fc.length_key(row, r['length']))
    return choices


STACK_BUTTONS = ('stk_add', 'stk_del', 'stk_up', 'stk_dn')


def _stack_table(inputs):
    return inputs.itemById('stk_tbl')


def _refresh_stack(inputs):
    """Rebuild the stack table from _st.stack (rows are re-created so ids stay unique)."""
    table = _stack_table(inputs)
    if table is None:
        return
    on = inputs.itemById('stack').value
    table.isVisible = on
    for bid in STACK_BUTTONS:  # Fusion keeps toolbar buttons on screen when only the table is hidden
        btn = inputs.itemById(bid)
        if btn is not None:
            btn.isVisible = on
            btn.isEnabled = on
    if not on:
        _show_warnings(inputs)
        return
    ref, h = _stack_ref()
    while table.rowCount > 0:
        table.deleteRow(0)
    ci = table.commandInputs
    _st.gen += 1
    g = _st.gen
    for c, head in enumerate(('Side', 'Part', 'Type', 'Size', 'Length', 'Material')):
        table.addCommandInput(ci.addTextBoxCommandInput('stk%d_h%d' % (g, c), '', '<b>%s</b>' % head, 1, True), 0, c)
    sides = _stack_sides()
    parts = _stack_parts()
    for i, r in enumerate(_st.stack):
        if r.get('side') not in [k for k, _ in sides]:
            r['side'] = sides[0][0]
        if r.get('kind') not in [k for k, _ in parts]:
            r['kind'] = parts[0][0]
        choices = _settle_row(r, ref, h)
        rid = 'stk%d_%d_' % (g, i)
        side = ci.addDropDownCommandInput(rid + 'side', '', adsk.core.DropDownStyles.TextListDropDownStyle)
        _fill(side, sides, r['side'])
        part = ci.addDropDownCommandInput(rid + 'kind', '', adsk.core.DropDownStyles.TextListDropDownStyle)
        _fill(part, parts, r['kind'])
        typ = ci.addDropDownCommandInput(rid + 'code', '', adsk.core.DropDownStyles.TextListDropDownStyle)
        _fill(typ, [(c, n) for c, n, _ in choices], r['code'])
        size_txt = '-'
        fin_items = []
        length_inp = None
        if r['code'] and r['size']:
            fam = fc.family(_catalog(), r['code'])
            row = fc.size_row(fam, r['size'])
            size_txt = fc.desc_thread(fam, row)
            fin_items = _finish_items(fam, row)
            if r['kind'] == 'screw':
                length_inp = ci.addDropDownCommandInput(rid + 'length', '',
                                                        adsk.core.DropDownStyles.TextListDropDownStyle)
                picked = _fill(length_inp, [(str(L), fc.length_label(fam, L)) for L in row['lengths']],
                               fc.length_key(row, r.get('length')))
                r['length'] = next(L for L in row['lengths'] if str(L) == picked)
        size = ci.addTextBoxCommandInput(rid + 'size', '', size_txt, 1, True)
        if length_inp is None:
            length_inp = ci.addTextBoxCommandInput(rid + 'length', '', '-', 1, True)
        fin = ci.addDropDownCommandInput(rid + 'finish', '', adsk.core.DropDownStyles.TextListDropDownStyle)
        _fill(fin, fin_items, r.get('finish'))
        for c, inp in enumerate((side, part, typ, size, length_inp, fin)):
            table.addCommandInput(inp, i + 1, c)
    _resize_stack(inputs)
    if _st.sel is not None and 0 <= _st.sel < len(_st.stack):
        try:
            table.selectedRow = _st.sel + 1
        except Exception:
            pass
    _show_warnings(inputs)


def _resize_stack(inputs):
    table = _stack_table(inputs)
    if table is None:
        return
    n = max(2, len(_st.stack) + 1)
    # Fusion rejects min > max, so grow the max first and shrink the min first
    order = ('maximumVisibleRows', 'minimumVisibleRows') if n >= table.maximumVisibleRows else \
        ('minimumVisibleRows', 'maximumVisibleRows')
    for name in order:
        try:
            setattr(table, name, n)
        except Exception:
            pass


def _selected_index(inputs):
    table = _stack_table(inputs)
    try:
        r = table.selectedRow - 1
    except Exception:
        r = -1
    return r if 0 <= r < len(_st.stack) else None


def _stack_button(inputs, cid):
    sel = _selected_index(inputs)
    if cid == 'stk_add':
        last = _st.stack[-1] if _st.stack else None
        sides = [k for k, _ in _stack_sides()]
        kinds = [k for k, _ in _stack_parts()]
        side = last['side'] if last and last.get('side') in sides else sides[0]
        kind = last['kind'] if last and last.get('kind') in kinds else kinds[0]
        _st.uid += 1
        _st.sel = fc.stack_add(_st.stack, {'side': side, 'kind': kind, 'code': None,
                                           'finish': None if _st.kind == 'press-in' else _target_finish()}, _st.uid)
    elif cid == 'stk_del':
        fc.stack_remove(_st.stack, sel)
        _st.sel = None
    elif cid in ('stk_up', 'stk_dn'):
        _st.sel = fc.stack_move(_st.stack, sel, -1 if cid == 'stk_up' else 1)
    _refresh_stack(inputs)


def _stack_row_changed(inputs, cid):
    """A dropdown inside the table changed: stk<gen>_<row>_<field>."""
    try:
        head, i, field = cid.split('_', 2)
        i = int(i)
    except ValueError:
        return
    if not (0 <= i < len(_st.stack)):
        return
    r = _st.stack[i]
    dd = inputs.itemById(cid)
    if dd is None or dd.selectedItem is None:
        return
    label = dd.selectedItem.name
    if field == 'side':
        r['side'] = next(k for k, n in _stack_sides() if n == label)
    elif field == 'kind':
        r['kind'] = next(k for k, n in _stack_parts() if n == label)
        r['code'] = None
    elif field == 'code':
        ref, h = _stack_ref()
        r['code'] = next((c for c, n, _ in _type_choices(r['kind'], ref, h) if n == label), r['code'])
    elif field == 'length':
        fam = fc.family(_catalog(), r['code'])
        row = fc.size_row(fam, r['size'])
        r['length'] = next(L for L in row['lengths'] if fc.length_label(fam, L) == label)
    elif field == 'finish':
        fam = fc.family(_catalog(), r['code'])
        r['finish'] = next((k for k, n in _finish_items(fam, fc.size_row(fam, r['size'])) if n == label), r['finish'])
    _st.sel = i
    _later_refresh_stack()


# A dropdown inside the table must not delete its own row while Fusion is still handling its change (that
# crashed Fusion in live testing), so row edits rebuild the table from a custom event after the handler returns.
REFRESH_EVENT = 'srFastenerStackRefresh'
_refresh_event = {}


class _RefreshHandler(adsk.core.CustomEventHandler):
    def notify(self, args):
        try:
            cmd = _last.get('cmd')
            if cmd is not None and getattr(cmd, 'isValid', True):
                _refresh_stack(cmd.commandInputs)
        except Exception:
            pass


def _later_refresh_stack():
    try:
        if not _refresh_event:
            ev = _app().registerCustomEvent(REFRESH_EVENT)
            h = _RefreshHandler()
            ev.add(h)
            _refresh_event.update(event=ev, handler=h)
        _app().fireCustomEvent(REFRESH_EVENT, '')
    except Exception:
        pass


def _drop_refresh_event():
    if _refresh_event:
        try:
            _refresh_event['event'].remove(_refresh_event['handler'])
            _app().unregisterCustomEvent(REFRESH_EVENT)
        except Exception:
            pass
        _refresh_event.clear()


def _needs_length():
    return _st.is_screw() or _st.kind == 'press-in'


def _read_num(inputs, iid):
    """Number typed in a press-in box, or None when the box is blank or hidden."""
    box = inputs.itemById(iid) if inputs is not None else None
    if box is None or not box.isVisible:
        return None
    text = (box.text or '').strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _prefill_sheet(inputs, edge):
    """Fill blank sheet and edge boxes from the picked hole. Hardness is not in the model."""
    try:
        sheet, edge_mm = fp.measure_mount(edge)
    except Exception:
        return
    for iid, value in (('sheet', sheet), ('edge', edge_mm)):
        box = inputs.itemById(iid)
        if box is not None and not (box.text or '').strip() and value is not None:
            box.text = '%g' % value


def _main_item():
    if not (_st.code and _st.size):
        return None
    if _needs_length() and _st.length is None:
        return None
    return fc.item(_catalog(), _st.code, _st.size, _st.finish, _st.length if _needs_length() else None)


def _stack_items(inputs):
    if not inputs.itemById('stack').value:
        return []
    out = []
    for r in _st.stack:
        if r.get('code') and r.get('size') and r.get('finish'):
            length = r.get('length') if r.get('kind') == 'screw' else None
            it = fc.item(_catalog(), r['code'], r['size'], r['finish'], length)
            it['side'] = r['side']
            out.append(it)
    return out


def _warnings(inputs, h=None):
    h = h or getattr(_st, 'hole', None) or _Hole()
    if _st.kind == 'press-in' and _st.code and _st.size and _st.length is not None:
        spec = fc.mount_spec(_st.family(), _st.row(), _st.length)
        hole_mm = (h.dia * 10.0) if h and h.dia else None
        warns = fc.press_warnings(spec, hole_mm, _read_num(inputs, 'sheet'), _read_num(inputs, 'edge'),
                                  _read_num(inputs, 'hard'))
        main = _main_item()
        rows = _stack_items(inputs)
        if main and rows:
            warns += [m for _, m in fc.press_stack_issues(_catalog(), main, rows)]
        return warns
    main = _main_item()
    items = list(h.existing) + ([main] if main else []) + _stack_items(inputs)
    return fc.compat_warnings(_catalog(), items, h.thread, h.dia) if items else []


def _show_warnings(inputs):
    box = inputs.itemById('warn')
    if box is None:
        return
    w = _warnings(inputs)
    box.text = ('Check: ' + '; '.join(w)) if w else 'Hardware matches.'


def _run_place(inputs, main=None, rows=None):
    app = _app()
    design = adsk.fusion.Design.cast(app.activeProduct)
    main = _main_item() if main is None else main
    rows = _stack_items(inputs) if rows is None else rows
    return fp.place_stack(app, design, _catalog(), main, rows, _edges(inputs),
                          flip=inputs.itemById('flip').value, thread=inputs.itemById('thread').value)


def _material_prompt(inputs):
    """If the new parts' materials differ from each other or from parts already in the first hole, ask whether to
    switch the new parts to match. Press-in parts are ignored, as the new part and as a part already in the hole.
    Returns (main, rows) to place, or None to go back to the dialog."""
    cat = _catalog()
    h = _first_hole(inputs)
    main, rows = _main_item(), _stack_items(inputs)
    new = ([main] if main else []) + rows
    if not fc.should_ask_material(cat, h.existing, new):
        return main, rows
    existing = fc.material_items(h.existing)
    fresh = fc.material_items(new)
    if h.screw is not None:
        target = h.screw['finish']
    elif main and main['kind'] == 'screw':
        target = main['finish']
    elif existing:
        target = existing[0]['finish']
    else:
        target = fresh[0]['finish']
    tname = cat['finishes'][target]['name']
    names = sorted({cat['finishes'][i['finish']]['name'] for i in existing + fresh})
    res = _ui().messageBox('These parts are different materials: %s.\n\nYes: switch the new parts to %s where that '
                           'material is sold.\nNo: insert them as picked.\nCancel: back to the dialog.'
                           % (', '.join(names), tname), CMD_NAME,
                           adsk.core.MessageBoxButtonTypes.YesNoCancelButtonType,
                           adsk.core.MessageBoxIconTypes.QuestionIconType)
    if res == adsk.core.DialogResults.DialogCancel:
        return None
    if res == adsk.core.DialogResults.DialogYes:
        updated, kept = fc.match_finishes(cat, new, target)
        for src, dst in zip(updated, new):
            dst['finish'] = src['finish']
        if main and main['kind'] != 'press-in':
            _st.finish = main['finish']
        usable = [r for r in _st.stack if r.get('code') and r.get('size') and r.get('finish')]
        for r, it in zip(usable, rows):
            r['finish'] = it['finish']
        if kept:
            _ui().messageBox('Not sold in %s, left as picked: %s' % (tname, ', '.join(kept)), CMD_NAME)
    return main, rows


# ---------- event handlers ----------

class _Created(adsk.core.CommandCreatedEventHandler):
    def notify(self, args):
        try:
            design = adsk.fusion.Design.cast(_app().activeProduct)
            if design is None:
                _ui().messageBox('Open a design first.', CMD_NAME)
                return
            s = _load_settings()
            _st.system = s.get('system', 'metric')
            _st.kind = s.get('kind', 'screw')
            _st.code = s.get('family')
            _st.size = s.get('size')
            _st.length = s.get('length')
            _st.finish = s.get('finish', 'SS')
            _st.stack, _st.uid, _st.sel, _st.hole = [], 0, None, None
            for r in s.get('stack_rows') or []:
                if r.get('side') in ('near', 'far') and r.get('kind') in ('nut', 'washer', 'screw'):
                    _st.uid += 1
                    _st.stack.append({'side': r['side'], 'kind': r['kind'], 'code': r.get('code'),
                                      'finish': r.get('finish', _st.finish), 'uid': _st.uid})
            cmd = args.command
            _last['cmd'] = cmd
            cmd.okButtonText = 'Insert'
            cmd.setDialogInitialSize(520, 560)
            inputs = cmd.commandInputs
            sysdd = inputs.addDropDownCommandInput('system', 'Units', adsk.core.DropDownStyles.TextListDropDownStyle)
            _st.system = _fill(sysdd, SYSTEMS, _st.system)
            kinddd = inputs.addDropDownCommandInput('kind', 'Part', adsk.core.DropDownStyles.TextListDropDownStyle)
            _st.kind = _fill(kinddd, list(fc.KINDS), _st.kind)
            inputs.addDropDownCommandInput('family', 'Type', adsk.core.DropDownStyles.TextListDropDownStyle)
            inputs.addDropDownCommandInput('size', 'Size', adsk.core.DropDownStyles.TextListDropDownStyle)
            inputs.addDropDownCommandInput('length', 'Length', adsk.core.DropDownStyles.TextListDropDownStyle)
            inputs.addDropDownCommandInput('finish', 'Material', adsk.core.DropDownStyles.TextListDropDownStyle)
            sel = inputs.addSelectionInput('holes', 'Holes', 'Pick circular hole edges')
            sel.addSelectionFilter('CircularEdges')
            sel.setSelectionLimits(1, 0)
            # Daniel 2026-11-17: on by default every time the dialog opens
            inputs.addBoolValueInput('auto', 'Match size to first hole', True, '', True)
            inputs.addBoolValueInput('flip', 'Flip direction', True, '', False)
            inputs.addBoolValueInput('thread', 'Cosmetic thread', True, '', bool(s.get('thread', True)))
            inputs.addBoolValueInput('stack', 'Stack nuts/washers', True, '', bool(s.get('stack_on', False)))
            table = inputs.addTableCommandInput('stk_tbl', 'Stack', 6, '2:2:3:2:2:3')
            table.tablePresentationStyle = adsk.core.TablePresentationStyles.itemBorderTablePresentationStyle
            ti = table.commandInputs
            for bid, label, tip in (('stk_add', '+', 'Add a nut or washer'),
                                    ('stk_del', '\u2212', 'Remove the highlighted row (or the newest one)'),
                                    ('stk_up', 'Up', 'Move the highlighted row up'),
                                    ('stk_dn', 'Down', 'Move the highlighted row down')):
                btn = ti.addBoolValueInput(bid, label, False, '', False)
                btn.tooltip = tip
                table.addToolbarCommandInput(btn)
            inputs.addTextBoxCommandInput('stk_help', '', 'Near side = the picked edge (under the screw head). Far '
                                          'side = the other end of the hole. Each side stacks from the part out, '
                                          'top row first.', 2, True)
            inputs.addTextBoxCommandInput('holeinfo', 'Hole', '', 2, True)
            inputs.addTextBoxCommandInput('mount', 'Mounting', '', 4, True)
            inputs.addTextBoxCommandInput('sheet', 'Sheet thickness mm', '', 1, False)
            inputs.addTextBoxCommandInput('edge', 'Centerline to edge mm', '', 1, False)
            inputs.addTextBoxCommandInput('hard', 'Sheet hardness HRB', '', 1, False)
            inputs.addTextBoxCommandInput('warn', 'Warnings', '', 2, True)
            grp = inputs.addGroupCommandInput('bom', 'BOM')
            gi = grp.children
            gi.addTextBoxCommandInput('pn', 'Part number', '', 1, True)
            gi.addTextBoxCommandInput('desc', 'Description', '', 2, True)
            gi.addTextBoxCommandInput('mat', 'Material', '', 1, True)
            _refresh(inputs, 'system')
            inputs.itemById('stk_help').isVisible = inputs.itemById('stack').value
            _hole_note(inputs)  # also hides the stack table (and its buttons) while the checkbox is off
            for ev, h in ((cmd.inputChanged, _Changed()), (cmd.executePreview, _Preview()),
                          (cmd.execute, _Execute()), (cmd.validateInputs, _Validate()),
                          (cmd.destroy, _Destroy())):
                ev.add(h)
                _handlers.append(h)
        except Exception:
            _ui().messageBox('SR Fastener failed to open:\n' + traceback.format_exc(), CMD_NAME)


def _root_inputs(args):
    try:
        return args.firingEvent.sender.commandInputs
    except Exception:
        return args.inputs


class _Changed(adsk.core.InputChangedEventHandler):
    def notify(self, args):
        try:
            inputs = _root_inputs(args)
            cid = args.input.id
            if cid == 'system':
                _st.system = _sel_key(inputs.itemById('system'), SYSTEMS)
                _refresh(inputs, 'system')
                _hole_note(inputs)
            elif cid == 'kind':
                _st.kind = _sel_key(inputs.itemById('kind'), list(fc.KINDS))
                _st.code = None
                _refresh(inputs, 'system')
                _hole_note(inputs)
            elif cid == 'family':
                _st.code = _sel_key(inputs.itemById('family'), _st.items['family'])
                _refresh(inputs, 'family')
                _hole_note(inputs)
            elif cid == 'size':
                _st.size = _sel_key(inputs.itemById('size'), _st.items['size'])
                _refresh(inputs, 'size')
                _refresh_stack(inputs)
            elif cid == 'length':
                key = _sel_key(inputs.itemById('length'), _st.items['length'])
                _st.length = key if _st.kind == 'press-in' else float(key)
                _bom_preview(inputs)
                _show_warnings(inputs)
            elif cid in ('sheet', 'edge', 'hard'):
                _show_warnings(inputs)
            elif cid == 'finish':
                _st.finish = _sel_key(inputs.itemById('finish'), _st.items['finish'])
                _bom_preview(inputs)
                _show_warnings(inputs)
            elif cid in ('holes', 'flip', 'auto'):
                _hole_note(inputs)
            elif cid == 'stack':
                inputs.itemById('stk_help').isVisible = args.input.value
                _refresh_stack(inputs)
                _show_warnings(inputs)
            elif cid in STACK_BUTTONS:
                _stack_button(inputs, cid)
            elif cid.startswith('stk') and '_' in cid:
                _stack_row_changed(inputs, cid)
        except Exception:
            _ui().messageBox('SR Fastener:\n' + traceback.format_exc(), CMD_NAME)


class _Validate(adsk.core.ValidateInputsEventHandler):
    def notify(self, args):
        inputs = args.inputs
        args.areInputsValid = bool(_edges(inputs)) and (_main_item() is not None or bool(_stack_items(inputs)))


class _Preview(adsk.core.CommandEventHandler):
    def notify(self, args):
        fp.PREVIEW = True
        try:
            _run_place(args.command.commandInputs)
        except Exception:
            pass
        finally:
            fp.PREVIEW = False


class _Execute(adsk.core.CommandEventHandler):
    def notify(self, args):
        try:
            inputs = args.command.commandInputs
            picked = _material_prompt(inputs)
            if picked is None:
                args.executeFailed = True
                args.executeFailedMessage = 'Insert cancelled: pick matching materials and try again.'
                return
            main, rows = picked
            warns = []
            for edge in _edges(inputs):
                hole = fp.read_hole(edge, inputs.itemById('flip').value)
                if hole is None:
                    continue
                if main and main['kind'] == 'press-in':
                    spec = fc.mount_spec(main['fam'], main['row'], main['length'])
                    warns += fc.press_warnings(spec, hole.radius * 20.0, _read_num(inputs, 'sheet'),
                                               _read_num(inputs, 'edge'), _read_num(inputs, 'hard'))
                    warns += [msg for _, msg in fc.press_stack_issues(_catalog(), main, rows)]
                    continue
                design = adsk.fusion.Design.cast(_app().activeProduct)
                items = fp.existing_items(_catalog(), design, hole) + ([main] if main else []) + rows
                warns += fc.compat_warnings(_catalog(), items, hole.thread, 2 * hole.radius)
            occs, notes = _run_place(inputs, main, rows)
            old = _load_settings()
            _save_settings({'system': _st.system, 'kind': _st.kind, 'family': _st.code, 'size': _st.size,
                            'length': _st.length if _needs_length() else old.get('length'),
                            'finish': _st.finish, 'thread': inputs.itemById('thread').value,
                            'stack_on': inputs.itemById('stack').value,
                            'stack_rows': [{k: r.get(k) for k in ('side', 'kind', 'code', 'finish')} for r in _st.stack]})
            msgs = sorted(set(warns)) + sorted(set(notes))
            if msgs:
                _ui().messageBox('Placed %d part(s).\n\nCheck:\n- %s' % (len(occs), '\n- '.join(msgs)), CMD_NAME)
        except Exception:
            _ui().messageBox('SR Fastener failed:\n' + traceback.format_exc(), CMD_NAME)


class _Destroy(adsk.core.CommandEventHandler):
    def notify(self, args):
        _last.pop('cmd', None)


# ---------- add-in entry points ----------

def _find_panel(ui, s):
    """(panel, created) for a spec; creates the panel on its tab when the spec asks for it."""
    ws = ui.workspaces.itemById(s['workspace'])
    if ws is None:
        return None, False
    panel = ws.toolbarPanels.itemById(s['panel'])
    if panel is not None or not s['create']:
        return panel, False
    tab = ws.toolbarTabs.itemById(s['tab'])
    if tab is None:
        return None, False
    return tab.toolbarPanels.add(s['panel'], s['name']), True


def _remove_controls(ui):
    """Remove every control this add-in added, and any panel it created that is now empty."""
    for wid, pid, created in reversed(_placed):
        try:
            ws = ui.workspaces.itemById(wid)
            panel = ws.toolbarPanels.itemById(pid) if ws else None
            if panel is None:
                continue
            ctrl = panel.controls.itemById(CMD_ID)
            if ctrl:
                ctrl.deleteMe()
            if created and panel.controls.count == 0:
                panel.deleteMe()
        except Exception:
            pass
    _placed.clear()


def run(context):
    try:
        ui = _ui()
        _remove_controls(ui)
        cdef = ui.commandDefinitions.itemById(CMD_ID)
        if cdef:
            cdef.deleteMe()
        res = os.path.join(_HERE, 'resources', 'cmd')
        cdef = ui.commandDefinitions.addButtonDefinition(CMD_ID, CMD_NAME, CMD_TIP, res)
        h = _Created()
        cdef.commandCreated.add(h)
        _handlers.append(h)
        specs, problems = sp.load(PANELS_FILE)
        for s in specs:
            panel, created = _find_panel(ui, s)
            if panel is None:
                problems.append('panel %s not found in %s' % (s['panel'], s['workspace']))
                continue
            old = panel.controls.itemById(CMD_ID)
            if old:
                old.deleteMe()
            ctrl = panel.controls.addCommand(cdef)
            if s['promote']:
                ctrl.isPromoted = True
                ctrl.isPromotedByDefault = True
            _placed.append((s['workspace'], s['panel'], s['create']))
        if problems:
            ui.messageBox('SR Fastener panel settings (%s):\n' % PANELS_FILE + '\n'.join(problems), CMD_NAME)
    except Exception:
        _ui().messageBox('SR Fastener failed to start:\n' + traceback.format_exc(), CMD_NAME)


def stop(context):
    try:
        ui = _ui()
        _remove_controls(ui)
        cdef = ui.commandDefinitions.itemById(CMD_ID)
        if cdef:
            cdef.deleteMe()
        _drop_refresh_event()
        _handlers.clear()
    except Exception:
        pass
