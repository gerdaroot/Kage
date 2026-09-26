import re
import string
import warnings
from dataclasses import dataclass, field

import pytest
from ruamel.yaml import YAML

from kage import translations

PACKS = sorted(translations.PACKS.glob("*.yml"))
TRANSLATIONS = [pack for pack in PACKS if pack.stem != "en"]

# Keys whose placeholders crash .format() today. Remove an entry once it's fixed;
# the test fails on entries that no longer reproduce so this list can't go stale.
KNOWN_BROKEN: dict[str, set[str]] = {}


@dataclass(frozen=True)
class Placeholders:
    positional: int = 0
    named: frozenset[str] = field(default_factory=frozenset)


def parse_placeholders(text: str) -> Placeholders:
    auto, highest_index, named = 0, -1, set()
    for _, field_name, _, _ in string.Formatter().parse(text):
        if field_name is None:
            continue
        base = re.split(r"[.\[]", field_name, maxsplit=1)[0]
        if not base:
            auto += 1
        elif base.isdigit():
            highest_index = max(highest_index, int(base))
        else:
            named.add(base)
    return Placeholders(max(auto, highest_index + 1), frozenset(named))


def load_pack(path) -> dict:
    return YAML(typ="safe").load(path.read_text(encoding="utf-8"))


def iter_strings(pack: dict):
    for section, keys in pack.items():
        for key, value in keys.items():
            if isinstance(value, str):
                yield f"{section}.{key}", value


def unparseable_keys(pack: dict) -> set[str]:
    broken = set()
    for key, text in iter_strings(pack):
        try:
            parse_placeholders(text)
        except ValueError:
            broken.add(key)
    return broken


def placeholder_problems(english: dict, translated: dict) -> tuple[set[str], list[str]]:
    """Returns keys whose placeholders English callers can't fill, and keys that drop some."""
    english_strings = dict(iter_strings(english))
    errors, dropping = set(), []
    for key, text in iter_strings(translated):
        if key not in english_strings:
            continue
        try:
            wanted = parse_placeholders(text)
            given = parse_placeholders(english_strings[key])
        except ValueError:
            errors.add(key)
            continue
        if wanted.positional > given.positional or not wanted.named <= given.named:
            errors.add(key)
        elif wanted != given:
            dropping.append(key)
    return errors, dropping


@pytest.fixture(scope="module")
def english() -> dict:
    return load_pack(translations.PACKS / "en.yml")


@pytest.mark.parametrize("path", PACKS, ids=lambda p: p.name)
def test_pack_is_valid_yaml_mapping(path):
    pack = load_pack(path)
    assert isinstance(pack, dict) and pack
    for section, keys in pack.items():
        assert isinstance(keys, dict), f"section {section!r} is not a mapping"


@pytest.mark.parametrize("path", TRANSLATIONS, ids=lambda p: p.name)
def test_pack_has_same_sections_as_english(path, english):
    sections = set(load_pack(path))
    assert sections == set(english), (
        f"missing: {sorted(set(english) - sections)}, unknown: {sorted(sections - set(english))}"
    )


def test_english_format_strings_parse(english):
    assert unparseable_keys(english) == KNOWN_BROKEN.get("en", set())


@pytest.mark.parametrize("path", TRANSLATIONS, ids=lambda p: p.name)
def test_translation_placeholders_are_fillable(path, english):
    """A translation may drop placeholders but must not ask for ones English callers don't pass."""
    translated = load_pack(path)
    errors, dropping = placeholder_problems(english, translated)
    missing = set(dict(iter_strings(english))) - set(dict(iter_strings(translated)))
    if dropping or missing:
        warnings.warn(
            f"{path.name}: {len(missing)} keys fall back to English, "
            f"placeholders dropped in {', '.join(dropping) or 'none'}",
            stacklevel=1,
        )
    errors -= KNOWN_BROKEN.get("en", set())
    assert errors == KNOWN_BROKEN.get(path.stem, set())


@pytest.mark.parametrize(
    "language", [*translations.SUPPORTED_LANGUAGES, *translations.MEME_LANGUAGES]
)
def test_every_offered_language_has_a_pack(language):
    assert translations.get_language_pack_path(language) is not None
