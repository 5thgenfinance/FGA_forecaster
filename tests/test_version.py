import re
from pathlib import Path

import pytest

from app.version import APP_VERSION, RELEASE_DATE, version_line


def test_version_is_semver():
    assert re.fullmatch(r"\d+\.\d+\.\d+", APP_VERSION)
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", RELEASE_DATE)


def test_version_line_contents():
    line = version_line()
    assert line.startswith(f"Version {APP_VERSION}") and RELEASE_DATE in line
    assert "build" not in version_line(include_build=False)


def test_matches_spec_major_minor():
    spec = Path(__file__).resolve().parents[1] / "SPEC.md"
    if not spec.exists():
        pytest.skip("SPEC.md not found")
    m = re.search(r"Version (\d+\.\d+)", spec.read_text(encoding="utf8").splitlines()[0])
    assert m, "no version in the SPEC.md title"
    assert APP_VERSION.startswith(m.group(1) + "."), f"app {APP_VERSION} vs spec {m.group(1)}"
