"""Writes SRFastener/data/catalog.json from the tables below.

Every number here comes from the cited source (checked 2026-11-16). Each family lists the
sources for its tables in `sources`, and each value block names the source key it came from.
Values a source did not give are left out, and docs/SOURCES.md lists them as TBD.
Do not add a size, a dimension or a length without a source.

Run: python tools/build_catalog.py   (the check script fails if the JSON is out of date)
"""
import json
import os

HK = 'https://www.holo-krome.com/uploads/7/2/7/5/72754089/'
ITEH = 'https://cdn.standards.iteh.ai/samples/'
SRC = {
    # Standards (official ISO preview pages, which carry the full dimension tables)
    'iso4762': ITEH + '34460/06335046afaf46fb8e84d91a3eda001d/ISO-4762-2004.pdf (ISO 4762:2004 Table 1: dk, k, s, t, b, lengths, ls/lg)',
    'iso7380': ITEH + '53671/84df01c5fcce4a91896ac3b0c55ca128/ISO-7380-1-2011.pdf (ISO 7380-1:2011 Table 1: dk, k, rf, s, t, b, lengths, ls/lg)',
    'iso7380_22': ITEH + '78699/a175805085534f98983d6c8aa583a5b0/ISO-7380-1-2022.pdf (ISO 7380-1:2022 Table 1: same dk, k, rf, s; t min)',
    'iso10642': ITEH + '34454/32dec7e84d974361b85f744935ab2175/ISO-10642-2004.pdf (ISO 10642:2004 Table 1: dk theor. max, k, s, t, b, lengths, ls/lg)',
    'iso4017': ITEH + '72585/1179998ddd594550a909d6e13c416f3e/ISO-4017-2022.pdf (ISO 4017:2022 Table 1: s max, k nom)',
    'iso4026': ITEH + '36431/f53ced64ab1946679bd80f0a0e6cac63/ISO-4026-2003.pdf (ISO 4026:2003 Table 1: s, dp max, t min short/long, lengths)',
    'iso4029': ITEH + '36433/631453640d214e7682ed5a23ddee05b5/ISO-4029-2003.pdf (ISO 4029:2003 Table 1: dz, s, t min short/long, lengths)',
    'iso7045': ITEH + '57372/fafe91d8504049fc8953281401736c79/ISO-7045-2011.pdf (ISO 7045:2011 Table 1: dk, k, rf, recess H no., m, penetration, b, lengths)',
    'iso1207': ITEH + '54039/15c540b697434b5d85128ca34672939c/ISO-1207-2011.pdf (ISO 1207:2011 Table 1: dk, k, n, t, b, lengths)',
    # Maker documents (Holo-Krome product standards are also Fastenal's product standards)
    'hk_shcs': HK + 'hk.usa.shcs.alloy.bo.pdf (Holo-Krome HK.USA.SHCS.ALLOY.BO: ASTM A574 alloy, black oxide; A, H, J, T, LT)',
    'hk_bhcs': HK + 'button_head_socket_cap_screws.pdf (Holo-Krome HK.BHSCS.ALLOY.BO: ASTM F835 alloy, black oxide; A, H, S, J, T, max length)',
    'hk_fhcs': HK + 'flat_head_socket_cap_screws.pdf (Holo-Krome HK.FHSCS.ALLOY.BO: ASTM F835 alloy, black oxide, 82 deg; A, H, J, T)',
    'hk_lhcs': HK + 'low_head_socket_cap_screws.pdf (Holo-Krome low head, ASTM A574 material, black oxide, #8 to 1/2; A, H, J, T)',
    'hk_m_shcs': HK + 'hk.m.shcs.12.9.bo.pdf (Holo-Krome HK.M.SHCS.12.9.BO: ISO 4762 class 12.9, black oxide; k, s, t)',
    'hk_m_bhcs': HK + 'metric_button_head_cap_screws.pdf (Holo-Krome HK.M.BHSCS.12.9.BO: ISO 7380 class 12.9, black oxide, M3 to M12)',
    'hk_m_fhcs': HK + 'metric_flat_head_cap_screws.pdf (Holo-Krome HK.M.FHSCS.10642.12.9.BO: ISO 10642 class 12.9, black oxide, M3 to M16)',
    'hk_tech': HK + 'hk_consolidated_tech_manual_full_2015.pdf (Holo-Krome technical manual: Table 2 SHCS grip lengths, Table 9 FHCS grip lengths, Tables 13-14 set screws)',
    'bbi_7984': 'https://www.brightonbest.com/download/pds/PDS_Metric_Socket_Low_Head_Cap_Screws.pdf (Brighton-Best DIN 7984 data sheet: dk, k, s, t min; stocked 10.9 thermal black oxide and A2-70)',
    'fn_7984': 'https://img1.wsimg.com/blobby/go/e4d6d25e-f207-42ab-b81b-af3cf3be0a8c/downloads/1cda5ngcl_731976.pdf (Fastener Network DIN 7984 sheet: second source for dk, k, s)',
    'b183_fhcs': 'https://patriotbolt.com/technical/hexagon-socket-flat-countersunk-head-cap-screws/ (ASME B18.3 FHCS table: #2 row, not in Holo-Krome)',
    'b183_lhcs': 'https://patriotbolt.com/technical/low-head-hexagon-socket-head-cap-screws/ (ASME B18.3 low head table: #4 and #6 rows, not in Holo-Krome)',
    'b1821_hex': 'https://www.fastenersetcinc.com/ (Brighton-Best inch hex cap screw table per ASME B18.2.1: F max, H max, LT)',
    # Alloy black-oxide availability (who sells it)
    'av_m_bhcs16': 'https://imsbolt.com/m16-2-00-x-40-mm-10-9-button-socket-caps-coarse-iso-7380-thermal-black-oxide-fully-threaded-qty-25/ (ISO 7380 M16 class 10.9 thermal black oxide)',
    'av_m_set': 'https://www.fastenersolutions.com/832070-p-37868.html (ISO 4026 / DIN 913 class 45H thermal black oxide)',
    'av_m_set2': 'https://www.fastenal.ca/product/details/90061 (Fastenal M6 x 25 ISO 4026 flat point, black oxide alloy steel)',
    'av_in_set': 'https://www.fastenal.ca/product/details/24879 (Fastenal 1/4-20 x 1-1/2 flat point, black oxide alloy steel, ASME B18.3 / ASTM F912)',
    'av_in_hex': 'https://www.raptorsupplies.com/c/fasteners/c5/black-oxide-grade-8-steel-hex-head-cap-screws (Grade 8 black oxide hex cap screws, ASME B18.2.1 / SAE J429)',
}

# Preferred length series. A size's range is trimmed from these by the cited standard or maker range.
MM_LENGTHS = [3, 4, 5, 6, 8, 10, 12, 14, 16, 18, 20, 22, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 80, 90, 100]
IN_LENGTHS = [0.125, 0.1875, 0.25, 0.3125, 0.375, 0.4375, 0.5, 0.625, 0.75, 0.875, 1.0, 1.25, 1.5,
              1.75, 2.0, 2.25, 2.5, 2.75, 3.0, 3.5, 4.0]

# Finish codes follow Daniel's BOM part-number rule (ends with 18-8 SS or 18-8 SS-BO).
# ALLOY-BO is a made-up code: his list has no code for alloy steel black oxide.
FINISHES = {
    'SS': {'code': '18-8 SS', 'name': '18-8 stainless steel', 'material': 'Stainless Steel AISI 304',
           'appearance': 'Stainless Steel - Satin'},
    'SS-BO': {'code': '18-8 SS-BO', 'name': '18-8 stainless steel, black oxide',
              'material': 'Stainless Steel AISI 304', 'appearance': 'Coating - Black Oxide'},
    'ALLOY-BO': {'code': 'ALLOY-BO', 'name': 'alloy steel, black oxide', 'material': 'Steel AISI 4142 400 QT',
                 'appearance': 'Coating - Black Oxide', 'made_up_code': True},
}
# Fusion has no generic 'alloy steel' material. The makers do not name the alloy (ASTM A574 and ISO 898-1
# allow several, e.g. 4037, 4140, 8740), so the material is a quenched-and-tempered Fusion steel whose
# hardness sits inside the grade's range. Density and stiffness are the same for all of them.
#   12.9 / A574 / F835: Holo-Krome HRC 39-44 -> 4142 at 400 HB (about HRC 43)
#   10.9: Brighton-Best HRC 32-39; Grade 8 (SAE J429, HRC 33-39, not from a cited page) -> 4340 at 350 HB (about HRC 38)
#   45H / F912 set screws (HRC 45-53 per ISO 898-5 / ASTM F912, not from a cited page) -> 4142 at 475 HB (about HRC 50)
ALLOY_MATERIAL = {
    'class 12.9': 'Steel AISI 4142 400 QT', 'ASTM A574': 'Steel AISI 4142 400 QT', 'ASTM F835': 'Steel AISI 4142 400 QT',
    'class 10.9': 'Steel AISI 4340 350A QT', 'SAE J429 Grade 8': 'Steel AISI 4340 350A QT',
    'class 45H': 'Steel AISI 4142 475 QT', 'ASTM F912': 'Steel AISI 4142 475 QT',
}

PITCH = {'M2': 0.4, 'M2.5': 0.45, 'M3': 0.5, 'M4': 0.7, 'M5': 0.8, 'M6': 1.0, 'M8': 1.25,
         'M10': 1.5, 'M12': 1.75, 'M16': 2.0, 'M20': 2.5}
UNC = {'#2': (0.086, 56), '#4': (0.112, 40), '#6': (0.138, 32), '#8': (0.164, 32), '#10': (0.190, 24),
       '1/4': (0.25, 20), '5/16': (0.3125, 18), '3/8': (0.375, 16), '1/2': (0.5, 13)}
# UNF threads per inch (ASME B1.1; Holo-Krome stocks UNRF in socket head, button, flat and low head).
UNF = {'#2': 64, '#4': 48, '#6': 40, '#8': 36, '#10': 32, '1/4': 28, '5/16': 24, '3/8': 24, '1/2': 20}

# Length ranges per size, (min, max), each from the cited table's preferred/standard lengths.
R_4762 = {'M2': (3, 20), 'M2.5': (4, 25), 'M3': (5, 30), 'M4': (6, 40), 'M5': (8, 50), 'M6': (10, 60),
          'M8': (12, 80), 'M10': (16, 100), 'M12': (20, 100), 'M16': (20, 100)}  # M16: TBD (not in preview)
R_7380 = {'M3': (6, 30), 'M4': (8, 40), 'M5': (10, 50), 'M6': (10, 60), 'M8': (12, 80), 'M10': (16, 90),
          'M12': (20, 90), 'M16': (25, 90)}
R_10642 = {'M3': (8, 30), 'M4': (8, 40), 'M5': (8, 50), 'M6': (8, 60), 'M8': (10, 80), 'M10': (12, 100),
           'M12': (20, 100), 'M16': (30, 100), 'M20': (35, 100)}
R_4026 = {'M3': (3, 16), 'M4': (4, 20), 'M5': (5, 25), 'M6': (6, 30), 'M8': (8, 40), 'M10': (10, 50),
          'M12': (12, 60)}
R_7045 = {'M2': (3, 20), 'M2.5': (3, 25), 'M3': (4, 30), 'M4': (5, 40), 'M5': (6, 45), 'M6': (8, 60),
          'M8': (10, 60), 'M10': (12, 60)}
R_1207 = {'M2': (3, 20), 'M2.5': (3, 25), 'M3': (4, 30), 'M4': (5, 40), 'M5': (6, 50), 'M6': (8, 60),
          'M8': (10, 80), 'M10': (12, 80)}
# Not verified against a standard length table (docs/SOURCES.md lists these as TBD):
R_MM_UNVERIFIED = {'M3': (4, 40), 'M4': (5, 50), 'M5': (6, 60), 'M6': (8, 80), 'M8': (10, 100),
                   'M10': (12, 100), 'M12': (16, 100), 'M16': (20, 100)}
IN_RANGE = {'#2': (0.125, 0.75), '#4': (0.125, 1.0), '#6': (0.125, 1.5), '#8': (0.25, 2.0),
            '#10': (0.25, 2.5), '1/4': (0.25, 3.0), '5/16': (0.375, 3.5), '3/8': (0.375, 4.0),
            '1/2': (0.5, 4.0)}  # inch stock ranges are not verified (TBD)
# Holo-Krome button head maximum standard lengths (HK.BHSCS.ALLOY.BO, per ASME B18.3).
R_BHCS_IN = {'#2': (0.125, 0.5), '#4': (0.125, 0.5), '#6': (0.125, 0.625), '#8': (0.25, 0.75),
             '#10': (0.25, 1.0), '1/4': (0.25, 1.0), '5/16': (0.375, 1.0), '3/8': (0.375, 1.25),
             '1/2': (0.5, 2.0)}
# Inch set screws: start at Holo-Krome Table 13 column B (shortest length with full key engagement)
# or a Table 14 short length; the upper end is not verified (TBD).
R_SET_IN = {'#2': (0.125, 0.5), '#4': (0.125, 0.75), '#6': (0.125, 1.0), '#8': (0.125, 1.0),
            '#10': (0.125, 1.5), '1/4': (0.1875, 2.0), '5/16': (0.25, 2.0), '3/8': (0.25, 2.0),
            '1/2': (0.5, 2.0)}

# Thread length rules.
#   {'b': x, 'partial_from': L}: lengths >= L carry thread length b (ref); shorter ones are threaded to the head.
#   {'lg': {L: LG}}: grip length per nominal length (inch SHCS under the head, inch FHCS from the head top);
#                    thread length = L - LG. Lengths not listed are threaded to the head.
#   no 'thread' key: threaded to the head for every offered length.
T_4762 = {'M2': (16, 20), 'M2.5': (17, 25), 'M3': (18, 25), 'M4': (20, 30), 'M5': (22, 30), 'M6': (24, 35),
          'M8': (28, 40), 'M10': (32, 45), 'M12': (36, 55)}  # M16: TBD, modeled threaded to the head
T_7380 = {'M3': (18, 25), 'M4': (20, 30), 'M5': (22, 30), 'M6': (24, 35), 'M8': (28, 40), 'M10': (32, 45),
          'M12': (36, 55), 'M16': (44, 65)}
T_10642 = {'M3': (18, 30), 'M4': (20, 30), 'M5': (22, 35), 'M6': (24, 40), 'M8': (28, 50), 'M10': (32, 55),
           'M12': (36, 65), 'M16': (44, 80), 'M20': (52, 100)}
T_7045 = {'M3': (25, 30), 'M5': (38, 45), 'M6': (38, 45), 'M8': (38, 45), 'M10': (38, 45)}  # b min
T_1207 = {'M5': (38, 45), 'M6': (38, 45), 'M8': (38, 45), 'M10': (38, 45)}  # b min
LG_SHCS = {  # Holo-Krome Table 2 (1960 series), LG max under the head
    '#4': {1.25: .25, 1.5: .75, 1.75: .75, 2.0: 1.25, 2.25: 1.25},
    '#6': {1.25: .50, 1.5: .50, 1.75: 1.00, 2.0: 1.00, 2.25: 1.50, 2.5: 1.50, 2.75: 2.00},
    '#8': {1.25: .38, 1.5: .38, 1.75: .88, 2.0: .88, 2.25: 1.38, 2.5: 1.38, 2.75: 1.88, 3.0: 1.88},
    '#10': {1.25: .38, 1.5: .38, 1.75: .88, 2.0: .88, 2.25: 1.38, 2.5: 1.38, 2.75: 1.88, 3.0: 1.88,
            3.5: 2.38, 4.0: 2.88},
    '1/4': {1.5: .50, 1.75: .50, 2.0: 1.00, 2.25: 1.00, 2.5: 1.50, 2.75: 1.50, 3.0: 2.00, 3.5: 2.50, 4.0: 3.00},
    '5/16': {1.75: .62, 2.0: .62, 2.25: 1.12, 2.5: 1.12, 2.75: 1.62, 3.0: 1.62, 3.5: 2.12, 4.0: 2.62},
    '3/8': {1.75: .50, 2.0: .50, 2.25: 1.00, 2.5: 1.00, 2.75: 1.50, 3.0: 1.50, 3.5: 2.00, 4.0: 2.50},
    '1/2': {2.25: .75, 2.5: .75, 2.75: .75, 3.0: 1.50, 3.5: 1.50, 4.0: 2.25},
}
LG_FHCS = {  # Holo-Krome Table 9, LGH max measured from the top of the head
    '#4': {1.25: .50, 1.5: .50, 1.75: 1.00, 2.0: 1.00, 2.25: 1.50},
    '#6': {1.25: .50, 1.5: .50, 1.75: 1.00, 2.0: 1.00, 2.25: 1.50, 2.5: 1.50, 2.75: 2.00},
    '#8': {1.25: .38, 1.5: .38, 1.75: .88, 2.0: .88, 2.25: 1.38, 2.5: 1.38, 2.75: 1.88, 3.0: 1.88},
    '#10': {1.5: .62, 1.75: .62, 2.0: 1.12, 2.25: 1.12, 2.5: 1.62, 2.75: 1.62, 3.0: 2.12, 3.5: 2.62, 4.0: 3.12},
    '1/4': {1.75: .75, 2.0: .75, 2.25: 1.25, 2.5: 1.25, 2.75: 1.75, 3.0: 1.75, 3.5: 2.25, 4.0: 2.75},
    '5/16': {2.0: .88, 2.25: .88, 2.5: 1.38, 2.75: 1.38, 3.0: 1.88, 3.5: 2.38, 4.0: 2.88},
    '3/8': {2.25: 1.00, 2.5: 1.00, 2.75: 1.50, 3.0: 1.50, 3.5: 2.00, 4.0: 2.50},
    '1/2': {2.5: 1.00, 2.75: 1.00, 3.0: 1.00, 3.5: 1.75, 4.0: 2.50},
}
# ASME B18.2.1 hex cap screw minimum thread length LT = 2D + 1/4 (lengths up to 6"); shorter screws are
# threaded as close to the head as practical, modeled here as threaded to the head when L <= LT.
LT_HEX = {'1/4': 0.75, '5/16': 0.875, '3/8': 1.0, '1/2': 1.25}


def _keep(series, rng):
    lo, hi = rng
    return [x for x in series if lo <= x <= hi]


def mm_sizes(rows, ranges, threads=None, alloy=None):
    """rows: [(size, dims)]. alloy: {size: grade} for sizes sold in alloy steel black oxide."""
    out = []
    for size, dims in rows:
        row = dict(size=size, d=float(size[1:]), pitch=PITCH[size], dims=dims,
                   lengths=_keep(MM_LENGTHS, ranges[size]))
        if threads and size in threads:
            b, first = threads[size]
            row['thread'] = {'b': b, 'partial_from': first}
        if alloy and size in alloy:
            row['grade'] = {'ALLOY-BO': alloy[size]}
        out.append(row)
    return out


def in_sizes(rows, ranges=IN_RANGE, lg=None, lt=None, alloy=None, unf=()):
    """unf: nominal sizes that also get a UNF row (same head data; the maker's document lists UNRF)."""
    out = []
    for series in ('UNC', 'UNF'):
        for size, dims in rows:
            if series == 'UNF' and size not in unf:
                continue
            d, tpi = UNC[size]
            key = size
            if series == 'UNF':
                tpi = UNF[size]
                key = '%s-%d' % (size, tpi)
            row = dict(size=key, nominal=size, series=series, d=d, tpi=tpi, dims=dims,
                       lengths=_keep(IN_LENGTHS, ranges[size]))
            if lg and size in lg:
                row['thread'] = {'lg': {('%g' % k): v for k, v in sorted(lg[size].items())}}
            if lt and size in lt:
                row['thread'] = {'b': lt[size], 'partial_from_over': lt[size]}
            if alloy and size in alloy:
                row['grade'] = {'ALLOY-BO': alloy[size]}
            out.append(row)
    return out


def cap(dk, k, s, t, **extra):
    d = {'dk': dk, 'k': k, 's': s, 't': t}
    d.update(extra)
    return d


def every(sizes, grade):
    return {s: grade for s in sizes}


M_ALL = ['M2', 'M2.5', 'M3', 'M4', 'M5', 'M6', 'M8', 'M10', 'M12', 'M16', 'M20']
I_ALL = ['#2', '#4', '#6', '#8', '#10', '1/4', '5/16', '3/8', '1/2']
STD = ['SS', 'SS-BO']
ALL = ['SS', 'SS-BO', 'ALLOY-BO']

FAMILIES = [
    dict(code='SSH-M', name='Socket head screw', standard='ISO 4762', system='metric', head='cap', drive='hex',
         finishes=ALL, source=SRC['iso4762'],
         sources={'dims': ['iso4762', 'hk_m_shcs'], 'lengths': ['iso4762'], 'thread': ['iso4762'],
                  'alloy': ['hk_m_shcs']},
         sizes=mm_sizes([
             ('M2', cap(3.8, 2.0, 1.5, 1.0)), ('M2.5', cap(4.5, 2.5, 2.0, 1.1)), ('M3', cap(5.5, 3.0, 2.5, 1.3)),
             ('M4', cap(7.0, 4.0, 3.0, 2.0)), ('M5', cap(8.5, 5.0, 4.0, 2.5)), ('M6', cap(10.0, 6.0, 5.0, 3.0)),
             ('M8', cap(13.0, 8.0, 6.0, 4.0)), ('M10', cap(16.0, 10.0, 8.0, 5.0)), ('M12', cap(18.0, 12.0, 10.0, 6.0)),
             ('M16', cap(24.0, 16.0, 14.0, 8.0))], R_4762, T_4762, every(M_ALL, 'class 12.9'))),
    dict(code='SBH-M', name='Button head hex-drive screw', standard='ISO 7380-1', system='metric', head='button',
         drive='hex', finishes=ALL, source=SRC['iso7380'],
         sources={'dims': ['iso7380', 'iso7380_22', 'hk_m_bhcs'], 'lengths': ['iso7380'], 'thread': ['iso7380'],
                  'alloy': ['hk_m_bhcs', 'av_m_bhcs16']},
         sizes=mm_sizes([
             ('M3', cap(5.7, 1.65, 2.0, 1.04, rf=3.5)), ('M4', cap(7.6, 2.2, 2.5, 1.3, rf=4.4)),
             ('M5', cap(9.5, 2.75, 3.0, 1.56, rf=5.5)), ('M6', cap(10.5, 3.3, 4.0, 2.08, rf=5.9)),
             ('M8', cap(14.0, 4.4, 5.0, 2.6, rf=7.7)), ('M10', cap(17.5, 5.5, 6.0, 3.12, rf=9.5)),
             ('M12', cap(21.0, 6.6, 8.0, 4.16, rf=10.85)), ('M16', cap(28.0, 8.8, 10.0, 5.2, rf=14.9))],
             R_7380, T_7380, dict(every(['M3', 'M4', 'M5', 'M6', 'M8', 'M10', 'M12'], 'class 12.9'),
                                  M16='class 10.9'))),
    dict(code='SFH-M', name='Hex-drive flat head screw, 90 deg', standard='ISO 10642', system='metric', head='flat',
         drive='hex', angle=90.0, finishes=ALL, source=SRC['iso10642'],
         sources={'dims': ['iso10642', 'hk_m_fhcs'], 'lengths': ['iso10642'], 'thread': ['iso10642'],
                  'alloy': ['hk_m_fhcs']},
         sizes=mm_sizes([
             ('M3', cap(6.72, 1.86, 2.0, 1.1)), ('M4', cap(8.96, 2.48, 2.5, 1.5)), ('M5', cap(11.2, 3.1, 3.0, 1.9)),
             ('M6', cap(13.44, 3.72, 4.0, 2.2)), ('M8', cap(17.92, 4.96, 5.0, 3.0)), ('M10', cap(22.4, 6.2, 6.0, 3.6)),
             ('M12', cap(26.88, 7.44, 8.0, 4.3)), ('M16', cap(33.6, 8.8, 10.0, 4.8)), ('M20', cap(40.32, 10.16, 12.0, 5.6))],
             R_10642, T_10642, every(['M3', 'M4', 'M5', 'M6', 'M8', 'M10', 'M12', 'M16'], 'class 12.9'))),
    dict(code='SLH-M', name='Low-profile socket head screw', standard='DIN 7984', system='metric', head='cap', drive='hex',
         finishes=ALL, source=SRC['bbi_7984'],
         sources={'dims': ['bbi_7984', 'fn_7984'], 'lengths': [], 'thread': [], 'alloy': ['bbi_7984']},
         sizes=mm_sizes([
             ('M3', cap(5.5, 2.0, 2.0, 1.38)), ('M4', cap(7.0, 2.8, 2.5, 2.18)), ('M5', cap(8.5, 3.5, 3.0, 2.58)),
             ('M6', cap(10.0, 4.0, 4.0, 2.88)), ('M8', cap(13.0, 5.0, 5.0, 3.65)), ('M10', cap(16.0, 6.0, 7.0, 4.35)),
             ('M12', cap(18.0, 7.0, 8.0, 4.85)), ('M16', cap(24.0, 9.0, 12.0, 5.35))],
             R_MM_UNVERIFIED, None, every(M_ALL, 'class 10.9'))),
    dict(code='SHH-M', name='Hex head screw, fully threaded', standard='ISO 4017', system='metric', head='hex',
         drive='none', finishes=STD, source=SRC['iso4017'],
         sources={'dims': ['iso4017'], 'lengths': [], 'thread': ['iso4017'], 'alloy': []},
         sizes=mm_sizes([
             ('M3', {'s': 5.5, 'k': 2.0}), ('M4', {'s': 7.0, 'k': 2.8}), ('M5', {'s': 8.0, 'k': 3.5}),
             ('M6', {'s': 10.0, 'k': 4.0}), ('M8', {'s': 13.0, 'k': 5.3}), ('M10', {'s': 16.0, 'k': 6.4}),
             ('M12', {'s': 18.0, 'k': 7.5}), ('M16', {'s': 24.0, 'k': 10.0})], R_MM_UNVERIFIED)),
    dict(code='SSF-M', name='Flat-tip set screw', standard='ISO 4026', system='metric', head='set', point='flat',
         drive='hex', finishes=ALL, source=SRC['iso4026'],
         sources={'dims': ['iso4026'], 'lengths': ['iso4026'], 'thread': ['iso4026'],
                  'alloy': ['av_m_set', 'av_m_set2']},
         sizes=mm_sizes([
             ('M3', {'s': 1.5, 'dp': 2.0, 't': 2.0, 't_short': 1.2, 'short_max': 3}),
             ('M4', {'s': 2.0, 'dp': 2.5, 't': 2.5, 't_short': 1.5, 'short_max': 4}),
             ('M5', {'s': 2.5, 'dp': 3.5, 't': 3.0, 't_short': 2.0, 'short_max': 5}),
             ('M6', {'s': 3.0, 'dp': 4.0, 't': 3.5, 't_short': 2.0, 'short_max': 6}),
             ('M8', {'s': 4.0, 'dp': 5.5, 't': 5.0, 't_short': 3.0, 'short_max': 8}),
             ('M10', {'s': 5.0, 'dp': 7.0, 't': 6.0, 't_short': 4.0, 'short_max': 10}),
             ('M12', {'s': 6.0, 'dp': 8.5, 't': 8.0, 't_short': 4.8, 'short_max': 12})],
             R_4026, None, every(M_ALL, 'class 45H'))),
    dict(code='SSC-M', name='Cup-tip set screw', standard='ISO 4029', system='metric', head='set', point='cup',
         drive='hex', finishes=ALL, source=SRC['iso4029'],
         sources={'dims': ['iso4029', 'hk_tech'], 'lengths': ['iso4029'], 'thread': ['iso4029'], 'alloy': ['hk_tech']},
         # dp = cup diameter dz max (ISO 4029 Table 1, same as Holo-Krome Table 45 C max); socket s and t min as ISO 4029
         sizes=mm_sizes([
             ('M3', {'s': 1.5, 'dp': 1.4, 't': 2.0, 't_short': 1.2, 'short_max': 3}),
             ('M4', {'s': 2.0, 'dp': 2.0, 't': 2.5, 't_short': 1.5, 'short_max': 4}),
             ('M5', {'s': 2.5, 'dp': 2.5, 't': 3.0, 't_short': 2.0, 'short_max': 5}),
             ('M6', {'s': 3.0, 'dp': 3.0, 't': 3.5, 't_short': 2.0, 'short_max': 6}),
             ('M8', {'s': 4.0, 'dp': 5.0, 't': 5.0, 't_short': 3.0, 'short_max': 8}),
             ('M10', {'s': 5.0, 'dp': 6.0, 't': 6.0, 'short_max': 10, 't_short': 4.0}),
             ('M12', {'s': 6.0, 'dp': 8.0, 't': 8.0, 't_short': 4.8, 'short_max': 12})],
             R_4026, None, every(M_ALL, 'class 45H'))),
    dict(code='SPH-M', name='Pan head Phillips screw', standard='ISO 7045', system='metric', head='pan',
         drive='phillips', finishes=STD, source=SRC['iso7045'],
         sources={'dims': ['iso7045'], 'lengths': ['iso7045'], 'thread': ['iso7045'], 'alloy': []},
         sizes=mm_sizes([
             ('M2', {'dk': 4.0, 'k': 1.6, 'rf': 3.2, 'recess': 0, 'm': 1.9, 'pen': 1.05}),
             ('M2.5', {'dk': 5.0, 'k': 2.1, 'rf': 4.0, 'recess': 1, 'm': 2.7, 'pen': 1.35}),
             ('M3', {'dk': 5.6, 'k': 2.4, 'rf': 5.0, 'recess': 1, 'm': 3.0, 'pen': 1.6}),
             ('M4', {'dk': 8.0, 'k': 3.1, 'rf': 6.5, 'recess': 2, 'm': 4.4, 'pen': 2.15}),
             ('M5', {'dk': 9.5, 'k': 3.7, 'rf': 8.0, 'recess': 2, 'm': 4.9, 'pen': 2.65}),
             ('M6', {'dk': 12.0, 'k': 4.6, 'rf': 10.0, 'recess': 3, 'm': 6.9, 'pen': 3.35}),
             ('M8', {'dk': 16.0, 'k': 6.0, 'rf': 13.0, 'recess': 4, 'm': 9.0, 'pen': 4.3}),
             ('M10', {'dk': 20.0, 'k': 7.5, 'rf': 16.0, 'recess': 4, 'm': 10.1, 'pen': 5.5})],
             R_7045, T_7045)),
    dict(code='SCH-M', name='Cheese head slotted screw', standard='ISO 1207', system='metric', head='cheese',
         drive='slot', finishes=STD, source=SRC['iso1207'],
         sources={'dims': ['iso1207'], 'lengths': ['iso1207'], 'thread': ['iso1207'], 'alloy': []},
         sizes=mm_sizes([
             ('M2', {'dk': 3.8, 'k': 1.4, 'n': 0.5, 't': 0.6}), ('M2.5', {'dk': 4.5, 'k': 1.8, 'n': 0.6, 't': 0.7}),
             ('M3', {'dk': 5.5, 'k': 2.0, 'n': 0.8, 't': 0.85}), ('M4', {'dk': 7.0, 'k': 2.6, 'n': 1.2, 't': 1.1}),
             ('M5', {'dk': 8.5, 'k': 3.3, 'n': 1.2, 't': 1.3}), ('M6', {'dk': 10.0, 'k': 3.9, 'n': 1.6, 't': 1.6}),
             ('M8', {'dk': 13.0, 'k': 5.0, 'n': 2.0, 't': 2.0}), ('M10', {'dk': 16.0, 'k': 6.0, 'n': 2.5, 't': 2.4})],
             R_1207, T_1207)),
    dict(code='SSH-I', name='Socket head screw', standard='ASME B18.3', system='inch', head='cap', drive='hex',
         finishes=ALL, source=SRC['hk_shcs'],
         sources={'dims': ['hk_shcs'], 'lengths': [], 'thread': ['hk_tech'], 'alloy': ['hk_shcs']},
         sizes=in_sizes([
             ('#2', cap(0.140, 0.086, 0.078, 0.038)), ('#4', cap(0.183, 0.112, 0.094, 0.051)),
             ('#6', cap(0.226, 0.138, 0.109, 0.064)), ('#8', cap(0.270, 0.164, 0.141, 0.077)),
             ('#10', cap(0.312, 0.190, 0.156, 0.090)), ('1/4', cap(0.375, 0.250, 0.188, 0.120)),
             ('5/16', cap(0.469, 0.312, 0.250, 0.151)), ('3/8', cap(0.562, 0.375, 0.312, 0.182)),
             ('1/2', cap(0.750, 0.500, 0.375, 0.245))], lg=LG_SHCS, alloy=every(I_ALL, 'ASTM A574'), unf=I_ALL)),
    dict(code='SBH-I', name='Button head hex-drive screw', standard='ASME B18.3', system='inch', head='button',
         drive='hex', finishes=ALL, source=SRC['hk_bhcs'],
         sources={'dims': ['hk_bhcs'], 'lengths': ['hk_bhcs'], 'thread': ['hk_tech'], 'alloy': ['hk_bhcs']},
         sizes=in_sizes([
             ('#2', cap(0.164, 0.046, 0.050, 0.028, side=0.010)), ('#4', cap(0.213, 0.059, 0.062, 0.035, side=0.015)),
             ('#6', cap(0.262, 0.073, 0.078, 0.044, side=0.015)), ('#8', cap(0.312, 0.087, 0.094, 0.052, side=0.015)),
             ('#10', cap(0.361, 0.101, 0.125, 0.070, side=0.020)), ('1/4', cap(0.437, 0.132, 0.156, 0.087, side=0.031)),
             ('5/16', cap(0.547, 0.166, 0.188, 0.105, side=0.031)), ('3/8', cap(0.656, 0.199, 0.219, 0.122, side=0.031)),
             ('1/2', cap(0.875, 0.265, 0.312, 0.175, side=0.046))], ranges=R_BHCS_IN,
             alloy=every(I_ALL, 'ASTM F835'), unf=I_ALL)),
    dict(code='SFH-I', name='Hex-drive flat head screw, 82 deg', standard='ASME B18.3', system='inch', head='flat',
         drive='hex', angle=82.0, finishes=ALL, source=SRC['hk_fhcs'],
         sources={'dims': ['hk_fhcs', 'b183_fhcs'], 'lengths': [], 'thread': ['hk_tech'], 'alloy': ['hk_fhcs']},
         sizes=in_sizes([
             ('#2', cap(0.197, 0.064, 0.050, 0.038)), ('#4', cap(0.255, 0.083, 0.062, 0.055)),
             ('#6', cap(0.307, 0.097, 0.078, 0.066)), ('#8', cap(0.359, 0.112, 0.094, 0.076)),
             ('#10', cap(0.411, 0.127, 0.125, 0.087)), ('1/4', cap(0.531, 0.161, 0.156, 0.111)),
             ('5/16', cap(0.656, 0.198, 0.188, 0.135)), ('3/8', cap(0.781, 0.234, 0.219, 0.159)),
             ('1/2', cap(0.938, 0.251, 0.312, 0.172))], lg=LG_FHCS,
             alloy=every(I_ALL[1:], 'ASTM F835'), unf=I_ALL)),
    dict(code='SLH-I', name='Low-profile socket head screw', standard='ASME B18.3', system='inch', head='cap',
         drive='hex', finishes=ALL, source=SRC['hk_lhcs'],
         sources={'dims': ['hk_lhcs', 'b183_lhcs'], 'lengths': [], 'thread': [], 'alloy': ['hk_lhcs']},
         sizes=in_sizes([
             ('#4', cap(0.183, 0.059, 0.050, 0.038)), ('#6', cap(0.226, 0.072, 0.062, 0.050)),
             ('#8', cap(0.270, 0.085, 0.078, 0.060)), ('#10', cap(0.312, 0.098, 0.094, 0.072)),
             ('1/4', cap(0.375, 0.127, 0.125, 0.094)), ('5/16', cap(0.437, 0.158, 0.156, 0.110)),
             ('3/8', cap(0.562, 0.192, 0.188, 0.115)), ('1/2', cap(0.750, 0.254, 0.250, 0.151))],
             alloy=every(I_ALL[3:], 'ASTM A574'), unf=I_ALL[3:])),
    dict(code='SHH-I', name='Hex head screw', standard='ASME B18.2.1', system='inch', head='hex', drive='none',
         finishes=ALL, source=SRC['b1821_hex'],
         sources={'dims': ['b1821_hex'], 'lengths': [], 'thread': ['b1821_hex'], 'alloy': ['av_in_hex']},
         sizes=in_sizes([
             ('1/4', {'s': 0.438, 'k': 0.163}), ('5/16', {'s': 0.500, 'k': 0.211}),
             ('3/8', {'s': 0.562, 'k': 0.243}), ('1/2', {'s': 0.750, 'k': 0.323})],
             lt=LT_HEX, alloy=every(I_ALL, 'SAE J429 Grade 8'))),
    dict(code='SSF-I', name='Flat-tip set screw', standard='ASME B18.3', system='inch', head='set', point='flat',
         drive='hex', finishes=ALL, source=SRC['hk_tech'],
         sources={'dims': ['hk_tech'], 'lengths': ['hk_tech'], 'thread': [], 'alloy': ['av_in_set']},
         sizes=in_sizes([
             ('#2', {'s': 0.035, 'dp': 0.047, 't': 0.060, 't_by_length': {'0.125': 0.060}}),
             ('#4', {'s': 0.050, 'dp': 0.061, 't': 0.070, 't_by_length': {'0.125': 0.060}}),
             ('#6', {'s': 0.062, 'dp': 0.074, 't': 0.080, 't_by_length': {'0.125': 0.060}}),
             ('#8', {'s': 0.078, 'dp': 0.087, 't': 0.090, 't_by_length': {'0.125': 0.060}}),
             ('#10', {'s': 0.094, 'dp': 0.102, 't': 0.100, 't_by_length': {'0.125': 0.060}}),
             ('1/4', {'s': 0.125, 'dp': 0.132, 't': 0.125, 't_by_length': {'0.1875': 0.090}}),
             ('5/16', {'s': 0.156, 'dp': 0.172, 't': 0.156, 't_by_length': {'0.25': 0.125}}),
             ('3/8', {'s': 0.188, 'dp': 0.212, 't': 0.188, 't_by_length': {'0.25': 0.110, '0.3125': 0.140}}),
             ('1/2', {'s': 0.250, 'dp': 0.291, 't': 0.250})], ranges=R_SET_IN,
             alloy=every(I_ALL, 'ASTM F912'), unf=I_ALL)),
    dict(code='SSC-I', name='Cup-tip set screw', standard='ASME B18.3', system='inch', head='set', point='cup',
         drive='hex', finishes=ALL, source=SRC['hk_tech'],
         sources={'dims': ['hk_tech'], 'lengths': ['hk_tech'], 'thread': [], 'alloy': ['hk_tech']},
         # dp = cup point diameter C1 max (Holo-Krome Table 13); key depths as flat point (Table 14 lists cup and flat together)
         sizes=in_sizes([
             ('#2', {'s': 0.035, 'dp': 0.043, 't': 0.060, 't_by_length': {'0.125': 0.060}}),
             ('#4', {'s': 0.050, 'dp': 0.056, 't': 0.070, 't_by_length': {'0.125': 0.060}}),
             ('#6', {'s': 0.062, 'dp': 0.069, 't': 0.080, 't_by_length': {'0.125': 0.060}}),
             ('#8', {'s': 0.078, 'dp': 0.082, 't': 0.090, 't_by_length': {'0.125': 0.060}}),
             ('#10', {'s': 0.094, 'dp': 0.095, 't': 0.100, 't_by_length': {'0.125': 0.060}}),
             ('1/4', {'s': 0.125, 'dp': 0.125, 't': 0.125, 't_by_length': {'0.1875': 0.090}}),
             ('5/16', {'s': 0.156, 'dp': 0.156, 't': 0.156, 't_by_length': {'0.25': 0.125}}),
             ('3/8', {'s': 0.188, 'dp': 0.187, 't': 0.188, 't_by_length': {'0.25': 0.110, '0.3125': 0.140}}),
             ('1/2', {'s': 0.250, 'dp': 0.250, 't': 0.250})], ranges=R_SET_IN,
             alloy=every(I_ALL, 'ASTM F912'), unf=I_ALL)),

]
# Set screws below Holo-Krome Table 13 column B that Table 14 does not list are dropped (no key depth source).
_SET_B = {'#2': 0.125, '#4': 0.1875, '#6': 0.1875, '#8': 0.1875, '#10': 0.1875, '1/4': 0.25, '5/16': 0.3125,
          '3/8': 0.375, '1/2': 0.5}
for _fam in FAMILIES:
    if _fam['code'] in ('SSF-I', 'SSC-I'):
        for _row in _fam['sizes']:
            short = {float(k) for k in _row['dims'].get('t_by_length', {})}
            _row['lengths'] = [L for L in _row['lengths'] if L >= _SET_B[_row['nominal']] - 1e-9 or L in short]


# McMaster-Carr category each family is named after (checked 2026-11-16 on mcmaster.com category pages).
# Codes: screws are S + head letter + H (Daniel's SSH/SBH/SFH/SLH pattern); set screws are SS + tip letter.
MCM = 'https://www.mcmaster.com/products/'
MCMASTER = {
    'SSH': ('Socket Head Screws', MCM + 'socket-head-screws/'),
    'SBH': ('Button Head Hex-Drive Screws', MCM + 'rounded-head-screws/'),
    'SFH': ('Hex-Drive Flat Head Screws', MCM + 'flat-head-screws/'),
    'SLH': ('Low-Profile Socket Head Screws', MCM + 'socket-head-screws/'),
    'SHH': ('Hex Head Screws', MCM + 'hex-head-screws/'),
    'SSF': ('Flat-Tip Set Screws', MCM + 'set-screws/'),
    'SSC': ('Cup-Tip Set Screws', MCM + 'set-screws/'),
    'SPH': ('Pan Head Phillips Screws', MCM + 'rounded-head-screws/'),
    'SCH': ('Cheese Head Slotted Screws', MCM + 'rounded-head-screws/'),
}
for _fam in FAMILIES:
    _fam['mcmaster'], _fam['mcmaster_url'] = MCMASTER[_fam['code'].rsplit('-', 1)[0]]

# Types held back from the dialog (the add-in only reads 'families'). Empty: Daniel approves new types
# automatically as long as they are checked against McMaster-Carr or Fastenal data.
PENDING_APPROVAL = set()
PENDING = [f for f in FAMILIES if f['code'] in PENDING_APPROVAL]
FAMILIES = [f for f in FAMILIES if f['code'] not in PENDING_APPROVAL]


def build():
    return {
        'schema': 2,
        'note': 'Generated by tools/build_catalog.py. Edit that file, not this one.',
        'sources': SRC,
        'finishes': FINISHES,
        'alloy_materials': ALLOY_MATERIAL,
        'families': FAMILIES,
        'pending_approval': PENDING,
    }


def path():
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'SRFastener', 'data', 'catalog.json')


def render():
    return json.dumps(build(), indent=1, sort_keys=False) + '\n'


def sources_md():
    """docs/SOURCES.md: one row per family with the source keys behind each value block."""
    out = ['# Dimension sources', '',
           'Generated by `tools/build_catalog.py` from the catalog. Every value in a family comes from the sources',
           'listed for it; `tests/test_sources.py` spot-checks rows against them. Blank means not sourced (TBD).', '',
           '| Code | Type (McMaster name) | Standard | Dimensions | Lengths | Thread length | Alloy black oxide |',
           '|---|---|---|---|---|---|---|']
    for fam in FAMILIES + PENDING:
        src = fam['sources']
        name = fam['name'] + (' (pending approval, not offered)' if fam in PENDING else '')
        out.append('| %s | %s | %s | %s |' % (fam['code'], name, fam['standard'], ' | '.join(
            ', '.join(src.get(k, [])) for k in ('dims', 'lengths', 'thread', 'alloy'))))
    out += ['', '## Source keys', '', '| Key | Source |', '|---|---|']
    out += ['| %s | %s |' % (k, v) for k, v in SRC.items()]
    out += ['', 'Lengths with no length source use the preferred series trimmed to an unverified range (TBD).',
            'Vendor part numbers and stocked lengths are TBD.', '']
    return '\n'.join(out)


if __name__ == '__main__':
    with open(path(), 'w', encoding='utf-8', newline='\n') as f:
        f.write(render())
    doc = os.path.join(os.path.dirname(os.path.dirname(path())), '..', 'docs', 'SOURCES.md')
    with open(os.path.normpath(doc), 'w', encoding='utf-8', newline='\n') as f:
        f.write(sources_md())
    print('wrote', path(), 'and docs/SOURCES.md')
