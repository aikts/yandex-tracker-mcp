"""`pyproject.toml`, `manifest.json`, `server.json` and `CHANGELOG.md` agree on the
version - see `rules/docs.md`. Publishing a release with one of them left behind is a
step nobody catches by reading the diff.
"""

import json
import tomllib
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).parents[1]

VERSION: str = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"][
    "version"
]
MANIFEST: dict[str, Any] = json.loads((ROOT / "manifest.json").read_text())
SERVER: dict[str, Any] = json.loads((ROOT / "server.json").read_text())
CHANGELOG: str = (ROOT / "CHANGELOG.md").read_text()


def test_manifest_carries_the_project_version() -> None:
    assert MANIFEST["version"] == VERSION


def test_server_json_carries_the_project_version() -> None:
    assert SERVER["version"] == VERSION


@pytest.mark.parametrize(
    "package", SERVER["packages"], ids=[p["registryType"] for p in SERVER["packages"]]
)
def test_published_packages_carry_the_project_version(package: dict[str, Any]) -> None:
    # The OCI entry states its version in the image tag rather than a `version` key,
    # and that tag is the one thing a release forgets to bump.
    stated = package.get("version") or package["identifier"].rsplit(":", 1)[-1]

    assert stated == VERSION, (
        f"the {package['registryType']} package in server.json is at {stated}, "
        f"not {VERSION}"
    )


def test_changelog_has_a_section_for_the_project_version() -> None:
    assert f"## [{VERSION}]" in CHANGELOG, (
        f"CHANGELOG.md has no section for {VERSION}. Every release gets one, patch "
        "releases included - see rules/changelog.md."
    )
