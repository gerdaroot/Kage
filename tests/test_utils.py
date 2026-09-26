import pytest

from kage.utils.entity import escape_html, remove_html
from kage.utils.other import format_file_size


@pytest.mark.parametrize(
    ("size", "expected"),
    [
        (0, "0 B"),
        (512, "512.0 B"),
        (1024, "1.0 KB"),
        (1536, "1.5 KB"),
        (1024**2, "1.0 MB"),
        (int(2.5 * 1024**3), "2.5 GB"),
        (3 * 1024**4, "3.0 TB"),
        (1024**5, "1024.0 TB"),
    ],
)
def test_format_file_size(size, expected):
    assert format_file_size(size) == expected


def test_escape_html():
    assert escape_html('<a href="x">&</a>') == '&lt;a href="x"&gt;&amp;&lt;/a&gt;'
    assert escape_html(42) == "42"


def test_escape_html_escapes_ampersand_first():
    assert escape_html("&lt;") == "&amp;lt;"


def test_remove_html_strips_telegram_tags():
    text = '<b>bold</b> <a href="tg://user?id=1">link</a> <code>x</code> <emoji document_id=1>😀</emoji>'
    assert remove_html(text) == "bold link x 😀"


def test_remove_html_keeps_plain_comparisons():
    assert remove_html("1 < 2 > 0") == "1 < 2 > 0"


def test_remove_html_keep_emojis():
    text = "<b>hi</b><emoji document_id=1>😀</emoji>"
    assert remove_html(text, keep_emojis=True) == "hi<emoji document_id=1>😀</emoji>"


def test_remove_html_escape():
    assert remove_html("<b>a & b</b> <i>c</i>", escape=True) == "a &amp; b c"
