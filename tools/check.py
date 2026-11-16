"""Repo checks: catalog up to date, tests pass, no secrets, machine paths or banned words. Exit 1 on any failure."""
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP_DIRS = {'.git', '__pycache__', '.pytest_cache', '.venv'}
BAD = [
    (re.compile(r'[A-Za-z]:\\\\?Users\\\\?[A-Za-z]', re.I), 'Windows home path'),
    (re.compile(r'/home/[a-z]'), 'Linux home path'),
    (re.compile(r'gh[pousr]_[A-Za-z0-9]{20,}'), 'GitHub token'),
    (re.compile(r'AKIA[0-9A-Z]{16}'), 'AWS key'),
    (re.compile(r'-----BEGIN [A-Z ]*PRIVATE KEY-----'), 'private key'),
    (re.compile('head' + 'less', re.I), 'banned word'),
]
BAD_EXT = ('.step', '.stp', '.f3d', '.sldprt', '.iges', '.igs', '.x_t', '.sat')


def scan():
    errors = []
    for root, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in files:
            path = os.path.join(root, name)
            rel = os.path.relpath(path, ROOT)
            if name.lower().endswith(BAD_EXT):
                errors.append('%s: vendor/CAD file type is not allowed in this public repo' % rel)
                continue
            if name.endswith(('.png', '.ico')):
                continue
            try:
                text = open(path, encoding='utf-8').read()
            except UnicodeDecodeError:
                continue
            for rx, what in BAD:
                if rel == os.path.join('tools', 'check.py') and what == 'banned word':
                    continue
                if rx.search(text):
                    errors.append('%s: %s' % (rel, what))
    return errors


def main():
    errors = scan()
    sys.path.insert(0, os.path.join(ROOT, 'tools'))
    import build_catalog
    with open(build_catalog.path(), encoding='utf-8') as f:
        if f.read() != build_catalog.render():
            errors.append('catalog.json is stale: run python tools/build_catalog.py')
    rc = subprocess.call([sys.executable, '-m', 'pytest', '-q', os.path.join(ROOT, 'tests')])
    if rc:
        errors.append('pytest failed')
    for e in errors:
        print('FAIL', e)
    print('checks: %s' % ('FAIL' if errors else 'PASS'))
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
