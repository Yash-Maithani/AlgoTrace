"""WSGI entry point for a production server.

    gunicorn wsgi:app            (Linux, and Render)
    waitress-serve wsgi:app      (Windows)

For local development, `flask --app algotrace run --port 5002` (see README.md).
Importing this module never starts a server and never turns debug mode on.
"""
from algotrace import create_app

app = create_app()

__all__ = ["app"]
