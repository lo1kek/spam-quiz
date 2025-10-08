"""Vercel entrypoint that exposes the Flask WSGI application."""

from app import app as _flask_app

app = _flask_app
