#!/usr/bin/env python3
"""
Quickly run mole menu actions:
1. Clear cache
3. Optimize

Usage:
  python3 mole_quick_run.py
  python3 mole_quick_run.py --cmd /path/to/mole
  python3 mole_quick_run.py --delay 2
"""

import argparse
import os
import pty
import select
import shlex
import subprocess
import sys
import time


def stream_available(master_fd):
    while True:
        ready, _, _ = select.select([master_fd], [], [], 0)
        if not ready:
            return
        try:
            data = os.read(master_fd, 4096)
        except OSError:
            return
        if not data:
            return
        sys.stdout.buffer.write(data)
        sys.stdout.buffer.flush()


def run_mole(command, choices, delay):
    master_fd, slave_fd = pty.openpty()
    args = shlex.split(command)

    process = subprocess.Popen(
        args,
        stdin=slave_fd,
        stdout=slave_fd,
        stderr=slave_fd,
        close_fds=True,
    )
    os.close(slave_fd)

    try:
        time.sleep(delay)
        stream_available(master_fd)

        for choice in choices:
            os.write(master_fd, f"{choice}\n".encode())
            time.sleep(delay)
            stream_available(master_fd)

        while process.poll() is None:
            stream_available(master_fd)
            time.sleep(0.1)

        stream_available(master_fd)
        return process.returncode
    finally:
        try:
            os.close(master_fd)
        except OSError:
            pass


def main():
    parser = argparse.ArgumentParser(
        description="Run mole and automatically select menu actions 1 and 3."
    )
    parser.add_argument(
        "--cmd",
        default=os.environ.get("MOLE_CMD", "mole"),
        help="mole command path or command string. Default: mole",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Seconds to wait before and after each menu choice. Default: 1.0",
    )
    parser.add_argument(
        "--choices",
        default="1,3",
        help="Comma-separated menu choices to send. Default: 1,3",
    )
    args = parser.parse_args()

    choices = [item.strip() for item in args.choices.split(",") if item.strip()]
    if not choices:
        print("No menu choices provided.", file=sys.stderr)
        return 2

    try:
        return run_mole(args.cmd, choices, args.delay)
    except FileNotFoundError:
        print(
            f"Could not find command: {args.cmd}\n"
            "Pass the full mole path with --cmd, or set MOLE_CMD.",
            file=sys.stderr,
        )
        return 127
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
