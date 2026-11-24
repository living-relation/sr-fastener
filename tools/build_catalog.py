import math
"""Writes SRFastener/data/catalog.json from the tables below.

Every number here comes from the cited source (checked 2026-11-16). Each family lists the
sources for its tables in `sources`, and each value block names the source key it came from.
Values a source did not give are left out, and docs/SOURCES.md lists them as TBD.
Do not add a size, a dimension or a length without a source.

Run: python tools/build_catalog.py   (the check script fails if the JSON is out of date)
"""
import json
import os
import sys

HK = 'https://www.holo-krome.com/uploads/7/2/7/5/72754089/'
ITEH = 'https://cdn.standards.iteh.ai/samples/'
SRC = {
    # Standards (official ISO preview pages, which carry the full dimension tables)
    'iso4762': ITEH + '34460/06335046afaf46fb8e84d91a3eda001d/ISO-4762-2004.pdf (ISO 4762:2004 Table 1: dk, k, s, t, b, lengths, ls/lg)',
    'iso7380': ITEH + '53671/84df01c5fcce4a91896ac3b0c55ca128/ISO-7380-1-2011.pdf (ISO 7380-1:2011 Table 1: dk, k, rf, s, t, b, lengths, ls/lg)',
    'iso7380_22': ITEH + '78699/a175805085534f98983d6c8aa583a5b0/ISO-7380-1-2022.pdf (ISO 7380-1:2022 Table 1: same dk, k, rf, s; t min. The preview ends before Table 2.)',
    'wasi_7380': 'https://www.wasishop.de/pdf_datenblatt/iso7380_en.pdf (WASI ISO 7380-1 datasheet, PDF dated 2020-12-14: length grid. M3 lengths 4 and 5 sit left of the step. Length 4 is 3.80 to 4.20. Head numbers match ISO 7380-1 Table 1.)',
    'iso10642': ITEH + '34454/32dec7e84d974361b85f744935ab2175/ISO-10642-2004.pdf (ISO 10642:2004 Table 1: dk theor. max, k, s, t, b, lengths, ls/lg)',
    'aspen_10642': 'https://www.aspenfasteners.com/m3-0-5-x-5mm-din-7991-iso-10642-metric-flat-head-socket-cap-screws-full-thread-a2-stainless-steel/ (Aspen ME126-305X5: M3 x 5 ISO 10642 / DIN 7991, full thread, length 5 mm overall)',
    'iso4017': ITEH + '72585/1179998ddd594550a909d6e13c416f3e/ISO-4017-2022.pdf (ISO 4017:2022 Table 1: s max, k nom)',
    'iso4026': ITEH + '36431/f53ced64ab1946679bd80f0a0e6cac63/ISO-4026-2003.pdf (ISO 4026:2003 Table 1: s, dp max, t min short/long, lengths)',
    'iso4029': ITEH + '36433/631453640d214e7682ed5a23ddee05b5/ISO-4029-2003.pdf (ISO 4029:2003 Table 1: dz, s, t min short/long, lengths)',
    'iso7045': ITEH + '57372/fafe91d8504049fc8953281401736c79/ISO-7045-2011.pdf (ISO 7045:2011 Table 1: dk, k, rf, recess H no., m, penetration, b, lengths)',
    'pan_m3_35': 'https://3fparts.com/productTechnical/generate/pdf/1662 (3FParts sheet 1662: M3 x 35 mm Phillips pan head, DIN 7985, A2-70, length 35 mm, fully threaded. Their head is 6 mm by 2.52 mm. This family keeps the ISO 7045 head.)',
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
# ALLOY-BO, STL, ZN, GR8, CL10.9 and CL10 are made-up codes: his list has no code for them.
# name: the words in the Material list and the match-materials prompt (Daniel 2026-11-17:
#   'Socket Head Screw, M4 x 0.7, 18-8 Stainless Steel' used name for the description too).
# desc_name: optional short wording used only at the end of the part description. Grade and class finishes
#   use this so descriptions stay short (Daniel 2026-11-19: 'GR-8 Steel', 'CL-10.9 Steel', 'CL-10 Steel').
#   When omitted, the description uses name.
# material: the Fusion material name shown on the part. Daniel: just the material name, no standard or alloy
#   acronym (no 'AISI 304'). The add-in makes a design material with this name, copied from `base` so mass and
#   stiffness stay right. Grade and class stay spelled out ('Grade 8 Steel', 'Class 10.9 Steel', 'Class 10 Steel').
# base: the Fusion Material Library material the physical properties come from.
# match: finishes with the same match key count as the same material when checking a stack (a Class 10 nut is
#   the mating nut for a Class 10.9 screw).
# system: only offered for that unit system (Grade 8 is an inch grade, Class 10.9 and Class 10 are metric).
FINISHES = {
    'SS': {'code': '18-8 SS', 'name': '18-8 Stainless Steel', 'material': 'Stainless Steel',
           'base': 'Stainless Steel AISI 304', 'appearance': 'Stainless Steel - Satin', 'match': 'SS'},
    'SS-BO': {'code': '18-8 SS-BO', 'name': '18-8 Stainless Steel Black Oxide', 'material': 'Stainless Steel Black Oxide',
              'base': 'Stainless Steel AISI 304', 'appearance': 'Coating - Black Oxide', 'match': 'SS-BO'},
    'ALLOY-BO': {'code': 'ALLOY-BO', 'name': 'Alloy Steel Black Oxide', 'material': 'Alloy Steel Black Oxide',
                 'base': 'Steel AISI 4142 400 QT', 'appearance': 'Coating - Black Oxide', 'made_up_code': True,
                 'match': 'ALLOY-BO'},
    'STL': {'code': 'STL', 'name': 'Plain Steel', 'material': 'Plain Steel', 'base': 'Steel',
            'appearance': 'Steel - Satin', 'made_up_code': True, 'match': 'STL'},
    'ZN': {'code': 'ZN', 'name': 'Zinc Plated Steel', 'material': 'Zinc Plated', 'base': 'Steel',
           'appearance': 'Steel - Galvanized (Small)', 'made_up_code': True, 'match': 'ZN'},
    'GR8': {'code': 'GR8', 'name': 'Grade 8 Steel', 'desc_name': 'GR-8 Steel', 'material': 'Grade 8 Steel',
            'base': 'Steel AISI 4340 350A QT', 'appearance': 'Steel - Satin', 'made_up_code': True, 'match': 'GR8',
            'system': 'inch'},
    'CL10.9': {'code': 'CL10.9', 'name': 'Class 10.9 Steel', 'desc_name': 'CL-10.9 Steel',
               'material': 'Class 10.9 Steel', 'base': 'Steel AISI 4340 350A QT', 'appearance': 'Steel - Satin',
               'made_up_code': True, 'match': 'CL10', 'system': 'metric'},
    'CL10': {'code': 'CL10', 'name': 'Class 10 Steel', 'desc_name': 'CL-10 Steel', 'material': 'Class 10 Steel',
             'base': 'Steel', 'appearance': 'Steel - Satin', 'made_up_code': True, 'match': 'CL10',
             'system': 'metric'},
    # PEM press-in finishes. The part number is the PEM designation, so these codes are not
    # appended to it. Names have no alloy number and no standard. The datasheet's "300 series"
    # and "400 series" wording stays in the citation, not in the name.
    'PEM-ZI': {'code': 'PEM-ZI', 'name': 'Zinc Plated Steel', 'material': 'Zinc Plated Steel',
               'base': 'Steel', 'appearance': 'Steel - Galvanized (Small)', 'match': 'PEM-ZI'},
    'PEM-SS': {'code': 'PEM-SS', 'name': 'Stainless Steel', 'material': 'Stainless Steel',
               'base': 'Stainless Steel AISI 304', 'appearance': 'Stainless Steel - Satin', 'match': 'PEM-SS'},
    'PEM-4SS': {'code': 'PEM-4SS', 'name': 'Hardened Stainless Steel', 'material': 'Hardened Stainless Steel',
                'base': 'Stainless Steel AISI 304', 'appearance': 'Stainless Steel - Satin', 'match': 'PEM-4SS'},
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
# M3 starts at 4 mm. ISO 7380-1:2011 Table 1 starts M3 at 6 mm. WASI's length grid (wasi_7380)
# puts 4 mm on M3 and M4 (the step is before M5) and 5 mm on M3 to M5 (the step is before M6).
# The 2022 edition says the shortest lengths changed, but the public preview ends before Table 2,
# so the two short M3 lengths are cited from that datasheet. M4 stays at 8 mm: its 4 mm and 5 mm
# rows were not asked for.
R_7380 = {'M3': (4, 30), 'M4': (8, 40), 'M5': (10, 50), 'M6': (10, 60), 'M8': (12, 80), 'M10': (16, 90),
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
         sources={'dims': ['iso7380', 'iso7380_22', 'hk_m_bhcs'], 'lengths': ['iso7380', 'wasi_7380'],
                  'thread': ['iso7380'],
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
         sources={'dims': ['iso10642', 'hk_m_fhcs'], 'lengths': ['iso10642', 'aspen_10642'],
                  'thread': ['iso10642'],
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
    dict(code='HHB-M', name='Hex head bolt, fully threaded', standard='ISO 4017', system='metric', head='hex',
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
         sources={'dims': ['iso7045'], 'lengths': ['iso7045', 'pan_m3_35'], 'thread': ['iso7045', 'pan_m3_35'], 'alloy': []},
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
    dict(code='HHB-I', name='Hex head bolt', standard='ASME B18.2.1', system='inch', head='hex', drive='none',
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
PT_CODE = {'cone': 'SSN-I', 'dog': 'SSE-I', 'oval': 'SSO-I'}
# Cup and flat point set screws below Holo-Krome Table 13 column B that Table 14 does not list are dropped.
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
    'HHB': ('Hex Head Screws', MCM + 'hex-head-screws/'),
    'SSF': ('Flat-Tip Set Screws', MCM + 'set-screws/'),
    'SSC': ('Cup-Tip Set Screws', MCM + 'set-screws/'),
    'SPH': ('Pan Head Phillips Screws', MCM + 'rounded-head-screws/'),
    'SCH': ('Cheese Head Slotted Screws', MCM + 'rounded-head-screws/'),
}
# ---------- More screws: cone, extended and oval tip set screws, flanged button head, Phillips tapping ----------
# Lengths are the ones McMaster-Carr stocks in 18-8 stainless (checked 2026-11-16), so every offered length is a real
# part. Head and point dimensions come from McMaster where it lists them, the rest from the cited standard or maker.
SRC.update({
    'mcm_cone': MCM + 'set-screws/material~18-8-stainless-steel/stainless-steel-cone-tip-set-screws-2~~/ (McMaster 18-8 cone-tip set screws: lengths, cone angle per length, drive size)',
    'mcm_ext': MCM + 'set-screws/material~18-8-stainless-steel/stainless-steel-extended-tip-set-screws-2~~/ (McMaster 18-8 extended-tip set screws: lengths, tip dia, tip length, drive size)',
    'mcm_oval': MCM + 'set-screws/material~18-8-stainless-steel/stainless-steel-oval-tip-set-screws-2~~/ (McMaster 18-8 oval-tip set screws: lengths, drive size)',
    'mcm_flbtn': MCM + 'rounded-head-screws/material~18-8-stainless-steel/stainless-steel-flanged-button-head-hex-drive-screws~~/ (McMaster 18-8 flanged button head: lengths, flange dia, head dia, head height, fully threaded)',
    'mcm_tap_pan': MCM + 'tapping-screws/material~18-8-stainless-steel/stainless-steel-phillips-rounded-head-screws-for-sheet-metal~~/ (McMaster 18-8 and black-oxide 18-8 Phillips rounded head sheet metal screws: lengths, head dia, head height, threads per inch, drive size)',
    'iso4027': ITEH + '36430/dfcea24c694e460ea6b659cfc216c6c1/ISO-4027-2003.pdf (ISO 4027:2003 Table 1: dt max, s, t min short/long)',
    'iso4028': 'https://cdn.standards.iteh.ai/samples/36432/747ac323337a46f7a02c6211e6675ce6/ISO-4028-2003.pdf (ISO 4028:2003 Table 1: dp, z short/long, s, t min short/long)',
    'iso7380_2': ITEH + '53672/801ec2c66dfc4359ba76493e3d01d97f/ISO-7380-2-2011.pdf (ISO 7380-2:2011 Table 1: c max, dc, dk, k, rf max, s, t min)',
    'iso7049': ITEH + '54046/cdf129d179c645d7b5c43390e21e0811/ISO-7049-2011.pdf (ISO 7049:2011 Table 1: P, rf, recess no., Type H m and penetration, y Type C)',
    'b1863_pan': 'https://adfastcomponents.com/weights/asme/weights-for-asme-b18-6-3-type-1-cross-recessed-pan-head-machine-screws/ (ASME B18.6.3 Table 18 Type I pan head: A, H, recess M, driver size, penetration P)',
})
CONE_MCM = {  # McMaster 18-8 cone-tip set screws: (length, cone angle deg) per thread
    '#2': [(0.125, 90), (0.1875, 90), (0.25, 90), (0.3125, 90), (0.375, 90)],
    '#4': [(0.125, 118), (0.1875, 90), (0.25, 90), (0.3125, 90), (0.375, 90), (0.4375, 90), (0.5, 90), (0.625, 90), (0.75, 90), (1, 90)],
    '#6': [(0.125, 118), (0.1875, 90), (0.25, 90), (0.3125, 90), (0.375, 90), (0.4375, 90), (0.5, 90), (0.625, 90), (0.75, 90), (1, 90)],
    '#8': [(0.125, 118), (0.1875, 118), (0.25, 90), (0.3125, 90), (0.375, 90), (0.5, 90), (0.625, 90), (0.75, 90), (1, 90)],
    '#10': [(0.1875, 118), (0.25, 90), (0.3125, 90), (0.375, 90), (0.5, 90), (0.625, 90), (0.75, 90), (1, 90)],
    '#10-32': [(0.125, 118), (0.1875, 118), (0.25, 90), (0.3125, 90), (0.375, 90), (0.5, 90), (0.625, 90), (0.75, 90), (1, 90)],
    '1/4': [(0.1875, 118), (0.25, 118), (0.3125, 90), (0.375, 90), (0.5, 90), (0.625, 90), (0.75, 90), (1, 90), (1.25, 90), (1.5, 90)],
    '1/4-28': [(0.1875, 118), (0.25, 118), (0.3125, 90), (0.375, 90), (0.5, 90), (0.625, 90), (0.75, 90), (1, 90)],
    '5/16': [(0.25, 118), (0.3125, 118), (0.375, 90), (0.5, 90), (0.625, 90), (0.75, 90), (0.875, 90), (1, 90), (1.25, 90)],
    '5/16-24': [(0.25, 118), (0.375, 118), (0.5, 90), (0.625, 90), (0.75, 90), (1, 90)],
    '3/8': [(0.375, 118), (0.5, 90), (0.625, 90), (0.75, 90), (1, 90), (1.25, 90), (1.5, 90), (2, 90)],
    '3/8-24': [(0.375, 118), (0.5, 90), (0.625, 90), (0.75, 90), (1, 90)],
    '1/2': [(0.5, 118), (0.75, 90), (1, 90), (1.25, 90), (1.5, 90)],
    'M2': [(3, 90), (4, 90), (5, 90), (10, 90)],
    'M2.5': [(3, 120), (4, 90), (5, 90), (6, 90), (8, 90), (10, 90)],
    'M3': [(3, 120), (4, 90), (5, 90), (6, 90), (8, 90), (10, 90), (12, 90), (16, 90), (20, 90)],
    'M4': [(3, 90), (4, 120), (5, 90), (6, 90), (8, 90), (10, 90), (12, 90), (16, 90), (20, 90)],
    'M5': [(5, 120), (6, 90), (8, 90), (10, 90), (12, 90), (30, 90)],
    'M6': [(6, 120), (8, 90), (10, 90), (12, 90), (16, 90), (20, 90), (30, 90)],
    'M8': [(8, 120), (10, 120), (12, 90), (16, 90), (20, 90), (30, 90)],
    'M10': [(10, 120), (12, 90), (16, 90), (20, 90), (25, 90), (30, 90)],
    'M12': [(12, 90), (20, 90)],
}
EXT_MCM = {  # McMaster 18-8 extended-tip set screws: (length, tip dia, tip length)
    '#2': [(0.125, 0.057, 0.024), (0.1875, 0.057, 0.024), (0.25, 0.057, 0.024), (0.3125, 0.057, 0.024)],
    '#4': [(0.125, 0.075, 0.03), (0.1875, 0.075, 0.03), (0.25, 0.075, 0.03), (0.3125, 0.075, 0.03), (0.375, 0.075, 0.03), (0.5, 0.075, 0.03)],
    '#6': [(0.125, 0.092, 0.038), (0.1875, 0.092, 0.038), (0.25, 0.092, 0.038), (0.3125, 0.092, 0.038), (0.375, 0.092, 0.038), (0.5, 0.092, 0.038), (0.625, 0.092, 0.038), (0.75, 0.092, 0.038)],
    '#8': [(0.125, 0.109, 0.043), (0.1875, 0.109, 0.043), (0.25, 0.109, 0.043), (0.3125, 0.109, 0.043), (0.375, 0.109, 0.043), (0.5, 0.109, 0.043), (0.625, 0.109, 0.043), (0.75, 0.109, 0.043), (1, 0.109, 0.043)],
    '#10': [(0.1875, 0.127, 0.049), (0.25, 0.127, 0.049), (0.3125, 0.127, 0.049), (0.375, 0.127, 0.049), (0.5, 0.127, 0.049), (0.625, 0.127, 0.049), (0.75, 0.127, 0.049), (1, 0.127, 0.049)],
    '#10-32': [(0.1875, 0.127, 0.049), (0.25, 0.127, 0.049), (0.3125, 0.127, 0.049), (0.375, 0.127, 0.049), (0.5, 0.127, 0.049), (0.625, 0.127, 0.049), (0.75, 0.127, 0.049), (1, 0.127, 0.049)],
    '1/4': [(0.1875, 0.156, 0.067), (0.25, 0.156, 0.067), (0.3125, 0.156, 0.067), (0.375, 0.156, 0.067), (0.5, 0.156, 0.067), (0.625, 0.156, 0.067), (0.75, 0.156, 0.067), (1, 0.156, 0.067), (1.25, 0.156, 0.067)],
    '1/4-28': [(0.1875, 0.156, 0.067), (0.25, 0.156, 0.067), (0.3125, 0.156, 0.067), (0.375, 0.156, 0.067), (0.5, 0.156, 0.067), (0.625, 0.156, 0.067), (0.75, 0.156, 0.067), (1, 0.156, 0.067), (1.25, 0.156, 0.067)],
    '5/16': [(0.25, 0.203, 0.082), (0.3125, 0.203, 0.082), (0.375, 0.203, 0.082), (0.5, 0.203, 0.082), (0.625, 0.203, 0.082), (0.75, 0.203, 0.082), (1, 0.203, 0.082), (1.25, 0.203, 0.082), (1.5, 0.203, 0.082)],
    '5/16-24': [(0.25, 0.203, 0.082), (0.3125, 0.203, 0.082), (0.375, 0.203, 0.082), (0.5, 0.203, 0.082), (0.625, 0.203, 0.082), (0.75, 0.203, 0.082), (1, 0.203, 0.082), (1.25, 0.203, 0.082)],
    '3/8': [(0.375, 0.25, 0.099), (0.5, 0.25, 0.099), (0.625, 0.25, 0.099), (0.75, 0.25, 0.099), (1, 0.25, 0.099), (1.25, 0.25, 0.099), (1.5, 0.25, 0.099)],
    '3/8-24': [(0.375, 0.25, 0.099), (0.5, 0.25, 0.099), (0.625, 0.25, 0.099), (0.75, 0.25, 0.099), (1, 0.25, 0.099), (1.25, 0.25, 0.099)],
    '1/2': [(0.375, 0.343, 0.13), (0.5, 0.343, 0.13), (0.625, 0.343, 0.13), (0.75, 0.343, 0.13), (1, 0.343, 0.13), (1.25, 0.343, 0.13), (1.5, 0.343, 0.13)],
    'M3': [(3, 2, 1), (4, 2, 1), (5, 2, 1), (6, 2, 1.75), (8, 2, 1.75), (10, 2, 1.75)],
    'M4': [(6, 2.5, 1.25), (8, 2.5, 2.25), (10, 2.5, 2.25), (12, 2.5, 2.25), (16, 2.5, 2.25), (20, 2.5, 2.25)],
    'M5': [(5, 3.5, 1.5), (6, 3.5, 1.5), (8, 3.5, 2.75), (10, 3.5, 2.75), (12, 3.5, 2.75), (16, 3.5, 2.75), (20, 3.5, 2.75), (25, 3.5, 2.75), (30, 3.5, 2.75)],
    'M6': [(6, 4, 1.75), (8, 4, 1.75), (10, 4, 3.25), (12, 4, 3.25), (16, 4, 3.25), (20, 4, 3.25), (25, 4, 3.25), (30, 4, 3.25), (35, 4, 3.25)],
    'M8': [(8, 5.5, 2.25), (10, 5.5, 2.25), (12, 5.5, 4.3), (16, 5.5, 4.3), (20, 5.5, 4.3), (25, 5.5, 4.3), (30, 5.5, 4.3), (35, 5.5, 4.3), (40, 5.5, 4.3), (50, 5.5, 4.3)],
    'M10': [(10, 7, 2.75), (12, 7, 2.75), (16, 7, 5.3), (20, 7, 5.3), (25, 7, 5.3), (30, 7, 5.3), (35, 7, 5.3), (40, 7, 5.3), (50, 7, 5.3)],
    'M12': [(12, 8.5, 3.25), (16, 8.5, 6.3), (20, 8.5, 6.3), (25, 8.5, 6.3), (30, 8.5, 6.3), (35, 8.5, 6.3), (40, 8.5, 6.3), (50, 8.5, 6.3)],
}
OVAL_MCM = {  # McMaster 18-8 oval-tip set screws: lengths
    '#4': [0.125, 0.1875, 0.25, 0.375],
    '#6': [0.125, 0.1875, 0.25, 0.375, 0.5],
    '#8': [0.25, 0.375, 0.5],
    '#10-32': [0.1875, 0.25, 0.375, 0.5, 0.75],
    '1/4': [0.375, 0.5],
    '3/8': [0.625],
}

# Holo-Krome Table 13 (hk_tech): socket J, key engagement TH for lengths >= column B, oval point radius R,
# and column B for 90 deg cone and oval points and for half dog points.
_HK13 = {  # nominal: (J, TH, R, B_cone_oval, B_half_dog)
    '#2': (0.035, 0.060, 0.064, 0.19, 0.19), '#4': (0.050, 0.070, 0.084, 0.19, 0.19),
    '#6': (0.062, 0.080, 0.104, 0.25, 0.19), '#8': (0.078, 0.090, 0.123, 0.25, 0.25),
    '#10': (0.094, 0.100, 0.142, 0.25, 0.25), '1/4': (0.125, 0.125, 0.188, 0.31, 0.31),
    '5/16': (0.156, 0.156, 0.234, 0.44, 0.38), '3/8': (0.188, 0.188, 0.281, 0.44, 0.44),
    '1/2': (0.250, 0.250, 0.375, 0.63, 0.63)}
# Holo-Krome Table 14: minimum key engagement for short set screws, by two-place nominal length:
# (118 deg cone and oval points, half dog point). None: not made.
_HK14 = {
    '#2': {0.06: (0.029, None), 0.09: (0.040, 0.035)},
    '#4': {0.09: (0.039, None), 0.13: (0.045, 0.045)},
    '#6': {0.09: (0.039, None), 0.13: (0.045, 0.045), 0.16: (0.065, 0.065)},
    '#8': {0.13: (0.050, 0.045), 0.16: (0.060, 0.060), 0.19: (0.065, 0.065)},
    '#10': {0.13: (0.042, 0.042), 0.19: (0.060, 0.060)},
    '1/4': {0.19: (0.065, 0.055), 0.25: (0.110, 0.090)},
    '5/16': {0.25: (0.099, 0.090), 0.31: (0.140, 0.105)},
    '3/8': {0.25: (0.090, 0.075), 0.31: (0.115, 0.105)},
    '1/2': {0.38: (0.130, 0.130), 0.44: (0.155, 0.155), 0.50: (0.195, 0.195)}}
_TWO = {0.0625: 0.06, 0.09375: 0.09, 0.125: 0.13, 0.15625: 0.16, 0.1875: 0.19, 0.25: 0.25, 0.3125: 0.31,
        0.375: 0.38, 0.4375: 0.44, 0.5: 0.50, 0.625: 0.63}
# ISO 4027 / ISO 4028 / ISO 4026 socket: s nom, t min (short lengths), t min (other lengths)
_ISO_SET = {'M2': (0.9, 0.8, 1.7), 'M2.5': (1.3, 1.2, 2.0), 'M3': (1.5, 1.2, 2.0), 'M4': (2.0, 1.5, 2.5),
            'M5': (2.5, 2.0, 3.0), 'M6': (3.0, 2.0, 3.5), 'M8': (4.0, 3.0, 5.0), 'M10': (5.0, 4.0, 6.0),
            'M12': (6.0, 4.8, 8.0)}
_ISO4027_DT = {'M2': 0.5, 'M2.5': 0.65, 'M3': 0.75, 'M4': 1.0, 'M5': 1.25, 'M6': 1.5, 'M8': 2.0, 'M10': 2.5,
               'M12': 3.0}


def _inch_t(nom, L, point):
    """Key engagement for an inch set screw: Table 13 TH at or above column B, else the Table 14 value for this
    length; None if neither table covers the length (see _short_t)."""
    j, th, r, b_co, b_hd = _HK13[nom]
    b = b_hd if point == 'dog' else b_co
    if _TWO.get(L, round(L, 2)) >= b - 1e-9:
        return th
    v = _HK14.get(nom, {}).get(_TWO.get(L))
    return v and v[1 if point == 'dog' else 0]


# Short lengths McMaster stocks that neither Holo-Krome table covers: the socket uses the size's standard depth
# (Table 13 TH; the socket depth is the same for every length of a size), cut back only where it would leave
# less than a quarter of the nominal diameter of solid metal above the point (Daniel, 2026-11-16).
SHORT_T = []  # filled by _set_rows: (point, size, L, TH, depth used)


def _point_h(point, d, tpi, it, R):
    """Point height (in) as fastener_core.geometry draws it: cone and dog points start at the thread root."""
    root_r = (d - 1.082532 / tpi) / 2.0
    if point == 'cone':
        return root_r / math.tan(math.radians(it[1] / 2.0))
    if point == 'dog':
        return it[2] + root_r - it[1] / 2.0
    return R - math.sqrt(R * R - (d / 2.0) ** 2)  # oval


def _short_t(point, size, d, tpi, it, th, R):
    cap = math.floor((it[0] - _point_h(point, d, tpi, it, R) - 0.25 * d) * 1000.0) / 1000.0
    t = min(th, cap)
    SHORT_T.append((point, size, it[0], th, t))
    return t


def _key(size):
    """'1/4-28' -> ('1/4', 'UNF'), '1/4' -> ('1/4', 'UNC')."""
    return (size.rsplit('-', 1)[0], 'UNF') if '-' in size else (size, 'UNC')


def _set_rows(table, point):
    rows = []
    for size, items in table.items():
        if size.startswith('M'):
            s, t_short, t_long = _ISO_SET[size]
            row = dict(size=size, d=float(size[1:]), pitch=PITCH[size], dims={'s': s, 't_by_length': {}},
                       lengths=[])
            for it in items:
                L = it[0]
                if point == 'cone':
                    short = it[1] != 90 or L <= row['d']  # McMaster's 118/120 deg lengths are ISO 4027's short ones
                    row['dims'].setdefault('angle_by_length', {})['%g' % L] = it[1]
                    row['dims']['tip_d'] = _ISO4027_DT[size]
                else:  # dog: McMaster's short tip lengths are ISO 4028's short dog points
                    row['dims']['dp'] = it[1]
                    row['dims'].setdefault('z_by_length', {})['%g' % L] = it[2]
                    short = it[2] < max(x[2] for x in items)
                row['dims']['t_by_length']['%g' % L] = t_short if short else t_long
                row['lengths'].append(float(L))
        else:
            nom, series = _key(size)
            d, tpi = UNC[nom]
            if series == 'UNF':
                tpi = UNF[nom]
            j, th, R, _b, _bd = _HK13[nom]
            row = dict(size=size if series == 'UNC' else '%s-%d' % (nom, tpi), nominal=nom, series=series, d=d,
                       tpi=tpi, dims={'s': j, 't_by_length': {}}, lengths=[])
            if point == 'oval':
                row['dims']['R'] = R
            for it in (items if point != 'oval' else [(L,) for L in items]):
                L = float(it[0])
                t = _inch_t(nom, L, point)
                if t is None:
                    t = _short_t(point, row['size'], d, tpi, (L,) + tuple(it[1:]), th, R)
                if point == 'cone':
                    row['dims'].setdefault('angle_by_length', {})['%g' % L] = it[1]
                    row['dims']['tip_d'] = 0.0
                elif point == 'dog':
                    row['dims']['dp'] = it[1]
                    row['dims'].setdefault('z_by_length', {})['%g' % L] = it[2]
                row['dims']['t_by_length']['%g' % L] = t
                row['lengths'].append(L)
        if row['lengths']:
            rows.append(row)
    return rows


def _tap_in(rows):
    """rows: (nominal, d, tpi, dims, lengths, McMaster stocks black oxide too (reference only))."""
    return [dict(size=n, nominal=n, series='tapping', d=d, tpi=tpi, dims=dims, lengths=ls)
            for n, d, tpi, dims, ls, bo in rows]


def _tap_m(rows):
    return [dict(size=n, d=float(n[1:]), pitch=p, dims=dims, lengths=ls) for n, p, dims, ls in rows]


def _pan_in(dk, k, recess, m, p_max, p_min):
    return {'dk': dk, 'k': k, 'flat_top': True, 'recess': recess, 'm': m, 'pen': round((p_max + p_min) / 2.0, 4)}


def _pan_m(dk, k, rf, recess, m, p_max, p_min, y):
    return {'dk': dk, 'k': k, 'rf': rf, 'recess': recess, 'm': m, 'pen': round((p_max + p_min) / 2.0, 4), 'tip': y}


def _fl(dk, k, rf, s, t, dc, c):
    return {'dk': dk, 'k': k, 'rf': rf, 's': s, 't': t, 'dc': dc, 'c': c}


FAMILIES += [
    dict(code='SSN-M', name='Cone-tip set screw', standard='ISO 4027', system='metric', head='set', point='cone',
         drive='hex', finishes=STD, source=SRC['iso4027'],
         sources={'dims': ['iso4027', 'mcm_cone'], 'lengths': ['mcm_cone'], 'thread': ['iso4027'], 'alloy': []},
         sizes=_set_rows({k: v for k, v in CONE_MCM.items() if k.startswith('M')}, 'cone')),
    dict(code='SSN-I', name='Cone-tip set screw', standard='ASME B18.3', system='inch', head='set', point='cone',
         drive='hex', finishes=STD, source=SRC['hk_tech'],
         sources={'dims': ['hk_tech', 'mcm_cone'], 'lengths': ['mcm_cone'], 'thread': [], 'alloy': []},
         sizes=_set_rows({k: v for k, v in CONE_MCM.items() if not k.startswith('M')}, 'cone')),
    dict(code='SSE-M', name='Extended-tip set screw', standard='ISO 4028', system='metric', head='set', point='dog',
         drive='hex', finishes=STD, source=SRC['iso4028'],
         sources={'dims': ['iso4028', 'mcm_ext'], 'lengths': ['mcm_ext'], 'thread': ['iso4028'], 'alloy': []},
         sizes=_set_rows({k: v for k, v in EXT_MCM.items() if k.startswith('M')}, 'dog')),
    dict(code='SSE-I', name='Extended-tip set screw', standard='ASME B18.3 (half dog)', system='inch', head='set',
         point='dog', drive='hex', finishes=STD, source=SRC['hk_tech'],
         sources={'dims': ['hk_tech', 'mcm_ext'], 'lengths': ['mcm_ext'], 'thread': [], 'alloy': []},
         sizes=_set_rows({k: v for k, v in EXT_MCM.items() if not k.startswith('M')}, 'dog')),
    dict(code='SSO-I', name='Oval-tip set screw', standard='ASME B18.3', system='inch', head='set', point='oval',
         drive='hex', finishes=STD, source=SRC['hk_tech'],
         sources={'dims': ['hk_tech'], 'lengths': ['mcm_oval'], 'thread': [], 'alloy': []},
         sizes=_set_rows(OVAL_MCM, 'oval')),
    # McMaster: dc (flange dia), dk (head dia), k; ISO 7380-2: rf, c (flange thickness), s, t. All fully threaded.
    # M10 lengths 20 to 30 mm have a different head on McMaster (20.6 mm flange) and are left out.
    dict(code='SBF-M', name='Flanged button head hex-drive screw', standard='ISO 7380-2', system='metric',
         head='flbutton', drive='hex', finishes=STD, source=SRC['iso7380_2'],
         sources={'dims': ['mcm_flbtn', 'iso7380_2'], 'lengths': ['mcm_flbtn'], 'thread': ['mcm_flbtn'], 'alloy': []},
         sizes=[dict(size=s, d=float(s[1:]), pitch=PITCH[s], dims=dims, lengths=ls) for s, dims, ls in [
             ('M3', _fl(5.2, 1.65, 3.7, 2.0, 1.04, 6.9, 0.7), [5, 6, 8, 10, 12, 14, 16, 20, 22, 25]),
             ('M4', _fl(7.2, 2.2, 4.6, 2.5, 1.3, 9.4, 0.8), [5, 6, 8, 10, 12, 14, 16, 18, 20, 22, 25, 30, 35, 40]),
             ('M5', _fl(8.8, 2.75, 5.75, 3.0, 1.56, 11.8, 1.0), [6, 8, 10, 12, 14, 16, 18, 20, 22, 25, 30, 35, 40]),
             ('M6', _fl(10.0, 3.3, 6.15, 4.0, 2.08, 13.6, 1.2),
              [6, 8, 10, 12, 14, 16, 18, 20, 22, 25, 30, 35, 40, 45, 50]),
             ('M8', _fl(13.2, 4.4, 7.95, 5.0, 2.6, 17.8, 1.5), [10, 12, 16, 20, 22, 25, 30, 35, 40, 45, 50]),
             ('M10', _fl(16.5, 5.5, 9.8, 6.0, 3.12, 22.0, 2.0), [12, 16, 35, 40])]]),
    # Inch: McMaster head (matches ASME B18.6.3 Table 18 A and H max) and threads per inch; recess M and mean
    # penetration from B18.6.3 Table 18.
    dict(code='STP-I', name='Phillips rounded head sheet metal screw', standard='ASME B18.6.3 head', system='inch',
         head='pan', drive='phillips', thread_form='tapping', finishes=STD, source=SRC['mcm_tap_pan'],
         sources={'dims': ['mcm_tap_pan', 'b1863_pan'], 'lengths': ['mcm_tap_pan'], 'thread': ['mcm_tap_pan'],
                  'alloy': []},
         sizes=_tap_in([
             ('#2', 0.086, 32, _pan_in(0.167, 0.062, 1, 0.097, 0.052, 0.034),
              [0.125, 0.1875, 0.25, 0.3125, 0.375, 0.4375, 0.5, 0.625, 0.75], False),
             ('#4', 0.112, 24, _pan_in(0.219, 0.080, 1, 0.115, 0.071, 0.053),
              [0.1875, 0.25, 0.3125, 0.375, 0.4375, 0.5, 0.625, 0.75, 1.0, 1.25, 1.5], False),
             ('#6', 0.138, 18, _pan_in(0.270, 0.097, 2, 0.159, 0.080, 0.055),
              [0.1875, 0.25, 0.3125, 0.375, 0.4375, 0.5, 0.625, 0.75, 0.875, 1.0, 1.125, 1.25, 1.5, 1.75, 2.0, 2.5],
              True),
             ('#8', 0.164, 15, _pan_in(0.322, 0.115, 2, 0.175, 0.097, 0.071),
              [0.25, 0.375, 0.5, 0.625, 0.75, 0.875, 1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 2.75, 3.0, 3.5], True),
             ('#10', 0.190, 12, _pan_in(0.373, 0.133, 2, 0.192, 0.113, 0.089),
              [0.25, 0.375, 0.4375, 0.5, 0.625, 0.75, 0.875, 1.0, 1.25, 1.5, 1.75], True),
             ('#12', 0.216, 11, _pan_in(0.425, 0.151, 3, 0.252, 0.124, 0.098),
              [0.375, 0.5, 0.625, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0, 3.5, 4.0], True)])),
    # Metric: McMaster head dk and k (slightly off ISO 7049: McMaster wins); pitch, crown rf, Type H recess m and
    # mean penetration, and Type C point length y from ISO 7049. M3.9 is not in ISO 7049 and is left out.
    dict(code='STP-M', name='Phillips rounded head sheet metal screw', standard='ISO 7049', system='metric',
         head='pan', drive='phillips', thread_form='tapping', finishes=STD, source=SRC['iso7049'],
         sources={'dims': ['mcm_tap_pan', 'iso7049'], 'lengths': ['mcm_tap_pan'], 'thread': ['iso7049'], 'alloy': []},
         sizes=_tap_m([
             ('M2.2', 0.8, _pan_m(4.2, 1.8, 3.2, 0, 1.9, 1.20, 0.85, 2.0), [6.5, 9.5, 13, 16]),
             ('M2.9', 1.1, _pan_m(5.6, 2.2, 5.0, 1, 3.0, 1.80, 1.40, 2.6), [6.5, 9.5, 13, 16, 19, 25]),
             ('M3.5', 1.3, _pan_m(6.9, 2.6, 6.0, 2, 3.9, 1.90, 1.40, 3.2), [9.5, 13, 16, 19, 25, 32]),
             ('M4.2', 1.4, _pan_m(8.2, 3.1, 6.5, 2, 4.4, 2.40, 1.90, 3.7), [9.5, 13, 16, 19, 22, 25, 32, 38]),
             ('M4.8', 1.6, _pan_m(9.5, 3.6, 8.0, 2, 4.9, 2.90, 2.40, 4.3), [13, 16, 19, 22, 25, 38]),
             ('M5.5', 1.8, _pan_m(10.8, 4.0, 9.0, 3, 6.4, 3.10, 2.60, 5.0), [13, 16, 19, 25, 38])])),
]
for _f in FAMILIES[-8:]:
    for _r in _f['sizes']:
        _r['lengths'] = [float(x) for x in _r['lengths']]
MCMASTER.update({
    'SSN': ('Cone-Tip Set Screws', MCM + 'set-screws/'),
    'SSE': ('Extended-Tip Set Screws', MCM + 'set-screws/'),
    'SSO': ('Oval-Tip Set Screws', MCM + 'set-screws/'),
    'SBF': ('Flanged Button Head Hex-Drive Screws', MCM + 'flanged-button-head-screws/'),
    'STP': ('Phillips Rounded Head Screws for Sheet Metal', MCM + 'tapping-screws/'),
})

for _fam in FAMILIES:
    _fam['mcmaster'], _fam['mcmaster_url'] = MCMASTER[_fam['code'].rsplit('-', 1)[0]]

# Types held back from the dialog (the add-in only reads 'families'). Empty: Daniel approves new types
# automatically as long as they are checked against McMaster-Carr or Fastenal data.
PENDING_APPROVAL = set()
PENDING = [f for f in FAMILIES if f['code'] in PENDING_APPROVAL]
FAMILIES = [f for f in FAMILIES if f['code'] not in PENDING_APPROVAL]


def _extra_length(code, size, length, full_to_head=False):
    """One length a supplier sells that the product standard's length table does not list."""
    for fam in FAMILIES:
        if fam['code'] != code:
            continue
        for row in fam['sizes']:
            if row['size'] != size or length in row['lengths']:
                continue
            row['lengths'] = sorted(list(row['lengths']) + [length])
            if full_to_head:
                row.setdefault('thread', {})
                row['thread'].setdefault('full_to_head', []).append(length)


# ISO 7045:2011 Table 1 stops M3 at 30 mm. JC Fasteners stocks M3 x 35 as a pan Phillips
# screw and calls the length fully threaded, so this one length is threaded to the head.
_extra_length('SPH-M', 'M3', 35, full_to_head=True)
# ISO 10642:2004 Table 1 starts at 8 mm. Aspen sells M3 x 5 as ISO 10642 / DIN 7991, full thread.
# The head stays the ISO 10642 head already on this size. 5 mm is overall, head included.
_extra_length('SFH-M', 'M3', 5)


# ---------- Nuts and washers ----------
# Dimensions are what McMaster-Carr lists for its 18-8 stainless stock (checked 2026-11-16), cross-checked with
# the standard or a maker data sheet; `notes` records where they differ. Catalog units (mm or in):
#   nuts: s across flats, m height (overall height for nylon-insert), flange: dc diameter, c flange thickness
#   washers: d1 inside, d2 outside, t thickness (middle of McMaster's range where it gives a range)
# Every size is offered in 18-8 SS and 18-8 SS-BO (Daniel's rule; McMaster is used for dimensions, not
# availability). No alloy black oxide on nuts and washers.
MCMP = 'https://www.mcmaster.com/products/'
SRC.update({
    'mcm_hexnut_m': MCMP + 'hex-nuts/material~18-8-stainless-steel/system-of-measurement~metric/hex-nuts-3~~/ (McMaster 18-8 metric hex nuts, DIN 934: width, height)',
    'mcm_hexnut_i': MCMP + 'hex-nuts/material~18-8-stainless-steel/hex-nuts-3~~/ (McMaster 18-8 inch hex nuts, ASME B18.2.2 / ASTM F594: width, height)',
    'mcm_hexnut_bo': MCMP + 'hex-nuts/finish~black-oxide/material~18-8-stainless-steel/hex-nuts-3~~/ (McMaster black-oxide 18-8 hex nuts: inch threads stocked, metric M3 to M6)',
    'mcm_thin_bo': MCMP + 'hex-nuts/finish~black-oxide/material~18-8-stainless-steel/thin-profile-hex-nuts-2~~/ (McMaster black-oxide 18-8 thin-profile hex nuts, DIN 439 B: width, height)',
    'mcm_nylon_m': MCMP + 'locknuts/material~18-8-stainless-steel/system-of-measurement~metric/nylon-insert-locknuts-2~~/ (McMaster 18-8 and black-oxide 18-8 metric nylon-insert locknuts: width, height)',
    'mcm_nylon_bo': MCMP + 'locknuts/finish~black-oxide/material~18-8-stainless-steel/nylon-insert-locknuts-2~~/ (McMaster black-oxide 18-8 nylon-insert locknuts, inch: width, height)',
    'mcm_flange_m': MCMP + 'flange-nuts/material~18-8-stainless-steel/system-of-measurement~metric/flange-nuts-1~~/ (McMaster 18-8 metric flange nuts: width, height, flange dia, flange thk)',
    'mcm_serr': MCMP + 'flange-nuts/material~18-8-stainless-steel/serrated-flange-nuts-1~~/ (McMaster 18-8 serrated flange nuts: width, height, flange dia, flange thk)',
    'mcm_gp_bo': MCMP + 'washers/finish~black-oxide/material~18-8-stainless-steel/general-purpose-washers-3~~/ (McMaster black-oxide 18-8 general purpose washers, metric M3 to M8: ID, OD, thk)',
    'mcm_sae_bo': MCMP + 'washers/finish~black-oxide/material~18-8-stainless-steel/sae-washers-1~~/ (McMaster black-oxide 18-8 SAE washers: ID, OD, thk)',
    'mcm_uss_bo': MCMP + 'washers/finish~black-oxide/material~18-8-stainless-steel/uss-washers-2~~/ (McMaster black-oxide 18-8 USS washers: ID, OD, thk)',
    'mcm_over_m': MCMP + 'oversized-washers/material~18-8-stainless-steel/system-of-measurement~metric/ (McMaster 18-8 metric oversized washers: ID, OD, thk)',
    'mcm_split': MCMP + 'lock-washers/material~18-8-stainless-steel/split-lock-washers-2~~/ (McMaster 18-8 split lock washers: ID, OD, thk)',
    'mcm_split_bo': MCMP + 'split-lock-washers/finish~black-oxide/material~18-8-stainless-steel/ (McMaster black-oxide 18-8 split lock washers: inch #2 to 1/2, metric M3 and M5 to M20)',
    'mcm_tooth_m': MCMP + 'lock-washers/material~18-8-stainless-steel/system-of-measurement~metric/tooth-lock-washers-2~~/ (McMaster 18-8 metric tooth lock washers, DIN 6797 A and J: ID, OD, thk)',
    'iso4161': ITEH + '61523/6933d05d5928493fa0aaa091527bed78/ISO-4161-2012.pdf (ISO 4161:2012 Table 1: s, m max, dc max, c min)',
    'iso4032': ITEH + '26382/0f8d850e82f741f5b13e5ed78b236426/ISO-4032-1999.pdf (ISO 4032:1999 Table 1 style 1: s max, m max)',
    'iso10511': 'https://preview.sist.si/sist-preview/61369/9332a361b820448895a2594727485014/ISO-10511-2012.pdf (ISO 10511:2012 Table 1: s max, h max)',
    'iso4035': ITEH + '61671/80e6085c74a64e5bb25f5198a1356852/ISO-4035-2012.pdf (ISO 4035:2012 Table 1: s, m max)',
    'iso7089': ITEH + '13666/bd926567c06846afbe5fef5c514ba406/ISO-7089-2000.pdf (ISO 7089:2000 Table 1: d1, d2, h)',
    'iso7093': ITEH + '13677/a0dc4c7265a048bcb627747f4d7cadf2/ISO-7093-1-2000.pdf (ISO 7093-1:2000 Table 1: d1, d2, h)',
    'bbi_985': 'https://www.brightonbest.com/download/pds/PDS_Metric_DIN_985_Nylon_Insert_Lock_Nuts.pdf (Brighton-Best DIN 985: s, h max)',
    'bbi_6923': 'https://www.brightonbest.com/download/pds/PDS_Metric_Serrated_Hex_Flange_Nuts.pdf (Brighton-Best DIN 6923 serrated flange nuts: s, m, dc)',
    'bbi_127': 'https://www.brightonbest.com/download/pds/PDS_Metric_Type_B_Spring_Lock_Washers_With_Square_Ends_DIN_127.pdf (Brighton-Best DIN 127 B: d1, d2, s)',
    'bbi_6797a': 'https://www.brightonbest.com/download/pds/PDS_Metric_External_Tooth_Lock_Washers_DIN_6797.pdf (Brighton-Best DIN 6797 A: d1, d2, s1)',
    'bbi_6797j': 'https://www.brightonbest.com/download/pds/PDS_Metric_Internal_Tooth_Lock_Washers_DIN_6797.pdf (Brighton-Best DIN 6797 J: d1, d2, s1)',
    'bbi_hexnut': 'https://www.brightonbest.com/download/pds/Hex_Nut_2019.pdf (Brighton-Best finished hex nuts, ASME B18.2.2: F, H)',
    'bbi_sae': 'https://www.brightonbest.com/download/pds/SAE_Flat_Washers.pdf (Brighton-Best SAE washers, ASME B18.21.1 narrow: ID, OD, thk)',
    'bbi_uss': 'https://www.brightonbest.com/download/pds/USS_Flat_Washers.pdf (Brighton-Best USS washers: ID, OD, thk)',
    'bbi_split': 'https://www.brightonbest.com/download/pds/Regular_Spring_Lock_Washers_2019.pdf (Brighton-Best regular split lock washers, ASME B18.21.1: A, B, T)',
    'keystone_standoff': 'https://static.datasheets.com/doc/25868727-keystone-electronics-24339-ds.pdf (Keystone metric standoffs, page 67: 5.5 mm hex, M3 thread, female-female. Length 6 mm stainless catalog 24481 and length 8 mm stainless catalog 24482. Lengths over 19 mm are tapped from both ends, so 6 mm and 8 mm are tapped through. Pitch 0.5 mm is the M3 coarse pitch.)',
})


def _fins(bo, key):
    # Daniel (2026-11-16): every size is offered in 18-8 SS and 18-8 SS-BO whether or not McMaster stocks the
    # black-oxide version. `bo` keeps the record of McMaster's black-oxide stock for reference only.
    return ['SS', 'SS-BO']


def part_mm(rows, bo=()):
    """rows: [(size, dims)]. bo: sizes McMaster sells in black-oxide 18-8 (reference only; every size gets SS-BO)."""
    return [dict(size=size, d=float(size[1:]), pitch=PITCH[size], dims=dims, finishes=_fins(bo, size))
            for size, dims in rows]


def washer_mm(rows, bo=()):
    return [dict(size=size, d=float(size[1:]), dims=dims, finishes=_fins(bo, size)) for size, dims in rows]


def part_in(rows, unf=(), bo=(), bo_unf=None):
    """Inch nuts: one row per thread (UNC, and UNF for sizes in `unf`)."""
    bo_unf = bo if bo_unf is None else bo_unf
    out = []
    for series in ('UNC', 'UNF'):
        for size, dims in rows:
            if series == 'UNF' and size not in unf:
                continue
            d, tpi = UNC[size]
            row = dict(size=size, nominal=size, d=d, series=series, tpi=tpi, dims=dims, finishes=_fins(bo, size))
            if series == 'UNF':
                row.update(size='%s-%d' % (size, UNF[size]), tpi=UNF[size], finishes=_fins(bo_unf, size))
            out.append(row)
    return out


def washer_in(rows, bo=()):
    return [dict(size=size, nominal=size, d=UNC[size][0], dims=dims, finishes=_fins(bo, size)) for size, dims in rows]


def nut(s, m, **kw):
    return dict(s=s, m=m, **kw)


def wash(d1, d2, t):
    return {'d1': d1, 'd2': d2, 't': t}


def fr(a, b):
    return round(a / b, 4)


ALL_IN = ['#2', '#4', '#6', '#8', '#10', '1/4', '5/16', '3/8', '1/2']
ISO4161 = [('M5', nut(8.0, 5.0, dc=11.8, c=1.0)), ('M6', nut(10.0, 6.0, dc=14.2, c=1.1)),
           ('M8', nut(13.0, 8.0, dc=17.9, c=1.2)), ('M10', nut(15.0, 10.0, dc=21.8, c=1.5)),
           ('M12', nut(18.0, 12.0, dc=26.0, c=1.8))]
TOOTH_M = [('M3', wash(3.2, 6.0, 0.4)), ('M4', wash(4.3, 8.0, 0.5)), ('M5', wash(5.3, 10.0, 0.6)),
           ('M6', wash(6.4, 11.0, 0.7)), ('M8', wash(8.4, 15.0, 0.8)), ('M10', wash(10.5, 18.0, 0.9)),
           ('M12', wash(13.0, 20.5, 1.05)), ('M16', wash(17.0, 26.0, 1.2)), ('M20', wash(21.0, 33.0, 1.4))]


def part(code, kind, shape, name, standard, system, sizes, dims, finish_src, notes=''):
    fins = ['SS', 'SS-BO']
    return dict(code=code, kind=kind, shape=shape, name=name, standard=standard, system=system, sizes=sizes,
                finishes=fins, source=SRC[dims[0]], sources={'dims': dims, 'finish': finish_src}, notes=notes)


PARTS = [
    part('NHX-M', 'nut', 'hex', 'Hex nut', 'DIN 934', 'metric',
         part_mm([('M3', nut(5.5, 2.4)), ('M4', nut(7.0, 3.2)), ('M5', nut(8.0, 4.0)), ('M6', nut(10.0, 5.0)),
                  ('M8', nut(13.0, 6.5)), ('M10', nut(17.0, 8.0)), ('M12', nut(19.0, 10.0)),
                  ('M16', nut(24.0, 13.0)), ('M20', nut(30.0, 16.0))], bo=('M3', 'M4', 'M5', 'M6')),
         ['mcm_hexnut_m'], ['mcm_hexnut_bo'],
         'McMaster stocks DIN 934. M3 and M4 match ISO 4032 style 1 (s max and m max), so they are not repeated. '
         'M2 and the sizes that differ are the regular hex nut.'),
    part('NTH-M', 'nut', 'hex', 'Thin-profile hex nut', 'DIN 439 B', 'metric',
         part_mm([('M3', nut(5.5, 1.8)), ('M4', nut(7.0, 2.2)), ('M5', nut(8.0, 2.7)), ('M6', nut(10.0, 3.2)),
                  ('M8', nut(13.0, 4.0)), ('M10', nut(17.0, 5.0)), ('M12', nut(19.0, 6.0)), ('M16', nut(24.0, 8.0))],
                 bo=('M3', 'M4', 'M5', 'M6', 'M8', 'M10', 'M12', 'M16')),
         ['mcm_thin_bo', 'iso4035'], ['mcm_thin_bo'],
         'Heights match ISO 4035; McMaster widths at M10 (17) and M12 (19) are DIN 439 B, ISO 4035 says 16 and 18.'),
    part('NNL-M', 'nut', 'nylon', 'Nylon-insert locknut', 'DIN 985', 'metric',
         part_mm([('M3', nut(5.5, 4.0)), ('M4', nut(7.0, 5.0)), ('M5', nut(8.0, 5.0)), ('M6', nut(10.0, 6.0)),
                  ('M8', nut(13.0, 8.0)), ('M10', nut(17.0, 10.0)), ('M12', nut(19.0, 12.0)),
                  ('M16', nut(24.0, 16.0)), ('M20', nut(30.0, 20.0))],
                 bo=('M3', 'M4', 'M5', 'M6', 'M8', 'M10', 'M12')),
         ['mcm_nylon_m', 'bbi_985'], ['mcm_nylon_m'],
         'DIN 985 overall height (McMaster and Brighton-Best agree). ISO 10511 is the thin nylon-insert family: '
         'same width and overall height at M4, M5 and M6, 0.1 mm shorter at M3, shorter from M8, and narrower at M10 and M12.'),
    part('NFL-M', 'nut', 'flange', 'Flange nut', 'ISO 4161 (DIN 6923)', 'metric',
         part_mm([('M3', nut(5.5, 4.0, dc=8.0, c=1.0)), ('M4', nut(7.0, 4.0, dc=10.0, c=0.9))] + ISO4161),
         ['mcm_flange_m', 'iso4161'], [],
         'M5 to M12 are ISO 4161 (c = flange thickness min); M3 and M4 are not in ISO 4161 and come from McMaster.'),
    part('NHR-M', 'nut', 'hex', 'Regular hex nut', 'ISO 4032', 'metric',
         part_mm([('M2', nut(4.0, 1.6)), ('M5', nut(8.0, 4.7)), ('M6', nut(10.0, 5.2)),
                  ('M8', nut(13.0, 6.8)), ('M10', nut(16.0, 8.4)), ('M12', nut(18.0, 10.8)),
                  ('M16', nut(24.0, 14.8)), ('M20', nut(30.0, 18.0))]),
         ['iso4032'], [],
         'ISO 4032:1999 Table 1 style 1, width s max and height m max. M3 is 5.5 by 2.4 and M4 is 7 by 3.2, '
         'the same as DIN 934, so those sizes stay on the hex nut. M2 is the same width and height as DIN 934 '
         'and is listed here because that family starts at M3. M2.5 is in Table 1 and is not offered.'),
    part('NTN-M', 'nut', 'nylon', 'Thin-profile nylon-insert locknut', 'ISO 10511', 'metric',
         part_mm([('M3', nut(5.5, 3.9)), ('M4', nut(7.0, 5.0)), ('M5', nut(8.0, 5.0)),
                  ('M6', nut(10.0, 6.0)), ('M8', nut(13.0, 6.76)), ('M10', nut(16.0, 8.56)),
                  ('M12', nut(18.0, 10.23)), ('M16', nut(24.0, 12.42)), ('M20', nut(30.0, 14.9))]),
         ['iso10511'], [],
         'ISO 10511:2012 Table 1, width s max and overall height h max. The insert is drawn as part of the hex. '
         'M4, M5 and M6 match the DIN 985 width and overall height. M3 is 3.9 versus 4.0. From M8 the nut is shorter, '
         'and M10 and M12 are also narrower. The table starts at M3.'),
    part('NSF-M', 'nut', 'flange', 'Serrated flange nut', 'ISO 4161 (DIN 6923)', 'metric',
         part_mm([('M3', nut(5.5, 4.0, dc=8.0, c=0.7)), ('M4', nut(7.0, 4.65, dc=10.0, c=1.0))] + ISO4161),
         ['mcm_serr', 'iso4161', 'bbi_6923'], [],
         'Serrations are not modelled. McMaster lists M5 flange dia 11 mm; ISO 4161 and Brighton-Best give 11.8 max.'),
    part('WGP-M', 'washer', 'flat', 'General purpose washer', 'ISO 7089', 'metric',
         washer_mm([('M3', wash(3.2, 7.0, 0.5)), ('M4', wash(4.3, 9.0, 0.8)), ('M5', wash(5.3, 10.0, 1.0)),
                    ('M6', wash(6.4, 12.0, 1.6)), ('M8', wash(8.4, 16.0, 1.6)), ('M10', wash(10.5, 20.0, 2.0)),
                    ('M12', wash(13.0, 24.0, 2.5)), ('M16', wash(17.0, 30.0, 3.0)), ('M20', wash(21.0, 37.0, 3.0))],
                   bo=('M3', 'M4', 'M5', 'M6', 'M8')),
         ['iso7089', 'mcm_gp_bo'], ['mcm_gp_bo'], 'McMaster rows read for M3 to M8; M10 to M20 from ISO 7089.'),
    part('WOV-M', 'washer', 'flat', 'Oversized washer', 'ISO 7093-1', 'metric',
         washer_mm([('M3', wash(3.2, 9.0, 0.8)), ('M4', wash(4.3, 12.0, 1.0)), ('M5', wash(5.3, 15.0, 1.0)),
                    ('M6', wash(6.4, 18.0, 1.6)), ('M8', wash(8.4, 24.0, 2.0)), ('M10', wash(10.5, 30.0, 2.5)),
                    ('M12', wash(13.0, 37.0, 3.0)), ('M16', wash(17.0, 50.0, 3.0)), ('M20', wash(21.0, 60.0, 4.0))]),
         ['iso7093', 'mcm_over_m'], [],
         'ISO 7093-1 values. McMaster lists M5 thk 1.0-1.4 and M20 ID 22.'),
    part('WSL-M', 'washer', 'split', 'Split lock washer', 'DIN 127 B', 'metric',
         washer_mm([('M2', wash(2.4, 4.4, 0.5)), ('M3', wash(3.4, 6.2, 0.8)), ('M4', wash(4.4, 7.6, 0.9)),
                    ('M5', wash(5.4, 9.2, 1.2)),
                    ('M6', wash(6.5, 11.8, 1.6)), ('M8', wash(8.5, 14.8, 2.0)), ('M10', wash(10.7, 18.1, 2.2)),
                    ('M12', wash(12.7, 21.1, 2.5)), ('M16', wash(17.0, 27.4, 3.5)), ('M20', wash(21.2, 33.6, 4.0))],
                   bo=('M3', 'M5', 'M6', 'M8', 'M10', 'M12', 'M16', 'M20')),
         ['mcm_split', 'bbi_127'], ['mcm_split_bo'],
         'Inside diameter is d1 max and outside diameter is d2 max. Thickness is the middle of the Brighton-Best range. '
         'M3 and up match McMaster. M2 is Brighton-Best only: d1 max 2.4, d2 max 4.4, thickness middle of 0.4 to 0.6.'),
    part('WTE-M', 'washer', 'tooth', 'External-tooth lock washer', 'DIN 6797 A', 'metric', washer_mm(TOOTH_M),
         ['mcm_tooth_m', 'bbi_6797a'], [], 'Teeth are not modelled (flat ring at the washer thickness).'),
    part('WTI-M', 'washer', 'tooth', 'Internal-tooth lock washer', 'DIN 6797 J', 'metric', washer_mm(TOOTH_M[:6]),
         ['mcm_tooth_m', 'bbi_6797j'], [], 'McMaster stocks 18-8 to M10. Teeth are not modelled.'),
    part('NHX-I', 'nut', 'hex', 'Hex nut', 'ASME B18.2.2', 'inch',
         part_in([('#2', nut(fr(3, 16), fr(1, 16))), ('#4', nut(0.25, fr(3, 32))), ('#6', nut(fr(5, 16), fr(7, 64))),
                  ('#8', nut(fr(11, 32), 0.125)), ('#10', nut(0.375, 0.125)), ('1/4', nut(fr(7, 16), fr(7, 32))),
                  ('5/16', nut(0.5, fr(17, 64))), ('3/8', nut(fr(9, 16), fr(21, 64))), ('1/2', nut(0.75, fr(7, 16)))],
                 unf=ALL_IN, bo=ALL_IN, bo_unf=('#6', '#8', '#10', '1/4', '5/16', '3/8', '1/2')),
         ['mcm_hexnut_i', 'bbi_hexnut'], ['mcm_hexnut_bo'],
         '#2 to #10 are machine screw nuts. McMaster also sells 1/4-20 at 3/16 high and 5/16, 3/8 in a wider '
         'B18.6.3 style; the ASTM F594 heights are used.'),
    part('NTH-I', 'nut', 'hex', 'Thin-profile hex nut', 'ASME B18.2.2 (jam)', 'inch',
         part_in([('1/4', nut(fr(7, 16), fr(5, 32))), ('5/16', nut(0.5, fr(3, 16))), ('3/8', nut(fr(9, 16), fr(7, 32))),
                  ('1/2', nut(0.75, fr(5, 16)))], unf=ALL_IN, bo=ALL_IN),
         ['mcm_thin_bo'], ['mcm_thin_bo']),
    part('NNL-I', 'nut', 'nylon', 'Nylon-insert locknut', 'IFI 100/107', 'inch',
         part_in([('#2', nut(0.25, fr(9, 64))), ('#4', nut(0.25, fr(9, 64))), ('#6', nut(fr(5, 16), fr(11, 64))),
                  ('#8', nut(fr(11, 32), fr(15, 64))), ('#10', nut(0.375, fr(15, 64))), ('1/4', nut(fr(7, 16), fr(5, 16))),
                  ('5/16', nut(0.5, fr(11, 32))), ('3/8', nut(fr(9, 16), fr(29, 64))), ('1/2', nut(0.75, fr(19, 32)))],
                 unf=('#6', '#8', '#10', '1/4', '5/16', '3/8', '1/2'), bo=ALL_IN),
         ['mcm_nylon_bo'], ['mcm_nylon_bo']),
    part('WSA-I', 'washer', 'flat', 'SAE washer', 'ASME B18.21.1 (SAE)', 'inch',
         washer_in([('#2', wash(0.094, 0.250, 0.015)), ('#4', wash(0.125, 0.312, 0.032)), ('#6', wash(0.156, 0.375, 0.049)),
                    ('#8', wash(0.188, 0.438, 0.049)), ('#10', wash(0.219, 0.500, 0.049)), ('1/4', wash(0.281, 0.625, 0.065)),
                    ('5/16', wash(0.344, 0.688, 0.065)), ('3/8', wash(0.406, 0.812, 0.065)), ('1/2', wash(0.531, 1.062, 0.095))],
                   bo=ALL_IN),
         ['mcm_sae_bo', 'bbi_sae'], ['mcm_sae_bo'],
         'Thickness is the Brighton-Best basic value (inside McMaster\'s range), except #2: McMaster 0.012-0.018 vs 0.020.'),
    part('WUS-I', 'washer', 'flat', 'USS washer', 'USS', 'inch',
         washer_in([('1/4', wash(0.312, 0.750, 0.065)), ('5/16', wash(0.375, 0.875, 0.083)),
                    ('3/8', wash(0.438, 1.000, 0.083)), ('1/2', wash(0.562, 1.375, 0.109))], bo=ALL_IN),
         ['mcm_uss_bo', 'bbi_uss'], ['mcm_uss_bo'], 'McMaster 1/4 OD is 0.750; Brighton-Best (B18.21.1 wide) gives 0.734.'),
    part('WSL-I', 'washer', 'split', 'Split lock washer', 'ASME B18.21.1', 'inch',
         washer_in([('#2', wash(0.094, 0.172, 0.020)), ('#4', wash(0.120, 0.209, 0.025)), ('#6', wash(0.148, 0.250, 0.031)),
                    ('#8', wash(0.174, 0.293, 0.040)), ('#10', wash(0.200, 0.334, 0.047)), ('1/4', wash(0.260, 0.487, 0.062)),
                    ('5/16', wash(0.322, 0.583, 0.078)), ('3/8', wash(0.385, 0.680, 0.094)), ('1/2', wash(0.512, 0.869, 0.125))],
                   bo=ALL_IN),
         ['mcm_split', 'bbi_split'], ['mcm_split_bo'], 'McMaster ID, OD and thickness = B18.21.1 A max, B max, T min.'),
]

# ---------- More nuts and washers (McMaster 18-8 listings read 2026-11-16) ----------
SRC.update({
    'mcm_flange_i': MCMP + 'flange-nuts/material~18-8-stainless-steel/system-of-measurement~inch/flange-nuts-1~~/ (McMaster 18-8 inch flange nuts: width, height, flange dia, flange thk)',
    'mcm_serr_i': MCMP + 'flange-nuts/material~18-8-stainless-steel/system-of-measurement~inch/serrated-flange-nuts-1~~/ (McMaster 18-8 inch serrated flange nuts: width, height, flange dia, flange thk)',
    'mcm_toplock': MCMP + 'locknuts/material~18-8-stainless-steel/top-lock-distorted-thread-locknuts~~/ (McMaster 18-8 top-lock distorted-thread locknuts, inch and metric: width, height)',
    'mcm_thinnyl': MCMP + 'locknuts/material~18-8-stainless-steel/thin-profile-nylon-insert-locknuts-2~~/ (McMaster 18-8 and black-oxide 18-8 thin-profile nylon-insert locknuts, inch: width, height)',
    'mcm_coupling': MCMP + 'coupling-nuts/material~18-8-stainless-steel/coupling-nuts-2~~/ (McMaster 18-8 and black-oxide 18-8 coupling nuts, fully threaded: length, width)',
    'mcm_cap': MCMP + 'cap-nuts/material~18-8-stainless-steel/ (McMaster 18-8 and black-oxide 18-8 cap nuts: thread depth, width, height; inch 91855A, metric 94000A)',
    'mcm_wing': MCMP + 'wing-nuts/material~18-8-stainless-steel/ (McMaster 18-8 wing nuts: width, height, base dia; inch Style 1 92001A, metric 94545A)',
    'mcm_square': MCMP + 'square-nuts/material~18-8-stainless-steel/ (McMaster 18-8 square nuts: width, height; inch 94785A, metric 90225A)',
    'mcm_thick_m': MCMP + 'oversized-washers/material~18-8-stainless-steel/system-of-measurement~metric/ (McMaster 18-8 metric oversized washers 97310A, DIN 7349 per the 97310A131 product page: ID, OD, thk)',
    'mcm_tooth_i': MCMP + 'lock-washers/material~18-8-stainless-steel/system-of-measurement~inch/tooth-lock-washers-2~~/ (McMaster 18-8 and black-oxide 18-8 inch tooth lock washers, ASME B18.21.1: ID, OD, thk)',
    'mcm_fender_i': MCMP + 'oversized-washers/material~18-8-stainless-steel/system-of-measurement~inch/oversized-washers-2~~/ (McMaster 18-8 inch oversized washers 90313A1xx: ID, OD, thk)',
})
UNF_ALL = ('#10', '1/4', '5/16', '3/8', '1/2')
PARTS += [
    # Family 'standard' is shown in the Fusion description and type list.
    # Never put a McMaster or other vendor part number there; cite those only in docs/SOURCES.md.
    part('NFL-I', 'nut', 'flange', 'Flange nut', 'inch flange', 'inch',
         part_in([('#4', nut(0.25, fr(7, 32), dc=0.375, c=0.05)), ('#6', nut(fr(5, 16), fr(7, 32), dc=fr(13, 32), c=0.05)),
                  ('#8', nut(fr(11, 32), 0.25, dc=fr(15, 32), c=0.06)), ('#10', nut(0.375, fr(5, 16), dc=0.5, c=0.06)),
                  ('1/4', nut(0.5, fr(5, 16), dc=0.625, c=0.09)), ('5/16', nut(fr(9, 16), 0.375, dc=0.75, c=0.09)),
                  ('3/8', nut(fr(11, 16), 0.5, dc=0.875, c=0.13)), ('1/2', nut(0.875, fr(11, 16), dc=1.125, c=0.16))],
                 unf=UNF_ALL),
         ['mcm_flange_i'], [], 'No ASME standard for inch flange nuts; dimensions from McMaster 94758A 18-8 listing.'),
    part('NSF-I', 'nut', 'flange', 'Serrated flange nut', 'inch serrated flange', 'inch',
         part_in([('#6', nut(fr(5, 16), fr(11, 64), dc=fr(27, 64), c=0.07)), ('#8', nut(fr(11, 32), fr(13, 64), dc=fr(15, 32), c=0.07)),
                  ('#10', nut(0.375, fr(7, 32), dc=0.5, c=0.09)), ('1/4', nut(fr(7, 16), fr(15, 64), dc=fr(19, 32), c=0.10)),
                  ('5/16', nut(0.5, fr(9, 32), dc=fr(43, 64), c=0.11)), ('3/8', nut(fr(9, 16), fr(11, 32), dc=0.75, c=0.12)),
                  ('1/2', nut(0.75, fr(29, 64), dc=fr(33, 32), c=0.15))],
                 unf=('#10', '1/4', '5/16', '3/8')),
         ['mcm_serr_i'], [], 'Serrations are not modelled. Dimensions from McMaster 93776A. 1/2-20 left out: McMaster lists a 0.05" flange on it.'),
    part('NTL-M', 'nut', 'hex', 'Top-lock distorted-thread locknut', 'metric top-lock', 'metric',
         part_mm([('M4', nut(7.0, 3.2)), ('M5', nut(8.0, 4.0)), ('M6', nut(10.0, 6.0)), ('M8', nut(13.0, 6.4)),
                  ('M10', nut(17.0, 8.0)), ('M12', nut(19.0, 12.0)), ('M16', nut(24.0, 16.0))]),
         ['mcm_toplock'], [], 'Distorted thread not modelled. Dimensions from McMaster 90045A (M6 6 mm, M8 6.4 mm as listed).'),
    part('NTL-I', 'nut', 'hex', 'Top-lock distorted-thread locknut', 'inch top-lock', 'inch',
         part_in([('#6', nut(fr(5, 16), fr(7, 64))), ('#8', nut(fr(11, 32), 0.125)), ('#10', nut(0.375, 0.125)),
                  ('1/4', nut(fr(7, 16), fr(7, 32))), ('5/16', nut(0.5, fr(17, 64))), ('3/8', nut(fr(9, 16), fr(21, 64))),
                  ('1/2', nut(0.75, fr(7, 16)))], unf=UNF_ALL),
         ['mcm_toplock'], [], 'Distorted thread not modelled. Dimensions from McMaster 90045A.'),
    part('NTN-I', 'nut', 'nylon', 'Thin-profile nylon-insert locknut', 'inch thin nylon-insert', 'inch',
         part_in([('#4', nut(0.25, fr(7, 64))), ('#6', nut(fr(5, 16), 0.125)), ('#8', nut(fr(11, 32), fr(11, 64))),
                  ('#10', nut(0.375, fr(11, 64))), ('1/4', nut(fr(7, 16), fr(13, 64))), ('5/16', nut(0.5, 0.25)),
                  ('3/8', nut(fr(9, 16), fr(17, 64))), ('1/2', nut(0.75, fr(5, 16)))],
                 unf=UNF_ALL, bo=('1/4', '5/16', '3/8', '1/2'), bo_unf=('3/8', '1/2')),
         ['mcm_thinnyl'], ['mcm_thinnyl'],
         'Black oxide is modelled with the plain 18-8 dimensions (McMaster\'s black-oxide #4 to #10 are taller). '
         'No metric 18-8 in this style. Dimensions from McMaster 90101A.'),
    part('NCP-M', 'nut', 'hex', 'Coupling nut', 'DIN 6334', 'metric',
         part_mm([('M3', nut(5.0, 9.0)), ('M4', nut(7.0, 12.0)), ('M5', nut(8.0, 15.0)), ('M6', nut(10.0, 18.0)),
                  ('M8', nut(13.0, 24.0)), ('M10', nut(17.0, 30.0)), ('M12', nut(19.0, 36.0)), ('M16', nut(24.0, 48.0)),
                  ('M20', nut(30.0, 60.0))], bo=('M3', 'M4', 'M5', 'M6', 'M8', 'M10', 'M12')),
         ['mcm_coupling'], ['mcm_coupling'], 'Length 3 x d (DIN 6334). Fully threaded 93590A series.'),
    part('NCP-I', 'nut', 'hex', 'Coupling nut', 'inch coupling', 'inch',
         part_in([('#4', nut(fr(5, 16), fr(7, 16))), ('#6', nut(fr(5, 16), 0.5)), ('#8', nut(0.375, 0.625)),
                  ('#10', nut(0.375, 0.75)), ('1/4', nut(0.375, 0.875)), ('5/16', nut(fr(7, 16), 1.0)),
                  ('3/8', nut(0.5, 1.125)), ('1/2', nut(0.625, 1.25))], unf=UNF_ALL),
         ['mcm_coupling'], [], 'Shortest fully threaded 90268A coupling nut per thread (McMaster also sells longer ones).'),
    part('NCA-M', 'nut', 'cap', 'Cap nut', 'DIN 1587', 'metric',
         part_mm([('M3', nut(5.5, 6.0, dp=3.8)), ('M4', nut(7.0, 8.0, dp=5.7)), ('M5', nut(8.0, 10.0, dp=4.5)),
                  ('M6', nut(10.0, 12.0, dp=7.7)), ('M8', nut(13.0, 15.0, dp=10.7)), ('M10', nut(17.0, 18.0, dp=12.7)),
                  ('M12', nut(19.0, 22.0, dp=15.7)), ('M16', nut(24.0, 28.0, dp=20.6)), ('M20', nut(30.0, 34.0, dp=25.6))]),
         ['mcm_cap'], [], 'Dome drawn as a half sphere of radius s/2 on the hex; thread depth dp is the blind bore depth.'),
    part('NCA-I', 'nut', 'cap', 'Cap nut', 'inch cap', 'inch',
         part_in([('#6', nut(fr(5, 16), fr(11, 32), dp=fr(5, 32))), ('#8', nut(fr(5, 16), fr(11, 32), dp=fr(5, 32))),
                  ('#10', nut(0.375, fr(13, 32), dp=fr(3, 16))), ('1/4', nut(fr(7, 16), fr(15, 32), dp=0.25)),
                  ('5/16', nut(0.5, fr(17, 32), dp=fr(5, 16))), ('3/8', nut(fr(9, 16), 0.625, dp=0.375)),
                  ('1/2', nut(0.75, fr(13, 16), dp=0.5))],
                 unf=UNF_ALL, bo=('#6', '#8', '#10', '1/4', '5/16', '3/8', '1/2'), bo_unf=('#10',)),
         ['mcm_cap'], ['mcm_cap'], 'Dome drawn as a half sphere of radius s/2 on the hex; thread depth dp is the blind bore depth. Dimensions from McMaster 91855A.'),
    part('NWG-M', 'nut', 'wing', 'Wing nut', 'DIN 315', 'metric',
         part_mm([('M3', nut(None, 12.0, w=23.2, db=10.9)), ('M4', nut(None, 10.3, w=21.5, db=9.0)),
                  ('M5', nut(None, 10.3, w=21.5, db=10.5)), ('M6', nut(None, 12.7, w=26.3, db=13.0)),
                  ('M8', nut(None, 15.1, w=30.1, db=15.25)), ('M10', nut(None, 18.3, w=34.9, db=18.0)),
                  ('M12', nut(None, 23.8, w=47.6, db=23.0)), ('M16', nut(None, 28.5, w=58.3, db=26.6)),
                  ('M20', nut(None, 33.8, w=68.5, db=29.5))]),
         ['mcm_wing'], [], 'DIN 315 sizes; overall width, height and base dia from McMaster 94545A; the wing shape is simplified (base height m/2, wing thickness db/4, not dimensioned by McMaster).'),
    part('NWG-I', 'nut', 'wing', 'Wing nut', 'Style 1', 'inch',
         part_in([('#6', nut(None, 0.5, w=0.875, db=fr(13, 32))), ('#8', nut(None, 0.5, w=0.875, db=fr(13, 32))),
                  ('#10', nut(None, 0.5, w=0.875, db=fr(13, 32))), ('1/4', nut(None, 0.625, w=1.125, db=fr(31, 64))),
                  ('5/16', nut(None, 0.625, w=1.25, db=fr(35, 64))), ('3/8', nut(None, 0.75, w=1.5, db=fr(43, 64))),
                  ('1/2', nut(None, 1.0, w=2.0, db=fr(29, 32)))], unf=('#10', '1/4', '5/16')),
         ['mcm_wing'], [], 'Style 1; overall width, height and base dia from McMaster 92001A; wing shape simplified. 3/8-24 and 1/2-20 left out (different McMaster dimensions).'),
    part('NSQ-M', 'nut', 'square', 'Square nut', 'DIN 557', 'metric',
         part_mm([('M5', nut(8.0, 4.0)), ('M6', nut(10.0, 5.0)), ('M8', nut(13.0, 6.5)), ('M10', nut(17.0, 8.0)),
                  ('M12', nut(19.0, 10.0)), ('M16', nut(24.0, 13.0))]),
         ['mcm_square'], [], 'McMaster 90225A; values equal DIN 557 s and m.'),
    part('NSQ-I', 'nut', 'square', 'Square nut', 'ASME B18.2.2', 'inch',
         part_in([('#2', nut(fr(3, 16), fr(1, 16))), ('#4', nut(0.25, fr(3, 32))), ('#6', nut(fr(5, 16), fr(7, 64))),
                  ('#8', nut(fr(11, 32), 0.125)), ('#10', nut(0.375, 0.125)), ('1/4', nut(fr(7, 16), fr(3, 16))),
                  ('5/16', nut(fr(9, 16), fr(7, 32))), ('3/8', nut(0.625, 0.25)), ('1/2', nut(fr(13, 16), fr(7, 16)))],
                 unf=('#10', '1/4', '5/16', '3/8')),
         ['mcm_square'], [], '#2 to #10 are machine screw nuts (McMaster 94785A).'),
    part('WTK-M', 'washer', 'flat', 'Thick washer', 'DIN 7349', 'metric',
         washer_mm([('M3', wash(3.2, 9.0, 1.0)), ('M4', wash(4.3, 12.0, 1.6)), ('M5', wash(5.3, 15.0, 2.0)),
                    ('M6', wash(6.4, 17.0, 3.0)), ('M8', wash(8.4, 21.0, 4.0)), ('M10', wash(10.5, 25.0, 4.0)),
                    ('M12', wash(13.0, 30.0, 6.0)), ('M16', wash(17.0, 40.0, 6.0)), ('M20', wash(21.0, 44.0, 8.0))]),
         ['mcm_thick_m'], [], 'Thickness is the middle of McMaster\'s range (= DIN 7349 nominal).'),
    part('WTE-I', 'washer', 'tooth', 'External-tooth lock washer', 'ASME B18.21.1', 'inch',
         washer_in([('#2', wash(0.086, 0.189, 0.0115)), ('#4', wash(0.115, 0.260, 0.015)), ('#6', wash(0.141, 0.320, 0.019)),
                    ('#8', wash(0.168, 0.381, 0.0205)), ('#10', wash(0.195, 0.410, 0.021)), ('1/4', wash(0.256, 0.510, 0.0255)),
                    ('5/16', wash(0.320, 0.610, 0.031)), ('3/8', wash(0.384, 0.694, 0.036)), ('1/2', wash(0.513, 0.900, 0.041))],
                   bo=('#6', '#8', '#10', '1/4', '5/16', '3/8')),
         ['mcm_tooth_i'], ['mcm_tooth_i'], 'Thickness is the middle of McMaster\'s range. Teeth are not modelled.'),
    part('WTI-I', 'washer', 'tooth', 'Internal-tooth lock washer', 'ASME B18.21.1', 'inch',
         washer_in([('#4', wash(0.115, 0.270, 0.015)), ('#6', wash(0.141, 0.295, 0.019)), ('#8', wash(0.168, 0.340, 0.0205)),
                    ('#10', wash(0.195, 0.381, 0.021)), ('1/4', wash(0.256, 0.478, 0.0255)), ('5/16', wash(0.320, 0.610, 0.031)),
                    ('3/8', wash(0.384, 0.692, 0.036)), ('1/2', wash(0.512, 0.900, 0.041))]),
         ['mcm_tooth_i'], [], 'Thickness is the middle of McMaster\'s range. Teeth are not modelled.'),
    part('WOV-I', 'washer', 'flat', 'Oversized washer', 'inch fender', 'inch',
         washer_in([('#6', wash(0.149, 0.625, 0.031)), ('#8', wash(0.174, 0.750, 0.040)), ('#10', wash(0.203, 1.000, 0.040)),
                    ('1/4', wash(0.281, 1.250, 0.050)), ('5/16', wash(0.344, 1.250, 0.050)), ('3/8', wash(0.406, 1.500, 0.062))]),
         ['mcm_fender_i'], [],
         'No inch standard; one McMaster 90313A1xx (fender) washer per size: 90313A101, A102, A104, A108, A111, A115. '
         'Thickness is the middle of McMaster\'s range.'),
    part('HFF-M', 'standoff', 'hex', 'Female-female hex standoff', 'Keystone 5.5 mm hex', 'metric',
         [dict(size='M3', d=3.0, pitch=PITCH['M3'], dims={'s': 5.5}, lengths=[6, 8],
               finishes=['SS', 'SS-BO'])],
         ['keystone_standoff'], [],
         'Keystone page 67, 5.5 mm across flats, M3 thread, female both ends. '
         '6 mm and 8 mm are shorter than 19 mm, so the thread runs through. '
         'The bore is the nominal diameter, the same simplification as a nut.'),
]
PART_MCMASTER = {
    'NHX': 'Hex Nuts', 'NHR': 'Regular Hex Nuts', 'NTH': 'Thin-Profile Hex Nuts', 'NNL': 'Nylon-Insert Locknuts',
    'HFF': 'Female Threaded Hex Standoffs',
    'NFL': 'Flange Nuts',
    'NSF': 'Serrated Flange Nuts', 'WGP': 'General Purpose Washers', 'WSA': 'SAE Washers', 'WUS': 'USS Washers',
    'WOV': 'Oversized Washers', 'WSL': 'Split Lock Washers', 'WTE': 'Tooth Lock Washers (external)',
    'WTI': 'Tooth Lock Washers (internal)', 'NTL': 'Top-Lock Distorted-Thread Locknuts',
    'NTN': 'Thin-Profile Nylon-Insert Locknuts', 'NCP': 'Coupling Nuts', 'NCA': 'Cap Nuts', 'NWG': 'Wing Nuts',
    'NSQ': 'Square Nuts', 'WTK': 'Oversized Washers (thick, DIN 7349)',
}
for _p in PARTS:
    _p['mcmaster'] = PART_MCMASTER[_p['code'].rsplit('-', 1)[0]]
    _p['mcmaster_url'] = _p['source'].split(' ')[0]


# ---------- Extra materials (Daniel 2026-11-17) ----------
# Plain Steel, Zinc Plated, Grade 8 (inch only) and Class 10.9 (metric only), plus Class 10 for the metric nuts
# that mate with Class 10.9 screws. A type gets a material only where McMaster-Carr sells that type in it,
# checked 2026-11-17 on McMaster category pages filtered by finish or strength grade (see MATERIAL_SOURCES and
# docs/SOURCES.md). The check is per type, not per size. Types left off a material are listed in
# docs/SOURCES.md with the reason.
MCM = 'https://www.mcmaster.com/products/'
MATERIAL_SOURCES = {
    'STL': [MCM + 'hex-head-screws/finish~unfinished/', MCM + 'hex-nuts/finish~unfinished/',
            MCM + 'washers/finish~unfinished/'],
    'ZN': [MCM + 'socket-head-screws/finish~zinc-plated/', MCM + 'socket-head-screws/finish~zinc-plated/socket-head-profile~low/',
           MCM + 'rounded-head-screws/finish~zinc-plated/', MCM + 'hex-head-screws/finish~zinc-plated/',
           MCM + 'set-screws/finish~zinc-plated/tip-type~cup/', MCM + 'set-screws/finish~zinc-plated/tip-type~cone/',
           MCM + 'tapping-screws/finish~zinc-plated/', MCM + 'hex-nuts/finish~zinc-plated/',
           MCM + 'lock-nuts/finish~zinc-plated/', MCM + 'flange-nuts/finish~zinc-plated/',
           MCM + 'coupling-nuts/finish~zinc-plated/', MCM + 'cap-nuts/finish~zinc-plated/',
           MCM + 'wing-nuts/finish~zinc-plated/', MCM + 'square-nuts/finish~zinc-plated/',
           MCM + 'washers/finish~zinc-plated/', MCM + 'lock-washers/finish~zinc-plated/'],
    'GR8': [MCM + 'hex-head-screws/fastener-strength-grade-class~sae-grade-8/',
            MCM + 'hex-nuts/fastener-strength-grade-class~sae-grade-8/',
            MCM + 'lock-nuts/fastener-strength-grade-class~sae-grade-8/',
            MCM + 'flange-nuts/fastener-strength-grade-class~sae-grade-8/',
            MCM + 'washers/fastener-strength-grade-class~sae-grade-8/'],
    'CL10.9': [MCM + 'hex-head-screws/fastener-strength-grade-class~class-10-9/',
               MCM + 'socket-head-screws/fastener-strength-grade-class~class-10-9/',
               MCM + 'flat-head-screws/fastener-strength-grade-class~class-10-9/'],
    'CL10': [MCM + 'hex-nuts/fastener-strength-grade-class~class-10/'],
}
EXTRA_FINISHES = {
    # screws
    'SSH': ['ZN', 'CL10.9'], 'SBH': ['ZN', 'CL10.9'], 'SFH': ['ZN', 'CL10.9'], 'SLH': ['ZN'],
    'HHB': ['STL', 'ZN', 'GR8', 'CL10.9'], 'SSC': ['ZN'], 'SSN': ['ZN'], 'SPH': ['ZN'], 'SCH': ['ZN'],
    'SBF': ['ZN'], 'STP': ['ZN'],
    # nuts
    'NHX': ['STL', 'ZN', 'GR8', 'CL10'], 'NTH': ['STL', 'ZN'], 'NNL': ['ZN', 'GR8'], 'NTN': ['ZN', 'GR8'],
    'NTL': ['ZN'], 'NFL': ['ZN', 'GR8', 'CL10'], 'NSF': ['ZN', 'GR8', 'CL10'], 'NCP': ['ZN', 'GR8', 'CL10'],
    'NCA': ['ZN'], 'NWG': ['ZN'], 'NSQ': ['ZN'],
    # washers
    'WGP': ['STL', 'ZN'], 'WSA': ['STL', 'ZN', 'GR8'], 'WUS': ['STL', 'ZN', 'GR8'], 'WOV': ['STL', 'ZN', 'GR8'],
    'WSL': ['ZN'], 'WTE': ['ZN'], 'WTI': ['ZN'],
}
# Left off on purpose (reason shown in docs/SOURCES.md).
LEFT_OFF = [
    ('Grade 8 on socket, button, flat and low-profile screws, set screws, pan, cheese and sheet metal screws',
     'Grade 8 is a hex bolt grade; McMaster lists no Grade 8 socket or machine screws (the Grade 8 filter does not exist on those pages).'),
    ('Class 10.9 on set screws, low-profile socket head, pan, cheese and sheet metal screws',
     'Not found on McMaster with a Class 10.9 filter (set screws are hardness rated, 45H).'),
    ('Class 10.9 and Class 10 on washers', 'Washers are not rated in property classes.'),
    ('Class 10.9 on nuts', 'Nuts use Class 10 (offered instead) to mate with Class 10.9 screws.'),
    ('Plain Steel on socket, button, flat and low-profile screws, set screws, pan, cheese and sheet metal screws',
     'McMaster sells those in alloy steel (black oxide or zinc) or stainless; unfinished plain steel only for hex bolts, hex nuts and flat washers.'),
    ('Zinc Plated on flat-tip, extended-tip and oval-tip set screws',
     'McMaster zinc-plated flat-tip set screws are magnetic-tip only; no zinc extended-tip or oval-tip found.'),
    ('Zinc Plated on thick washers (DIN 7349)', 'Not checked on McMaster.'),
    ('Grade 8 on thin hex nuts and top-lock nuts', 'Not listed under the McMaster Grade 8 filter.'),
    ('Plain Steel on locknuts, flange, coupling, cap, wing and square nuts, lock washers', 'Not checked on McMaster.'),
    ('Plain steel, zinc, Grade 8 and Class 10 on regular hex nuts',
     'McMaster hex-nut finish and class pages are the DIN 934 nuts already offered. The regular hex nut is ISO 4032 style 1.'),
    ('Zinc plated on metric thin nylon-insert locknuts',
     'McMaster zinc-plated thin nylon-insert locknuts are the inch family. The metric sizes are ISO 10511 and were not on that page.'),
]


def _apply_extra_finishes():
    for fam in FAMILIES + PARTS:
        extra = [k for k in EXTRA_FINISHES.get(fam['code'].rsplit('-', 1)[0], [])
                 if FINISHES[k].get('system') in (None, fam['system'])]
        fam['finishes'] = list(fam['finishes']) + [k for k in extra if k not in fam['finishes']]
        for row in fam['sizes']:
            if 'finishes' in row:
                row['finishes'] = list(row['finishes']) + [k for k in extra if k not in row['finishes']]


# Daniel 2026-11-17: type names with nouns capitalized and no standards in them (the standard stays in the
# 'standard' field for docs/SOURCES.md only). Flat head angle is dropped from the name: metric is always 90 and
# inch always 82, and the name must not carry dimensions.
def title_name(name):
    name = name.replace(', 90 deg', '').replace(', 82 deg', '')
    out = []
    for word in name.split(' '):
        out.append('-'.join(w[:1].upper() + w[1:] for w in word.split('-')))
    return ' '.join(out)


def _drop_finishes(code, keys):
    """Take finishes off one family after the per-type list is applied."""
    for fam in PARTS:
        if fam['code'] != code:
            continue
        fam['finishes'] = [k for k in fam['finishes'] if k not in keys]
        for row in fam['sizes']:
            if 'finishes' in row:
                row['finishes'] = [k for k in row['finishes'] if k not in keys]


_apply_extra_finishes()
# NTN is shared with the inch thin nylon-insert nut, which McMaster sells in zinc. The metric
# sizes are ISO 10511 and were not on that zinc page, so zinc is not offered on them.
_drop_finishes('NTN-M', ('ZN',))
_TOOLS = os.path.dirname(os.path.abspath(__file__))
if _TOOLS not in sys.path:
    sys.path.insert(0, _TOOLS)
import pem_press  # noqa: E402
SRC.update(pem_press.SOURCES)
PARTS.extend(pem_press.build_parts())
for _f in FAMILIES + PENDING + PARTS:
    _f['name'] = title_name(_f['name'])


def build():
    press = [p for p in PARTS if p.get('kind') == 'press-in']
    hardware = [p for p in PARTS if p.get('kind') != 'press-in']
    return {
        'schema': 2,
        'note': 'Generated by tools/build_catalog.py. Edit that file, not this one.',
        'sources': SRC,
        'finishes': FINISHES,
        'alloy_materials': ALLOY_MATERIAL,
        'families': FAMILIES,
        'pending_approval': PENDING,
        'parts': hardware,
        'press_in': press,
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
           'McMaster series and item numbers in this file are dimension sources only. '
           'Shop screws, nuts and washers never use a vendor number as the Fusion part number. '
           'Press-in parts do: the part number is the PEM designation.', '',
           '| Code | Type (McMaster name) | Standard | Dimensions | Lengths | Thread length | Alloy black oxide |',
           '|---|---|---|---|---|---|---|']
    for fam in FAMILIES + PENDING:
        src = fam['sources']
        name = fam['name'] + (' (pending approval, not offered)' if fam in PENDING else '')
        out.append('| %s | %s | %s | %s |' % (fam['code'], name, fam['standard'], ' | '.join(
            ', '.join(src.get(k, [])) for k in ('dims', 'lengths', 'thread', 'alloy'))))
    out += ['', '## Nuts and washers', '',
            'Dimensions follow McMaster-Carr 18-8 stock, cross-checked with the listed standard or maker sheet.',
           'Every size is offered in 18-8 SS and 18-8 SS-BO; McMaster is used for dimensions, not availability.', '',
            '| Code | McMaster name | Standard | Sizes | Dimension sources | Notes |',
            '|---|---|---|---|---|---|']
    for p in PARTS:
        if p.get('kind') == 'press-in':
            continue
        out.append('| %s | %s | %s | %s | %s | %s |' % (
            p['code'], p['mcmaster'], p['standard'], ', '.join(r['size'] for r in p['sizes']),
            ', '.join(p['sources']['dims']), p['notes'] or ''))
    out += ['', '## Press-in (PEM)', '',
            'Metric PEM self-clinching parts. The Fusion part number is the PEM designation. '
            'Hole size, hole tolerance and minimum sheet thickness are on every size. '
            'Sizes PEM does not list are left out (see tools/pem_press.py OMITTED).', '',
            '| Code | Type | Sizes | Citation |', '|---|---|---|---|']
    for p in PARTS:
        if p.get('kind') != 'press-in':
            continue
        out.append('| %s | %s | %s | %s |' % (
            p['code'], p['name'], ', '.join(r['size'] for r in p['sizes']), p['citation']))
    out += ['', '## Short inch set screw socket depths', '',
            'These McMaster lengths are shorter than Holo-Krome Table 13 column B and are not in Table 14. The '
            'socket uses the size\'s standard depth (Table 13 TH), cut back only where it would leave less than '
            '0.25 x nominal diameter of metal above the point. Depth source: hk_tech Table 13 (copied, not a '
            'published value for these lengths).', '',
            '| Type | Size | Length (in) | Table 13 TH (in) | Depth used (in) |', '|---|---|---|---|---|']
    out += ['| %s | %s | %g | %.3f | %.3f%s |' % (fam, s, L, th, t, ' (cut back for the point)' if t < th else '')
            for fam, s, L, th, t in sorted({(PT_CODE[p], s, L, th, t) for p, s, L, th, t in SHORT_T})]
    out += ['', '## Materials', '',
            'Materials offered per type (checked on McMaster-Carr 2026-11-17, per type, not per size). Codes are the '
            'shop part number finish codes; STL, ZN, GR8, CL10.9, CL10 and ALLOY-BO are made-up codes.', '',
            '| Code | Description words | Fusion material name | Physical properties from |', '|---|---|---|---|']
    out += ['| %s | %s | %s | %s |' % (v['code'], v.get('desc_name', v['name']), v['material'], v['base']) for v in FINISHES.values()]
    out += ['', '| Type | Extra materials |', '|---|---|']
    out += ['| %s | %s |' % (k, ', '.join(v)) for k, v in EXTRA_FINISHES.items()]
    out += ['', 'McMaster pages used:', '']
    out += ['- %s: %s' % (k, ' , '.join(v)) for k, v in MATERIAL_SOURCES.items()]
    out += ['', 'Left off:', ''] + ['- %s. %s' % (a, b) for a, b in LEFT_OFF]
    out += ['', '## Source keys', '', '| Key | Source |', '|---|---|']
    out += ['| %s | %s |' % (k, v) for k, v in SRC.items()]
    out += ['', 'Lengths with no length source use the preferred series trimmed to an unverified range (TBD).',
            'The add-in part number is always the shop smart code (type + size + length + finish), never a vendor number.', '']
    return '\n'.join(out)


if __name__ == '__main__':
    with open(path(), 'w', encoding='utf-8', newline='\n') as f:
        f.write(render())
    doc = os.path.join(os.path.dirname(os.path.dirname(path())), '..', 'docs', 'SOURCES.md')
    with open(os.path.normpath(doc), 'w', encoding='utf-8', newline='\n') as f:
        f.write(sources_md())
    print('wrote', path(), 'and docs/SOURCES.md')
