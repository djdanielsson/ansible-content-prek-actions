#!/usr/bin/env python3
"""Run tox-ansible test suites (sanity, unit, integration).

Wraps tox-ansible with automatic tox-ansible.ini creation when one is
not already present in the collection root.
"""

import os
import subprocess
import sys

DEFAULT_TOX_ANSIBLE_INI = """\
[ansible]
skip =
    py3.7
    py3.8
    2.9
    2.10
    2.11
    2.12
    2.13
"""


def run_tox(test_type: str, extra_args: list[str] | None = None):
    """Run tox-ansible for the given test type.

    :param test_type: One of 'sanity', 'unit', or 'integration'.
    :param extra_args: Additional arguments forwarded to tox.
    """
    created_default = False

    if not os.path.isfile("tox-ansible.ini"):
        print("INFO: No tox-ansible.ini found, creating default...")
        with open("tox-ansible.ini", "w") as fh:
            fh.write(DEFAULT_TOX_ANSIBLE_INI)
        created_default = True

    try:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "tox",
                "--ansible",
                "--conf",
                "tox-ansible.ini",
                "-l",
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        envs = [
            line.strip()
            for line in result.stdout.splitlines()
            if line.strip().startswith(f"{test_type}-")
        ]

        if not envs:
            print(f"No {test_type} test environments found.")
            raise SystemExit(0)

        cmd = [
            sys.executable,
            "-m",
            "tox",
            "--ansible",
            "--conf",
            "tox-ansible.ini",
            "-e",
            ",".join(envs),
        ]
        if extra_args:
            cmd.extend(extra_args)

        result = subprocess.run(cmd, check=False)
        raise SystemExit(result.returncode)
    finally:
        if created_default:
            try:
                os.remove("tox-ansible.ini")
            except OSError:
                pass


def main_sanity():
    """Entry point for the run-tox-sanity console script."""
    run_tox("sanity", sys.argv[1:])


def main_unit():
    """Entry point for the run-tox-unit console script."""
    run_tox("unit", sys.argv[1:])


def main_integration():
    """Entry point for the run-tox-integration console script."""
    run_tox("integration", sys.argv[1:])


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("test_type", choices=["sanity", "unit", "integration"])
    args, extra = parser.parse_known_args()
    run_tox(args.test_type, extra)
