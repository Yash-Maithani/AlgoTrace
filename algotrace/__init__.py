"""AlgoTrace: sorting, searching and graph algorithms played one step at a time.

    algorithms/   the algorithms, plain Python that yields teacher steps
    routes/       the pages and the /run_* endpoints, one blueprint per family
    core/         the step builder, gzip, the rate limit, and the public site
                  setup (meta tags, robots, sitemap, error pages, headers)
    catalog.py    which algorithms exist, in what order, and the counts
    templates/, static/

create_app() builds the app; wsgi.py calls it once for the production servers,
and `flask --app algotrace run` finds it for local development.
"""
from flask import Flask

from .catalog import deep_links
from .core.compression import init_compression
from .core.siteconfig import init_site
from .routes import register_blueprints


def create_app():
    app = Flask(__name__)
    # gzip first: after_request hooks run in reverse order of registration, so
    # it runs last and compresses the response every other hook has finished.
    init_compression(app)
    register_blueprints(app)
    # Robots, sitemap, meta tags, error pages, security and cache headers.
    init_site(app, deep_links)
    return app
