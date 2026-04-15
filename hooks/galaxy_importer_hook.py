#!/usr/bin/env python3
"""Run galaxy-importer to validate an Ansible collection.

Builds the collection tarball and runs galaxy-importer validation on it.
"""

import argparse
import shutil
import subprocess
import sys
import tempfile

from hooks.galaxy_auth import add_galaxy_server_args, apply_galaxy_server_env


def main():
    """Entry point for the run-galaxy-importer console script."""
    parser = argparse.ArgumentParser(
        description="Run galaxy-importer to validate an Ansible collection",
    )
    add_galaxy_server_args(parser)
    args, extra = parser.parse_known_args()
    apply_galaxy_server_env(args)

    tmpdir = tempfile.mkdtemp()
    try:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "galaxy_importer.main",
                "--git-clone-path",
                ".",
                "--output-path",
                tmpdir,
                *extra,
            ],
            check=False,
        )
        raise SystemExit(result.returncode)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    main()
