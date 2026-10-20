"""gzip for large JSON and HTML responses, standard library only.

A 100 value bubble sort answers with about 7 MB of steps. The step format is not
touched: these tests hold the decompressed body to the uncompressed one, byte
for byte, and the headers to what a cache and a browser need.
"""
import gzip
import json
import os
import random
import sys

import pytest

from app import app, _client_accepts_gzip

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GZIP = {'Accept-Encoding': 'gzip, deflate, br'}


@pytest.fixture(scope='module')
def client():
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c


def strip_nonce(body):
    import re
    return re.sub(rb'nonce="[^"]*"|nonce-[A-Za-z0-9_-]+', b'', body)


def bubble_100():
    rng = random.Random(5)
    return {'algorithm': 'Bubble Sort', 'values': ', '.join(str(rng.randint(1, 99)) for _ in range(100))}


def floyd(k=14):
    rng = random.Random(5)
    nodes = [chr(65 + i) for i in range(k)]
    edges = [[nodes[i], nodes[j], rng.randint(1, 9)] for i in range(k) for j in range(i + 1, k) if rng.random() < 0.7]
    return {'nodes': nodes, 'edges': edges}


# ---------------------------------------------------------------------------
# What is sent
# ---------------------------------------------------------------------------

def test_a_large_run_is_gzipped_for_a_client_that_accepts_it(client):
    plain = client.post('/run_sort', json=bubble_100())
    packed = client.post('/run_sort', json=bubble_100(), headers=GZIP)

    assert packed.headers['Content-Encoding'] == 'gzip'
    assert 'Content-Encoding' not in plain.headers
    assert len(plain.data) > 5_000_000
    assert len(packed.data) < len(plain.data) / 10                  # a few percent of the size


def test_the_headers_are_correct(client):
    packed = client.post('/run_sort', json=bubble_100(), headers=GZIP)

    assert packed.headers['Content-Length'] == str(len(packed.data))
    assert 'Accept-Encoding' in packed.headers['Vary']
    assert packed.mimetype == 'application/json'
    assert packed.status_code == 200


def test_the_decompressed_body_is_exactly_the_uncompressed_one(client):
    plain = client.post('/run_sort', json=bubble_100())
    packed = client.post('/run_sort', json=bubble_100(), headers=GZIP)

    assert gzip.decompress(packed.data) == plain.data
    # So the step format is the one it always was.
    steps = json.loads(gzip.decompress(packed.data))['steps']
    assert steps[0].keys() >= {'array', 'compared', 'action', 'indices', 'values', 'line', 'vars', 'explain'}


def test_a_graph_run_is_compressed_and_unchanged_too(client):
    plain = client.post('/run_floyd_warshall', json=floyd())
    packed = client.post('/run_floyd_warshall', json=floyd(), headers=GZIP)

    assert len(plain.data) > 1_000_000 and packed.headers['Content-Encoding'] == 'gzip'
    assert gzip.decompress(packed.data) == plain.data
    assert len(packed.data) < len(plain.data) / 10


def test_html_pages_over_a_kilobyte_are_compressed(client):
    for path in ('/', '/sorting', '/learn', '/graph?algo=bfs', '/big-o', '/privacy'):
        plain = client.get(path)
        packed = client.get(path, headers=GZIP)
        assert packed.headers['Content-Encoding'] == 'gzip', path
        assert packed.mimetype == 'text/html'
        # The page carries a fresh CSP nonce per request, so compare with it removed.
        assert strip_nonce(gzip.decompress(packed.data)) == strip_nonce(plain.data), path
        assert packed.headers['Content-Length'] == str(len(packed.data))


# ---------------------------------------------------------------------------
# What is not
# ---------------------------------------------------------------------------

def test_no_gzip_without_the_header_or_when_refused(client):
    for headers in ({}, {'Accept-Encoding': 'identity'}, {'Accept-Encoding': 'deflate, br'},
                    {'Accept-Encoding': 'gzip;q=0'}, {'Accept-Encoding': 'gzip;q=0, *;q=1'}):
        reply = client.post('/run_sort', json=bubble_100(), headers=headers)
        assert 'Content-Encoding' not in reply.headers, headers
        json.loads(reply.data)                                           # still plain JSON


def test_a_small_body_is_left_alone(client):
    reply = client.post('/run_sort', json={'algorithm': 'No Such Sort'}, headers=GZIP)

    assert reply.status_code == 400 and len(reply.data) <= 1024
    assert 'Content-Encoding' not in reply.headers
    assert 'Accept-Encoding' in reply.headers['Vary']                    # but a cache is still told


def test_a_body_of_exactly_one_kilobyte_is_not_compressed():
    """The limit is "over 1 KB": 1024 bytes stays plain, 1025 is compressed."""
    from flask import Response
    from app import compress_response

    def through(size):
        with app.test_request_context('/', headers=GZIP):
            return compress_response(Response('x' * size, mimetype='text/html'))

    assert 'Content-Encoding' not in through(1024).headers
    big = through(1025)
    assert big.headers['Content-Encoding'] == 'gzip' and gzip.decompress(big.get_data()) == b'x' * 1025
    assert big.headers['Content-Length'] == str(len(big.get_data()))


def test_static_files_and_errors_are_not_touched(client):
    css = client.get('/static/styles.css', headers=GZIP)
    missing = client.get('/no-such-page', headers=GZIP)

    assert css.status_code == 200 and 'Content-Encoding' not in css.headers      # not JSON or HTML
    assert missing.status_code == 404 and 'Content-Encoding' not in missing.headers


def test_a_response_already_encoded_is_not_encoded_twice(client):
    once = client.post('/run_sort', json=bubble_100(), headers=GZIP)
    # Run the hook again over the same response, as a second layer would.
    from app import compress_response
    with app.test_request_context('/run_sort', headers=GZIP):
        again = compress_response(once)
    assert again.headers['Content-Encoding'] == 'gzip' and gzip.decompress(again.get_data())[:1] == b'{'


@pytest.mark.parametrize('header,expected', [
    ('gzip', True), ('gzip, deflate, br', True), ('GZIP', True), ('x-gzip', True),
    ('gzip;q=0.5', True), ('gzip;q=0', False), ('gzip; q=0', False),
    ('*', True), ('*;q=0', False), ('*, gzip;q=0', False), ('deflate', False), ('', False),
    ('identity', False), ('gzip;q=bogus', False),
])
def test_the_accept_encoding_parser(header, expected):
    assert _client_accepts_gzip(header) is expected


def test_the_hook_uses_only_the_standard_library():
    source = open(os.path.join(ROOT, 'app.py'), encoding='utf-8').read()
    requirements = open(os.path.join(ROOT, 'requirements.txt'), encoding='utf-8').read().lower()

    assert 'import gzip' in source
    assert 'flask-compress' not in requirements and 'brotli' not in requirements
    assert source.count('@app.after_request') == 1
