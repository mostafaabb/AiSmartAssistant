#!/usr/bin/env python3
"""
NexusAI - Intelligent Code Assistant
Entry point for the Flask development server.

Usage:
    python run.py
    python run.py --port 8080
    python run.py --host 0.0.0.0
"""

import argparse
import sys
from ai_smart_assistant.app import create_app


def main():
    """Parse arguments and start the NexusAI development server."""
    parser = argparse.ArgumentParser(
        description='NexusAI - Intelligent Code Assistant'
    )
    parser.add_argument(
        '--host', default='127.0.0.1',
        help='Host to bind to (default: 127.0.0.1)'
    )
    parser.add_argument(
        '--port', type=int, default=5000,
        help='Port to listen on (default: 5000)'
    )
    parser.add_argument(
        '--no-debug', action='store_true',
        help='Disable debug mode'
    )
    args = parser.parse_args()

    app = create_app()
    debug = not args.no_debug

    url = f"http://{args.host}:{args.port}"
    debug_str = "ON" if debug else "OFF"

    print(f"""
╔══════════════════════════════════════════════╗
║          NexusAI Code Assistant v2.1         ║
╠══════════════════════════════════════════════╣
║  🌐 {url:<41s} ║
║  🔧 Debug: {debug_str:<33s} ║
║  📝 Press Ctrl+C to quit                    ║
╚══════════════════════════════════════════════╝
    """)

    app.run(
        host=args.host,
        port=args.port,
        debug=debug,
        threaded=True
    )


if __name__ == '__main__':
    main()
