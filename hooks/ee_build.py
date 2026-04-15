#!/usr/bin/env python3
"""Build an Ansible execution environment image.

Wraps ansible-builder, auto-detecting podman or docker as the
container runtime.
"""

import argparse
import os
import shutil
import subprocess
import sys

from hooks.galaxy_auth import add_galaxy_server_args, apply_galaxy_server_env


def main():
    """Entry point for the ansible-ee-build console script."""
    parser = argparse.ArgumentParser(
        description="Build an Ansible execution environment image",
    )
    add_galaxy_server_args(parser)
    args, extra = parser.parse_known_args()
    apply_galaxy_server_env(args)

    runtime = None
    if shutil.which("podman"):
        runtime = "podman"
    elif shutil.which("docker"):
        runtime = "docker"
    else:
        print("ERROR: Neither podman nor docker is installed.")
        print("Install one of them to build execution environments.")
        raise SystemExit(1)

    if not os.path.isfile("execution-environment.yml"):
        print(
            "ERROR: No execution-environment.yml found in the current directory."
        )
        print("This hook requires an execution-environment.yml to build.")
        raise SystemExit(1)

    cmd = [
        "ansible-builder",
        "build",
        "-v",
        "3",
        "--container-runtime",
        runtime,
        *extra,
    ]

    result = subprocess.run(cmd, check=False)
    raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
