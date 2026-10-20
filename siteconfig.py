"""Everything about running AlgoTrace as a public site, kept out of app.py.

  * the site name and the page descriptions used in meta tags
  * SITE_URL, the canonical address, read from the environment so a custom
    domain is a setting and not a code change
  * robots.txt and sitemap.xml, generated from the routes
  * the 404 and 500 pages, in the site's own layout
  * security headers, including a Content-Security-Policy with a nonce per
    request, and the cache headers that go with cache busted static files

app.py calls init_site(app, deep_links) once, after its routes exist.

Environment (all optional; see README.md):
  SITE_URL      https://example.com, no trailing slash. Without it, links are
                built from the address the request came to, which is right for
                local use and wrong behind a proxy.
  SECRET_KEY    Flask's secret key. The site keeps no sessions, so nothing needs
                it today; it is read from here so that a future feature never
                tempts anyone into committing one.
  FLASK_DEBUG   1 turns Flask's debug mode on (local development only).
  TRUST_PROXY   1 to believe X-Forwarded-Proto, X-Forwarded-Host and X-Forwarded-For
                from the one proxy in front, as on Render. The rate limit counts
                the client address that gives.
  RATE_LIMIT_PER_MINUTE   requests an address may make to /run_* in a minute
                (30 by default, 0 turns the limit off). See ratelimit.py.
"""
import hashlib
import os
import secrets

from flask import Response, abort, g, json, jsonify, render_template, request, url_for

from ratelimit import init_rate_limit

SITE_NAME = "AlgoTrace"
TAGLINE = "Watch algorithms run, step by step"
OG_IMAGE = "og-image.png"
ICONS = [("favicon-32.png", 32), ("icon-192.png", 192), ("icon-512.png", 512)]
THEME_COLOR = "#FAF8F5"                # --bg in styles.css, light; the layout's meta theme-color says the same
MAX_REQUEST_BYTES = 1_000_000          # the largest legitimate input is a few KB of text

DESCRIPTIONS = {
    "index": ("AlgoTrace plays sorting, searching and graph algorithms one step at a time, "
              "explains every move in plain language, and counts what each one costs."),
    "learn": ("Every algorithm on AlgoTrace in a suggested order, with its best and worst case "
              "time and the extra memory it needs, worked out from the code."),
    "sorting_page": ("Watch bubble, selection, insertion, heap, merge, quick, counting and radix "
                     "sort run on your own numbers, one comparison at a time, with the code and "
                     "the cost beside every step."),
    "compare_page": ("Run two sorting algorithms on the same input at once and see which one does "
                     "less work, step by step, with a counter for each."),
    "searching_page": ("Step through linear, binary and jump search on your own list, see exactly "
                       "which values are checked, and why a sorted list changes everything."),
    "graph_page": ("Step through breadth-first and depth-first search, Dijkstra, Prim, Kruskal, "
                   "Floyd-Warshall, Bellman-Ford, topological sort and A* on a graph or grid you draw."),
    "big_o_page": ("What O, Omega and Theta really mean, how to count steps from code, and why the "
                   "counter on a finished run and the textbook formula rarely match."),
    "privacy": ("What AlgoTrace stores in your browser (a theme, a code language and which "
                "guided tours you have seen, nothing sent to a server) and how to clear it."),
    "terms": "The terms for using AlgoTrace, a free learning tool.",
}



def site_url():
    """The public address, no trailing slash."""
    configured = os.environ.get("SITE_URL", "").strip().rstrip("/")
    return configured or request.host_url.rstrip("/")


def _file_hash(filename, static_folder, cache={}):
    """A short hash of a static file's bytes, for ?v= cache busting. Recomputed
    only when the file's modification time changes."""
    path = os.path.join(static_folder, filename)
    try:
        stamp = os.stat(path).st_mtime_ns
    except OSError:
        return None
    hit = cache.get(path)
    if hit and hit[0] == stamp:
        return hit[1]
    with open(path, "rb") as handle:
        digest = hashlib.sha256(handle.read()).hexdigest()[:12]
    cache[path] = (stamp, digest)
    return digest


def csp_for(nonce):
    """Scripts and styles from this site, plus the Google Fonts the stylesheet
    imports. Inline scripts and style blocks must carry the request's nonce. Style
    attributes (style="--v: 40") are allowed on their own, because they cannot
    run code."""
    return "; ".join([
        "default-src 'self'",
        "script-src 'self' 'nonce-%s'" % nonce,
        "style-src 'self' 'nonce-%s' https://fonts.googleapis.com" % nonce,
        "style-src-attr 'unsafe-inline'",
        "font-src 'self' https://fonts.gstatic.com",
        "img-src 'self' data:",
        "manifest-src 'self'",
        "connect-src 'self'",
        "object-src 'none'",
        "base-uri 'self'",
        "form-action 'self'",
        "frame-ancestors 'none'",
    ])


def _wants_json():
    return (request.method != "GET" or request.is_json
            or request.path.startswith(("/run_", "/generate_")))


def init_site(app, deep_links):
    """Wire the site setup into the app. `deep_links()` returns the extra
    entry points worth listing in the sitemap, as paths with a query string."""
    app.config["MAX_CONTENT_LENGTH"] = MAX_REQUEST_BYTES
    app.config["SEND_FILE_MAX_AGE_DEFAULT"] = None
    secret = os.environ.get("SECRET_KEY")
    if secret:
        app.config["SECRET_KEY"] = secret

    if os.environ.get("TRUST_PROXY") == "1":
        from werkzeug.middleware.proxy_fix import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    init_rate_limit(app)

    # --- cache busting: every url_for('static', ...) gets ?v=<hash of the file> ---
    @app.url_defaults
    def add_static_version(endpoint, values):
        if endpoint == "static" and "filename" in values and "v" not in values:
            digest = _file_hash(values["filename"], app.static_folder)
            if digest:
                values["v"] = digest

    # --- a nonce per request, and the values every page's head needs ---
    @app.before_request
    def make_nonce():
        g.csp_nonce = secrets.token_urlsafe(16)

    @app.before_request
    def refuse_oversized_requests():
        # Refused before any endpoint reads the body: the endpoints turn every
        # exception into their own 500, which would hide the real reason.
        if request.content_length is not None and request.content_length > MAX_REQUEST_BYTES:
            abort(413)

    @app.context_processor
    def page_context():
        base = site_url()
        endpoint = request.endpoint or ""
        # The pages that open on a chosen algorithm are different pages to a
        # search engine, so the choice stays in the canonical address.
        query = ""
        for key in ("algo", "algorithm"):
            value = request.args.get(key)
            if value and endpoint in ("graph_page", "sorting_page", "searching_page"):
                query = "?%s=%s" % (key, value.replace(" ", "+"))
        description = DESCRIPTIONS.get(endpoint, DESCRIPTIONS["index"])
        return {
            "csp_nonce": getattr(g, "csp_nonce", ""),
            "site_name": SITE_NAME,
            "tagline": TAGLINE,
            "meta_description": description,
            "canonical_url": base + request.path + query,
            "og_image_url": base + url_for("static", filename=OG_IMAGE),
        }

    # --- headers on every response ---
    @app.after_request
    def security_and_cache_headers(response):
        headers = response.headers
        headers["X-Content-Type-Options"] = "nosniff"
        headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        headers["X-Frame-Options"] = "DENY"
        if response.mimetype == "text/html" or request.endpoint == "static":
            headers["Content-Security-Policy"] = csp_for(getattr(g, "csp_nonce", secrets.token_urlsafe(16)))
        if request.endpoint == "static":
            if "v" in request.args:
                # The address changes with the file's contents, so it never goes stale.
                headers["Cache-Control"] = "public, max-age=31536000, immutable"
            else:
                headers["Cache-Control"] = "public, max-age=86400"
        elif response.mimetype == "text/html" and response.status_code == 200:
            headers["Cache-Control"] = "no-cache"          # revalidate, so a deploy shows at once
        return response

    # --- robots.txt and sitemap.xml ---
    @app.route("/robots.txt")
    def robots_txt():
        body = "\n".join([
            "User-agent: *",
            "Allow: /",
            "Disallow: /run_",
            "Disallow: /generate_random_graph",
            "",
            "Sitemap: %s/sitemap.xml" % site_url(),
            "",
        ])
        return Response(body, mimetype="text/plain")

    @app.route("/sitemap.xml")
    def sitemap_xml():
        base = site_url()
        paths = []
        for rule in app.url_map.iter_rules():
            if ("GET" in rule.methods and not rule.arguments and rule.endpoint != "static"
                    and rule.endpoint not in ("robots_txt", "sitemap_xml", "site_webmanifest")):
                paths.append(rule.rule)
        paths = sorted(set(paths), key=lambda p: (p != "/", p))
        paths += list(deep_links())
        lines = ['<?xml version="1.0" encoding="UTF-8"?>',
                 '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
        for path in paths:
            lines.append("  <url><loc>%s</loc></url>" % (base + path).replace("&", "&amp;"))
        lines.append("</urlset>")
        return Response("\n".join(lines) + "\n", mimetype="application/xml")

    # --- the web app manifest: name, colours and the icons, at the site root so its scope is the site ---
    @app.route("/site.webmanifest")
    def site_webmanifest():
        manifest = {
            "name": SITE_NAME,
            "short_name": SITE_NAME,
            "description": DESCRIPTIONS["index"],
            "start_url": "/",
            "scope": "/",
            "display": "standalone",
            "theme_color": THEME_COLOR,
            "background_color": THEME_COLOR,
            "icons": [{"src": url_for("static", filename=name), "sizes": "%dx%d" % (size, size),
                       "type": "image/png", "purpose": "any"} for name, size in ICONS[1:]],
        }
        return Response(json.dumps(manifest, indent=2) + "\n", mimetype="application/manifest+json")

    # --- error pages, in the site's layout; JSON for the endpoints that return JSON ---
    @app.errorhandler(404)
    def not_found(error):
        if _wants_json():
            return jsonify({"error": "Not found."}), 404
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def server_error(error):
        if _wants_json():
            return jsonify({"error": "Something went wrong on the server."}), 500
        return render_template("500.html"), 500

    @app.errorhandler(413)
    def too_large(error):
        return jsonify({"error": "That request is too large. Try a smaller input."}), 413
