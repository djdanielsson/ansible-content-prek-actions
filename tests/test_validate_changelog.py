"""Tests for changelog fragment validation."""

from pathlib import Path

import pytest
import yaml

from hooks.validate_changelog import is_valid_changelog_format


@pytest.fixture
def changelog_config(tmp_path, monkeypatch):
    """Minimal changelogs/config.yaml for validation."""
    config_dir = tmp_path / "changelogs"
    config_dir.mkdir()
    fragments = config_dir / "fragments"
    fragments.mkdir()
    (config_dir / "config.yaml").write_text(
        yaml.dump(
            {
                "sections": [["minor_changes", "Minor Changes"], ["bugfixes", "Bugfixes"]],
                "trivial_section_name": "trivial",
                "prelude_section_name": "release_summary",
            }
        )
    )
    monkeypatch.chdir(tmp_path)
    return fragments


def test_valid_string_entries(changelog_config):
    path = changelog_config / "good.yml"
    path.write_text(
        "minor_changes:\n"
        "  - Fixed something important.\n"
    )
    assert is_valid_changelog_format(str(path)) is True


def test_rejects_dict_parsed_from_colon_in_entry(changelog_config):
    path = changelog_config / "bad.yml"
    path.write_text(
        "minor_changes:\n"
        "  - example - skip when ``state: absent``.\n"
    )
    assert is_valid_changelog_format(str(path)) is False
