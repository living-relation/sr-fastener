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


def _plate_with_holes(design, holes):
    """holes: list of (x_cm, diameter_cm). Plate 1 cm thick on XY, holes cut through from the top (z=1)."""
    root = design.rootComponent
    sk = root.sketches.add(root.xYConstructionPlane)
    width = max(x for x, _ in holes) + 2.0
    sk.sketchCurves.sketchLines.addTwoPointRectangle(adsk.core.Point3D.create(-1, -1.5, 0),
                                                     adsk.core.Point3D.create(width, 1.5, 0))
    prof = max((sk.profiles.item(i) for i in range(sk.profiles.count)), key=lambda p: p.areaProperties().area)
    ext = root.features.extrudeFeatures.addSimple(prof, adsk.core.ValueInput.createByReal(1.0),
                                                  adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    body = ext.bodies.item(0)
    top = max((f for f in body.faces if f.geometry.surfaceType == adsk.core.SurfaceTypes.PlaneSurfaceType),
              key=lambda f: f.centroid.z)
    sk2 = root.sketches.add(top)
    for x, dia in holes:
        p = sk2.modelToSketchSpace(adsk.core.Point3D.create(x, 0, 1.0))
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


def _top_edge(body, x):
    best = None
    for e in body.edges:
        c = adsk.core.Circle3D.cast(e.geometry)
        if c and abs(c.center.z - 1.0) < 1e-6 and abs(c.center.x - x) < 1e-6:
            best = e
    return best


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
                 ('SHH-M', 'M6', 20, 'SS-BO', 0.66), ('SSF-M', 'M8', 10, 'SS', 0.68),
                 ('SSH-I', '1/4', 1.0, 'SS-BO', 0.66), ('SBH-I', '#10', 0.5, 'SS', 0.51),
                 ('SFH-I', '#8', 0.5, 'SS-BO', 0.44), ('SLH-I', '#6', 0.375, 'SS', 0.37), ('SHH-I', '1/4', 1.0, 'SS', 0.66),
                 # alloy steel black oxide, one per family that offers it
                 ('SSH-M', 'M5', 16, 'ALLOY-BO', 0.55), ('SBH-M', 'M6', 12, 'ALLOY-BO', 0.66),
                 ('SFH-M', 'M5', 16, 'ALLOY-BO', 0.55), ('SLH-M', 'M8', 20, 'ALLOY-BO', 0.88),
                 ('SSF-M', 'M6', 8, 'ALLOY-BO', 0.5), ('SSH-I', '1/4', 2.0, 'ALLOY-BO', 0.66),
                 ('SBH-I', '#10-32', 0.5, 'ALLOY-BO', 0.51), ('SFH-I', '#10', 2.0, 'ALLOY-BO', 0.51),
                 ('SLH-I', '1/4', 0.75, 'ALLOY-BO', 0.66), ('SHH-I', '1/4', 1.5, 'ALLOY-BO', 0.66),
                 ('SSF-I', '1/4', 0.5, 'ALLOY-BO', 0.53),
                 # new types and a partly threaded metric screw
                 ('SSC-M', 'M6', 10, 'SS', 0.5), ('SSC-I', '1/4', 0.5, 'ALLOY-BO', 0.53), ('SSH-M', 'M6', 35, 'SS', 0.66),
                 ('SPH-M', 'M4', 12, 'SS', 0.45), ('SCH-M', 'M5', 10, 'SS', 0.55)]
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
        root = design.rootComponent
        same = [o for o in root.occurrences if o.component.partNumber == 'SSH-M3-0.5 x 10 18-8 SS']
        check('reuse: two occurrences, one component', len(same) == 2 and same[0].component == same[1].component,
              len(same))
        check('joints made', root.joints.count == len(cases), root.joints.count)
        threads = sum(c.features.threadFeatures.count for c in design.allComponents)
        report['cosmetic_threads'] = threads
        # toolbar button
        main_mod.run(None)
        ws = ui.workspaces.itemById(main_mod.WORKSPACE)
        ctrl = ws.toolbarPanels.itemById('InsertPanel').controls.itemById(main_mod.CMD_ID)
        check('toolbar button in Insert panel', ctrl is not None and ctrl.isVisible)
        check('button promoted', ctrl is not None and ctrl.isPromoted)
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
