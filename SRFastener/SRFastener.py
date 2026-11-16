"""SR Fastener: pick a screw (type, size, length, finish), click hole edges, and it is placed, joined and BOM-filled.

Library screws are made by this add-in from data/catalog.json. Nobody opens or inserts a library file by hand.
"""
import json
import os
import traceback

import adsk.core
import adsk.fusion

_HERE = os.path.dirname(os.path.abspath(__file__))

from . import fastener_core as fc  # noqa: E402
from . import fastener_place as fp  # noqa: E402

CMD_ID = 'srFastenerInsertCmd'
CMD_NAME = 'SR Fastener'
CMD_TIP = ('Insert a socket head, button head, flat head, low-profile or hex head bolt, or a cup-tip or flat-tip set screw, into hole edges. '
           'Pick type, size, length and finish (stainless, stainless black oxide or alloy black oxide); '
           'BOM fields fill in.')
WORKSPACE = 'FusionSolidEnvironment'
PANELS = ['InsertPanel', 'SolidScriptsAddinsPanel']
SYSTEMS = [('metric', 'Metric'), ('inch', 'Inch')]
SETTINGS_DIR = os.path.join(os.environ.get('APPDATA') or os.path.expanduser('~'), 'SRFastener')
SETTINGS_FILE = os.path.join(SETTINGS_DIR, 'settings.json')

_handlers = []
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
        self.code = None
        self.size = None
        self.length = None
        self.finish = 'SS'
        self.items = {}

    def family(self):
        return fc.family(_catalog(), self.code)

    def row(self):
        return fc.size_row(self.family(), self.size)


_st = _State()


def _family_items(system):
    return [(f['code'], '%s (%s)' % (f['name'], f['standard'])) for f in fc.families(_catalog(), system)]


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
        g = fc.grade(row, k)
        items.append((k, label + (' (%s)' % g if g else '')))
    return items


def _refresh(inputs, level):
    """level: 'system' rebuilds everything below it, 'family' sizes down, 'size' lengths down."""
    if level == 'system':
        _st.items['family'] = _family_items(_st.system)
        _st.code = _fill(inputs.itemById('family'), _st.items['family'], _st.code)
        level = 'family'
    fam = _st.family()
    if level == 'family':
        _st.items['size'] = _size_items(fam)
        _st.size = _fill(inputs.itemById('size'), _st.items['size'], _st.size)
        level = 'size'
    row = _st.row()
    if level == 'size':
        _st.items['length'] = _length_items(fam, row)
        cur = str(_st.length) if _st.length is not None else None
        _st.length = float(_fill(inputs.itemById('length'), _st.items['length'], cur))
        _st.items['finish'] = _finish_items(fam, row)
        _st.finish = _fill(inputs.itemById('finish'), _st.items['finish'], _st.finish)
    _bom_preview(inputs)


def _bom_preview(inputs):
    fam, row = _st.family(), _st.row()
    bom = fc.bom_fields(_catalog(), fam, row, _st.length, _st.finish)
    inputs.itemById('pn').text = bom['part_number']
    inputs.itemById('desc').text = bom['description']
    inputs.itemById('mat').text = '%s%s  (appearance: %s)' % (bom['material'], (', ' + bom['grade']) if bom['grade'] else '',
                                                              bom['appearance'])


def _edges(inputs):
    sel = inputs.itemById('holes')
    return [sel.selection(i).entity for i in range(sel.selectionCount)]


def _hole_note(inputs):
    """Describe the first picked hole and auto-pick the size if it is threaded or an obvious fit."""
    edges = _edges(inputs)
    box = inputs.itemById('holeinfo')
    if not edges:
        box.text = 'Pick one or more circular hole edges (top edge of each hole or countersink).'
        return
    try:
        hole = fp.read_hole(edges[0], inputs.itemById('flip').value)
        dia = hole.radius * 2.0
        fam = _st.family()
        size = fc.size_from_designation(fam, hole.thread) if hole.thread else fc.suggest_size(_catalog(), fam, dia)
        unit = '%.3f in' % (dia / 2.54) if fam['system'] == 'inch' else '%.2f mm' % (dia * 10)
        msg = '%d hole(s). First hole: %s%s.' % (len(edges), unit, (', thread ' + hole.thread) if hole.thread else '')
        if size and size != _st.size and inputs.itemById('auto').value:
            _st.size = size
            inputs.itemById('size').listItems.clear()
            _refresh(inputs, 'family')
            msg += ' Size set to %s.' % size
        elif not size:
            msg += ' No size in this type fits that hole; check it.'
        box.text = msg
    except Exception as e:
        box.text = 'Could not read that edge: %s' % e


def _run_place(inputs):
    app = _app()
    design = adsk.fusion.Design.cast(app.activeProduct)
    fam, row = _st.family(), _st.row()
    return fp.place(app, design, _catalog(), fam, row, _st.length, _st.finish, _edges(inputs),
                    flip=inputs.itemById('flip').value, thread=inputs.itemById('thread').value)


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
            _st.code = s.get('family')
            _st.size = s.get('size')
            _st.length = s.get('length')
            _st.finish = s.get('finish', 'SS')
            cmd = args.command
            cmd.okButtonText = 'Insert'
            cmd.setDialogInitialSize(460, 520)
            inputs = cmd.commandInputs
            sysdd = inputs.addDropDownCommandInput('system', 'Units', adsk.core.DropDownStyles.TextListDropDownStyle)
            _st.system = _fill(sysdd, SYSTEMS, _st.system)
            inputs.addDropDownCommandInput('family', 'Type', adsk.core.DropDownStyles.TextListDropDownStyle)
            inputs.addDropDownCommandInput('size', 'Size', adsk.core.DropDownStyles.TextListDropDownStyle)
            inputs.addDropDownCommandInput('length', 'Length', adsk.core.DropDownStyles.TextListDropDownStyle)
            inputs.addDropDownCommandInput('finish', 'Finish', adsk.core.DropDownStyles.TextListDropDownStyle)
            sel = inputs.addSelectionInput('holes', 'Holes', 'Pick circular hole edges')
            sel.addSelectionFilter('CircularEdges')
            sel.setSelectionLimits(1, 0)
            inputs.addBoolValueInput('auto', 'Match size to first hole', True, '', bool(s.get('auto', True)))
            inputs.addBoolValueInput('flip', 'Flip direction', True, '', False)
            inputs.addBoolValueInput('thread', 'Cosmetic thread', True, '', bool(s.get('thread', True)))
            inputs.addTextBoxCommandInput('holeinfo', 'Hole', '', 2, True)
            grp = inputs.addGroupCommandInput('bom', 'BOM')
            gi = grp.children
            gi.addTextBoxCommandInput('pn', 'Part number', '', 1, True)
            gi.addTextBoxCommandInput('desc', 'Description', '', 3, True)
            gi.addTextBoxCommandInput('mat', 'Material', '', 2, True)
            _refresh(inputs, 'system')
            _hole_note(inputs)
            for ev, h in ((cmd.inputChanged, _Changed()), (cmd.executePreview, _Preview()),
                          (cmd.execute, _Execute()), (cmd.validateInputs, _Validate()),
                          (cmd.destroy, _Destroy())):
                ev.add(h)
                _handlers.append(h)
        except Exception:
            _ui().messageBox('SR Fastener failed to open:\n' + traceback.format_exc(), CMD_NAME)


class _Changed(adsk.core.InputChangedEventHandler):
    def notify(self, args):
        try:
            inputs = args.inputs
            cid = args.input.id
            if cid == 'system':
                _st.system = _sel_key(inputs.itemById('system'), SYSTEMS)
                _refresh(inputs, 'system')
            elif cid == 'family':
                _st.code = _sel_key(inputs.itemById('family'), _st.items['family'])
                _refresh(inputs, 'family')
            elif cid == 'size':
                _st.size = _sel_key(inputs.itemById('size'), _st.items['size'])
                _refresh(inputs, 'size')
            elif cid == 'length':
                _st.length = float(_sel_key(inputs.itemById('length'), _st.items['length']))
                _bom_preview(inputs)
            elif cid == 'finish':
                _st.finish = _sel_key(inputs.itemById('finish'), _st.items['finish'])
                _bom_preview(inputs)
            elif cid in ('holes', 'flip', 'auto'):
                _hole_note(inputs)
        except Exception:
            _ui().messageBox('SR Fastener:\n' + traceback.format_exc(), CMD_NAME)


class _Validate(adsk.core.ValidateInputsEventHandler):
    def notify(self, args):
        args.areInputsValid = bool(_edges(args.inputs)) and _st.length is not None


class _Preview(adsk.core.CommandEventHandler):
    def notify(self, args):
        try:
            _run_place(args.command.commandInputs)
        except Exception:
            pass


class _Execute(adsk.core.CommandEventHandler):
    def notify(self, args):
        try:
            inputs = args.command.commandInputs
            occs, notes = _run_place(inputs)
            _save_settings({'system': _st.system, 'family': _st.code, 'size': _st.size, 'length': _st.length,
                            'finish': _st.finish, 'auto': inputs.itemById('auto').value,
                            'thread': inputs.itemById('thread').value})
            if notes:
                uniq = sorted(set(notes))
                _ui().messageBox('Placed %d screw(s). Notes:\n- %s' % (len(occs), '\n- '.join(uniq)), CMD_NAME)
        except Exception:
            _ui().messageBox('SR Fastener failed:\n' + traceback.format_exc(), CMD_NAME)


class _Destroy(adsk.core.CommandEventHandler):
    def notify(self, args):
        pass


# ---------- add-in entry points ----------

def run(context):
    try:
        ui = _ui()
        cdef = ui.commandDefinitions.itemById(CMD_ID)
        if cdef:
            cdef.deleteMe()
        res = os.path.join(_HERE, 'resources', 'cmd')
        cdef = ui.commandDefinitions.addButtonDefinition(CMD_ID, CMD_NAME, CMD_TIP, res)
        h = _Created()
        cdef.commandCreated.add(h)
        _handlers.append(h)
        ws = ui.workspaces.itemById(WORKSPACE)
        for pid in PANELS:
            panel = ws.toolbarPanels.itemById(pid) if ws else None
            if panel is None:
                continue
            old = panel.controls.itemById(CMD_ID)
            if old:
                old.deleteMe()
            ctrl = panel.controls.addCommand(cdef)
            if pid == PANELS[0]:
                ctrl.isPromoted = True
                ctrl.isPromotedByDefault = True
    except Exception:
        _ui().messageBox('SR Fastener failed to start:\n' + traceback.format_exc(), CMD_NAME)


def stop(context):
    try:
        ui = _ui()
        ws = ui.workspaces.itemById(WORKSPACE)
        for pid in PANELS:
            panel = ws.toolbarPanels.itemById(pid) if ws else None
            ctrl = panel.controls.itemById(CMD_ID) if panel else None
            if ctrl:
                ctrl.deleteMe()
        cdef = ui.commandDefinitions.itemById(CMD_ID)
        if cdef:
            cdef.deleteMe()
        _handlers.clear()
    except Exception:
        pass
