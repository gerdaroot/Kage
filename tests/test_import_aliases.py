import pytest

from kage import loader


def resolve(name: str, monkeypatch) -> list[str]:
    requested = []
    # restored before asserting: pytest's failure reporting imports modules too
    with monkeypatch.context() as patch:
        patch.setattr(loader, "native_import", lambda name, *a, **kw: requested.append(name))
        loader.patched_import(name)
    return requested


@pytest.mark.parametrize(
    ("requested", "resolved"),
    [
        ("hikka", "kage"),
        ("hikka.utils", "kage.utils"),
        ("heroku", "kage"),
        ("heroku.inline.types", "kage.inline.types"),
        ("telethon", "herokutl"),
        ("telethon.tl.types", "herokutl.tl.types"),
        ("hikkatl.tl.functions", "herokutl.tl.functions"),
        ("heroku3", "heroku3"),
        ("herokutl", "herokutl"),
        ("hikkalls", "hikkalls"),
        ("hikka_extra", "hikka_extra"),
        ("kage.utils", "kage.utils"),
        ("requests", "requests"),
    ],
)
def test_patched_import_rewrites_legacy_names(monkeypatch, requested, resolved):
    assert resolve(requested, monkeypatch) == [resolved]


def test_legacy_imports_resolve_to_kage_objects():
    import herokutl.tl.types
    import kage.utils

    namespace = {}
    exec(
        "from hikka import utils as hikka_utils\n"
        "from heroku.utils import escape_html\n"
        "from telethon.tl.types import Message\n",
        namespace,
    )
    assert namespace["hikka_utils"] is kage.utils
    assert namespace["escape_html"] is kage.utils.escape_html
    assert namespace["Message"] is herokutl.tl.types.Message
