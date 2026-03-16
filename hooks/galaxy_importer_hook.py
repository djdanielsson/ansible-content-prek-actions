#!/usr/bin/env python3
"""Run galaxy-importer to validate an Ansible collection.

Builds the collection tarball and runs galaxy-importer validation on it.
"""

import shutil
import subprocess
import sys
import tempfile


def main():
    """Entry point for the run-galaxy-importer console script."""
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
            ],
            check=False,
        )
        raise SystemExit(result.returncode)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    main()
