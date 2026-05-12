#!/usr/bin/env python3
"""
NexusAI - Intelligent Code Assistant
Entry point for the Flask development server.

Usage:
    python run.py
    python run.py --port 8080
    python run.py --host 0.0.0.0

Production: use Gunicorn instead of this script:
    gunicorn --bind 0.0.0.0:5000 --workers 1 --threads 8 wsgi:app
"""

import argparse
import os
import sys

from ai_smart_assistant.app import create_app


def _is_production() -> bool:
    return os.environ.get("FLASK_ENV", "").lower() == "production" or (
        os.environ.get("NEXUS_PRODUCTION", "").lower() in ("1", "true", "yes")
    )


def main():
    """Parse arguments and start the NexusAI development server."""
    parser = argparse.ArgumentParser(
        description="NexusAI - Intelligent Code Assistant"
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind to (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port", type=int, default=5000, help="Port to listen on (default: 5000)"
    )
    parser.add_argument(
        "--no-debug", action="store_true", help="Disable debug mode"
    )
    parser.add_argument(
        "--allow-insecure-dev-server",
        action="store_true",
        help="Allow Flask built-in server when FLASK_ENV=production (not recommended)",
    )
    args = parser.parse_args()

    if _is_production() and not args.allow_insecure_dev_server:
        print(
            "Refusing to use Flask's development server in production.\n"
            "Run: gunicorn --bind 0.0.0.0:5000 --workers 1 --threads 8 wsgi:app\n"
            "Or pass --allow-insecure-dev-server only for debugging.",
            file=sys.stderr,
        )
        sys.exit(1)

    app = create_app()
    debug = not args.no_debug and not _is_production()

    url = f"http://{args.host}:{args.port}"
    debug_str = "ON" if debug else "OFF"

    print(f"""
+----------------------------------------------+
|          NexusAI Code Assistant v2.1         |
+----------------------------------------------+
|  Host: {url:<38s} |
|  Debug: {debug_str:<37s} |
|  Action: Press Ctrl+C to quit               |
+----------------------------------------------+
    """)

    app.run(host=args.host, port=args.port, debug=debug, threaded=True)


if __name__ == "__main__":
    main()
