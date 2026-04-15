#!/usr/bin/env python3
"""Wrapper around ansible-lint that supports Galaxy server authentication.

Sets ANSIBLE_GALAXY_SERVER_* env vars (when requested) before invoking
ansible-lint, so collections with private dependencies can be resolved.
"""

import argparse
import subprocess
import sys

from hooks.galaxy_auth import add_galaxy_server_args, apply_galaxy_server_env


def main():
    """Entry point for the run-ansible-lint console script."""
    parser = argparse.ArgumentParser(add_help=False)
    add_galaxy_server_args(parser)
    known, remaining = parser.parse_known_args()
    apply_galaxy_server_env(known)

    result = subprocess.run(["ansible-lint", *remaining], check=False)
    raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
