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

LOG_TAIL_BYTES = 64 * 1024
LOG_LINE_CHARS = 500
LOG_TOTAL_CHARS = 25_000


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
    line_count = max(0, min(lines, 50))
    try:
        with open(path, 'rb') as log_file:
            log_file.seek(0, os.SEEK_END)
            read_size = min(log_file.tell(), LOG_TAIL_BYTES)
            log_file.seek(-read_size, os.SEEK_END)
            raw = log_file.read(read_size)
        decoded_lines = raw.decode('utf-8', errors='replace').splitlines()
        raw_lines = decoded_lines[-line_count:] if line_count else []
    except OSError:
        raw_lines = ['[no output captured]']

    sanitized = []
    remaining_chars = LOG_TOTAL_CHARS
    for line in reversed(raw_lines):
        clean = ''.join(char for char in line if char.isprintable())
        clean = clean[-LOG_LINE_CHARS:]
        clean = clean[-remaining_chars:]
        sanitized.append(clean)
        remaining_chars -= len(clean)
        if remaining_chars == 0:
            break
    sanitized.reverse()
    return '\n'.join([begin, *(f'| {line}' for line in sanitized), end])


def raise_if_process_exited(process, host, port, log_path):
    """Raise a bounded diagnostic if the server child has exited."""
    exit_code = process.poll()
    if exit_code is not None:
        raise RuntimeError(
            f'Server process exited with exit code {exit_code} before listening '
            f'on {host}:{port}.\n{sanitize_log_tail(log_path)}'
        )


def wait_for_server(host, port, process, log_path, timeout, poll_interval=0.1):
    """Wait for the automation address, failing immediately for a dead child."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        raise_if_process_exited(process, host, port, log_path)
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except OSError:
            raise_if_process_exited(process, host, port, log_path)
            time.sleep(poll_interval)
    raise_if_process_exited(process, host, port, log_path)
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


def parse_server_command(command):
    """Parse one configured command without exposing parser details."""
    try:
        argv = shlex.split(command)
    except ValueError as error:
        raise RuntimeError('Server command is invalid.') from error
    if not argv:
        raise RuntimeError('Server command is invalid.')
    return argv


def start_server(argv, log_file):
    """Start one no-shell server command behind a stable launcher boundary."""
    try:
        return subprocess.Popen(
            argv,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            start_new_session=True
        )
    except OSError as error:
        raise RuntimeError('Server command could not be started.') from error


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
        servers.append({
            'argv': parse_server_command(cmd),
            'host': host,
            'port': port,
        })

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

            print(f"Starting server {i+1}/{len(servers)}")

            # Unread PIPEs fill up (~64KB) and block the server, so write output to a log file
            log_file = tempfile.NamedTemporaryFile(
                mode='w', prefix=f"with_server_port{server['port']}_", suffix='.log', delete=False)
            log_files.append(log_file)

            # The command is split with shlex and run without a shell, so shell
            # metacharacters in --server are inert; for cd/&& chains pass an
            # explicit shell: --server "bash -c 'cd app && npm run dev'".
            # start_new_session puts the command and its children in one process
            # group so cleanup can kill them all (terminate() alone leaves orphans)
            process = start_server(server['argv'], log_file)
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
