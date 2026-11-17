"""Where the SR Fastener button goes. Pure Python (no adsk import) so it can be unit tested.

The button can sit on any number of Fusion toolbar panels. The list comes from panels.json in the settings
folder (%APPDATA%/SRFastener/panels.json); if that file is missing or unreadable the defaults below are used.
Each entry:
  workspace  Fusion workspace id (default "FusionSolidEnvironment", the Design workspace)
  tab        toolbar tab id the panel is on (default "SolidTab"); used to find or create the panel
  panel      toolbar panel id, e.g. "InsertPanel", "SolidScriptsAddinsPanel", or a new id like "SRToolsPanel"
  name       panel name shown in Fusion; only needed when the panel is created
  create     true: create the panel on the tab if it does not exist (removed on stop when empty)
  promote    true: also show the button on the panel face, not only in its drop-down
See panels.example.json in the repo.
"""
import json

SR_TOOLS = {'workspace': 'FusionSolidEnvironment', 'tab': 'SolidTab', 'panel': 'SRToolsPanel',
            'name': 'SR Tools', 'create': True, 'promote': True}
DEFAULT_PANELS = [
    {'workspace': 'FusionSolidEnvironment', 'tab': 'SolidTab', 'panel': 'InsertPanel', 'promote': True},
    dict(SR_TOOLS),
    {'workspace': 'FusionSolidEnvironment', 'tab': 'ToolsTab', 'panel': 'SolidScriptsAddinsPanel', 'promote': False},
]
_KEYS = {'workspace': str, 'tab': str, 'panel': str, 'name': str, 'create': bool, 'promote': bool}


def normalize(entries):
    """Validate a list of panel entries; bad entries are skipped and reported. Returns (specs, problems)."""
    specs, problems, seen = [], [], set()
    if not isinstance(entries, list):
        return [], ['"panels" must be a list']
    for i, e in enumerate(entries):
        if isinstance(e, str):
            e = {'panel': e}
        if not isinstance(e, dict) or not isinstance(e.get('panel'), str) or not e['panel'].strip():
            problems.append('entry %d: needs a "panel" id' % (i + 1))
            continue
        bad = [k for k, t in _KEYS.items() if k in e and not isinstance(e[k], t)]
        unknown = [k for k in e if k not in _KEYS]
        if bad or unknown:
            problems.append('entry %d: %s' % (i + 1, ', '.join(['bad type for %s' % k for k in bad] +
                                                             ['unknown key %s' % k for k in unknown])))
            continue
        s = {'workspace': e.get('workspace', 'FusionSolidEnvironment'), 'tab': e.get('tab', 'SolidTab'),
             'panel': e['panel'].strip(), 'name': e.get('name', e['panel'].strip()),
             'create': e.get('create', False), 'promote': e.get('promote', False)}
        key = (s['workspace'], s['panel'])
        if key in seen:
            problems.append('entry %d: %s is listed twice' % (i + 1, s['panel']))
            continue
        seen.add(key)
        specs.append(s)
    return specs, problems


def load(path):
    """Panel specs from panels.json, or the defaults when the file is missing, unreadable or lists nothing valid."""
    try:
        with open(path, encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        return normalize(DEFAULT_PANELS)[0], []
    except Exception as exc:  # noqa: BLE001
        return normalize(DEFAULT_PANELS)[0], ['%s: %s (using the default panels)' % (path, exc)]
    specs, problems = normalize(data.get('panels') if isinstance(data, dict) else data)
    if not specs:
        return normalize(DEFAULT_PANELS)[0], problems + ['no usable panels listed (using the default panels)']
    return specs, problems
