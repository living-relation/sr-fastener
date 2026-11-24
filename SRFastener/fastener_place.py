"""Reads a picked hole edge, makes or reuses the screw, nut or washer component, places it and joins it (Fusion API).

Every placed fastener is a real component with a solid body saved in the design, so anyone can open the design
without the add-in. data/catalog.json is only the size table the add-in builds new parts from.

Stacks: place_stack() puts a screw (or a lone nut or washer) plus any number of nuts and washers on the near side
(the picked edge, under the screw head) and the far side (the other end of a through hole), in the order given,
each sitting on the one before. Parts already placed at that edge are stacked on too. A press-in part uses the
same stack: a mating screw on an internal thread, or a nut and washer on a stud. A mismatched thread is skipped."""
import re

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


def _hole_feature_thread(native, comp):
    """Designation from a tapped Hole feature whose side faces include this face (Fusion Hole command, Tapped)."""
    try:
        for hf in comp.features.holeFeatures:
            try:
                faces = hf.sideFaces
                hit = any(faces.item(i).tempId == native.tempId for i in range(faces.count))
                if not hit:
                    continue
                for name in ('tappedHoleInfo', 'threadInfo'):
                    try:
                        ti = getattr(hf, name, None)
                    except Exception:  # not a tapped hole
                        ti = None
                    if ti is not None and getattr(ti, 'threadDesignation', None):
                        return ti.threadDesignation
            except Exception:
                continue
    except Exception:
        pass
    return None


def _thread_designation(face):
    """Designation of a thread on this hole face, if any (e.g. 'M3x0.5'): a Thread feature, or a tapped Hole
    feature. None means a plain (untapped) hole."""
    try:
        native = face.nativeObject or face
        comp = native.body.parentComponent
        des = _hole_feature_thread(native, comp)
        if des:
            return des
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


def measure_mount(edge):
    """(sheet thickness mm, minimum centerline-to-edge mm) from the picked hole, or (None, None).
    Sheet thickness is the cylindrical wall's extent along the hole. Edge distance is the nearest
    other edge on a flat face of the hole. Hardness is not in the model."""
    curve = adsk.core.Circle3D.cast(edge.geometry) or adsk.core.Arc3D.cast(edge.geometry)
    if curve is None:
        return None, None
    normal = curve.normal.copy()
    normal.normalize()
    centre = curve.center
    sheet = None
    for i in range(edge.faces.count):
        face = edge.faces.item(i)
        if face.geometry.surfaceType != adsk.core.SurfaceTypes.CylinderSurfaceType:
            continue
        box = face.boundingBox
        lo, hi = box.minPoint, box.maxPoint
        dots = []
        for x in (lo.x, hi.x):
            for y in (lo.y, hi.y):
                for z in (lo.z, hi.z):
                    dots.append((x - centre.x) * normal.x + (y - centre.y) * normal.y + (z - centre.z) * normal.z)
        sheet = (max(dots) - min(dots)) * 10.0
        break
    nearest = None
    for i in range(edge.faces.count):
        face = edge.faces.item(i)
        if face.geometry.surfaceType != adsk.core.SurfaceTypes.PlaneSurfaceType:
            continue
        for other in face.edges:
            if other == edge:
                continue
            try:
                ok, point = other.evaluator.getClosestPointTo(centre)
            except Exception:
                continue
            if not ok:
                continue
            dist = point.distanceTo(centre) * 10.0
            if nearest is None or dist < nearest:
                nearest = dist
    return sheet, nearest


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


def _library_material(app, name):
    for libname in ('Fusion Material Library',):
        lib = app.materialLibraries.itemByName(libname)
        if lib:
            m = lib.materials.itemByName(name)
            if m:
                return m
    return None


def _material(app, design, name, base, notes):
    """A design material called `name` (Daniel's plain material name, e.g. 'Stainless Steel'), copied from the
    library material `base` so mass and stiffness are right. Made once per design and reused."""
    try:
        m = design.materials.itemByName(name)
        if m:
            return m
    except Exception:
        pass
    src = _library_material(app, base)
    if src is None:
        notes.append('material not found: %s' % base)
        return None
    try:
        return design.materials.addByCopy(src, name)
    except Exception as e:
        notes.append('could not make material "%s" (%s); used %s' % (name, e, base))
        return src


APPEARANCE_FALLBACK = {'Steel - Galvanized (Small)': ['Steel - Galvanized (Small)', 'Steel - Satin']}


def _appearance(app, design, name):
    for want in APPEARANCE_FALLBACK.get(name, [name]):
        a = design.appearances.itemByName(want)
        if a:
            return a
        for libname in ('Fusion Appearance Library', 'Fusion Material Library'):
            lib = app.materialLibraries.itemByName(libname)
            if lib:
                src = lib.appearances.itemByName(want)
                if src:
                    return design.appearances.addByCopy(src, want)
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
        g = fc.press_geometry(fam, row, length) if fc.kind(fam) == 'press-in' else fc.geometry(fam, row, length)
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


# True while the dialog's live preview is placing parts. Preview parts are tagged so hardware_at() does not
# mistake them for parts already in the hole (Fusion keeps the preview on screen while inputs change).
PREVIEW = False


def _mark_preview(occ):
    # on the occurrence: a preview often reuses a component that is already in the design
    if PREVIEW:
        try:
            occ.attributes.add(ATTR, 'preview', '1')
        except Exception:
            pass


def _is_preview(occ):
    try:
        native = occ.nativeObject or occ
        return native.attributes.itemByName(ATTR, 'preview') is not None
    except Exception:
        return False


def make_component(app, design, parent, cat, fam, row, length, finish_key, matrix, thread=True, notes=None):
    """Create (or reuse) the screw component and add an occurrence at `matrix` (parent-local)."""
    notes = notes if notes is not None else []
    bom = fc.bom_fields(cat, fam, row, length, finish_key)
    pn = bom['part_number']
    existing = _find_component(design, pn)
    if existing is not None:
        occ = parent.occurrences.addExistingComponent(existing, matrix)
        _mark_preview(occ)
        return occ, notes
    occ = parent.occurrences.addNewComponent(matrix)
    _mark_preview(occ)
    comp = occ.component
    comp.name = pn
    comp.partNumber = pn
    comp.description = bom['description']
    press = fc.kind(fam) == 'press-in'
    is_part = fc.kind(fam) not in ('screw', 'press-in')
    if press:
        built = geom.build_press_body(fam, row, length)
    elif is_part:
        built = geom.build_part_body(fam, row)[0]
    else:
        built = geom.build_body(fam, row, length)
    bodies = built if isinstance(built, (list, tuple)) else [built]
    if design.designType == adsk.fusion.DesignTypes.ParametricDesignType:
        bf = comp.features.baseFeatures.add()
        bf.startEdit()
        for one in bodies:
            comp.bRepBodies.add(one, bf)
        bf.finishEdit()
        bf.name = 'SR Fastener'
    else:
        for one in bodies:
            comp.bRepBodies.add(one)
    for i in range(comp.bRepBodies.count):
        comp.bRepBodies.item(i).name = pn if i == 0 else (pn + ' nut')
    b = comp.bRepBodies.item(0)
    mat = _material(app, design, bom['material'], bom['base_material'], notes)
    if mat:
        comp.material = mat
        for i in range(comp.bRepBodies.count):
            comp.bRepBodies.item(i).material = mat
    ap = _appearance(app, design, bom['appearance'])
    if ap:
        for i in range(comp.bRepBodies.count):
            comp.bRepBodies.item(i).appearance = ap
    else:
        notes.append('appearance not found: %s' % bom['appearance'])
    for k in ('part_number', 'description', 'finish', 'finish_key', 'grade'):
        comp.attributes.add(ATTR, k, str(bom[k]))
    comp.attributes.add(ATTR, 'family', fam['code'])
    comp.attributes.add(ATTR, 'size', row['size'])
    comp.attributes.add(ATTR, 'length', str(length) if length is not None else '')
    comp.attributes.add(ATTR, 'kind', fc.kind(fam))
    if is_part:
        comp.attributes.add(ATTR, 'thickness', repr(fc.part_geometry(fam, row)['thickness']))
    elif press:
        _press_properties(design, comp, fam, row, length, notes)
        if thread and fam.get('shape') == 'stud' and design.designType == adsk.fusion.DesignTypes.ParametricDesignType:
            _apply_thread(comp, fam, row, length, notes)
    elif thread and design.designType == adsk.fusion.DesignTypes.ParametricDesignType:
        _apply_thread(comp, fam, row, length, notes)
    return occ, notes


def _param_name(pn, suffix):
    safe = re.sub(r'[^A-Za-z0-9]', '_', pn)
    return 'pem_%s_%s' % (safe, suffix)


def _press_properties(design, comp, fam, row, length, notes):
    """Hole size, tolerance and minimum sheet as user parameters and attributes.
    They are not written into the description, so they are not a BOM column."""
    spec = fc.mount_spec(fam, row, length)
    comp.attributes.add(ATTR, 'mount_hole', '%g mm' % spec['hole'])
    comp.attributes.add(ATTR, 'mount_tol', '+%g/-%g mm' % (spec['hole_plus'], spec['hole_minus']))
    comp.attributes.add(ATTR, 'min_sheet', '%g mm' % spec['min_sheet'])
    comp.attributes.add(ATTR, 'citation', spec['citation'])
    try:
        params = design.userParameters
    except Exception as e:
        notes.append('user parameters not added: %s' % e)
        return
    # The PEM designation does not use the finish key; the family's finish still satisfies the call.
    pn = fc.part_number(fam, row, length, fam['finishes'][0])
    for suffix, mm, comment in fc.parameter_values(fam, row, length):
        name = _param_name(pn, suffix)
        try:
            if params.itemByName(name) is None:
                params.add(name, adsk.core.ValueInput.createByReal(mm / 10.0), 'mm', comment)
        except Exception as e:
            notes.append('user parameter %s not added: %s' % (name, e))


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


def far_side(hole):
    """The other end of the hole (exit edge of a through hole), as a Hole whose `into` points back into the part.
    None for a blind hole."""
    axis = hole.into
    best = None
    try:
        edges = hole.edge.body.edges
    except Exception:
        return None
    for e in edges:
        c = adsk.core.Circle3D.cast(e.geometry)
        if c is None:
            continue
        n = c.normal.copy()
        n.normalize()
        if abs(n.dotProduct(axis)) < 0.999:
            continue
        v = hole.centre.vectorTo(c.center)
        along = v.dotProduct(axis)
        if along <= _TOL:
            continue
        if max(v.dotProduct(v) - along * along, 0.0) > 1e-6:
            continue
        exit_face = False
        for i in range(e.faces.count):
            f = e.faces.item(i)
            if f.geometry.surfaceType != adsk.core.SurfaceTypes.PlaneSurfaceType:
                continue
            ok, normal = f.evaluator.getNormalAtPoint(f.pointOnFace)
            if ok and normal.dotProduct(axis) > 0.99:
                exit_face = True
        if not exit_face:
            continue
        key = (round(along, 5), c.radius)
        if best is None or key[0] > best[0][0] + 1e-5 or (abs(key[0] - best[0][0]) < 1e-5 and key[1] < best[0][1]):
            best = (key, e, c)
    if best is None:
        return None
    _, e, c = best
    into = axis.copy()
    into.scaleBy(-1)
    return Hole(e, c.center, into, c.radius, hole.thread)


def _finish_from_pn(pn):
    for key, code in sorted(fc._FIN_CODE.items(), key=lambda kv: -len(kv[1])):
        if (pn or '').endswith(' ' + code):
            return key
    return None


def hardware_at(design, hole, reach=15.0):
    """SR screws, nuts and washers already on this hole's axis (either side, within `reach` cm):
    [{'code', 'size', 'finish', 'length', 'kind', 'along'}]."""
    out = []
    axis = hole.into
    for occ in design.rootComponent.allOccurrences:
        comp = occ.component
        k = _attr(comp, 'kind')
        if k not in ('screw', 'nut', 'washer') or _is_preview(occ):
            continue
        origin, _, _, z = occ.transform2.getAsCoordinateSystem()
        if abs(z.dotProduct(axis)) < 0.999:
            continue
        v = hole.centre.vectorTo(origin)
        along = v.dotProduct(axis)
        if abs(along) > reach or max(v.dotProduct(v) - along * along, 0.0) > 1e-6:
            continue
        fin = _attr(comp, 'finish_key') or _finish_from_pn(_attr(comp, 'part_number'))
        try:
            length = float(_attr(comp, 'length')) if _attr(comp, 'length') else None
        except ValueError:
            length = None
        out.append({'code': _attr(comp, 'family'), 'size': _attr(comp, 'size'), 'finish': fin, 'length': length,
                    'kind': k, 'along': along})
    return out


def existing_items(cat, design, hole):
    """hardware_at() as fastener_core stack items (unknown types are skipped)."""
    items = []
    for h in hardware_at(design, hole):
        try:
            it = fc.item(cat, h['code'], h['size'], h['finish'], h['length'])
        except (KeyError, TypeError):
            continue
        it['existing'] = True
        items.append(it)
    return items


def _local(design, wm):
    local = wm.copy()
    active_occ = design.activeOccurrence
    if active_occ is not None:
        inv = active_occ.transform2.copy()
        inv.invert()
        local.transformBy(inv)
    return local


def _place_one(app, design, cat, it, hole, off, thread, notes, join_hole=None, join_off=None):
    parent = design.activeComponent
    wm = world_matrix(hole, off)
    local = _local(design, wm)
    occ, notes = make_component(app, design, parent, cat, it['fam'], it['row'], it.get('length'), it['finish'],
                                local, thread and it['kind'] == 'screw', notes)
    join(design, parent, occ, join_hole or hole, wm, local, notes, off if join_off is None else join_off)
    return occ


def _hole_along(hole, distance_cm):
    """Same hole edge, with the seat moved `distance_cm` along `into` and the part's head pointing that way."""
    centre = hole.centre.copy()
    step = hole.into.copy()
    step.scaleBy(distance_cm)
    centre.translateBy(step)
    into = hole.into.copy()
    into.scaleBy(-1)
    return Hole(hole.edge, centre, into, hole.radius, hole.thread)


def _place_press(app, design, cat, main, rows, hole, thread, notes, occs):
    """The PEM sits on the install face. Allowed mates then sit on the end the rule names."""
    occs.append(_place_one(app, design, cat, main, hole, 0.0, thread, notes))
    issues = fc.press_stack_issues(cat, main, rows)
    for _, msg in issues:
        notes.append(msg)
    far_hole = None
    far_base = 0.0
    for place in fc.press_mate_places(main, rows):
        mate = rows[place['index']]
        end = place['end']
        if end == 'out':
            occs.append(_place_one(app, design, cat, mate, hole, place['offset_cm'], thread, notes))
        elif end == 'tip':
            dist = place['distance_cm']
            occs.append(_place_one(app, design, cat, mate, _hole_along(hole, dist), 0.0, thread, notes,
                                   join_hole=hole, join_off=dist))
        else:
            if far_hole is None:
                far_hole = far_side(hole)
                far_base = stack_offset(design, far_hole) if far_hole is not None else 0.0
            if far_hole is None:
                notes.append('nut or washer skipped: no far side found (blind hole?)')
                continue
            occs.append(_place_one(app, design, cat, mate, far_hole, far_base + place['offset_cm'], thread, notes))


def _thickness(it):
    return fc.part_geometry(it['fam'], it['row'])['thickness']


def place_stack(app, design, cat, main, rows, edges, flip=False, thread=True):
    """Place `main` (a screw, nut or washer item, or None) and the stack `rows` on every picked edge.
    rows: items with 'side' 'near' (picked edge side, under the screw head) or 'far' (other end of the hole), each
    side listed from the part outward. Returns (occurrences, notes)."""
    occs, notes = [], []
    for edge in edges:
        hole = read_hole(edge, flip)
        if hole is None:
            notes.append('skipped a non-circular edge')
            continue
        if main is not None and main['kind'] == 'press-in':
            _place_press(app, design, cat, main, rows, hole, thread, notes, occs)
            continue
        near = [r for r in rows if r.get('side', 'near') == 'near']
        far = [r for r in rows if r.get('side') == 'far']
        off = stack_offset(design, hole)
        if main is not None and main['kind'] == 'screw' and main['fam'].get('head') not in _STACKS and near:
            notes.append('near-side nuts/washers skipped: a %s screw does not sit on a washer' % main['fam']['head'])
            near = []
        for it in near:
            occs.append(_place_one(app, design, cat, it, hole, off, thread, notes))
            off += _thickness(it)
        if main is not None:
            stacks = main['kind'] != 'screw' or main['fam'].get('head') in _STACKS
            occs.append(_place_one(app, design, cat, main, hole, off if stacks else 0.0, thread, notes))
        if far:
            fh = far_side(hole)
            if fh is None:
                notes.append('far-side nuts/washers skipped: no far side found (blind hole?)')
            else:
                off2 = stack_offset(design, fh)
                for it in far:
                    occs.append(_place_one(app, design, cat, it, fh, off2, thread, notes))
                    off2 += _thickness(it)
    return occs, notes


def place(app, design, cat, fam, row, length, finish_key, edges, flip=False, thread=True, stack=True):
    """One screw, nut or washer per picked edge, stacked on SR nuts/washers already at that edge (used by the
    smoke test). Returns (occurrences, notes)."""
    main = {'fam': fam, 'row': row, 'length': length, 'finish': finish_key, 'kind': fc.kind(fam)}
    return place_stack(app, design, cat, main, [], edges, flip, thread)
