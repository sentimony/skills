#!/usr/bin/env python3
"""Behavior tests for the with_server readiness boundary."""

import importlib.util
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
