import asyncio

import pytest

from kage.inline.types import BotInlineCall, InlineCall


class FakeTelegramCall:
    def __init__(self):
        self.answers = []

    async def answer(self, text, **kwargs):
        self.answers.append((text, kwargs))
        return True


def answer_via(call_type, *args, **kwargs):
    call = object.__new__(call_type)
    call.original_call = FakeTelegramCall()
    # not asyncio.run: it would unset the event loop kage.main installed at import
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(call.answer(*args, **kwargs))
    finally:
        loop.close()
    return call.original_call.answers[-1]


@pytest.mark.parametrize("call_type", [InlineCall, BotInlineCall])
def test_answer_strips_html_and_unescapes(call_type):
    text, _ = answer_via(
        call_type,
        '<tg-emoji emoji-id=1>✅</tg-emoji> <b>Saved</b> <code>a &amp; b</code> <a href="x">&lt;3</a>',
    )
    assert text == "✅ Saved a & b <3"


def test_answer_maps_show_alert_and_defaults():
    text, kwargs = answer_via(InlineCall, "plain", show_alert=True)
    assert text == "plain"
    assert kwargs == {"alert": True, "cache_time": 0, "url": None}


def test_answer_explicit_alert_wins():
    _, kwargs = answer_via(InlineCall, "x", show_alert=True, alert=False, cache_time=5)
    assert kwargs["alert"] is False
    assert kwargs["cache_time"] == 5


def test_answer_without_text():
    text, _ = answer_via(InlineCall)
    assert text is None
