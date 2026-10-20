"""WSGI entry point for a production server.

    gunicorn wsgi:app            (Linux, and Render)
    waitress-serve wsgi:app      (Windows)

`python app.py` is for local development only. Importing this module never
starts a server and never turns debug mode on.
"""
from app import app

__all__ = ["app"]
