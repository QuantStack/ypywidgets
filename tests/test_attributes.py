from __future__ import annotations
import asyncio

import pytest
from pycrdt import Text
from ypywidgets import Widget, reactive


class Widget1(Widget):
    foo = reactive("foo1")
    bar = reactive("bar1")
    baz: reactive[str | None] = reactive(None)


class Widget2(Widget):
    foo = reactive("")

    def watch_foo(self, old, new):
        print(f"foo changed: '{old}'->'{new}'")


@pytest.mark.asyncio
async def test_create_ydoc(synced_widgets):
    local_widget, remote_widget = await synced_widgets

    local_text = Text()
    local_widget._ydoc["text"] = local_text
    text = "hello world!"
    local_text += text

    remote_text = Text()
    remote_widget._ydoc["text"] = remote_text
    await asyncio.sleep(0.01)
    assert str(remote_text) == text


@pytest.mark.asyncio
@pytest.mark.parametrize("widget_factories", ((Widget1, Widget1),))
async def test_sync_attribute(widget_factories, synced_widgets):
    local_widget, remote_widget = await synced_widgets

    with pytest.raises(AttributeError):
        assert local_widget.wrong_attr1

    with pytest.raises(AttributeError):
        assert remote_widget.wrong_attr2

    local_widget.foo = "foo2"
    assert remote_widget.foo == "foo1"  # not synced yet
    await asyncio.sleep(0.01)  # wait for sync
    assert remote_widget.foo == "foo2"

    remote_widget.baz = "baz2"
    assert local_widget.baz is None  # not synced yet
    await asyncio.sleep(0.01)  # wait for sync
    assert local_widget.baz == "baz2"


@pytest.mark.asyncio
@pytest.mark.parametrize("widget_factories", ((Widget1, Widget2),))
async def test_watch_attribute(widget_factories, synced_widgets, capfd):
    local_widget, remote_widget = await synced_widgets

    local_widget.foo = "foo"

    # we're seeing the remote widget watch callback
    await asyncio.sleep(0.01)
    out, err = capfd.readouterr()
    assert out == "foo changed: ''->''\nfoo changed: ''->'foo'\n"
