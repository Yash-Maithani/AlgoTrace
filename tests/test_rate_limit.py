"""The per-address rate limit on /run_*, standard library only (ratelimit.py).

tests/conftest.py turns the limit off for the rest of the suite, so each test here
turns it on for itself through app.config and puts it back.
"""
import json
import os
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import ratelimit
from app import app

SORT = {'algorithm': 'Bubble Sort', 'values': [3, 1, 2]}
RUN_ENDPOINTS = ['/run_sort', '/run_search', '/run_bfs', '/run_dfs', '/run_dijkstra', '/run_prim',
                 '/run_kruskal', '/run_floyd_warshall', '/run_bellman_ford', '/run_topological_sort',
                 '/run_astar']


@pytest.fixture
def limited():
    """The limit on, at 5 a minute, with nobody counted yet."""
    old = app.config['RATE_LIMIT_PER_MINUTE']
    app.config['RATE_LIMIT_PER_MINUTE'] = 5
    app.extensions['rate_limiter'].reset()
    yield app.test_client()
    app.config['RATE_LIMIT_PER_MINUTE'] = old
    app.extensions['rate_limiter'].reset()


class Clock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


def test_the_limiter_counts_a_sliding_minute():
    clock = Clock()
    limiter = ratelimit.Limiter(clock)
    assert [limiter.check('a', 3) for _ in range(3)] == [0, 0, 0]
    assert limiter.check('a', 3) == 60                 # the fourth waits the whole minute
    clock.now += 20
    assert limiter.check('a', 3) == 40                 # and the wait shrinks as the minute passes
    clock.now += 40
    assert limiter.check('a', 3) == 0                  # the first three have aged out together
    assert [limiter.check('a', 3) for _ in range(2)] == [0, 0]
    assert limiter.check('a', 3) > 0


def test_one_address_does_not_use_up_another():
    limiter = ratelimit.Limiter(Clock())
    for _ in range(3):
        limiter.check('a', 3)
    assert limiter.check('a', 3) > 0
    assert limiter.check('b', 3) == 0


def test_the_wait_is_never_zero_and_never_over_the_window():
    clock = Clock()
    limiter = ratelimit.Limiter(clock)
    limiter.check('a', 1)
    for step in (0, 0.2, 30, 59.5, 59.99):
        clock.now = 1000.0 + step
        wait = limiter.check('a', 1)
        assert 1 <= wait <= 60


def test_idle_addresses_are_forgotten_past_the_cap(monkeypatch):
    monkeypatch.setattr(ratelimit, 'MAX_TRACKED', 10)
    clock = Clock()
    limiter = ratelimit.Limiter(clock)
    for i in range(10):
        limiter.check('old%d' % i, 5)
    clock.now += 61
    limiter.check('new', 5)
    assert list(limiter._seen) == ['new']


def test_the_sixth_run_in_a_minute_is_refused_with_json(limited):
    codes = [limited.post('/run_sort', json=SORT).status_code for _ in range(5)]
    assert 429 not in codes
    refused = limited.post('/run_sort', json=SORT)
    assert refused.status_code == 429
    assert refused.mimetype == 'application/json'
    body = refused.get_json()
    assert 'faster than this site allows' in body['error']
    assert body['retry_after'] == int(refused.headers['Retry-After'])
    assert 1 <= body['retry_after'] <= 60
    assert ('%d second' % body['retry_after']) in body['error']


def test_every_run_endpoint_shares_one_count_per_address(limited):
    for path in RUN_ENDPOINTS[:5]:
        assert limited.post(path, json={}).status_code != 429
    for path in RUN_ENDPOINTS:
        assert limited.post(path, json={}).status_code == 429, path


def test_a_refused_request_does_no_work(limited, monkeypatch):
    for _ in range(5):
        limited.post('/run_sort', json=SORT)
    import app as app_module
    called = []

    def spy(values, *args, **kwargs):
        called.append(1)
        return iter(())

    monkeypatch.setitem(app_module.sorting_algo_dict, 'Bubble Sort', spy)
    assert limited.post('/run_sort', json=SORT).status_code == 429
    assert called == []


def test_pages_and_static_files_are_never_limited(limited):
    for _ in range(5):
        limited.post('/run_sort', json=SORT)
    assert limited.post('/run_sort', json=SORT).status_code == 429
    for path in ('/', '/sorting', '/learn', '/robots.txt', '/site.webmanifest', '/static/styles.css'):
        assert limited.get(path).status_code == 200, path


def test_the_limit_can_be_turned_off(limited):
    app.config['RATE_LIMIT_PER_MINUTE'] = 0
    assert all(limited.post('/run_sort', json=SORT).status_code != 429 for _ in range(40))


def test_a_forged_forwarded_for_header_does_not_buy_a_fresh_count(limited):
    for _ in range(5):
        limited.post('/run_sort', json=SORT)
    forged = limited.post('/run_sort', json=SORT, headers={'X-Forwarded-For': '203.0.113.9'})
    assert forged.status_code == 429


def test_each_address_has_its_own_count(limited):
    for _ in range(5):
        limited.post('/run_sort', json=SORT, environ_overrides={'REMOTE_ADDR': '198.51.100.1'})
    assert limited.post('/run_sort', json=SORT, environ_overrides={'REMOTE_ADDR': '198.51.100.1'}).status_code == 429
    assert limited.post('/run_sort', json=SORT, environ_overrides={'REMOTE_ADDR': '198.51.100.2'}).status_code != 429


PROBE = r"""
import json, os
from app import app
c = app.test_client()
sort = {'algorithm': 'Bubble Sort', 'values': [3, 1, 2]}
def codes(headers, n):
    return [c.post('/run_sort', json=sort, headers=headers, environ_overrides={'REMOTE_ADDR': '10.0.0.1'}).status_code for _ in range(n)]
first = codes({'X-Forwarded-For': '203.0.113.7'}, 31)
other = codes({'X-Forwarded-For': '203.0.113.8'}, 1)
print(json.dumps({'limit': app.config['RATE_LIMIT_PER_MINUTE'], 'first': first, 'other': other}))
"""


def probe(extra_env):
    env = {k: v for k, v in os.environ.items()
           if k not in ('RATE_LIMIT_PER_MINUTE', 'TRUST_PROXY', 'SITE_URL')}
    env.update(extra_env)
    out = subprocess.run([sys.executable, '-c', PROBE], cwd=ROOT, env=env, capture_output=True, text=True, check=True)
    return json.loads(out.stdout.strip().splitlines()[-1])


def test_by_default_a_fresh_process_allows_30_a_minute_and_refuses_the_31st():
    result = probe({})
    assert result['limit'] == 30
    assert 429 not in result['first'][:30]
    assert result['first'][30] == 429
    assert result['other'] == [429]                    # without TRUST_PROXY the header changes nothing


def test_behind_a_trusted_proxy_the_forwarded_address_is_the_client():
    result = probe({'TRUST_PROXY': '1'})
    assert result['first'][30] == 429                  # 203.0.113.7 ran out
    assert result['other'] != [429]                    # 203.0.113.8 is somebody else


def test_the_limit_is_read_from_the_environment():
    assert probe({'RATE_LIMIT_PER_MINUTE': '10'})['first'][10] == 429
    assert 429 not in probe({'RATE_LIMIT_PER_MINUTE': '0'})['first']
    assert probe({'RATE_LIMIT_PER_MINUTE': 'lots'})['limit'] == 30      # nonsense falls back to the default


def test_the_environment_variable_is_documented():
    for name in ('README.md', os.path.join('project_documentation', 'Quick_Reference.md')):
        with open(os.path.join(ROOT, name), encoding='utf-8') as handle:
            assert 'RATE_LIMIT_PER_MINUTE' in handle.read(), name
    with open(os.path.join(ROOT, 'render.yaml'), encoding='utf-8') as handle:
        assert 'TRUST_PROXY' in handle.read()          # the real client address, not the proxy's
