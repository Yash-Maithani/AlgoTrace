"""gzip for large JSON and HTML responses, standard library only.

A run is a list of steps, one per comparison or write, and the list is large:
about 7 MB for a bubble sort of 100 values and 11 MB for a big Floyd-Warshall
run. It is also highly repetitive JSON, so gzip takes it to a few percent of
its size. Only the standard library is used, and the step format is untouched:
the browser decompresses before any of this site's code sees the body.
"""
import gzip

from flask import request

COMPRESSIBLE_TYPES = ("application/json", "text/html")
MIN_COMPRESS_BYTES = 1024


def client_accepts_gzip(header):
    """True if an Accept-Encoding header allows gzip: named with a quality above
    zero, or covered by `*` and not refused by name."""
    named = None
    star = None
    for part in header.split(","):
        coding, _, params = part.strip().partition(";")
        quality = 1.0
        params = params.strip()
        if params.startswith("q="):
            try:
                quality = float(params[2:])
            except ValueError:
                quality = 0.0
        coding = coding.strip().lower()
        if coding in ("gzip", "x-gzip"):
            named = quality > 0
        elif coding == "*":
            star = quality > 0
    return named if named is not None else bool(star)


def compress_response(response):
    """gzip JSON and HTML bodies over 1 KB for a client that accepts it.

    Vary: Accept-Encoding goes on every response of these types, compressed or
    not, so a cache never hands a gzipped body to a client that cannot read it.
    """
    if response.mimetype not in COMPRESSIBLE_TYPES:
        return response
    response.vary.add("Accept-Encoding")

    if (response.status_code != 200 or response.direct_passthrough
            or response.is_streamed or "Content-Encoding" in response.headers):
        return response
    if not client_accepts_gzip(request.headers.get("Accept-Encoding", "")):
        return response

    body = response.get_data()
    if len(body) <= MIN_COMPRESS_BYTES:
        return response

    # mtime=0 keeps the bytes the same for the same body, which suits caches
    # and tests; level 6 is the usual speed against size trade.
    response.set_data(gzip.compress(body, compresslevel=6, mtime=0))
    response.headers["Content-Encoding"] = "gzip"
    response.headers["Content-Length"] = str(len(response.get_data()))
    return response


def init_compression(app):
    """Register the hook. create_app calls this before anything else adds an
    after_request hook, so it runs last, on the finished response."""
    app.after_request(compress_response)
