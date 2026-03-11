#!/usr/bin/env python3
"""Build and import an Ansible collection for validation.

Builds the collection tarball and runs galaxy-importer to validate it.
"""

import shutil
import subprocess
import sys
import tempfile


def main():
    """Entry point for the build-import-collection console script."""
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
