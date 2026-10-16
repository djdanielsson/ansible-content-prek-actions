"""Tests for automated release versioning and generated README references."""

from pathlib import Path

from scripts.release_metadata import next_version
from scripts.sync_hooks import sync_readme


def test_next_version_uses_new_ansible_dev_tools_version():
    assert next_version((26, 10, 0), [(26, 8, 1)]) == (26, 10, 0)


def test_next_version_increments_patch_for_other_changes():
    assert next_version((26, 9, 0), [(26, 9, 0)]) == (26, 9, 1)


def test_sync_readme_uses_release_tag_independently_of_dependency_version(tmp_path):
    readme = tmp_path / "README.md"
    readme.write_text(
        "ansible-dev-tools==26.9.0\n"
        "galaxy-importer==0.4.43\n"
        "rev: v26.9.0\n"
        'rev = "v26.9.0"\n'
    )
    pins = {
        "ansible-dev-tools": "ansible-dev-tools==26.9.0",
        "galaxy-importer": "galaxy-importer==0.4.44",
    }

    assert sync_readme(pins, Path(readme), "v26.9.1") is True
    content = readme.read_text()
    assert "ansible-dev-tools==26.9.0" in content
    assert "galaxy-importer==0.4.44" in content
    assert "rev: v26.9.1" in content
    assert 'rev = "v26.9.1"' in content
