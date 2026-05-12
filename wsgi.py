"""
WSGI entrypoint for production servers (Gunicorn, Waitress).

    gunicorn --bind 0.0.0.0:5000 --workers 1 --threads 8 wsgi:app
"""

from ai_smart_assistant.app import create_app

app = create_app()
