import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'SRFastener'))
import panels as sp  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_defaults_put_the_button_on_more_than_one_panel(tmp_path):
    specs, problems = sp.load(str(tmp_path / 'missing.json'))
    assert problems == []
    ids = [s['panel'] for s in specs]
    assert ids == ['InsertPanel', 'SRToolsPanel', 'SolidScriptsAddinsPanel']
    sr = specs[1]
    assert sr['create'] and sr['name'] == 'SR Tools' and sr['tab'] == 'SolidTab' and sr['promote']


def test_settings_file_adds_panels(tmp_path):
    p = tmp_path / 'panels.json'
    p.write_text(json.dumps({'panels': ['InsertPanel', {'panel': 'SolidCreatePanel', 'promote': True},
                                        {'workspace': 'FusionSolidEnvironment', 'tab': 'SolidTab',
                                         'panel': 'SRToolsPanel', 'name': 'SR Tools', 'create': True}]}))
    specs, problems = sp.load(str(p))
    assert problems == []
    assert [s['panel'] for s in specs] == ['InsertPanel', 'SolidCreatePanel', 'SRToolsPanel']
    assert specs[0]['workspace'] == 'FusionSolidEnvironment' and specs[0]['create'] is False
    assert specs[1]['promote'] is True


def test_bad_entries_are_reported_and_skipped(tmp_path):
    p = tmp_path / 'panels.json'
    p.write_text(json.dumps({'panels': ['InsertPanel', 'InsertPanel', {'name': 'x'}, {'panel': 'A', 'promote': 'yes'},
                                        {'panel': 'B', 'colour': 1}]}))
    specs, problems = sp.load(str(p))
    assert [s['panel'] for s in specs] == ['InsertPanel']
    assert len(problems) == 4


def test_unreadable_or_empty_file_falls_back_to_defaults(tmp_path):
    p = tmp_path / 'panels.json'
    p.write_text('{not json')
    specs, problems = sp.load(str(p))
    assert len(specs) == len(sp.DEFAULT_PANELS) and problems
    p.write_text(json.dumps({'panels': []}))
    specs, problems = sp.load(str(p))
    assert len(specs) == len(sp.DEFAULT_PANELS) and problems


def test_example_file_is_valid():
    specs, problems = sp.load(os.path.join(ROOT, 'panels.example.json'))
    assert problems == [] and len(specs) == 4


def test_addin_tracks_and_removes_every_control():
    src = open(os.path.join(ROOT, 'SRFastener', 'SRFastener.py'), encoding='utf-8').read()
    stop = src[src.index('def stop('):]
    assert '_remove_controls(ui)' in stop and "commandDefinitions.itemById(CMD_ID)" in stop
    assert 'PANELS = [' not in src  # no hard-coded panel list left
