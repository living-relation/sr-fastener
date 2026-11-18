"""Live test of the 2026-11-17 changes: tapped-hole detection, sizing order, the one-click stack (near and far
side), compatibility warnings and plain material names. Run inside Fusion through the AutodeskFusionMCP
execute_python tool, holding the Fusion lock:

    import os; os.environ['SRFASTENER_DIR'] = r'<clone>\\SRFastener'; exec(open(r'<clone>\\dev\\fusion_stack_smoke.py').read()); main()

Opens a NEW scratch design and closes it WITHOUT saving (keep=True leaves it open for screenshots; close it
yourself afterwards, never save it). Never touches other open documents.
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
    if parent not in sys.path:
        sys.path.insert(0, parent)
    for m in [k for k in sys.modules if k == 'SRFastener' or k.startswith('SRFastener.')]:
        del sys.modules[m]
    importlib.import_module('SRFastener')
    return importlib.import_module('SRFastener.fastener_core'), importlib.import_module('SRFastener.fastener_place')


def _plate(design):
    """1 cm plate on XY, top face z=1. Holes: x=0 6.6 mm through (M6 clearance), x=3 5.0 mm through with an M6x1
    thread feature (tapped), x=6 4.5 mm through (plain, M4-ish)."""
    root = design.rootComponent
    sk = root.sketches.add(root.xYConstructionPlane)
    sk.sketchCurves.sketchLines.addTwoPointRectangle(adsk.core.Point3D.create(-1.5, -1.5, 0),
                                                     adsk.core.Point3D.create(7.5, 1.5, 0))
    ext = root.features.extrudeFeatures.addSimple(sk.profiles.item(0), adsk.core.ValueInput.createByReal(1.0),
                                                  adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    body = ext.bodies.item(0)
    sk2 = root.sketches.add(root.xYConstructionPlane)
    for x, dia in ((0.0, 0.66), (3.0, 0.50), (6.0, 0.45)):
        sk2.sketchCurves.sketchCircles.addByCenterRadius(adsk.core.Point3D.create(x, 0, 0), dia / 2.0)
    profs = adsk.core.ObjectCollection.create()
    for i in range(sk2.profiles.count):
        p = sk2.profiles.item(i)
        if p.areaProperties().area < 1.0:
            profs.add(p)
    cut = root.features.extrudeFeatures.createInput(profs, adsk.fusion.FeatureOperations.CutFeatureOperation)
    cut.setDistanceExtent(False, adsk.core.ValueInput.createByReal(1.0))
    root.features.extrudeFeatures.add(cut)
    # thread feature M6x1 on the 5 mm hole wall
    tf = root.features.threadFeatures
    wall = None
    for f in body.faces:
        if f.geometry.surfaceType == adsk.core.SurfaceTypes.CylinderSurfaceType:
            c = adsk.core.Cylinder.cast(f.geometry)
            if abs(c.radius - 0.25) < 1e-6 and abs(c.origin.x - 3.0) < 1e-6:
                wall = f
    info = tf.createThreadInfo(True, 'ISO Metric profile', 'M6x1', '6H')
    faces = adsk.core.ObjectCollection.create()
    faces.add(wall)
    ti = tf.createInput(faces, info)
    ti.isFullLength = True
    tf.add(ti)
    return body


def _edge(body, x, z):
    for e in body.edges:
        c = adsk.core.Circle3D.cast(e.geometry)
        if c and abs(c.center.z - z) < 1e-6 and abs(c.center.x - x) < 1e-6 and abs(c.center.y) < 1e-6:
            return e
    return None


def main(keep=False):
    app = adsk.core.Application.get()
    res = {'checks': [], 'fails': []}

    def check(name, ok, got=None):
        res['checks'].append(name)
        if not ok:
            res['fails'].append('%s: %r' % (name, got))

    doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    try:
        fc, fp = _load()
        cat = fc.load_catalog()
        design = adsk.fusion.Design.cast(app.activeProduct)
        body = _plate(design)
        clear, tapped, small = _edge(body, 0.0, 1.0), _edge(body, 3.0, 1.0), _edge(body, 6.0, 1.0)
        hc, ht = fp.read_hole(clear), fp.read_hole(tapped)
        check('plain hole reads as not tapped', hc.thread is None, hc.thread)
        check('thread feature hole reads as tapped M6x1', (ht.thread or '').replace(' ', '') == 'M6x1', ht.thread)
        check('screw size from clearance hole', fc.size_for(cat, fc.family(cat, 'SSH-M'), None, hc.thread,
                                                            hc.radius * 2) == 'M6')
        check('screw size from tapped hole', fc.size_for(cat, fc.family(cat, 'SSH-M'), None, ht.thread,
                                                         ht.radius * 2) == 'M6')
        far = fp.far_side(hc)
        check('far side of a through hole found at z=0', far is not None and abs(far.centre.z) < 1e-6,
              far and far.centre.z)

        # one insert: near washer, screw, far washer + nut on the clearance hole
        screw = fc.item(cat, 'SSH-M', 'M6', 'SS', 20)
        sref = fc.thread_ref(screw['fam'], screw['row'])
        rows = []
        for side, code in (('near', 'WGP-M'), ('far', 'WGP-M'), ('far', 'NHX-M')):
            f = fc.family(cat, code)
            it = fc.item(cat, code, fc.size_for(cat, f, sref, hc.thread, 0.45), 'SS')
            it['side'] = side
            rows.append(it)
        check('nut sized from the screw, not the 4.5 mm reference', rows[2]['row']['size'] == 'M6', rows[2]['row']['size'])
        occs, notes = fp.place_stack(app, design, cat, screw, rows, [clear])
        check('stack placed 4 parts', len(occs) == 4, (len(occs), notes))
        check('stack notes empty', not [n for n in notes if 'thread' not in n], notes)
        z = [o.transform2.translation.z for o in occs]
        wt = fc.part_geometry(rows[0]['fam'], rows[0]['row'])['thickness']
        check('near washer on top face', abs(z[0] - 1.0) < 1e-4, z[0])
        check('screw seat on the washer', abs(z[1] - (1.0 + wt)) < 1e-4, z[1])
        check('far washer on bottom face', abs(z[2] - 0.0) < 1e-4, z[2])
        check('far nut under the far washer', abs(z[3] - (-wt)) < 1e-4, z[3])
        ex = fp.existing_items(cat, design, hc)
        check('existing hardware found on the hole', len(ex) == 4, [fc.item_label(cat, i) for i in ex])
        check('matching stack has no warnings', fc.compat_warnings(cat, ex, hc.thread) == [],
              fc.compat_warnings(cat, ex, hc.thread))
        bad = ex + [fc.item(cat, 'NHX-I', '#8', 'SS-BO')]
        w = fc.compat_warnings(cat, bad, hc.thread)
        check('mismatched nut warns size and material', any('does not fit' in x for x in w) and
              any('mixed materials' in x for x in w), w)
        w2 = fc.compat_warnings(cat, [fc.item(cat, 'SSH-M', 'M5', 'SS', 12)], ht.thread)
        check('wrong screw in tapped hole warns', any('tapped hole' in x for x in w2), w2)

        # nut alone and washer alone
        n_occs, _ = fp.place_stack(app, design, cat, fc.item(cat, 'NHX-M', 'M4', 'ZN'), [], [small])
        check('nut alone placed', len(n_occs) == 1)
        w_occs, _ = fp.place_stack(app, design, cat, None, [dict(fc.item(cat, 'WGP-M', 'M4', 'ZN'), side='near')],
                                   [_edge(body, 6.0, 0.0)])
        check('washer alone (stack only) placed', len(w_occs) == 1)

        # material and appearance
        comp = occs[1].component
        check('material name is plain', comp.material and comp.material.name == 'Stainless Steel',
              comp.material.name if comp.material else None)
        lib = app.materialLibraries.itemByName('Fusion Material Library').materials.itemByName('Stainless Steel AISI 304')
        try:
            dens = comp.material.materialProperties.itemByName('Density').value
            dens_lib = lib.materialProperties.itemByName('Density').value
            check('density copied from Stainless Steel AISI 304', abs(dens - dens_lib) < 1e-9, (dens, dens_lib))
        except Exception as e:
            check('density readable', False, str(e))
        zn = n_occs[0].component
        check('zinc nut material', zn.material and zn.material.name == 'Zinc Plated', zn.material and zn.material.name)
        res['zinc_appearance'] = zn.bRepBodies.item(0).appearance.name if zn.bRepBodies.item(0).appearance else None
        res['zinc_nut_pn'] = zn.partNumber
        res['zinc_nut_desc'] = zn.description
        res['screw_pn'], res['screw_desc'] = comp.partNumber, comp.description
        res['washer_pn'] = occs[0].component.partNumber
        res['notes'] = notes
    except Exception:
        res['fails'].append(traceback.format_exc())
    finally:
        if not keep:
            doc.close(False)
    res['pass'] = not res['fails']
    print(json.dumps(res, indent=1, default=str))
    return res
