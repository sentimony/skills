#!/usr/bin/env python3
"""
Start one or more servers, wait for them to be ready, run a command, then clean up.

Usage:
    # Single server
    python scripts/with_server.py --server "npm run dev" --host 127.0.0.1 --port 5173 -- python automation.py
    python scripts/with_server.py --server "npm start" --port 3000 -- python test.py

    # Multiple servers (shell chains need an explicit shell wrapper)
    python scripts/with_server.py \
      --server "bash -c 'cd backend && python server.py'" --host ::1 --port 3000 \
      --server "bash -c 'cd frontend && npm run dev'" --host 127.0.0.1 --port 5173 \
      -- python test.py

Note: server cleanup relies on POSIX process groups (start_new_session + killpg),
so this script works on macOS/Linux only.
"""

import subprocess
import shlex
import socket
import time
import sys
import os
import signal
import argparse
import tempfile

def is_port_free(host, port):
    """Check whether the automation host is free on the requested port."""
    try:
        with socket.create_connection((host, port), timeout=1):
            return False
    except OSError:
        return True


def sanitize_log_tail(path, lines=50):
    """Return a bounded log tail as untrusted display data."""
    begin = '--- BEGIN UNTRUSTED SERVER LOG (last 50 lines) ---'
    end = '--- END UNTRUSTED SERVER LOG ---'
    try:
        with open(path, errors='replace') as log_file:
            raw_lines = log_file.read().splitlines()[-lines:]
    except OSError:
        raw_lines = ['[no output captured]']

    sanitized = []
    for line in raw_lines:
        sanitized.append(''.join(char for char in line if char.isprintable()))
    return '\n'.join([begin, *(f'| {line}' for line in sanitized), end])


def wait_for_server(host, port, process, log_path, timeout, poll_interval=0.1):
    """Wait for the automation address, failing immediately for a dead child."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        exit_code = process.poll()
        if exit_code is not None:
            raise RuntimeError(
                f'Server process exited with exit code {exit_code} before listening '
                f'on {host}:{port}.\n{sanitize_log_tail(log_path)}'
            )
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except OSError:
            time.sleep(poll_interval)
    raise RuntimeError(
        f'Server failed to start on {host}:{port} within {timeout}s.\n'
        f'{sanitize_log_tail(log_path)}'
    )


def normalize_hosts(hosts, server_count):
    """Default omitted hosts while preserving the server order."""
    if not hosts:
        return ['127.0.0.1'] * server_count
    if len(hosts) != server_count:
        raise ValueError('Number of --host arguments must match --server count')
    return hosts


def main():
    parser = argparse.ArgumentParser(description='Run command with one or more servers')
    parser.add_argument('--server', action='append', dest='servers', required=True, help='Server command, run without a shell (wrap in "bash -c \'...\'" for shell syntax); can be repeated')
    parser.add_argument('--host', action='append', dest='hosts', help='Host for each server readiness probe (defaults to 127.0.0.1 for every server); can be repeated')
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
    try:
        args.hosts = normalize_hosts(args.hosts or [], len(args.servers))
    except ValueError as error:
        print(f'Error: {error}')
        sys.exit(1)

    servers = []
    for cmd, host, port in zip(args.servers, args.hosts, args.ports):
        servers.append({'cmd': cmd, 'host': host, 'port': port})

    server_processes = []
    log_files = []

    try:
        # Start all servers
        for i, server in enumerate(servers):
            if not is_port_free(server['host'], server['port']):
                raise RuntimeError(
                    f"{server['host']}:{server['port']} is already in use - "
                    f"stop the process listening on it before starting this server"
                )

            print(f"Starting server {i+1}/{len(servers)}: {server['cmd']}")

            # Unread PIPEs fill up (~64KB) and block the server, so write output to a log file
            log_file = tempfile.NamedTemporaryFile(
                mode='w', prefix=f"with_server_port{server['port']}_", suffix='.log', delete=False)
            log_files.append(log_file)
            print(f"Server log: {log_file.name}")

            # The command is split with shlex and run without a shell, so shell
            # metacharacters in --server are inert; for cd/&& chains pass an
            # explicit shell: --server "bash -c 'cd app && npm run dev'".
            # start_new_session puts the command and its children in one process
            # group so cleanup can kill them all (terminate() alone leaves orphans)
            process = subprocess.Popen(
                shlex.split(server['cmd']),
                stdout=log_file,
                stderr=subprocess.STDOUT,
                start_new_session=True
            )
            server_processes.append(process)

            # Wait for this server to be ready
            print(f"Waiting for server on {server['host']}:{server['port']}...")
            wait_for_server(
                server['host'], server['port'], process, log_file.name, args.timeout)

            print(f"Server ready on {server['host']}:{server['port']}")

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
    try:
        main()
    except RuntimeError as error:
        print(f'Error: {error}', file=sys.stderr)
        sys.exit(1)
