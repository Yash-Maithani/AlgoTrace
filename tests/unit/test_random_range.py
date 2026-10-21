"""Phase 20, Step 0: one range for every random value on the site.

Random arrays (server side), the presets, Compare (which draws through the
presets) and the searching page's Random array all use whole numbers from 1
to RANDOM_MAX. That range sits inside the 0 to KEY_MAX Counting and Radix
Sort accept, so a generated or preset input runs on every sort, and /compare
with either of them on a side never refuses one.
"""
import json
import os
import shutil
import subprocess

import pytest

from paths import ROOT, package_source
from wsgi import app
from algotrace.algorithms.sorting.counting_sort import KEY_MAX
from algotrace.catalog import sorting_algo_dict
from algotrace.routes.sorting import RANDOM_MAX

NODE = shutil.which('node')


def read(*parts):
    with open(os.path.join(ROOT, *parts), encoding='utf-8') as f:
        return f.read()


@pytest.fixture(scope='module')
def client():
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c


def test_one_range_inside_the_keyed_sorts_range():
    assert RANDOM_MAX == 99 and 1 <= RANDOM_MAX <= KEY_MAX
    assert 'var RANDOM_MAX = 99;' in read('algotrace', 'static', 'js', 'presets.js')
    assert 'Math.random() * Presets.RANDOM_MAX' in read('algotrace', 'templates', 'searching.html')
    assert "Presets.generate('random'" in read('algotrace', 'static', 'js', 'compare.js')
    assert 'randint(1, 100)' not in package_source()


@pytest.mark.parametrize('name', sorted(sorting_algo_dict))
def test_server_random_arrays_stay_in_range(client, name):
    for _ in range(15):
        body = client.post('/run_sort', json={'algorithm': name, 'size': 100}).get_json()
        assert all(1 <= v <= RANDOM_MAX for v in body['array']), name


@pytest.mark.skipif(NODE is None, reason='node is not installed')
def test_every_preset_runs_on_every_sort(client):
    """Every preset at every size Compare and /sorting allow, on every sort:
    nothing is refused."""
    script = ("const P=require('./algotrace/static/js/presets.js');const out=[];"
              "for(const k of P.ORDER)for(const n of [5,12,30,64,100])for(let s=1;s<=6;s++)"
              "out.push(P.generate(k,n,s));console.log(JSON.stringify(out))")
    arrays = json.loads(subprocess.run([NODE, '-e', script], capture_output=True, text=True,
                                       cwd=ROOT, check=True).stdout)
    assert all(1 <= v <= RANDOM_MAX for a in arrays for v in a)
    for name in sorted(sorting_algo_dict):
        for values in arrays[::7]:
            r = client.post('/run_sort', json={'algorithm': name, 'values': values})
            assert r.status_code == 200, (name, r.get_json())
