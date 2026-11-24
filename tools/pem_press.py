"""PEM press-in parts for the catalog.

Every number is copied from a PEM datasheet (the bulletins) or the matching
catalog.pemnet.com item page. Page numbers are the ones the datasheet prints
in its own contents and footers. Nothing here is a guess: a size PEM does not
list is left out of the catalog and named in OMITTED.

Direct PDF download from pemnet.com was blocked by a CloudFront check, so the
datasheet text was read through the published PDF contents and checked against
the catalog item pages named in SOURCES. STEP files were not reachable.
"""

CL_URL = 'https://www.pemnet.com/wp-content/uploads/sites/2/2022/06/cldata.pdf'
FH_URL = 'https://www.pemnet.com/wp-content/uploads/sites/2/2022/06/fhdata.pdf'
SO_URL = 'https://www.pemnet.com/wp-content/uploads/sites/9/2023/10/sodata.pdf'
ALA_URL = 'https://www.pemnet.com/wp-content/uploads/sites/2/2022/06/aladata.pdf'
CAT = 'https://catalog.pemnet.com'

SOURCES = {
    'pem_cl': CL_URL + ' (PEM CL datasheet, self-clinching nuts S/SS/CLS/CLSS. Metric table page 5, drawing page 4, materials page 9.)',
    'pem_fh': FH_URL + ' (PEM FH datasheet, flush-head studs. FH/FHS metric table page 5, FH4 metric table page 6, materials page 17.)',
    'pem_so': SO_URL + ' (PEM SO datasheet, self-clinching standoffs. Thru-hole page 3, blind page 4, materials page 8.)',
    'pem_ala': ALA_URL + ' (PEM ALA datasheet, floating nuts AS/LAS. Dimension table footer ALA-2; metric values confirmed on catalog.pemnet.com item pages.)',
}

# Hole callouts on the metric tables are "+0.08". The inch table in the same
# datasheet prints "-.000", so the minus side is zero.
HOLE_PLUS = 0.08
HOLE_MINUS = 0.0

CL_CITE = (
    'PEM CL datasheet page 5 (metric S/SS/CLS/CLSS table; drawing on page 4). '
    'Hole +0.08 mm; inch table on page 4 prints -.000. Hardness notes on page 5; material chart page 9. ' + CL_URL)
FH_CITE = (
    'PEM FH datasheet page 5 (metric FH/FHS table). Hole +0.08 mm. '
    'H is the head diameter, S Max is the unthreaded length. The table does not publish a separate head thickness. ' + FH_URL)
FH4_CITE = (
    'PEM FH datasheet page 6 (metric FH4 table). Sheet thickness is the published range. '
    'Hole +0.08 mm. H is the head diameter. ' + FH_URL)
SO_CITE = (
    'PEM SO datasheet page 3 (metric SO/SOS thru-hole table and length chart). '
    'Hole +0.08 mm. C is the clinch diameter, H is the hex across flats. ' + SO_URL)
BSO_CITE = (
    'PEM SO datasheet page 4 (metric BSO/BSOS table). F minimum by length is the single F row on that page, '
    'mapped with the catalog.pemnet.com BSO metric listing (same F at each length for M3, 3.5M3 and M3.5). ' + SO_URL)
ALA_CITE = (
    'PEM ALA datasheet drawing note: "Float - .015 in / 0.38 mm minimum, in all directions from center, '
    '.030 in / 0.76 mm total." 0.76 mm is the total travel. 0.38 mm is the minimum from center to each side. '
    'The same page also says the part permits a total of .030 in / 0.76 mm adjustment for misalignment. '
    'E, C, A, T and D are the catalog item pages. The captive nut diameter is the STEP body. '
    'The model gap is the bulletin total, not the larger or smaller gap in the STEP. ' + ALA_URL)
# STEP-measured captive-nut body diameter (mm). The radial gap is not this number.
_NUT_DIA = {'M3': 5.978, 'M4': 7.527, 'M5': 8.346, 'M6': 10.512}

# Flush-stud head, measured from official PEM STEP files (data/pem_step_checks/fh.md).
# Same solid for FH, FHS and FH4 of one thread. Thickness T = H/10. The edge is a full
# round of radius T/2, so the crest H is at mid-thickness and each face is diameter H-T.
# Collar length is T/2. Barrel start is where the plain major-diameter cylinder begins.
# That start is shorter than catalog S. S is a maximum, so the shorter start is in spec.
# (thread, head thk, edge r, face dia, collar dia, collar len, neck len, undercut min dia, undercut len, barrel start)
_STUD_HEAD = {
    'M2.5': (0.410, 0.205, 3.690, 3.485, 0.205, 0.498, 2.233, 0.188, 1.300),
    'M3': (0.460, 0.230, 4.140, 3.910, 0.230, 0.485, 2.680, 0.225, 1.400),
    'M3.5': (0.530, 0.265, 4.770, 4.505, 0.265, 0.443, 3.127, 0.263, 1.500),
    'M4': (0.590, 0.295, 5.310, 5.015, 0.295, 0.415, 3.573, 0.300, 1.600),
    'M5': (0.650, 0.325, 5.850, 5.525, 0.325, 0.450, 4.467, 0.375, 1.800),
    'M6': (0.820, 0.410, 7.380, 6.970, 0.410, 0.320, 5.360, 0.450, 2.000),
    'M8': (0.960, 0.480, 8.640, 8.160, 0.480, 0.427, 7.146, 0.600, 2.467),
}

# (shank code, A max mm, minimum sheet mm) from the CL metric table.
_SHANK_012 = (('0', 0.77, 0.8), ('1', 0.97, 1.0), ('2', 1.38, 1.4))
_SHANK_M6 = (('00', 0.89, 0.92), ('0', 1.15, 1.2), ('1', 1.38, 1.4), ('2', 2.21, 2.29))
_SHANK_M8 = (('1', 1.38, 1.4), ('2', 2.21, 2.29))
_SHANK_M10 = (('1', 2.21, 2.29), ('2', 3.05, 3.18))

# size, major, pitch, C max, E, T, hole, edge, carbon type, stainless type, shanks.
# M5 is SS / CLSS in the table, not S / CLS. M2 is two steps below M3 and M12 is
# two steps above M8, so they are not in this one-step extension.
_NUTS = (
    ('M2.5', 2.5, 0.45, 4.2, 6.35, 1.5, 4.22, 4.8, 'S', 'CLS', _SHANK_012),
    ('M3', 3.0, 0.5, 4.2, 6.35, 1.5, 4.22, 4.8, 'S', 'CLS', _SHANK_012),
    ('M3.5', 3.5, 0.6, 4.73, 7.11, 1.5, 4.75, 5.6, 'S', 'CLS', _SHANK_012),
    ('M4', 4.0, 0.7, 5.38, 7.87, 2.0, 5.41, 6.9, 'S', 'CLS', _SHANK_012),
    ('M5', 5.0, 0.8, 6.33, 8.64, 2.0, 6.35, 7.1, 'SS', 'CLSS', _SHANK_012),
    ('M6', 6.0, 1.0, 8.73, 11.18, 4.08, 8.75, 8.6, 'S', 'CLS', _SHANK_M6),
    ('M8', 8.0, 1.25, 10.47, 12.7, 5.47, 10.5, 9.7, 'S', 'CLS', _SHANK_M8),
    ('M10', 10.0, 1.5, 13.97, 17.35, 7.48, 14.0, 13.5, 'S', 'CLS', _SHANK_M10),
)

# lengths, min sheet, hole, H, S, attached-hole, edge. max sheet is None except FH4.
_FH = (
    ('M2.5', 2.5, 0.45, (6, 8, 10, 12, 15, 18), 1.0, None, 2.5, 4.1, 1.95, 3.1, 5.4),
    ('M3', 3.0, 0.5, (6, 8, 10, 12, 15, 18, 20, 25), 1.0, None, 3.0, 4.6, 2.1, 3.6, 5.6),
    ('M3.5', 3.5, 0.6, (6, 8, 10, 12, 15, 18, 20, 25, 30), 1.0, None, 3.5, 5.3, 2.25, 4.1, 6.4),
    ('M4', 4.0, 0.7, (6, 8, 10, 12, 15, 18, 20, 25, 30, 35), 1.0, None, 4.0, 5.9, 2.4, 4.6, 7.2),
    ('M5', 5.0, 0.8, (8, 10, 12, 15, 18, 20, 25, 30, 35), 1.0, None, 5.0, 6.5, 2.7, 5.6, 7.2),
    ('M6', 6.0, 1.0, (10, 12, 15, 18, 20, 25, 30, 35), 1.6, None, 6.0, 8.2, 3.0, 6.6, 7.9),
    ('M8', 8.0, 1.25, (12, 15, 18, 20, 25, 30, 35), 2.4, None, 8.0, 9.6, 3.7, 8.6, 9.6),
)
_FH4 = (
    ('M3', 3.0, 0.5, (6, 8, 10, 12, 15, 18, 20, 25), 1.0, 2.4, 3.0, 4.6, 2.1, 3.3, 5.6),
    ('M4', 4.0, 0.7, (6, 8, 10, 12, 15, 18, 20, 25, 30, 35), 1.0, 2.4, 4.0, 5.9, 2.4, 4.7, 7.2),
    ('M5', 5.0, 0.8, (8, 10, 12, 15, 18, 20, 25, 30, 35), 1.0, 2.4, 5.0, 6.5, 2.7, 5.3, 7.2),
    ('M6', 6.0, 1.0, (10, 12, 15, 18, 20, 25, 30, 35), 1.6, 3.0, 6.0, 8.2, 3.0, 6.8, 7.9),
)

_SO_SHORT = (3, 4, 6, 8, 10, 12, 14, 16, 18)
_SO_LONG = (3, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 25)
# size key, thread code, major, pitch, menu thread, min sheet, hole, B, C, H, edge, lengths
_SO = (
    ('M3', 'M3', 3.0, 0.5, 'M3 x 0.5', 1.0, 4.22, 3.2, 4.2, 4.8, 6.0, _SO_SHORT),
    ('3.5M3', '3.5M3', 3.0, 0.5, 'M3 x 0.5', 1.0, 5.41, 3.2, 5.39, 6.4, 6.8, _SO_SHORT),
    ('M3.5', 'M3.5', 3.5, 0.6, 'M3.5 x 0.6', 1.0, 5.41, 3.9, 5.39, 6.4, 6.8, _SO_LONG),
    ('M4', 'M4', 4.0, 0.7, 'M4 x 0.7', 1.27, 7.14, 4.8, 7.12, 7.9, 8.0, _SO_LONG),
    ('M5', 'M5', 5.0, 0.8, 'M5 x 0.8', 1.27, 7.14, 5.35, 7.12, 7.9, 8.0, _SO_LONG),
)
# Blind thread depth F min (mm) by length. Bulletin page 4 lists 3.2, 4, 5, 6.5, 9.5
# once under the length columns. The catalog listing assigns them as follows.
_BSO_F = {6: 3.2, 8: 4.0, 10: 4.0, 12: 5.0, 14: 6.5, 16: 6.5, 18: 9.5, 20: 9.5, 22: 9.5, 25: 9.5}
_BSO_LEN = (6, 8, 10, 12, 14, 16, 18, 20, 22, 25)

# Floating nuts. T1/T2/D/edge read from catalog item pages; A and the hole from
# those pages and the metric listing. Shank 1 minimum sheet is 0.97 and shank 2
# is 1.38 (equal to A). M6 is published in shank 2 only. No M8 row.
_FLOAT = (
    # size, major, pitch, hole, C, D, E, T1, T2, edge, ((shank, A, min sheet), ...)
    ('M3', 3.0, 0.5, 7.37, 7.35, 7.37, 9.14, 3.31, 4.83, 7.62, (('1', 0.97, 0.97), ('2', 1.38, 1.38))),
    ('M4', 4.0, 0.7, 9.35, 9.33, 9.28, 11.18, 3.31, 5.34, 8.64, (('1', 0.97, 0.97), ('2', 1.38, 1.38))),
    ('M5', 5.0, 0.8, 10.31, 10.29, 10.29, 11.94, 4.32, 6.86, 9.14, (('1', 0.97, 0.97), ('2', 1.38, 1.38))),
    ('M6', 6.0, 1.0, 13.08, 13.06, 12.96, 15.24, 5.34, 7.88, 10.67, (('2', 1.38, 1.38),)),
)

OMITTED = (
    ('S and CLS at M5', 'CL datasheet page 5 lists SS and CLSS for M5, not S or CLS. SS and CLSS are included.'),
    ('S/CLS M2 and M12', 'One size below M3 is M2.5 and one size above M8 is M10. M2 and M12 are a further step.'),
    ('SP, CLA, SMPS, SMPP nuts', 'Not the S/CLS/CLSS families asked for.'),
    ('FH/FHS above M8, and M2', 'The metric FH table runs from M2.5 to M8. No M2 and no M10 row.'),
    ('FH4 outside M3-M6', 'The metric FH4 table has M3, M4, M5 and M6 only.'),
    ('FHA and FHP studs', 'Not the FH/FHS/FH4 families asked for.'),
    ('Helical thread on flush studs',
     'The official STEP is a plain major-diameter cylinder. The solid has no helix. The dialog can still add a cosmetic thread on the barrel.'),
    ('SO/BSO below M3 or above M5', 'The SO datasheet metric table starts at M3 and ends at M5. Micro sizes are bulletin MPF, a different family.'),
    ('SOA, SO4, BSOA, BSO4', 'Not the SO/SOS and BSO/BSOS families asked for.'),
    ('Standoff dimension D',
     'D changes with length (None, 4, 8, 11 mm) but the column groups were not clear enough to assign a D to every length without guessing. D is not used.'),
    ('AS/LAS M8 and M6 shank 1', 'The metric catalog listing has M3-M6, and M6 only as shank 2.'),
    ('AC, A4, LAC, LA4', 'Not the AS/LAS families asked for. LAS is the locking steel part, not a stainless body.'),
    ('Optional finishes (ZC yellow zinc, NC nickel)', 'Only the standard finish on each datasheet is included.'),
    ('Install force, pushout and torque-out',
     'The datasheets give those as tables by test sheet, not one number per part. The extract was not clean enough to copy a whole table without a wrong cell, so those figures are not stored.'),
    ('STEP cross-check for nuts, standoffs and floating nuts',
     'FH, FHS and FH4 studs were checked against official STEP files (data/pem_step_checks/fh.md). The other families are still waiting on their measurement reports.'),
)


def _num_lengths(lengths):
    return [int(n) for n in lengths]


def _hole_fields(hole, sheet, edge, hrb, hb):
    dims = {
        'hole': float(hole),
        'hole_plus': HOLE_PLUS,
        'hole_minus': HOLE_MINUS,
        'edge': float(edge),
        'max_hrb': int(hrb),
        'max_hb': int(hb),
    }
    if isinstance(sheet, dict):
        dims['min_sheet'] = {k: float(v) for k, v in sheet.items()}
    else:
        dims['min_sheet'] = float(sheet)
    return dims


def _row(size, major, pitch, thread_code, lengths, dims, cite, menu=None):
    row = {
        'size': size,
        'd': float(major),
        'pitch': float(pitch),
        'thread_code': thread_code,
        'lengths': list(lengths),
        'dims': dims,
        'citation': cite,
    }
    if menu:
        row['menu'] = menu
    return row


def _family(code, shape, name, finish, suffix, rows, cite, src_key, length_kind):
    return {
        'code': code,
        'kind': 'press-in',
        'shape': shape,
        'name': name,
        'system': 'metric',
        'length_kind': length_kind,
        'pem_suffix': suffix,
        'finishes': [finish],
        'sizes': rows,
        'source': SOURCES[src_key].split(' ')[0],
        'sources': {'dims': [src_key], 'lengths': [src_key], 'hole': [src_key], 'material': [src_key]},
        'citation': cite,
        'notes': cite,
    }


def _nut_rows(which):
    """which is 'carbon' or 'stainless'."""
    rows = []
    for size, major, pitch, c, e, t, hole, edge, carbon, stainless, shanks in _NUTS:
        code = carbon if which == 'carbon' else stainless
        if (which == 'carbon' and code not in ('S', 'SS')) or (which == 'stainless' and code not in ('CLS', 'CLSS')):
            continue
        # Built per type below; this helper filters by the type we are emitting.
        if which == 'carbon' and code != _emit:
            continue
        if which == 'stainless' and code != _emit:
            continue
        sheet = {sk: sh for sk, _a, sh in shanks}
        aa = {sk: a for sk, a, _sh in shanks}
        dims = _hole_fields(hole, sheet, edge, 80 if which == 'carbon' else 70, 150 if which == 'carbon' else 125)
        dims.update(C=float(c), E=float(e), T=float(t), A=aa, e_tol=0.25, t_tol=0.25)
        rows.append(_row(size, major, pitch, size, [sk for sk, _a, _sh in shanks], dims, CL_CITE))
    return rows


def _nuts(code):
    global _emit
    _emit = code
    which = 'carbon' if code in ('S', 'SS') else 'stainless'
    finish = 'PEM-ZI' if which == 'carbon' else 'PEM-SS'
    suffix = 'ZI' if which == 'carbon' else ''
    return _family(code, 'clinch-nut', 'Self-Clinching Nut', finish, suffix, _nut_rows(which), CL_CITE, 'pem_cl', 'shank')


def _studs(code, table, cite, hrb, hb, finish, suffix):
    rows = []
    for size, major, pitch, lengths, sheet, sheet_max, hole, h, s, attached, edge in table:
        dims = _hole_fields(hole, sheet, edge, hrb, hb)
        # S is the datasheet maximum unthreaded length, not a shoulder in the solid.
        thk, edge_r, face, collar_d, collar_l, neck, umin, ulen, barrel = _STUD_HEAD[size]
        dims.update(H=float(h), S=float(s), max_attached=float(attached), length_tol=0.4,
                    head_thk=float(thk), edge_r=float(edge_r), face_dia=float(face),
                    collar_dia=float(collar_d), collar_len=float(collar_l), neck_len=float(neck),
                    undercut_min_dia=float(umin), undercut_len=float(ulen), barrel_start=float(barrel))
        if sheet_max is not None:
            dims['max_sheet'] = float(sheet_max)
        rows.append(_row(size, major, pitch, size, _num_lengths(lengths), dims, cite))
    return _family(code, 'stud', 'Flush-Head Stud', finish, suffix, rows, cite, 'pem_fh', 'length')


def _standoffs(code, blind):
    finish = 'PEM-ZI' if code in ('SO', 'BSO') else 'PEM-SS'
    suffix = 'ZI' if finish == 'PEM-ZI' else ''
    hrb, hb = (80, 150) if finish == 'PEM-ZI' else (70, 125)
    cite = BSO_CITE if blind else SO_CITE
    name = 'Blind Standoff' if blind else 'Thru-Hole Standoff'
    rows = []
    for size, thread_code, major, pitch, menu, sheet, hole, b, c, h, edge, lengths in _SO:
        use = _BSO_LEN if blind else lengths
        dims = _hole_fields(hole, sheet, edge, hrb, hb)
        dims.update(C=float(c), H=float(h), length_plus=0.05, length_minus=0.13)
        if not blind:
            dims['B'] = float(b)
        else:
            dims['F'] = {str(n): float(_BSO_F[n]) for n in use}
        label = menu if size == thread_code else '%s (%s, thick wall)' % (menu, thread_code)
        rows.append(_row(size, major, pitch, thread_code, _num_lengths(use), dims, cite, menu=label))
    src = 'pem_so'
    return _family(code, 'standoff', name, finish, suffix, rows, cite, src, 'length')


def _floating(code):
    locking = code == 'LAS'
    rows = []
    for size, major, pitch, hole, c, d, e, t1, t2, edge, shanks in _FLOAT:
        sheet = {sk: sh for sk, _a, sh in shanks}
        aa = {sk: a for sk, a, _sh in shanks}
        dims = _hole_fields(hole, sheet, edge, 70, 125)
        dims.update(C=float(c), D=float(d), E=float(e), T1=float(t1), A=aa,
                    float_total=0.76, float_radial=0.38, nut_dia=float(_NUT_DIA[size]))
        if locking:
            dims['T2'] = float(t2)
        rows.append(_row(size, major, pitch, size, [sk for sk, _a, _sh in shanks], dims, ALA_CITE))
    name = 'Locking Floating Nut' if locking else 'Floating Nut'
    suffix = 'MD' if locking else 'ZI'
    return _family(code, 'floating', name, 'PEM-ZI', suffix, rows, ALA_CITE, 'pem_ala', 'shank')


def build_parts():
    parts = [
        _nuts('S'), _nuts('SS'), _nuts('CLS'), _nuts('CLSS'),
        _studs('FH', _FH, FH_CITE, 80, 150, 'PEM-ZI', 'ZI'),
        _studs('FHS', _FH, FH_CITE, 70, 125, 'PEM-SS', ''),
        _studs('FH4', _FH4, FH4_CITE, 92, 195, 'PEM-4SS', ''),
        _standoffs('SO', False), _standoffs('SOS', False),
        _standoffs('BSO', True), _standoffs('BSOS', True),
        _floating('AS'), _floating('LAS'),
    ]
    for part in parts:
        for row in part['sizes']:
            for key in ('hole', 'hole_plus', 'hole_minus', 'min_sheet', 'citation'):
                if key not in row['dims'] and key != 'citation':
                    raise RuntimeError('%s %s missing %s' % (part['code'], row['size'], key))
            if not row['citation'] or not row['dims']['hole']:
                raise RuntimeError('empty citation or hole')
    return parts
