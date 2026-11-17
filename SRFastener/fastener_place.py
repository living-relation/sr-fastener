"""Reads a picked hole edge, makes or reuses the screw, nut or washer component, places it and joins it (Fusion API).

Stacking: a nut, washer or screw head placed at a hole edge sits on top of any SR nuts and washers already
placed at that edge (same axis, touching), so pick the same edge for a washer and then a screw or nut."""
import adsk.core
import adsk.fusion

from . import fastener_core as fc
from . import fastener_geom as geom

ATTR = 'srfastener'
_TOL = 1e-4  # cm


class Hole:
    """centre (Point3D, world), into (unit Vector3D pointing into the material), radius (cm), thread (str|None)."""

    def __init__(self, edge, centre, into, radius, thread):
        self.edge, self.centre, self.into, self.radius, self.thread = edge, centre, into, radius, thread


def _thread_designation(face):
    """Designation of a thread feature on this face, if any (e.g. 'M3x0.5')."""
    try:
        native = face.nativeObject or face
        comp = native.body.parentComponent
        for tf in comp.features.threadFeatures:
            try:
                faces = tf.faces
                for i in range(faces.count):
                    if faces.item(i).tempId == native.tempId:
                        return tf.threadInfo.threadDesignation
            except Exception:
                continue
    except Exception:
        pass
    return None


def read_hole(edge, flip=False):
    circle = adsk.core.Circle3D.cast(edge.geometry)
    if circle is None:
        arc = adsk.core.Arc3D.cast(edge.geometry)
        if arc is None:
            return None
        centre, normal, radius = arc.center, arc.normal, arc.radius
    else:
        centre, normal, radius = circle.center, circle.normal, circle.radius
    normal = normal.copy()
    normal.normalize()
    into, thread = None, None
    for i in range(edge.faces.count):
        face = edge.faces.item(i)
        st = face.geometry.surfaceType
        if st in (adsk.core.SurfaceTypes.CylinderSurfaceType, adsk.core.SurfaceTypes.ConeSurfaceType):
            v = centre.vectorTo(face.pointOnFace).dotProduct(normal)
            if abs(v) > _TOL:
                into = normal.copy()
                if v < 0:
                    into.scaleBy(-1)
            if st == adsk.core.SurfaceTypes.CylinderSurfaceType:
                thread = thread or _thread_designation(face)
            if into is not None:
                break
    if into is None:  # no wall found: point away from the planar face's side we can't see; user can flip
        into = normal.copy()
        into.scaleBy(-1)
    if flip:
        into.scaleBy(-1)
    return Hole(edge, centre, into, radius, thread)


def world_matrix(hole, offset=0.0):
    """Part +z points out of the hole (head side); origin on the seat plane, moved `offset` cm outward."""
    z = hole.into.copy()
    z.scaleBy(-1)
    ref = adsk.core.Vector3D.create(1, 0, 0) if abs(z.x) < 0.9 else adsk.core.Vector3D.create(0, 1, 0)
    x = ref.crossProduct(z)
    x.normalize()
    y = z.crossProduct(x)
    origin = hole.centre.copy()
    if offset:
        v = z.copy()
        v.scaleBy(offset)
        origin.translateBy(v)
    m = adsk.core.Matrix3D.create()
    m.setWithCoordinateSystem(origin, x, y, z)
    return m


def _attr(comp, name):
    a = comp.attributes.itemByName(ATTR, name)
    return a.value if a else None


def stack_offset(design, hole):
    """How far (cm) out of the hole the next part's seat is: the top of the SR nuts and washers already stacked
    on this hole's axis, starting at the hole face and touching each other."""
    out = hole.into.copy()
    out.scaleBy(-1)
    spans = []
    for occ in design.rootComponent.allOccurrences:
        comp = occ.component
        if _attr(comp, 'kind') not in ('nut', 'washer'):
            continue
        try:
            t = float(_attr(comp, 'thickness'))
        except (TypeError, ValueError):
            continue
        origin, _, _, z = occ.transform2.getAsCoordinateSystem()
        if z.dotProduct(out) < 0.999:
            continue
        v = hole.centre.vectorTo(origin)
        along = v.dotProduct(out)
        radial2 = max(v.dotProduct(v) - along * along, 0.0)
        if radial2 > 1e-6:
            continue
        spans.append((along, along + t))
    top = 0.0
    for lo, hi in sorted(spans):
        if lo > top + 1e-3:
            break
        if lo > -1e-3:
            top = max(top, hi)
    return top


def _find_component(design, pn):
    for comp in design.allComponents:
        a = comp.attributes.itemByName(ATTR, 'part_number')
        if a and a.value == pn:
            return comp
    return None


def _material(app, name):
    for libname in ('Fusion Material Library',):
        lib = app.materialLibraries.itemByName(libname)
        if lib:
            m = lib.materials.itemByName(name)
            if m:
                return m
    return None


def _appearance(app, design, name):
    a = design.appearances.itemByName(name)
    if a:
        return a
    for libname in ('Fusion Appearance Library', 'Fusion Material Library'):
        lib = app.materialLibraries.itemByName(libname)
        if lib:
            src = lib.appearances.itemByName(name)
            if src:
                return design.appearances.addByCopy(src, name)
    return None


def _tip_end_location(face, tip_z):
    """ThreadLocations value whose end of this cylindrical face is the screw tip (lowest z in the component)."""
    ev = face.evaluator
    rng = ev.parametricRange()
    best = None
    for axis in (0, 1):
        a0 = adsk.core.Point2D.create(rng.minPoint.x, rng.minPoint.y)
        a1 = adsk.core.Point2D.create(rng.maxPoint.x if axis == 0 else rng.minPoint.x,
                                      rng.maxPoint.y if axis == 1 else rng.minPoint.y)
        _, p0 = ev.getPointAtParameter(a0)
        _, p1 = ev.getPointAtParameter(a1)
        dz = p1.z - p0.z
        if best is None or abs(dz) > abs(best[1]):
            best = (axis, dz, p0.z, p1.z)
    _, dz, z_lo, z_hi = best
    low_is_tip = abs(z_lo - tip_z) < abs(z_hi - tip_z)
    return (adsk.fusion.ThreadLocations.LowEndThreadLocation if low_is_tip
            else adsk.fusion.ThreadLocations.HighEndThreadLocation)


def _apply_thread(comp, fam, row, length, notes):
    try:
        spec = fc.thread_spec(fam, row)
        if spec is None:
            return
        ttype, designation, tclass = spec
        query = comp.features.threadFeatures.threadDataQuery
        body = comp.bRepBodies.item(0)
        g = fc.geometry(fam, row, length)
        r = g['r']
        face = None
        for f in body.faces:
            if f.geometry.surfaceType == adsk.core.SurfaceTypes.CylinderSurfaceType:
                cyl = adsk.core.Cylinder.cast(f.geometry)
                if abs(cyl.radius - r) < _TOL:
                    if face is None or f.area > face.area:
                        face = f
        if face is None:
            notes.append('cosmetic thread skipped: no shank face found')
            return
        size_list = query.allSizes(ttype)
        nominal = None
        for s in size_list:
            for d in query.allDesignations(ttype, s):
                if d == designation:
                    nominal = s
        if nominal is None:
            notes.append('cosmetic thread skipped: Fusion has no %s %s' % (ttype, designation))
            return
        info = comp.features.threadFeatures.createThreadInfo(False, ttype, designation, tclass)
        faces = adsk.core.ObjectCollection.create()
        faces.add(face)
        ti = comp.features.threadFeatures.createInput(faces, info)
        ti.isModeled = False
        shank_len = g['shank'][0] - g['shank'][1]
        if g['thread_len'] < shank_len - 1e-4:
            ti.isFullLength = False
            ti.threadLength = adsk.core.ValueInput.createByReal(g['thread_len'])
            ti.threadOffset = adsk.core.ValueInput.createByReal(0.0)
            ti.threadLocation = _tip_end_location(face, -g['L'] + g.get('point_h', 0.0))
        else:
            ti.isFullLength = True
        comp.features.threadFeatures.add(ti)
    except Exception as e:  # cosmetic only; never block placing the screw
        notes.append('cosmetic thread skipped: %s' % e)


def make_component(app, design, parent, cat, fam, row, length, finish_key, matrix, thread=True, notes=None):
    """Create (or reuse) the screw component and add an occurrence at `matrix` (parent-local)."""
    notes = notes if notes is not None else []
    bom = fc.bom_fields(cat, fam, row, length, finish_key)
    pn = bom['part_number']
    existing = _find_component(design, pn)
    if existing is not None:
        return parent.occurrences.addExistingComponent(existing, matrix), notes
    occ = parent.occurrences.addNewComponent(matrix)
    comp = occ.component
    comp.name = pn
    comp.partNumber = pn
    comp.description = bom['description']
    is_part = fc.kind(fam) != 'screw'
    body = geom.build_part_body(fam, row)[0] if is_part else geom.build_body(fam, row, length)
    if design.designType == adsk.fusion.DesignTypes.ParametricDesignType:
        bf = comp.features.baseFeatures.add()
        bf.startEdit()
        comp.bRepBodies.add(body, bf)
        bf.finishEdit()
        bf.name = 'SR Fastener'
    else:
        comp.bRepBodies.add(body)
    b = comp.bRepBodies.item(0)
    b.name = pn
    mat = _material(app, bom['material'])
    if mat:
        comp.material = mat
        b.material = mat
    else:
        notes.append('material not found: %s' % bom['material'])
    ap = _appearance(app, design, bom['appearance'])
    if ap:
        b.appearance = ap
    else:
        notes.append('appearance not found: %s' % bom['appearance'])
    for k in ('part_number', 'description', 'finish', 'grade', 'vendor_pn', 'standard', 'source'):
        comp.attributes.add(ATTR, k, str(bom[k]))
    comp.attributes.add(ATTR, 'family', fam['code'])
    comp.attributes.add(ATTR, 'size', row['size'])
    comp.attributes.add(ATTR, 'length', str(length) if length is not None else '')
    comp.attributes.add(ATTR, 'kind', fc.kind(fam))
    if is_part:
        comp.attributes.add(ATTR, 'thickness', repr(fc.part_geometry(fam, row)['thickness']))
    elif thread and design.designType == adsk.fusion.DesignTypes.ParametricDesignType:
        _apply_thread(comp, fam, row, length, notes)
    return occ, notes


def _seat_edge(occ, matrix, prefer_radius):
    """Circular edge of the placed screw whose centre is the seat point; closest radius to the hole wins."""
    origin = matrix.translation
    seat = adsk.core.Point3D.create(origin.x, origin.y, origin.z)
    best = None
    for body in occ.bRepBodies:
        for e in body.edges:
            c = adsk.core.Circle3D.cast(e.geometry) or adsk.core.Arc3D.cast(e.geometry)  # arcs: split washer
            if c and c.center.distanceTo(seat) < 1e-3:
                score = abs(c.radius - prefer_radius)
                if best is None or score < best[0]:
                    best = (score, e)
    return best[1] if best else None


def _z_of(occ):
    return occ.transform2.getAsCoordinateSystem()[3]


def join(design, parent, occ, hole, world_m, local_m, notes, offset=0.0):
    """Rigid joint between the part's seat edge and the hole edge, `offset` cm out of the hole (stacking).
    Tries both flip states and both offset signs and keeps the one that lands where world_m says."""
    if design.designType != adsk.fusion.DesignTypes.ParametricDesignType:
        notes.append('no joint: design is in direct modeling mode')
        return None
    try:
        screw_edge = _seat_edge(occ, world_m, hole.radius)
        if screw_edge is None:
            notes.append('no joint: seat edge not found')
            return None
        key = adsk.fusion.JointKeyPointTypes.CenterKeyPoint
        g1 = adsk.fusion.JointGeometry.createByCurve(screw_edge, key)
        g2 = adsk.fusion.JointGeometry.createByCurve(hole.edge, key)
        want = world_m.getAsCoordinateSystem()[3]
        want_o = world_m.translation.asPoint()
        joint = None
        tries = [(f, sg) for f in (False, True) for sg in ((1.0, -1.0) if offset else (1.0,))]
        for flipped, sign in tries:
            ji = parent.joints.createInput(g1, g2)
            ji.setAsRigidJointMotion()
            ji.isFlipped = flipped
            if offset:
                ji.offset = adsk.core.ValueInput.createByReal(sign * offset)
            joint = parent.joints.add(ji)
            if (_z_of(occ).dotProduct(want) > 0.999
                    and occ.transform2.translation.asPoint().distanceTo(want_o) < 1e-3):
                break
            joint.deleteMe()
            joint = None
            occ.transform2 = local_m  # put it back before the next try
            screw_edge = _seat_edge(occ, world_m, hole.radius)
            g1 = adsk.fusion.JointGeometry.createByCurve(screw_edge, key)
        if joint is None:
            notes.append('no joint: neither joint direction kept the screw in the hole')
            return None
        got = occ.transform2.translation
        if got.asPoint().distanceTo(world_m.translation.asPoint()) > 1e-3:
            notes.append('joint moved the screw off the hole centre; check it')
        return joint
    except Exception as e:
        notes.append('no joint: %s' % e)
        return None


_STACKS = ('cap', 'button', 'flbutton', 'pan', 'cheese', 'hex')  # screw heads that sit on a washer (not flat or set screws)


def place(app, design, cat, fam, row, length, finish_key, edges, flip=False, thread=True, stack=True):
    """Place one screw, nut or washer per picked edge, stacked on SR nuts/washers already at that edge.
    Returns (occurrences, notes)."""
    parent = design.activeComponent
    active_occ = design.activeOccurrence
    occs, notes = [], []
    for edge in edges:
        hole = read_hole(edge, flip)
        if hole is None:
            notes.append('skipped a non-circular edge')
            continue
        stacks = stack and (fc.kind(fam) != 'screw' or fam.get('head') in _STACKS)
        off = stack_offset(design, hole) if stacks else 0.0
        wm = world_matrix(hole, off)
        local = wm.copy()
        if active_occ is not None:
            inv = active_occ.transform2.copy()
            inv.invert()
            local.transformBy(inv)
        occ, notes = make_component(app, design, parent, cat, fam, row, length, finish_key, local, thread, notes)
        join(design, parent, occ, hole, wm, local, notes, off)
        occs.append(occ)
    return occs, notes
