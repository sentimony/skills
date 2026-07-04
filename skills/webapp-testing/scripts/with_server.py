#!/usr/bin/env python3
"""
Start one or more servers, wait for them to be ready, run a command, then clean up.

Usage:
    # Single server
    python scripts/with_server.py --server "npm run dev" --port 5173 -- python automation.py
    python scripts/with_server.py --server "npm start" --port 3000 -- python test.py

    # Multiple servers
    python scripts/with_server.py \
      --server "cd backend && python server.py" --port 3000 \
      --server "cd frontend && npm run dev" --port 5173 \
      -- python test.py

Note: server cleanup relies on POSIX process groups (start_new_session + killpg),
so this script works on macOS/Linux only.
"""

import subprocess
import socket
import time
import sys
import os
import signal
import argparse
import tempfile

def is_port_free(port):
    """Check that nothing is already listening on the port."""
    try:
        with socket.create_connection(('localhost', port), timeout=1):
            return False
    except OSError:
        return True


def is_server_ready(port, timeout=30):
    """Wait for server to be ready by polling the port."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with socket.create_connection(('localhost', port), timeout=1):
                return True
        except (socket.error, ConnectionRefusedError):
            time.sleep(0.5)
    return False


def tail(path, lines=50):
    """Return the last lines of a file."""
    try:
        with open(path, errors='replace') as f:
            return ''.join(f.readlines()[-lines:])
    except OSError:
        return '[no output captured]'


def main():
    parser = argparse.ArgumentParser(description='Run command with one or more servers')
    parser.add_argument('--server', action='append', dest='servers', required=True, help='Server command (can be repeated)')
    parser.add_argument('--port', action='append', dest='ports', type=int, required=True, help='Port for each server (must match --server count)')
    parser.add_argument('--timeout', type=int, default=30, help='Timeout in seconds per server (default: 30)')
    parser.add_argument('command', nargs=argparse.REMAINDER, help='Command to run after server(s) ready')

    args = parser.parse_args()

    # Remove the '--' separator if present
    if args.command and args.command[0] == '--':
        args.command = args.command[1:]

    if not args.command:
        print("Error: No command specified to run")
        sys.exit(1)

    # Parse server configurations
    if len(args.servers) != len(args.ports):
        print("Error: Number of --server and --port arguments must match")
        sys.exit(1)

    servers = []
    for cmd, port in zip(args.servers, args.ports):
        servers.append({'cmd': cmd, 'port': port})

    server_processes = []
    log_files = []

    try:
        # Start all servers
        for i, server in enumerate(servers):
            if not is_port_free(server['port']):
                raise RuntimeError(
                    f"Port {server['port']} is already in use - "
                    f"stop the process listening on it before starting this server"
                )

            print(f"Starting server {i+1}/{len(servers)}: {server['cmd']}")

            # Unread PIPEs fill up (~64KB) and block the server, so write output to a log file
            log_file = tempfile.NamedTemporaryFile(
                mode='w', prefix=f"with_server_port{server['port']}_", suffix='.log', delete=False)
            log_files.append(log_file)
            print(f"Server log: {log_file.name}")

            # Use shell=True to support commands with cd and &&;
            # start_new_session puts the shell and its children in one process group
            # so cleanup can kill them all (terminate() alone leaves orphans)
            process = subprocess.Popen(
                server['cmd'],
                shell=True,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                start_new_session=True
            )
            server_processes.append(process)

            # Wait for this server to be ready
            print(f"Waiting for server on port {server['port']}...")
            if not is_server_ready(server['port'], timeout=args.timeout):
                raise RuntimeError(
                    f"Server failed to start on port {server['port']} within {args.timeout}s.\n"
                    f"Last output ({log_file.name}):\n{tail(log_file.name)}"
                )

            print(f"Server ready on port {server['port']}")

        print(f"\nAll {len(servers)} server(s) ready")

        # Run the command
        print(f"Running: {' '.join(args.command)}\n")
        result = subprocess.run(args.command)
        sys.exit(result.returncode)

    finally:
        # Clean up all servers
        print(f"\nStopping {len(server_processes)} server(s)...")
        for i, process in enumerate(server_processes):
            try:
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                except ProcessLookupError:
                    pass  # Died between SIGTERM and SIGKILL
                process.wait()
            except ProcessLookupError:
                pass  # Process group already gone
            print(f"Server {i+1} stopped")
        for log_file in log_files:
            log_file.close()
        print("All servers stopped")


if __name__ == '__main__':
    main()
