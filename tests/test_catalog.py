import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'SRFastener'))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import build_catalog  # noqa: E402
import fastener_core as fc  # noqa: E402

CAT = fc.load_catalog()


def test_catalog_json_is_generated():
    with open(build_catalog.path(), encoding='utf-8') as f:
        assert f.read() == build_catalog.render(), 'run python tools/build_catalog.py'


def test_every_family_cites_a_source_and_has_sizes():
    for fam in CAT['families'] + CAT['pending_approval']:
        assert fam['source'].startswith('https://'), fam['code']
        assert fam['sources']['dims'], fam['code']
        for keys in fam['sources'].values():
            for k in keys:
                assert CAT['sources'][k].startswith('https://'), (fam['code'], k)
        if any('ALLOY-BO' in r.get('grade', {}) for r in fam['sizes']):
            assert fam['sources']['alloy'], fam['code']
        assert fam['sizes'], fam['code']
        for row in fam['sizes']:
            assert row['lengths'], (fam['code'], row['size'])


def test_part_numbers_unique():
    seen = set()
    for fam in CAT['families']:
        for row in fam['sizes']:
            for L in row['lengths']:
                for fk in fc.finishes_for(CAT, fam, row):
                    pn = fc.part_number(fam, row, L, fk)
                    assert pn not in seen
                    seen.add(pn)


def test_heads_bigger_than_shank_and_key_fits():
    for fam in CAT['families']:
        for row in fam['sizes']:
            dims = row['dims']
            if 'dk' in dims and 's' in dims:
                assert dims['dk'] > row['d'], (fam['code'], row['size'])
                assert dims['s'] < row['d'] * 1.2 + (dims['dk'] - row['d']), (fam['code'], row['size'])
                assert 't' not in dims and 't_by_length' not in dims, (fam['code'], row['size'])
            if fam['head'] == 'hex':
                assert dims['s'] > row['d']
            if fam['head'] == 'set':
                assert dims.get('dp', 0.0) < row['d'] and dims['s'] < row['d']


def test_banned_words():
    for root, _, files in os.walk(ROOT):
        if '.git' in root or 'cache' in root:
            continue
        for name in files:
            if name.endswith(('.py', '.md', '.json')):
                with open(os.path.join(root, name), encoding='utf-8') as f:
                    assert 'head' + 'less' not in f.read().lower(), name
