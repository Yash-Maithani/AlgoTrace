"""The site's routes, as five blueprints: pages, sorting, searching, graphs, grid.

A Flask blueprint normally prefixes its endpoint names ("sorting.run_sort").
These keep the names the site has always used ("run_sort", "sorting_page"),
because the templates, the sitemap, the page descriptions and the /learn order
all build links with url_for on those names. URLs are unchanged either way.
"""
from flask import Blueprint
from flask.blueprints import BlueprintSetupState


class _UnprefixedSetupState(BlueprintSetupState):
    def add_url_rule(self, rule, endpoint=None, view_func=None, **options):
        self.app.add_url_rule(rule, endpoint or view_func.__name__, view_func, **options)


class SiteBlueprint(Blueprint):
    """A blueprint whose endpoints keep their bare names. It has no URL prefix
    and no hooks of its own; app-wide hooks use the app_* decorators."""

    def make_setup_state(self, app, options, first_registration=False):
        return _UnprefixedSetupState(self, app, options, first_registration)


def register_blueprints(app):
    from . import graphs, grid, pages, searching, sorting

    for module in (pages, sorting, searching, graphs, grid):
        app.register_blueprint(module.bp)
