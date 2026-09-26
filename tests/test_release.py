import re

from conftest import REPO_ROOT
from kage import version
from kage.modules.updater import extract_release_notes

CHANGELOG = (REPO_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
SAMPLE_CHANGELOG = """# Kage Changelog

Intro text.

## [1.2.0] - 2026-10-01

### Added
- Newest thing.

## [1.1.0] - 2026-09-30

### Fixed
- Older fix.

---

# Heroku history
## 🪐 Heroku 2.1.0
- upstream
"""


def test_extract_newest_section():
    notes = extract_release_notes(SAMPLE_CHANGELOG)
    assert notes == "## [1.2.0] - 2026-10-01\n\n### Added\n- Newest thing."


def test_extract_specific_section_stops_at_separator():
    notes = extract_release_notes(SAMPLE_CHANGELOG, "1.1.0")
    assert notes == "## [1.1.0] - 2026-09-30\n\n### Fixed\n- Older fix."


def test_extract_unknown_release_is_empty():
    assert extract_release_notes(SAMPLE_CHANGELOG, "9.9.9") == ""
    assert extract_release_notes("# Heroku history\n## 🪐 Heroku 2.1.0\n") == ""


def test_extract_handles_crlf():
    crlf = SAMPLE_CHANGELOG.replace("\n", "\r\n")
    assert extract_release_notes(crlf) == extract_release_notes(SAMPLE_CHANGELOG)


def test_changelog_top_section_matches_version():
    newest = re.search(r"^## \[(\d+\.\d+\.\d+)\]", CHANGELOG, re.M)
    assert newest, "CHANGELOG.md has no '## [X.Y.Z]' section"
    assert newest[1] == version.kage_version


def test_real_changelog_notes_for_current_version():
    notes = extract_release_notes(CHANGELOG, version.kage_version)
    assert notes.startswith(f"## [{version.kage_version}]")
    assert "### " in notes
    assert "Heroku history" not in notes
    assert "---" not in notes


def test_kage_version_is_derived_from_kage_tuple():
    assert version.kage_version == ".".join(map(str, version.__kage_version__))
    assert len(version.__kage_version__) == 3
    assert all(isinstance(part, int) for part in version.__kage_version__)


def test_heroku_api_level_stays_separate():
    # third-party modules compare heroku_min against __version__, the Heroku API level
    assert version.__version__ >= (2, 1, 0)
    assert len(version.__version__) == 3


def test_release_workflow_can_parse_version_file():
    # docker-deploy.yml extracts the tag version from kage/version.py with this regex
    source = (REPO_ROOT / "kage" / "version.py").read_text(encoding="utf-8")
    match = re.search(r"^__kage_version__ = \((\d+), (\d+), (\d+)\)", source, re.M)
    assert match, "__kage_version__ no longer matches the release workflow regex"
    assert ".".join(match.groups()) == version.kage_version
