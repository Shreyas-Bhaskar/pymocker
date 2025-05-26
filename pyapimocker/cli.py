import argparse
import sys
from pathlib import Path

import uvicorn

from pyapimocker.server import MockServer


def main():
    parser = argparse.ArgumentParser(description="Start a mock API server")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Start command
    start_parser = subparsers.add_parser("start", help="Start the mock server")
    start_parser.add_argument(
        "config_path",
        type=str,
        help="Path to the YAML or JSON configuration file",
    )
    start_parser.add_argument(
        "--port",
        "-p",
        type=int,
        default=8000,
        help="Port to run the server on (default: 8000)",
    )
    start_parser.add_argument(
        "--host",
        "-H",
        type=str,
        default="0.0.0.0",
        help="Host to bind the server to (default: 0.0.0.0)",
    )
    start_parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output",
    )
    start_parser.add_argument(
        "--record",
        action="store_true",
        help="Enable record mode: proxy unknown requests and record responses",
    )
    start_parser.add_argument(
        "--proxy-base-url",
        type=str,
        default=None,
        help="Base URL of the real API to proxy to in record mode",
    )

    args = parser.parse_args()

    if args.command != "start":
        parser.print_help()
        sys.exit(1)

    config_path = Path(args.config_path)
    if not config_path.exists():
        print(f"Error: Configuration file not found: {args.config_path}")
        sys.exit(1)

    server = MockServer(str(config_path), record_mode=args.record, proxy_base_url=args.proxy_base_url)
    
    if args.verbose:
        print(f"Starting mock server on {args.host}:{args.port}")
        print(f"Loaded configuration from: {args.config_path}")
        print("Available routes:")
        for route in server.config.routes:
            print(f"  {route.method} {route.path}")

    uvicorn.run(
        server.app,
        host=args.host,
        port=args.port,
        log_level="debug" if args.verbose else "info",
    )


if __name__ == "__main__":
    main() 