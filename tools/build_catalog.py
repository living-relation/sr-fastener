"""Writes SRFastener/data/catalog.json from the tables below.

Every number here comes from the cited page (checked 2026-11-16). Values a page did not
give are left out, and the README lists them as TBD. Do not add a size or a dimension
without a source.

Run: python tools/build_catalog.py   (the check script fails if the JSON is out of date)
"""
import json
import os

SRC = {
    'iso4762': 'https://www.fasteners.eu/standards/ISO/4762/ (ISO 4762 table: dk max, k max, s nominal, t min)',
    'iso7380': 'https://www.fasteners.eu/standards/ISO/7380/ (ISO 7380-1 table: dk max, k max, s nominal, t min)',
    'iso10642': 'https://www.engineersedge.com/hardware/bs_en_iso_10642_14583.htm (BS EN ISO 10642: dk theoretical max, k max, s nominal, t min)',
    'din7984': 'https://www.fasteners.eu/standards/DIN/7984/ (DIN 7984 table: dk max, k max, s nominal, t min)',
    'iso4017': 'https://www.fasteners.eu/standards/ISO/4017/ (ISO 4017 table: s nominal max, k nominal)',
    'iso4026': 'https://www.fasteners.eu/standards/ISO/4026/ (ISO 4026 / DIN 913 table: s nominal, dp max, t min first row)',
    'b183_shcs': 'https://patriotbolt.com/technical/hexagon-socket-head-cap-screws/ (ASME B18.3: A max, H max, J nominal, T min)',
    'b183_bhcs': 'https://patriotbolt.com/technical/hexagon-socket-button-head-cap-screws/ (ASME B18.3: A max, H max, J nominal, T min)',
    'b183_fhcs': 'https://patriotbolt.com/technical/hexagon-socket-flat-countersunk-head-cap-screws/ (ASME B18.3: A max sharp, H ref, J nominal, T min; 82 deg)',
    'b183_lhcs': 'https://patriotbolt.com/technical/low-head-hexagon-socket-head-cap-screws/ (ASME B18.3: A max, H max, J nominal, T min)',
    'b1821_hex': 'https://patriotbolt.com/technical/hex-cap-screws/ (ASME B18.2.1 hex cap screws: F basic, H basic)',
}

# Preferred length series. Per-size stock at a given maker is NOT verified (README says TBD).
MM_LENGTHS = [3, 4, 5, 6, 8, 10, 12, 14, 16, 18, 20, 22, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 80, 90, 100]
IN_LENGTHS = [0.125, 0.1875, 0.25, 0.3125, 0.375, 0.4375, 0.5, 0.625, 0.75, 0.875, 1.0, 1.25, 1.5,
              1.75, 2.0, 2.25, 2.5, 2.75, 3.0, 3.5, 4.0]

# Finish codes follow Daniel's BOM part-number rule (ends with 18-8 SS or 18-8 SS-BO).
FINISHES = {
    'SS': {'code': '18-8 SS', 'name': '18-8 stainless steel', 'material': 'Stainless Steel AISI 304',
           'appearance': 'Stainless Steel - Satin'},
    'SS-BO': {'code': '18-8 SS-BO', 'name': '18-8 stainless steel, black oxide',
              'material': 'Stainless Steel AISI 304', 'appearance': 'Coating - Black Oxide'},
}

# Metric coarse pitch per size (ISO 261 coarse, as printed in the ISO 4762 table above).
PITCH = {'M2': 0.4, 'M2.5': 0.45, 'M3': 0.5, 'M4': 0.7, 'M5': 0.8, 'M6': 1.0, 'M8': 1.25,
         'M10': 1.5, 'M12': 1.75, 'M16': 2.0, 'M20': 2.5}
# UNC threads per inch and basic diameter (ASME B18.3 tables above list both).
UNC = {'#2': (0.086, 56), '#4': (0.112, 40), '#6': (0.138, 32), '#8': (0.164, 32), '#10': (0.190, 24),
       '1/4': (0.25, 20), '5/16': (0.3125, 18), '3/8': (0.375, 16), '1/2': (0.5, 13)}

# Length range per size (min, max), used only to trim the preferred series.
MM_RANGE = {'M2': (3, 20), 'M2.5': (3, 25), 'M3': (4, 40), 'M4': (5, 50), 'M5': (6, 60), 'M6': (8, 80),
            'M8': (10, 100), 'M10': (12, 100), 'M12': (16, 100), 'M16': (20, 100), 'M20': (25, 100)}
IN_RANGE = {'#2': (0.125, 0.75), '#4': (0.125, 1.0), '#6': (0.125, 1.5), '#8': (0.25, 2.0),
            '#10': (0.25, 2.5), '1/4': (0.25, 3.0), '5/16': (0.375, 3.5), '3/8': (0.375, 4.0),
            '1/2': (0.5, 4.0)}


def mm_sizes(rows, ranges=MM_RANGE):
    out = []
    for size, dims in rows:
        lo, hi = ranges[size]
        out.append(dict(size=size, d=float(size[1:]), pitch=PITCH[size], dims=dims,
                        lengths=[x for x in MM_LENGTHS if lo <= x <= hi]))
    return out


def in_sizes(rows):
    out = []
    for size, dims in rows:
        d, tpi = UNC[size]
        lo, hi = IN_RANGE[size]
        out.append(dict(size=size, d=d, tpi=tpi, dims=dims,
                        lengths=[x for x in IN_LENGTHS if lo <= x <= hi]))
    return out


def cap(dk, k, s, t):
    return {'dk': dk, 'k': k, 's': s, 't': t}


FAMILIES = [
    dict(code='SSH-M', name='Socket head cap screw', standard='ISO 4762', system='metric', head='cap',
         source=SRC['iso4762'], sizes=mm_sizes([
             ('M2', cap(3.8, 2.0, 1.5, 1.0)), ('M2.5', cap(4.5, 2.5, 2.0, 1.1)), ('M3', cap(5.5, 3.0, 2.5, 1.3)),
             ('M4', cap(7.0, 4.0, 3.0, 2.0)), ('M5', cap(8.5, 5.0, 4.0, 2.5)), ('M6', cap(10.0, 6.0, 5.0, 3.0)),
             ('M8', cap(13.0, 8.0, 6.0, 4.0)), ('M10', cap(16.0, 10.0, 8.0, 5.0)), ('M12', cap(18.0, 12.0, 10.0, 6.0)),
             ('M16', cap(24.0, 16.0, 14.0, 8.0))])),
    dict(code='SBH-M', name='Button head socket cap screw', standard='ISO 7380-1', system='metric', head='button',
         source=SRC['iso7380'], sizes=mm_sizes([
             ('M3', cap(5.7, 1.65, 2.0, 1.04)), ('M4', cap(7.6, 2.2, 2.5, 1.3)), ('M5', cap(9.5, 2.75, 3.0, 1.56)),
             ('M6', cap(10.5, 3.3, 4.0, 2.08)), ('M8', cap(14.0, 4.4, 5.0, 2.6)), ('M10', cap(17.5, 5.5, 6.0, 3.12)),
             ('M12', cap(21.0, 6.6, 8.0, 4.16)), ('M16', cap(28.0, 8.8, 10.0, 5.2))])),
    dict(code='SFH-M', name='Flat head socket cap screw, 90 deg', standard='ISO 10642', system='metric', head='flat',
         angle=90.0, source=SRC['iso10642'], sizes=mm_sizes([
             ('M3', cap(6.72, 1.86, 2.0, 1.1)), ('M4', cap(8.96, 2.48, 2.5, 1.5)), ('M5', cap(11.2, 3.1, 3.0, 1.9)),
             ('M6', cap(13.44, 3.72, 4.0, 2.2)), ('M8', cap(17.92, 4.96, 5.0, 3.0)), ('M10', cap(22.4, 6.2, 6.0, 3.6)),
             ('M12', cap(26.88, 7.44, 8.0, 4.3)), ('M16', cap(33.6, 8.8, 10.0, 4.8)), ('M20', cap(40.32, 10.16, 12.0, 5.6))])),
    dict(code='SLH-M', name='Low head socket cap screw', standard='DIN 7984', system='metric', head='cap',
         source=SRC['din7984'], sizes=mm_sizes([
             ('M3', cap(5.5, 2.0, 2.0, 1.38)), ('M4', cap(7.0, 2.8, 2.5, 2.18)), ('M5', cap(8.5, 3.5, 3.0, 2.58)),
             ('M6', cap(10.0, 4.0, 4.0, 2.88)), ('M8', cap(13.0, 5.0, 5.0, 3.62)), ('M10', cap(16.0, 6.0, 7.0, 4.35)),
             ('M12', cap(18.0, 7.0, 8.0, 4.85)), ('M16', cap(24.0, 9.0, 12.0, 5.35))])),
    dict(code='SHX-M', name='Hex head screw, fully threaded', standard='ISO 4017', system='metric', head='hex',
         source=SRC['iso4017'], sizes=mm_sizes([
             ('M3', {'s': 5.5, 'k': 2.0}), ('M4', {'s': 7.0, 'k': 2.8}), ('M5', {'s': 8.0, 'k': 3.5}),
             ('M6', {'s': 10.0, 'k': 4.0}), ('M8', {'s': 13.0, 'k': 5.3}), ('M10', {'s': 16.0, 'k': 6.4}),
             ('M12', {'s': 18.0, 'k': 7.5}), ('M16', {'s': 24.0, 'k': 10.0})])),
    dict(code='SSF-M', name='Socket set screw, flat point', standard='ISO 4026', system='metric', head='set',
         source=SRC['iso4026'], sizes=mm_sizes([
             ('M3', {'s': 1.5, 'dp': 2.0, 't': 1.2}), ('M4', {'s': 2.0, 'dp': 2.5, 't': 1.5}),
             ('M5', {'s': 2.5, 'dp': 3.5, 't': 2.0}), ('M6', {'s': 3.0, 'dp': 4.0, 't': 2.0}),
             ('M8', {'s': 4.0, 'dp': 5.5, 't': 3.0}), ('M10', {'s': 5.0, 'dp': 7.0, 't': 4.0}),
             ('M12', {'s': 6.0, 'dp': 8.5, 't': 4.8})],
             ranges={'M3': (3, 20), 'M4': (4, 20), 'M5': (5, 25), 'M6': (6, 35), 'M8': (8, 40),
                     'M10': (10, 40), 'M12': (16, 40)})),
    dict(code='SSH-I', name='Socket head cap screw', standard='ASME B18.3', system='inch', head='cap',
         source=SRC['b183_shcs'], sizes=in_sizes([
             ('#2', cap(0.140, 0.086, 0.078, 0.038)), ('#4', cap(0.183, 0.112, 0.094, 0.051)),
             ('#6', cap(0.226, 0.138, 0.109, 0.064)), ('#8', cap(0.270, 0.164, 0.141, 0.077)),
             ('#10', cap(0.312, 0.190, 0.156, 0.090)), ('1/4', cap(0.375, 0.250, 0.188, 0.120)),
             ('5/16', cap(0.469, 0.312, 0.250, 0.151)), ('3/8', cap(0.562, 0.375, 0.312, 0.182)),
             ('1/2', cap(0.750, 0.500, 0.375, 0.245))])),
    dict(code='SBH-I', name='Button head socket cap screw', standard='ASME B18.3', system='inch', head='button',
         source=SRC['b183_bhcs'], sizes=in_sizes([
             ('#2', cap(0.164, 0.046, 0.050, 0.028)), ('#4', cap(0.213, 0.059, 0.062, 0.035)),
             ('#6', cap(0.262, 0.073, 0.078, 0.044)), ('#8', cap(0.312, 0.087, 0.094, 0.052)),
             ('#10', cap(0.361, 0.101, 0.125, 0.070)), ('1/4', cap(0.437, 0.132, 0.156, 0.087)),
             ('5/16', cap(0.547, 0.166, 0.188, 0.105)), ('3/8', cap(0.656, 0.199, 0.219, 0.122)),
             ('1/2', cap(0.875, 0.265, 0.312, 0.175))])),
    dict(code='SFH-I', name='Flat head socket cap screw, 82 deg', standard='ASME B18.3', system='inch', head='flat',
         angle=82.0, source=SRC['b183_fhcs'], sizes=in_sizes([
             ('#2', cap(0.197, 0.064, 0.050, 0.038)), ('#4', cap(0.255, 0.083, 0.062, 0.055)),
             ('#6', cap(0.307, 0.097, 0.078, 0.066)), ('#8', cap(0.359, 0.112, 0.094, 0.076)),
             ('#10', cap(0.411, 0.127, 0.125, 0.087)), ('1/4', cap(0.531, 0.161, 0.156, 0.111)),
             ('5/16', cap(0.656, 0.198, 0.188, 0.135)), ('3/8', cap(0.781, 0.234, 0.219, 0.159)),
             ('1/2', cap(0.938, 0.251, 0.312, 0.172))])),
    dict(code='SLH-I', name='Low head socket cap screw', standard='ASME B18.3', system='inch', head='cap',
         source=SRC['b183_lhcs'], sizes=in_sizes([
             ('#4', cap(0.183, 0.059, 0.050, 0.038)), ('#6', cap(0.226, 0.072, 0.062, 0.050)),
             ('#8', cap(0.270, 0.085, 0.078, 0.060)), ('#10', cap(0.312, 0.098, 0.094, 0.072)),
             ('1/4', cap(0.375, 0.127, 0.125, 0.094)), ('5/16', cap(0.437, 0.158, 0.156, 0.110)),
             ('3/8', cap(0.562, 0.192, 0.188, 0.115)), ('1/2', cap(0.750, 0.254, 0.250, 0.151))])),
    dict(code='SHX-I', name='Hex head cap screw', standard='ASME B18.2.1', system='inch', head='hex',
         source=SRC['b1821_hex'], sizes=in_sizes([
             ('1/4', {'s': 0.4375, 'k': 0.15625}), ('5/16', {'s': 0.5, 'k': 0.203125}),
             ('3/8', {'s': 0.5625, 'k': 0.234375}), ('1/2', {'s': 0.75, 'k': 0.3125})])),
]


def build():
    return {
        'schema': 1,
        'note': 'Generated by tools/build_catalog.py. Edit that file, not this one.',
        'finishes': FINISHES,
        'families': FAMILIES,
    }


def path():
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'SRFastener', 'data', 'catalog.json')


def render():
    return json.dumps(build(), indent=1, sort_keys=False) + '\n'


if __name__ == '__main__':
    with open(path(), 'w', encoding='utf-8', newline='\n') as f:
        f.write(render())
    print('wrote', path())
