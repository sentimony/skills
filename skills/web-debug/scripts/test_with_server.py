#!/usr/bin/env python3
"""Behavior tests for the with_server readiness boundary."""

import importlib.util
import builtins
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch


SCRIPT = Path(__file__).with_name("with_server.py")
SPEC = importlib.util.spec_from_file_location("with_server", SCRIPT)
with_server = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(with_server)


class DeadProcess:
    """A child process that has already exited before readiness probing."""

    def poll(self):
        return 9


class LiveProcess:
    """A child process that remains alive while the readiness probe connects."""

    def poll(self):
        return None


class ExitAfterConnectionFailureProcess:
    """A child that exits while the final connection attempt is in progress."""

    def __init__(self):
        self.exit_codes = iter([None, 9])

    def poll(self):
        return next(self.exit_codes)


class TrackingReader:
    """Record how many bytes the production log reader requests and receives."""

    def __init__(self, wrapped, read_sizes, byte_counts):
        self.wrapped = wrapped
        self.read_sizes = read_sizes
        self.byte_counts = byte_counts

    def read(self, size=-1):
        data = self.wrapped.read(size)
        self.read_sizes.append(size)
        self.byte_counts.append(
            len(data.encode("utf-8")) if isinstance(data, str) else len(data)
        )
        return data

    def __enter__(self):
        self.wrapped.__enter__()
        return self

    def __exit__(self, *args):
        return self.wrapped.__exit__(*args)

    def __getattr__(self, name):
        return getattr(self.wrapped, name)


class WithServerTests(unittest.TestCase):
    def test_normalize_hosts_defaults_each_server_to_ipv4_loopback(self):
        """Catches a mutation that shares one default or rejects omitted hosts."""
        self.assertEqual(
            with_server.normalize_hosts([], 2), ["127.0.0.1", "127.0.0.1"]
        )

    def test_normalize_hosts_preserves_explicit_ipv6_and_ipv4_order(self):
        """Catches a mutation that overwrites explicit hosts with a default."""
        self.assertEqual(
            with_server.normalize_hosts(["::1", "127.0.0.1"], 2),
            ["::1", "127.0.0.1"],
        )

    def test_is_port_free_probes_the_requested_host(self):
        """Catches a mutation that probes localhost instead of the automation host."""
        with patch.object(
            with_server.socket, "create_connection", return_value=MagicMock()
        ) as connect:
            self.assertFalse(with_server.is_port_free("::1", 4173))
        connect.assert_called_once_with(("::1", 4173), timeout=1)

    def test_wait_for_server_fails_immediately_for_dead_child_with_bounded_log_tail(self):
        """Catches a mutation that waits for a port after the child has exited."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as log_file:
            for index in range(55):
                log_file.write(f"entry-{index:02d}{chr(27)}[31m\n")
            log_path = log_file.name

        try:
            start = time.monotonic()
            with self.assertRaises(RuntimeError) as raised:
                with_server.wait_for_server(
                    "127.0.0.1", 4173, DeadProcess(), log_path, timeout=5,
                    poll_interval=0.01,
                )
            elapsed = time.monotonic() - start
        finally:
            Path(log_path).unlink(missing_ok=True)

        message = str(raised.exception)
        self.assertLess(elapsed, 0.2)
        self.assertIn("exit code 9", message)
        self.assertIn("--- BEGIN UNTRUSTED SERVER LOG (last 50 lines) ---", message)
        self.assertIn("--- END UNTRUSTED SERVER LOG ---", message)
        self.assertIn("entry-05", message)
        self.assertNotIn("entry-04", message)
        self.assertNotIn("\x1b", message)

    def test_wait_for_server_connects_to_the_requested_ipv6_host(self):
        """Catches a mutation that probes localhost instead of the readiness host."""
        with patch.object(
            with_server.socket, "create_connection", return_value=MagicMock()
        ) as connect:
            self.assertTrue(with_server.wait_for_server(
                "::1", 4173, LiveProcess(), "/missing-log-is-fine", timeout=1,
            ))
        connect.assert_called_once_with(("::1", 4173), timeout=1)

    def test_log_tail_bounds_bytes_and_rendered_chars_for_one_huge_line(self):
        """Catches a mutation that reads or renders an unbounded single log line."""
        with tempfile.NamedTemporaryFile(mode="wb", delete=False) as log_file:
            log_file.write(b"A" * (2 * 1024 * 1024))
            log_file.write(b"\x1b[31mTAIL")
            log_path = log_file.name

        read_sizes = []
        byte_counts = []
        real_open = builtins.open

        def tracking_open(*args, **kwargs):
            return TrackingReader(real_open(*args, **kwargs), read_sizes, byte_counts)

        try:
            with patch("builtins.open", side_effect=tracking_open):
                message = with_server.sanitize_log_tail(log_path)
        finally:
            Path(log_path).unlink(missing_ok=True)

        self.assertEqual(
            message.count("--- BEGIN UNTRUSTED SERVER LOG (last 50 lines) ---"), 1
        )
        self.assertEqual(message.count("--- END UNTRUSTED SERVER LOG ---"), 1)
        self.assertIn("TAIL", message)
        self.assertNotIn("\x1b", message)
        self.assertNotIn(-1, read_sizes)
        self.assertLessEqual(sum(byte_counts), 64 * 1024)
        self.assertLessEqual(len(message), 26_000)

    def test_log_tail_caps_each_payload_and_total_untrusted_content(self):
        """Catches mutations that loosen per-line or aggregate character limits."""
        with tempfile.NamedTemporaryFile(mode="wb", delete=False) as log_file:
            for index in range(50):
                payload = f"{index:02d}-".encode() + (b"A" * 597)
                log_file.write(payload + b"\n")
            log_path = log_file.name

        try:
            message = with_server.sanitize_log_tail(log_path)
        finally:
            Path(log_path).unlink(missing_ok=True)

        output_lines = message.splitlines()
        self.assertEqual(
            output_lines[0],
            "--- BEGIN UNTRUSTED SERVER LOG (last 50 lines) ---",
        )
        self.assertEqual(output_lines[-1], "--- END UNTRUSTED SERVER LOG ---")

        rendered_lines = output_lines[1:-1]
        self.assertEqual(len(rendered_lines), 50)
        self.assertTrue(all(line.startswith("| ") for line in rendered_lines))

        payloads = [line[2:] for line in rendered_lines]
        for payload in payloads:
            with self.subTest(payload=payload[:12]):
                self.assertLessEqual(len(payload), 500)
        self.assertEqual(sum(len(payload) for payload in payloads), 25_000)

    def test_log_tail_never_exceeds_50_lines_when_caller_requests_more(self):
        """Catches a mutation that lets the public lines argument bypass the cap."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as log_file:
            for index in range(100):
                log_file.write(f"entry-{index:03d}\n")
            log_path = log_file.name

        try:
            message = with_server.sanitize_log_tail(log_path, lines=50_000)
        finally:
            Path(log_path).unlink(missing_ok=True)

        rendered_lines = [line for line in message.splitlines() if line.startswith("| ")]
        self.assertEqual(len(rendered_lines), 50)
        self.assertEqual(rendered_lines[0], "| entry-050")
        self.assertEqual(rendered_lines[-1], "| entry-099")

    def test_wait_for_server_reports_exit_after_final_connection_failure(self):
        """Catches a mutation that labels a last-attempt child exit as a timeout."""
        process = ExitAfterConnectionFailureProcess()
        with (
            patch.object(
                with_server.socket, "create_connection", side_effect=OSError
            ),
            patch.object(with_server.time, "time", side_effect=[0.0, 0.0, 1.0]),
            patch.object(with_server.time, "sleep"),
            self.assertRaises(RuntimeError) as raised,
        ):
            with_server.wait_for_server(
                "127.0.0.1", 4173, process, "/missing-log-is-fine",
                timeout=1, poll_interval=0.1,
            )

        message = str(raised.exception)
        self.assertIn("exit code 9", message)
        self.assertNotIn("within 1s", message)

    def test_cli_reports_dead_child_without_a_python_traceback(self):
        """Catches a mutation that exposes implementation tracebacks to CLI users."""
        command = [
            sys.executable, str(SCRIPT),
            '--server', f'{sys.executable} -c "import sys; print(\'dead child\'); sys.exit(9)"',
            '--host', '127.0.0.1', '--port', '0', '--timeout', '5', '--',
            sys.executable, '-c', 'print("unreachable")',
        ]
        completed = subprocess.run(command, capture_output=True, text=True, timeout=2)

        self.assertEqual(completed.returncode, 1)
        self.assertIn('Error: Server process exited with exit code 9', completed.stderr)
        self.assertIn('--- BEGIN UNTRUSTED SERVER LOG (last 50 lines) ---', completed.stderr)
        self.assertIn('--- END UNTRUSTED SERVER LOG ---', completed.stderr)
        self.assertNotIn('Traceback', completed.stderr)


if __name__ == "__main__":
    unittest.main()
