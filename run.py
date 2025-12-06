#!/usr/bin/env python3
"""
Run Logic-Guard-Layer without pip installation.

Usage:
    python run.py              # Start server on port 8000
    python run.py --port 3000  # Custom port
    python run.py --reload     # Auto-reload for development
    python run.py --help       # Show help
"""

import sys
import os

# Add src to path so we can import without pip install
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Run Logic-Guard-Layer development server"
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind to (default: 8000)"
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode"
    )

    args = parser.parse_args()

    # Set debug mode if requested
    if args.debug:
        os.environ["DEBUG"] = "true"

    try:
        import uvicorn
    except ImportError:
        print("Error: uvicorn is required. Install with:")
        print("  pip install uvicorn[standard]")
        sys.exit(1)

    print(f"""
  _    ___   ___ ___ ___    ___ _   _   _   ___ ___
 | |  / _ \\ / __|_ _/ __|  / __| | | | /_\\ | _ \\   \\
 | |_| (_) | (_ || | (__  | (_ | |_| |/ _ \\|   / |) |
 |____\\___/ \\___|___|\\___| \\___|\\___//_/ \\_\\_|_\\___/

  _      ___   _____ ___
 | |    /_\\ \\ / / __| _ \\
 | |__ / _ \\ V /| _||   /
 |____/_/ \\_\\_| |___|_|_\\

    Starting development server...
    URL: http://{args.host}:{args.port}
    Auto-reload: {'enabled' if args.reload else 'disabled'}

    Press Ctrl+C to stop
    """)

    uvicorn.run(
        "logic_guard_layer.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        reload_dirs=["src"] if args.reload else None,
        log_level="debug" if args.debug else "info",
    )
