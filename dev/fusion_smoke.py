"""Live smoke test. Run inside Fusion through the AutodeskFusionMCP execute_python tool, holding the Fusion lock.

    import os; os.environ['SRFASTENER_DIR'] = r'<clone>\\SRFastener'; exec(open(r'<clone>\\dev\\fusion_smoke.py').read()); main()

Opens a NEW scratch design, cuts test holes, places every type and size class it can, checks BOM fields,
material, joints and reuse, registers the toolbar button, then closes the scratch design WITHOUT saving
(pass keep=True to leave it open for screenshots; close it yourself afterwards, never save it).
"""
import importlib
import json
import os
import sys
import traceback

import adsk.core
import adsk.fusion


def _load():
    d = os.environ['SRFASTENER_DIR']
    parent = os.path.dirname(d)
    sys.path[:] = [x for x in sys.path if os.path.normcase(os.path.abspath(x)) != os.path.normcase(os.path.abspath(d))]
    if parent not in sys.path:
        sys.path.insert(0, parent)
    for m in [k for k in sys.modules if k == 'SRFastener' or k.startswith('SRFastener.')]:
        del sys.modules[m]
    pkg = importlib.import_module('SRFastener')
    core = importlib.import_module('SRFastener.fastener_core')
    place = importlib.import_module('SRFastener.fastener_place')
    main_mod = importlib.import_module('SRFastener.SRFastener')
    return pkg, core, place, main_mod


def _plate_with_holes(design, holes, y0=0.0):
    """holes: list of (x_cm, diameter_cm). Plate 1 cm thick on XY centred on y=y0, holes cut through from the top (z=1)."""
    root = design.rootComponent
    sk = root.sketches.add(root.xYConstructionPlane)
    width = max(x for x, _ in holes) + 2.0
    sk.sketchCurves.sketchLines.addTwoPointRectangle(adsk.core.Point3D.create(-1, y0 - 1.5, 0),
                                                     adsk.core.Point3D.create(width, y0 + 1.5, 0))
    prof = max((sk.profiles.item(i) for i in range(sk.profiles.count)), key=lambda p: p.areaProperties().area)
    ext = root.features.extrudeFeatures.addSimple(prof, adsk.core.ValueInput.createByReal(1.0),
                                                  adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    body = ext.bodies.item(0)
    top = max((f for f in body.faces if f.geometry.surfaceType == adsk.core.SurfaceTypes.PlaneSurfaceType),
              key=lambda f: f.centroid.z)
    sk2 = root.sketches.add(top)
    for x, dia in holes:
        p = sk2.modelToSketchSpace(adsk.core.Point3D.create(x, y0, 1.0))
        sk2.sketchCurves.sketchCircles.addByCenterRadius(p, dia / 2.0)
    profs = adsk.core.ObjectCollection.create()
    for i in range(sk2.profiles.count):
        pr = sk2.profiles.item(i)
        if pr.areaProperties().area < 1.0:
            profs.add(pr)
    cut = root.features.extrudeFeatures.createInput(profs, adsk.fusion.FeatureOperations.CutFeatureOperation)
    cut.setAllExtent(adsk.fusion.ExtentDirections.NegativeExtentDirection)
    root.features.extrudeFeatures.add(cut)
    return body


def _top_edge(body, x, z=1.0, y=None):
    best = None
    for e in body.edges:
        c = adsk.core.Circle3D.cast(e.geometry)
        if c and abs(c.center.z - z) < 1e-6 and abs(c.center.x - x) < 1e-6 and (y is None or abs(c.center.y - y) < 1e-6):
            best = e
    return best


# Nuts and washers: (hole dia cm, [(code, size, finish, 'top'|'bottom')...]) placed in order on one hole,
# so later parts stack on earlier ones. Expected seat height = plate face +/- thickness of what is below it.
PART_STACKS = [
    (0.55, [('WGP-M', 'M5', 'SS', 'top'), ('SSH-M', 'M5', 'SS', 'top', 16), ('WSL-M', 'M5', 'SS', 'bottom'),
            ('NHX-M', 'M5', 'SS-BO', 'bottom')]),
    (0.66, [('WSA-I', '1/4', 'SS-BO', 'top'), ('HHB-I', '1/4', 'SS', 'top', 1.0), ('WUS-I', '1/4', 'SS', 'bottom'),
            ('NNL-I', '1/4', 'SS-BO', 'bottom')]),
    (0.66, [('NTH-M', 'M6', 'SS-BO', 'bottom'), ('NFL-M', 'M6', 'SS', 'top')]),
    (0.88, [('WOV-M', 'M8', 'SS', 'top'), ('NSF-M', 'M8', 'SS', 'bottom')]),
    (0.55, [('WTE-M', 'M5', 'SS', 'top'), ('WTI-M', 'M5', 'SS', 'bottom')]),
    (0.88, [('NNL-M', 'M8', 'SS-BO', 'top'), ('WSL-M', 'M8', 'SS-BO', 'bottom'), ('NTH-M', 'M8', 'SS', 'bottom')]),
    (1.0, [('NTH-I', '3/8', 'SS-BO', 'top'), ('WSL-I', '3/8', 'SS', 'bottom'), ('NHX-I', '3/8-24', 'SS-BO', 'bottom')]),
    (0.51, [('NHX-I', '#10-32', 'SS-BO', 'bottom'), ('WSL-I', '#10', 'SS-BO', 'top'), ('WSA-I', '#10', 'SS', 'top')]),
    (0.37, [('NHX-I', '#6', 'SS', 'bottom'), ('NNL-I', '#6-40', 'SS-BO', 'top')]),
    (0.66, [('WTK-M', 'M6', 'SS', 'top'), ('NCA-M', 'M6', 'SS', 'bottom')]),
    (0.55, [('NWG-M', 'M5', 'SS-BO', 'top'), ('NSQ-M', 'M5', 'SS', 'bottom')]),
    (0.66, [('NFL-I', '1/4', 'SS-BO', 'top'), ('NSF-I', '1/4-28', 'SS-BO', 'bottom')]),
    (0.66, [('WTE-I', '1/4', 'SS-BO', 'top'), ('NTN-I', '1/4', 'SS-BO', 'top'), ('WTI-I', '1/4', 'SS', 'bottom'),
            ('NTL-I', '1/4-28', 'SS', 'bottom')]),
    (0.88, [('NTL-M', 'M8', 'SS-BO', 'top'), ('NCP-M', 'M8', 'SS-BO', 'bottom')]),
    (0.51, [('WOV-I', '#10', 'SS-BO', 'top'), ('NCA-I', '#10-32', 'SS-BO', 'bottom')]),
    (0.51, [('NWG-I', '#10', 'SS', 'top'), ('NSQ-I', '#10-32', 'SS-BO', 'bottom')]),
    (0.66, [('NCP-I', '1/4', 'SS', 'top')]),
]


def _parts(app, design, core, place, cat, check, report):
    y0 = 4.0
    holes = [(i * 2.5, dia) for i, (dia, _) in enumerate(PART_STACKS)]
    body = _plate_with_holes(design, holes, y0)
    joints_before = design.rootComponent.joints.count
    placed = 0
    for i, (dia, seq) in enumerate(PART_STACKS):
        x = holes[i][0]
        height = {'top': 0.0, 'bottom': 0.0}
        for item in seq:
            code, size, fin, side = item[:4]
            length = item[4] if len(item) > 4 else None
            fam = core.family(cat, code)
            row = core.size_row(fam, size)
            edge = _top_edge(body, x, 1.0 if side == 'top' else 0.0, y0)
            tag = '%s %s %s %s' % (code, size, fin, side)
            check('%s edge found' % tag, edge is not None)
            occs, notes = place.place(app, design, cat, fam, row, length, fin, [edge])
            placed += 1
            report['notes'] += ['%s: %s' % (tag, n) for n in notes]
            occ = occs[0]
            comp = occ.component
            bom = core.bom_fields(cat, fam, row, length, fin)
            check('%s part number' % tag, comp.partNumber == bom['part_number'], comp.partNumber)
            check('%s description' % tag, comp.description == bom['description'], comp.description)
            check('%s material' % tag, comp.material and comp.material.name == bom['material'],
                  comp.material.name if comp.material else None)
            b = comp.bRepBodies.item(0)
            check('%s solid' % tag, b.isSolid and b.volume > 0, b.volume)
            origin, _, _, z = occ.transform2.getAsCoordinateSystem()
            sign = 1.0 if side == 'top' else -1.0
            want_z = (1.0 + height['top']) if side == 'top' else -height['bottom']
            check('%s seat height (stacked)' % tag, abs(origin.x - x) < 1e-4 and abs(origin.y - y0) < 1e-4
                  and abs(origin.z - want_z) < 1e-4, (origin.x, origin.y, origin.z, want_z))
            check('%s faces out of the hole' % tag, abs(z.z - sign) < 1e-6, z.asArray())
            check('%s joint, no notes' % tag, not notes, notes)
            bb = occ.bRepBodies.item(0).boundingBox
            if core.kind(fam) != 'screw':
                g = core.part_geometry(fam, row)
                check('%s thickness' % tag, abs((bb.maxPoint.z - bb.minPoint.z) - g['thickness']) < 1e-3,
                      (bb.maxPoint.z - bb.minPoint.z, g['thickness']))
                width = max(bb.maxPoint.x - bb.minPoint.x, bb.maxPoint.y - bb.minPoint.y)  # split gap cuts one side
                want_w = 2 * g.get('flange_r', g.get('outer_r', 0)) if g['shape'] != 'hex' and g['shape'] != 'nylon' else None
                if g['shape'] == 'wing':
                    check('%s wing span' % tag, width >= g['wing_w'] - 1e-3, (width, g['wing_w']))
                elif want_w:
                    check('%s outside diameter' % tag, abs(width - want_w) < 1e-3, (width, want_w))
                else:
                    check('%s hex at least across flats' % tag, width >= g['across_flats'] - 1e-3, (width, g['across_flats']))
                height[side] += g['thickness']
    check('part joints made', design.rootComponent.joints.count - joints_before == placed,
          (design.rootComponent.joints.count - joints_before, placed))
    return placed


def main(keep=False, out=None):
    app = adsk.core.Application.get()
    ui = app.userInterface
    report = {'checks': [], 'notes': [], 'ok': True}

    def check(name, cond, detail=''):
        report['checks'].append({'check': name, 'pass': bool(cond), 'detail': str(detail)})
        if not cond:
            report['ok'] = False

    pkg, core, place, main_mod = _load()
    cat = core.load_catalog()
    doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    try:
        design = adsk.fusion.Design.cast(app.activeProduct)
        design.designType = adsk.fusion.DesignTypes.ParametricDesignType
        cases = [('SSH-M', 'M3', 10, 'SS', 0.34), ('SSH-M', 'M3', 10, 'SS', 0.34), ('SSH-M', 'M5', 16, 'SS-BO', 0.55),
                 ('SBH-M', 'M4', 12, 'SS-BO', 0.45), ('SFH-M', 'M4', 12, 'SS', 0.45), ('SLH-M', 'M6', 16, 'SS', 0.66),
                 ('HHB-M', 'M6', 20, 'SS-BO', 0.66), ('SSF-M', 'M8', 10, 'SS', 0.68),
                 ('SSH-I', '1/4', 1.0, 'SS-BO', 0.66), ('SBH-I', '#10', 0.5, 'SS', 0.51),
                 ('SFH-I', '#8', 0.5, 'SS-BO', 0.44), ('SLH-I', '#6', 0.375, 'SS', 0.37), ('HHB-I', '1/4', 1.0, 'SS', 0.66),
                 # alloy steel black oxide, one per family that offers it
                 ('SSH-M', 'M5', 16, 'ALLOY-BO', 0.55), ('SBH-M', 'M6', 12, 'ALLOY-BO', 0.66),
                 ('SFH-M', 'M5', 16, 'ALLOY-BO', 0.55), ('SLH-M', 'M8', 20, 'ALLOY-BO', 0.88),
                 ('SSF-M', 'M6', 8, 'ALLOY-BO', 0.5), ('SSH-I', '1/4', 2.0, 'ALLOY-BO', 0.66),
                 ('SBH-I', '#10-32', 0.5, 'ALLOY-BO', 0.51), ('SFH-I', '#10', 2.0, 'ALLOY-BO', 0.51),
                 ('SLH-I', '1/4', 0.75, 'ALLOY-BO', 0.66), ('HHB-I', '1/4', 1.5, 'ALLOY-BO', 0.66),
                 ('SSF-I', '1/4', 0.5, 'ALLOY-BO', 0.53),
                 # new types and a partly threaded metric screw
                 ('SSC-M', 'M6', 10, 'SS', 0.5), ('SSC-I', '1/4', 0.5, 'ALLOY-BO', 0.53), ('SSH-M', 'M6', 35, 'SS', 0.66),
                 ('SPH-M', 'M4', 12, 'SS', 0.45), ('SCH-M', 'M5', 10, 'SS', 0.55),
                 # cone, extended and oval tips, flanged button head, Phillips sheet metal screws
                 ('SSN-M', 'M6', 10, 'SS-BO', 0.5), ('SSN-M', 'M3', 3, 'SS', 0.25), ('SSN-I', '1/4', 0.5, 'SS', 0.53),
                 ('SSE-M', 'M6', 8, 'SS', 0.5), ('SSE-M', 'M12', 16, 'SS', 1.0), ('SSE-I', '#10-32', 0.5, 'SS-BO', 0.44),
                 ('SSO-I', '#6', 0.25, 'SS-BO', 0.33), ('SBF-M', 'M5', 10, 'SS-BO', 0.55), ('SBF-M', 'M10', 35, 'SS', 1.1),
                 ('STP-I', '#8', 0.5, 'SS-BO', 0.44), ('STP-I', '#2', 0.125, 'SS-BO', 0.22),
                 ('STP-M', 'M4.2', 13, 'SS-BO', 0.45),
                 # short inch set screws with the standard socket depth (cut back for the point where needed)
                 ('SSN-I', '#2', 0.125, 'SS', 0.22), ('SSN-I', '#6', 0.1875, 'SS-BO', 0.37),
                 ('SSN-I', '5/16', 0.375, 'SS', 0.8), ('SSN-I', '5/16-24', 0.375, 'SS-BO', 0.8),
                 ('SSN-I', '3/8', 0.375, 'SS', 0.95), ('SSN-I', '3/8-24', 0.375, 'SS-BO', 0.95),
                 ('SSE-I', '#2', 0.125, 'SS-BO', 0.22), ('SSE-I', '3/8', 0.375, 'SS', 0.95),
                 ('SSE-I', '3/8-24', 0.375, 'SS-BO', 0.95), ('SSE-I', '1/2', 0.625, 'SS', 1.1),
                 ('SSO-I', '#6', 0.1875, 'SS-BO', 0.37)]
        holes = [(i * 2.5, c[4]) for i, c in enumerate(cases)]
        body = _plate_with_holes(design, holes)
        for i, (code, size, length, fin, dia) in enumerate(cases):
            fam = core.family(cat, code)
            row = core.size_row(fam, size)
            edge = _top_edge(body, holes[i][0])
            check('%s hole edge found' % code, edge is not None)
            hole = place.read_hole(edge)
            check('%s hole points down' % code, hole.into.z < -0.99, hole.into.asArray())
            check('%s size suggestion' % code, core.suggest_size(cat, fam, dia) is not None, core.suggest_size(cat, fam, dia))
            occs, notes = place.place(app, design, cat, fam, row, length, fin, [edge])
            report['notes'] += ['%s: %s' % (code, n) for n in notes]
            occ = occs[0]
            comp = occ.component
            bom = core.bom_fields(cat, fam, row, length, fin)
            check('%s part number' % code, comp.partNumber == bom['part_number'], comp.partNumber)
            check('%s description' % code, comp.description == bom['description'], comp.description)
            check('%s material' % code, comp.material and comp.material.name == bom['material'],
                  comp.material.name if comp.material else None)
            b = comp.bRepBodies.item(0)
            # Fusion reports a stale override name when the wanted appearance equals the
            # material's own appearance, so accept either source.
            shown = [x.name for x in (b.appearance, b.material.appearance if b.material else None) if x]
            check('%s appearance' % code, bom['appearance'] in shown, shown)
            check('%s solid' % code, b.isSolid and b.volume > 0, b.volume)
            m = occ.transform2
            o = m.translation
            check('%s on hole centre' % code, abs(o.x - holes[i][0]) < 1e-4 and abs(o.y) < 1e-4 and abs(o.z - 1.0) < 1e-4,
                  (o.x, o.y, o.z))
            bb = occ.bRepBodies.item(0).boundingBox  # occurrence boxes read back empty
            g = core.geometry(fam, row, length)
            low = 1.0 - g['L']
            check('%s tip depth' % code, abs(bb.minPoint.z - low) < 2e-3, (bb.minPoint.z, low))
            check('%s joint' % code, not any('joint' in n for n in notes), notes)
            check('%s no notes' % code, not notes, notes)
            if comp.features.threadFeatures.count:
                tf = comp.features.threadFeatures.item(0)
                shank = g['shank'][0] - g['shank'][1]
                want_full = g['thread_len'] >= shank - 1e-4
                check('%s thread full/partial' % code, tf.isFullLength == want_full, (tf.isFullLength, g['thread_len'], shank))
                if not want_full:
                    got = tf.threadLength.value if hasattr(tf.threadLength, 'value') else None
                    check('%s thread length' % code, got is not None and abs(got - g['thread_len']) < 1e-3, (got, g['thread_len']))
                    # model the thread briefly to see which end it is on: the helix must reach the tip
                    def _set_modeled(v):
                        tf.timelineObject.rollTo(True)
                        tf.isModeled = v
                        design.timeline.moveToEnd()
                    _set_modeled(True)
                    zs = []
                    for f in comp.bRepBodies.item(0).faces:
                        if f.geometry.surfaceType not in (adsk.core.SurfaceTypes.PlaneSurfaceType,
                                                          adsk.core.SurfaceTypes.CylinderSurfaceType,
                                                          adsk.core.SurfaceTypes.ConeSurfaceType,
                                                          adsk.core.SurfaceTypes.SphereSurfaceType):
                            zs += [f.boundingBox.minPoint.z, f.boundingBox.maxPoint.z]
                    _set_modeled(False)
                    tip = -g['L']
                    check('%s thread at tip end' % code, zs and min(zs) < tip + 0.2 and max(zs) < tip + g['thread_len'] + 0.2,
                          (min(zs) if zs else None, max(zs) if zs else None, tip, g['thread_len']))
        report['parts_placed'] = _parts(app, design, core, place, cat, check, report)
        root = design.rootComponent
        same = [o for o in root.occurrences if o.component.partNumber == 'SSH-M3-0.5 x 10 18-8 SS']
        check('reuse: two occurrences, one component', len(same) == 2 and same[0].component == same[1].component,
              len(same))
        check('joints made', root.joints.count == len(cases) + report['parts_placed'], root.joints.count)
        threads = sum(c.features.threadFeatures.count for c in design.allComponents)
        report['cosmetic_threads'] = threads
        # toolbar button
        # toolbar buttons on every default panel (no panels.json in the test settings folder), removed on stop
        main_mod.PANELS_FILE = os.path.join(os.path.dirname(out or '.'), 'srf-no-panels.json')
        main_mod.run(None)
        ws = ui.workspaces.itemById('FusionSolidEnvironment')
        for s in main_mod.sp.DEFAULT_PANELS:
            panel = ws.toolbarPanels.itemById(s['panel'])
            ctrl = panel.controls.itemById(main_mod.CMD_ID) if panel else None
            check('toolbar button in %s' % s['panel'], ctrl is not None and ctrl.isVisible)
            if s['promote']:
                check('button promoted in %s' % s['panel'], ctrl is not None and ctrl.isPromoted)
        tab = ws.toolbarTabs.itemById('SolidTab')
        check('SR Tools panel on the Solid tab', tab.toolbarPanels.itemById('SRToolsPanel') is not None)
        main_mod.stop(None)
        left = [s['panel'] for s in main_mod.sp.DEFAULT_PANELS
                if ws.toolbarPanels.itemById(s['panel']) is not None
                and ws.toolbarPanels.itemById(s['panel']).controls.itemById(main_mod.CMD_ID) is not None]
        check('stop removes every button', not left, left)
        srp = ws.toolbarPanels.itemById('SRToolsPanel')
        # other SR add-ins may still have buttons there; the panel only goes once it is empty
        check('stop removes the SR Tools panel once empty', srp is None or srp.controls.count > 0,
              srp.controls.count if srp else None)
        check('stop removes the command', ui.commandDefinitions.itemById(main_mod.CMD_ID) is None)
        report['bom'] = [{'pn': o.component.partNumber, 'desc': o.component.description,
                          'material': o.component.material.name if o.component.material else None}
                         for o in root.occurrences]
    except Exception:
        report['ok'] = False
        report['error'] = traceback.format_exc()
    finally:
        if not keep:
            doc.close(False)
    text = json.dumps(report, indent=1)
    if out:
        with open(out, 'w', encoding='utf-8') as f:
            f.write(text)
    print(text)
    return report
