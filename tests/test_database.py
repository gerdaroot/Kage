import json

import pytest

from kage.database import _kage_owner, migrate_legacy_db

LEGACY_DB = {
    "hikka.main": {"lang": "ru", "note": "heroku.main stays in values"},
    "heroku.inline": {"bot_token": "123:abc"},
    "legacy.security": {"owner": [1]},
    "HerokuInfoMod": {"banner_url": "x"},
    "HikkaSettingsMod": {},
    "kage.forums": {"topics": {"heroku-userbot": 7}},
    "Weather": {"city": "hikka.example"},
}
MIGRATED_DB = {
    "kage.main": {"lang": "ru", "note": "heroku.main stays in values"},
    "kage.inline": {"bot_token": "123:abc"},
    "kage.security": {"owner": [1]},
    "KageInfoMod": {"banner_url": "x"},
    "KageSettingsMod": {},
    "kage.forums": {"topics": {"kage-userbot": 7}},
    "Weather": {"city": "hikka.example"},
}


@pytest.mark.parametrize("indent", [None, 2, 4], ids=["default", "indent2", "indent4"])
def test_migrate_legacy_db_renames_core_keys(indent):
    migrated = migrate_legacy_db(json.dumps(LEGACY_DB, indent=indent))
    assert json.loads(migrated) == MIGRATED_DB


def test_migrate_legacy_db_compact_json():
    migrated = migrate_legacy_db(json.dumps(LEGACY_DB, separators=(",", ":")))
    assert json.loads(migrated) == MIGRATED_DB


def test_migrate_legacy_db_is_idempotent():
    once = migrate_legacy_db(json.dumps(LEGACY_DB))
    assert migrate_legacy_db(once) == once


def test_migrate_legacy_db_leaves_kage_db_untouched():
    text = json.dumps(MIGRATED_DB, indent=4)
    assert migrate_legacy_db(text) == text


@pytest.mark.parametrize(
    ("owner", "expected"),
    [
        ("heroku.main", "kage.main"),
        ("hikka.inline", "kage.inline"),
        ("hikka.translations.extra", "kage.translations.extra"),
        ("kage.main", "kage.main"),
        ("HerokuInfoMod", "HerokuInfoMod"),
        ("herokuX.main", "herokuX.main"),
        ("Weather", "Weather"),
        (None, None),
        (42, 42),
    ],
)
def test_kage_owner(owner, expected):
    assert _kage_owner(owner) == expected
