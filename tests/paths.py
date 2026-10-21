"""Where things are, for every test and tool that reads a file.

pyproject.toml puts the repository root and tests/ on sys.path, so a test
imports the site (`from wsgi import app`, `from algotrace... import`) and
these names directly, from whichever folder it is in.
"""
import os

TESTS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(TESTS)
PACKAGE = os.path.join(ROOT, 'algotrace')

JS = os.path.join(TESTS, 'js')                  # the node checks the tests run
BASELINES = os.path.join(TESTS, 'baselines')    # responses recorded before the rebuild


def package_source():
    """All of the site's Python as one string, for the tests that check a
    pattern appears, or never appears, anywhere in the server code."""
    parts = []
    for dirpath, dirnames, filenames in os.walk(PACKAGE):
        dirnames[:] = sorted(d for d in dirnames if d not in ('static', 'templates', '__pycache__'))
        for name in sorted(filenames):
            if name.endswith('.py'):
                with open(os.path.join(dirpath, name), encoding='utf-8') as handle:
                    parts.append(handle.read())
    return '\n'.join(parts)
