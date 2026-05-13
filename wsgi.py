"""
WSGI entrypoint for production servers (Gunicorn, Waitress).
Includes WhiteNoise for serving static assets in production.
"""

import os
from ai_smart_assistant.app import create_app
from whitenoise import WhiteNoise

# Initialize the Flask app
app = create_app()

# Wrap with WhiteNoise to serve static files (CSS, JS, etc.)
# The assets folder is located in ai_smart_assistant/app/assets
static_dir = os.path.join(os.path.dirname(__file__), "ai_smart_assistant/app/assets")
app.wsgi_app = WhiteNoise(app.wsgi_app, root=static_dir, prefix="static/")
